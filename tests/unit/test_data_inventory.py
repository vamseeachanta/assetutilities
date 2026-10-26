"""Read-only consolidation inventory: synthetic inputs, exact byte arithmetic."""

import errno
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from html.parser import HTMLParser

import pytest

from assetutilities.data_inventory import inventory, main


def test_inventory_totals_and_relative_paths(tmp_path):
    """Hand calculation: b'abc' + b'xy' + b'' = 3 + 2 + 0 = 5 bytes."""
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "a.txt").write_bytes(b"abc")
    (tmp_path / "b.txt").write_bytes(b"xy")
    (tmp_path / "empty").write_bytes(b"")

    report = inventory(tmp_path)

    assert report["status"] == "COMPLETE"
    assert report["file_count"] == 3
    assert report["logical_bytes"] == 5
    assert report["files"] == [
        {"path": "b.txt", "size_bytes": 2},
        {"path": "empty", "size_bytes": 0},
        {"path": "nested/a.txt", "size_bytes": 3},
    ]
    assert report["duplicate_status"] == "NOT_EVALUATED"


def test_hash_groups_require_content_equality(tmp_path):
    """Hand calculation: lengths 3 + 3 + 3 = 9; only two b'abc' match.

    SHA-256('abc') is the first input/output in NIST's SHA-256 example
    (undated), https://csrc.nist.gov/CSRC/media/Projects/
    Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf.
    """
    (tmp_path / "copy").write_bytes(b"abc")
    (tmp_path / "original").write_bytes(b"abc")
    (tmp_path / "different").write_bytes(b"xyz")

    report = inventory(tmp_path, hash_contents=True)

    assert report["logical_bytes"] == 9
    assert report["duplicate_status"] == "EVALUATED"
    assert report["duplicate_groups"] == [
        {
            "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            "size_bytes": 3,
            "paths": ["copy", "original"],
        }
    ]


def test_module_cli_json_and_source_preservation(tmp_path):
    """Hand calculation: b'abc' twice = 3 + 3 = 6 logical bytes."""
    root = tmp_path / "data"
    root.mkdir()
    for name in ("a", "b"):
        (root / name).write_bytes(b"abc")
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[2] / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "assetutilities.data_inventory", str(root), "--hash"],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["file_count"] == 2
    assert report["logical_bytes"] == 6
    assert report["duplicate_groups"][0]["paths"] == ["a", "b"]
    assert str(tmp_path) not in result.stdout + result.stderr
    assert sorted(path.name for path in root.iterdir()) == ["a", "b"]
    assert [(root / name).read_bytes() for name in ("a", "b")] == [b"abc", b"abc"]


@pytest.mark.parametrize("kind", ["complete", "partial", "invalid"])
def test_cli_writes_to_streams_without_print(tmp_path, kind, monkeypatch, capsys):
    """All exit paths retain newline-terminated output without print calls."""
    root = tmp_path / "data"
    if kind != "invalid":
        root.mkdir()
        blocked = root / "blocked"
        blocked.write_bytes(b"abc")
    if kind == "partial":
        real_lstat = Path.lstat

        def lstat(path, *args, **kwargs):
            if path == blocked:
                raise PermissionError(errno.EACCES, "denied", str(path))
            return real_lstat(path, *args, **kwargs)

        monkeypatch.setattr(Path, "lstat", lstat)

    def forbid_print(*args, **kwargs):
        raise AssertionError("CLI output must use stream writes")

    monkeypatch.setattr("builtins.print", forbid_print)
    assert main([str(root)]) == {"complete": 0, "partial": 1, "invalid": 2}[kind]
    captured = capsys.readouterr()
    if kind == "invalid":
        assert captured.out == ""
        assert captured.err == (
            "input root must be an existing directory, not a symlink\n"
        )
    else:
        assert captured.err == ""
        report = json.loads(captured.out)
        assert report["status"] == kind.upper()
        assert report["errors"] == (
            [{"path": "blocked", "error": "EACCES"}] if kind == "partial" else []
        )
        assert captured.out == json.dumps(report, indent=2, sort_keys=True) + "\n"
    assert str(tmp_path) not in captured.out + captured.err


def test_unreadable_subdirectory_is_partial(tmp_path, monkeypatch, capsys):
    """Hand calculation: readable b'abc' contributes 3; unreadable is unknown."""
    (tmp_path / "visible").write_bytes(b"abc")
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    real_scandir = os.scandir

    def scandir(path):
        if Path(path) == blocked:
            raise PermissionError(errno.EACCES, "denied", str(blocked))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)
    assert main([str(tmp_path), "--hash"]) == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "PARTIAL"
    assert report["logical_bytes"] == 3
    assert report["errors"] == [{"path": "blocked", "error": "EACCES"}]
    assert report["duplicate_status"] == "NOT_EVALUATED"
    assert report["duplicate_groups"] == []
    assert str(tmp_path) not in captured.out + captured.err


def test_hash_read_failure_keeps_metadata_but_no_duplicate_claim(tmp_path, monkeypatch):
    """Hand calculation: the two regular-file lengths remain 3 + 3 = 6."""
    for name in ("readable", "blocked"):
        (tmp_path / name).write_bytes(b"abc")
    real_open = Path.open

    def open_file(path, *args, **kwargs):
        if path.name == "blocked":
            raise PermissionError(errno.EACCES, "denied", str(path))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_file)
    report = inventory(tmp_path, hash_contents=True)
    assert report["status"] == "PARTIAL"
    assert report["logical_bytes"] == 6
    assert report["errors"] == [{"path": "blocked", "error": "EACCES"}]
    assert "sha256" not in report["files"][0]
    assert report["duplicate_status"] == "NOT_EVALUATED"
    assert report["duplicate_groups"] == []


def test_file_changed_before_read_is_not_fingerprinted(tmp_path, monkeypatch):
    """A changed length invalidates the fingerprint; no value is guessed."""
    path = tmp_path / "changing"
    path.write_bytes(b"abc")
    real_open = Path.open

    def open_file(target, *args, **kwargs):
        if target == path and args == ("rb",):
            with real_open(target, "ab") as stream:
                stream.write(b"x")
        return real_open(target, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_file)
    report = inventory(tmp_path, hash_contents=True)
    assert report["status"] == "PARTIAL"
    assert report["errors"] == [{"path": "changing", "error": "ESTALE"}]
    assert "sha256" not in report["files"][0]
    assert report["duplicate_status"] == "NOT_EVALUATED"
    assert report["duplicate_groups"] == []


def test_file_changed_during_read_is_not_fingerprinted(tmp_path, monkeypatch):
    """A read-time append must be detected by the post-read descriptor check."""
    path = tmp_path / "changing"
    for name in ("changing", "copy", "original"):
        (tmp_path / name).write_bytes(b"abc")
    real_open = Path.open
    changed = False

    def open_file(target, *args, **kwargs):
        stream = real_open(target, *args, **kwargs)
        if target == path and args == ("rb",):
            real_read = stream.read

            def read(size):
                nonlocal changed
                chunk = real_read(size)
                if not changed:
                    with real_open(target, "ab") as writer:
                        writer.write(b"x")
                    changed = True
                return chunk

            monkeypatch.setattr(stream, "read", read)
        return stream

    monkeypatch.setattr(Path, "open", open_file)
    report = inventory(tmp_path, hash_contents=True)
    assert changed
    assert report["status"] == "PARTIAL"
    assert report["errors"] == [{"path": "changing", "error": "ESTALE"}]
    assert "sha256" not in report["files"][0]
    assert report["duplicate_status"] == "NOT_EVALUATED"
    assert report["duplicate_groups"] == []


def test_path_replaced_after_read_is_not_fingerprinted(tmp_path, monkeypatch):
    """Replace after closing so only the final path signature check can fail."""
    root = tmp_path / "data"
    root.mkdir()
    path = root / "changing"
    for name in ("changing", "copy", "original"):
        (root / name).write_bytes(b"abc")
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"xyz")
    real_open = Path.open
    replaced = False

    @contextmanager
    def open_file(target, *args, **kwargs):
        nonlocal replaced
        with real_open(target, *args, **kwargs) as stream:
            yield stream
        if target == path and args == ("rb",):
            replacement.replace(path)
            replaced = True

    monkeypatch.setattr(Path, "open", open_file)
    report = inventory(root, hash_contents=True)
    assert replaced
    assert report["status"] == "PARTIAL"
    assert report["errors"] == [{"path": "changing", "error": "ESTALE"}]
    assert "sha256" not in report["files"][0]
    assert report["duplicate_status"] == "NOT_EVALUATED"
    assert report["duplicate_groups"] == []


def test_links_are_skipped_and_hardlinks_are_logical_paths(tmp_path):
    """Hand calculation: one b'abc' inode with two names = 3 + 3 logical bytes."""
    root = tmp_path / "data"
    root.mkdir()
    (root / "original").write_bytes(b"abc")
    os.link(root / "original", root / "hardlink")
    (tmp_path / "outside").write_bytes(b"secret")
    (root / "linked-file").symlink_to(tmp_path / "outside")
    (root / "linked-dir").symlink_to(tmp_path, target_is_directory=True)
    (root / "broken").symlink_to(tmp_path / "missing")
    report = inventory(root, hash_contents=True)
    assert report["status"] == "COMPLETE"
    assert report["file_count"] == 2
    assert report["logical_bytes"] == 6
    assert report["skipped"] == [
        {"path": "broken", "reason": "symlink"},
        {"path": "linked-dir", "reason": "symlink"},
        {"path": "linked-file", "reason": "symlink"},
    ]


@pytest.mark.parametrize("kind", ["missing", "file", "symlink"])
def test_invalid_root_is_a_redacted_input_error(tmp_path, kind, capsys):
    root = tmp_path / kind
    if kind == "file":
        root.write_bytes(b"abc")
    elif kind == "symlink":
        root.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="input root"):
        inventory(root)
    assert main([str(root)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "input root" in captured.err
    assert str(tmp_path) not in captured.err


@pytest.mark.parametrize("hash_contents", [False, True])
def test_empty_directory_is_complete(tmp_path, hash_contents):
    """Hand calculation: the sum over no regular files is zero."""
    report = inventory(tmp_path, hash_contents=hash_contents)
    assert report["status"] == "COMPLETE"
    assert report["logical_bytes"] == 0
    assert report["file_count"] == 0
    assert report["files"] == []
    assert report["duplicate_groups"] == []


def test_metadata_scan_never_opens_file_contents(tmp_path, monkeypatch):
    """Hand calculation: b'abc' has length 3 without opening its contents."""
    (tmp_path / "data").write_bytes(b"abc")

    def forbid_open(*args, **kwargs):
        raise AssertionError("metadata scan opened contents")

    monkeypatch.setattr(Path, "open", forbid_open)
    assert inventory(tmp_path)["logical_bytes"] == 3


def test_disappeared_file_is_partial(tmp_path, monkeypatch):
    """A file without a readable length contributes no guessed byte value."""
    vanished = tmp_path / "vanished"
    vanished.write_bytes(b"abc")
    real_lstat = Path.lstat

    def lstat(path, *args, **kwargs):
        if path == vanished:
            raise FileNotFoundError(errno.ENOENT, "missing", str(path))
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", lstat)
    report = inventory(tmp_path)
    assert report["status"] == "PARTIAL"
    assert report["file_count"] == 0
    assert report["logical_bytes"] == 0
    assert report["errors"] == [{"path": "vanished", "error": "ENOENT"}]


def test_fifo_is_listed_without_opening(tmp_path):
    """No regular files means zero logical bytes; a FIFO has no file length."""
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO creation is unavailable on this platform")
    os.mkfifo(tmp_path / "pipe")
    report = inventory(tmp_path, hash_contents=True)
    assert report["status"] == "COMPLETE"
    assert report["logical_bytes"] == 0
    assert report["skipped"] == [{"path": "pipe", "reason": "special_file"}]


def test_zero_length_duplicates_are_valid_groups(tmp_path):
    """Hand calculation: two empty files = 0 + 0 logical bytes, one group."""
    for name in ("a", "b"):
        (tmp_path / name).write_bytes(b"")
    report = inventory(tmp_path, hash_contents=True)
    assert report["logical_bytes"] == 0
    assert len(report["duplicate_groups"]) == 1
    assert report["duplicate_groups"][0]["paths"] == ["a", "b"]
    assert report["duplicate_groups"][0]["size_bytes"] == 0


def test_repeat_reports_are_deterministic(tmp_path):
    """Hand calculation: b'abc' three times = 3 + 3 + 3 = 9 bytes."""
    for name in ("z", "a", "m"):
        (tmp_path / name).write_bytes(b"abc")
    first = inventory(tmp_path, hash_contents=True)
    second = inventory(tmp_path, hash_contents=True)
    assert first == second
    assert first["logical_bytes"] == 9
    assert first["duplicate_groups"][0]["paths"] == ["a", "m", "z"]


def test_relative_root_and_unusual_names(tmp_path, monkeypatch):
    """Hand calculation: b'abc' is 3 bytes regardless of its filename."""
    root = tmp_path / "data"
    root.mkdir()
    name = "space and\nnewline-\N{GREEK SMALL LETTER ALPHA}"
    (root / name).write_bytes(b"abc")
    monkeypatch.chdir(tmp_path)
    report = inventory("data", hash_contents=True)
    assert report["files"][0]["path"] == name
    assert report["logical_bytes"] == 3
    assert json.loads(json.dumps(report)) == report


def test_same_length_replacement_invalidates_hash(tmp_path, monkeypatch):
    """A replaced file is not the inode whose length was inventoried."""
    path = tmp_path / "changing"
    replacement = tmp_path / "replacement"
    path.write_bytes(b"abc")
    replacement.write_bytes(b"xyz")
    real_open = Path.open

    def open_file(target, *args, **kwargs):
        if target == path and args == ("rb",):
            replacement.replace(path)
        return real_open(target, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_file)
    report = inventory(tmp_path, hash_contents=True)
    assert report["status"] == "PARTIAL"
    assert {"path": "changing", "error": "ESTALE"} in report["errors"]
    assert "sha256" not in report["files"][0]
    assert report["duplicate_status"] == "NOT_EVALUATED"
    assert report["duplicate_groups"] == []


def test_documented_worked_example(tmp_path, monkeypatch, capsys):
    """Run the guide's example; hand result is 3 + 3 + 2 = 8 bytes."""

    class CodeBlocks(HTMLParser):
        def __init__(self):
            super().__init__()
            self.blocks = []
            self.active = False

        def handle_starttag(self, tag, attrs):
            if tag == "code":
                self.active = True
                self.blocks.append("")

        def handle_endtag(self, tag):
            if tag == "code":
                self.active = False

        def handle_data(self, data):
            if self.active:
                self.blocks[-1] += data

    guide = Path(__file__).parents[2] / "docs" / "modules" / "data_inventory.html"
    parser = CodeBlocks()
    parser.feed(guide.read_text(encoding="utf-8"))
    example = next(code for code in parser.blocks if "root.mkdir()" in code)
    monkeypatch.chdir(tmp_path)
    exec(compile(example, guide.name, "exec"), {})
    assert capsys.readouterr().out == "8 ['a.txt', 'copy.txt']\n"


def test_root_metadata_error_is_redacted(tmp_path, monkeypatch, capsys):
    """Unavailable input-root metadata cannot establish a valid input directory."""
    real_lstat = Path.lstat

    def lstat(path, *args, **kwargs):
        if path == tmp_path:
            raise PermissionError(errno.EACCES, "denied", str(path))
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", lstat)
    assert main([str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "input root" in captured.err
    assert str(tmp_path) not in captured.err
