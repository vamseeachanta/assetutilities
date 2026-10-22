"""Independent source fixtures specify the clean-code gate's expected findings."""

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/hygiene/check_clean_code.py"


@pytest.fixture
def checker():
    spec = importlib.util.spec_from_file_location("clean_code", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "source, rules",
    [
        ("print('hello')\n", ["print"]),
        ("import builtins\nbuiltins.print('hello')\n", ["print"]),
        ("try:\n    work()\nexcept:\n    recover()\n", ["bare-except"]),
        ("try:\n    work()\nexcept ValueError:\n    recover()\n", []),
        ("# print('comment')\ntext = \"print('text')\"\n", []),
        ("text = '''\n<<<<<<< example\n=======\n>>>>>>> example\n'''\n", []),
        ("<<<<<<< branch\nx = 1\n=======\nx = 2\n>>>>>>> branch\n", ["syntax"]),
        ("def broken(:\n", ["syntax"]),
        ("return\n", ["syntax"]),
        ("break\n", ["syntax"]),
        ("def f(a, a): pass\n", ["syntax"]),
    ],
)
def test_source_rules(checker, source, rules):
    """Each literal statement above independently determines the expected rule."""
    assert [item["rule"] for item in checker.inspect_source(source)] == rules


def run_checker(root, baseline):
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        env.pop(name, None)
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--root",
            str(root),
            "--baseline",
            str(baseline),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


@pytest.fixture
def tree(tmp_path):
    source = tmp_path / "src/assetutilities/sample.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"print('legacy')\n")
    baseline = tmp_path / "baseline.json"
    return tmp_path, source, baseline


def save_baseline(checker, tree):
    root, _, baseline = tree
    baseline.write_bytes(json.dumps(checker.scan_tree(root)).encode("utf-8"))


def test_exact_legacy_inventory_passes(checker, tree):
    save_baseline(checker, tree)
    result = run_checker(tree[0], tree[2])
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


@pytest.mark.parametrize(
    "source, line",
    [
        ("return\n", 1),
        ("\nbreak\n", 2),
        ("def f(a, a): pass\n", 1),
    ],
    ids=["top-level-return", "top-level-break", "duplicate-argument"],
)
def test_cli_rejects_compilation_errors(tree, source, line):
    root, path, baseline = tree
    path.write_bytes(source.encode("utf-8"))
    baseline.write_bytes(b"[]")
    result = run_checker(root, baseline)
    assert result.returncode == 1, result.stdout + result.stderr
    assert (
        f"src/assetutilities/sample.py:{line}: invalid Python syntax" in result.stdout
    )


@pytest.mark.parametrize(
    "payload",
    [
        b"message = 'caf\xc3\xa9'\nraise RuntimeError(message)\n",
        b"\xef\xbb\xbfraise RuntimeError('must not execute')\n",
        b"# coding: latin-1\nmessage = 'caf\xe9'\nraise RuntimeError(message)\n",
    ],
    ids=["utf8", "utf8-bom", "coding-cookie"],
)
def test_cli_compiles_source_without_execution(tree, payload):
    root, path, baseline = tree
    path.write_bytes(payload)
    baseline.write_bytes(b"[]")
    result = run_checker(root, baseline)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


@pytest.mark.parametrize("kind", ["file", "directory", "source-root"])
@pytest.mark.parametrize("tag", [0xA000000C, 0xA0000003], ids=["symlink", "junction"])
def test_reparse_points_fail_closed(checker, tree, monkeypatch, kind, tag):
    """Windows symlinks and junctions must not enter the scan."""
    root, source, _ = tree
    target = {"file": source, "directory": source.parent, "source-root": root / "src"}[
        kind
    ]
    original_lstat = Path.lstat

    def lstat(path, *args, **kwargs):
        result = original_lstat(path, *args, **kwargs)
        if path == target:
            return SimpleNamespace(
                st_mode=result.st_mode,
                st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
                st_reparse_tag=tag,
            )
        return result

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="link"):
        checker.scan_tree(root)


@pytest.mark.parametrize(
    "source",
    [
        "print('legacy')\nprint('legacy')\n",
        "print('changed')\n",
        "value = 1\n",
        "<<<<<<< branch\n",
    ],
)
def test_inventory_cannot_hide_changes(checker, tree, source):
    """Two identical calls exceed one entry; changed or removed calls mismatch."""
    save_baseline(checker, tree)
    tree[1].write_bytes(source.encode("utf-8"))
    assert run_checker(tree[0], tree[2]).returncode == 1


def test_line_only_movement_preserves_fingerprint(checker, tree):
    save_baseline(checker, tree)
    tree[1].write_bytes(b"# explanation\n\nprint( 'legacy' )\n")
    assert run_checker(tree[0], tree[2]).returncode == 0


@pytest.mark.parametrize(
    "payload, cause",
    [
        ("{", "invalid JSON"),
        ("{}", "baseline must be a list"),
        ('[{"rule": "syntax"}]', "invalid baseline record"),
    ],
)
def test_invalid_baseline_fails_closed(tree, payload, cause):
    tree[2].write_bytes(payload.encode("utf-8"))
    result = run_checker(tree[0], tree[2])
    assert result.returncode == 1
    assert "baseline.json" in result.stderr
    assert cause in result.stderr
    assert str(tree[0]) not in result.stdout + result.stderr


def test_missing_source_root_fails_closed(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_bytes(b"[]")
    result = run_checker(tmp_path, baseline)
    assert result.returncode == 1
    assert "src" in result.stderr and "missing" in result.stderr
    assert str(tmp_path) not in result.stdout + result.stderr


def test_repository_inventory():
    result = run_checker(ROOT, ROOT / "scripts/hygiene/clean_code_baseline.json")
    assert result.returncode == 0, result.stdout + result.stderr


def test_fingerprint_uses_version_independent_fields(checker):
    """The AST for print('legacy') has one Name and one string Constant.

    Empty optional fields are excluded explicitly: ast.dump changed how empty
    fields are displayed across Python versions and is not a portable inventory.
    """
    expected = {
        "type": "Call",
        "func": {"type": "Name", "id": "print", "ctx": {"type": "Load"}},
        "args": [{"type": "Constant", "value": "legacy"}],
    }
    digest = hashlib.sha256(
        json.dumps(expected, sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert checker.inspect_source("print('legacy')")[0]["fingerprint"] == digest


@pytest.mark.parametrize(
    "actual_count, expected_count, exit_code",
    [
        (1, 1, 0),
        (2, 1, 1),
        (0, 1, 1),
        (1, 0, 1),
        (0, 0, 0),
    ],
)
def test_cli_occurrence_accounting(
    checker, monkeypatch, actual_count, expected_count, exit_code
):
    """Hand calculation: equal counts pass; positive or negative deltas fail."""
    item = {"path": "src/example.py", **checker.inspect_source("print('x')")[0]}
    monkeypatch.setattr(
        Path, "read_text", lambda *a, **kw: json.dumps([item] * expected_count)
    )
    monkeypatch.setattr(checker, "scan_tree", lambda root: [item] * actual_count)
    assert checker.main([]) == exit_code


@pytest.mark.parametrize("payload", ["{", "{}", '[{"rule": "syntax"}]'])
def test_cli_invalid_inventory(checker, monkeypatch, payload):
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: payload)
    assert checker.main([]) == 1


def test_cli_syntax_cannot_be_inventoried(checker, monkeypatch):
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: "[]")
    monkeypatch.setattr(
        checker,
        "scan_tree",
        lambda root: [{"path": "src/example.py", "rule": "syntax", "fingerprint": "1"}],
    )
    assert checker.main([]) == 1


@pytest.mark.parametrize(
    "payload",
    [b"\x00", b"\xef\xbb\xbf# coding: latin-1\n", b"-" * 200_000 + b"0\n"],
    ids=["null-byte", "conflicting-encoding", "parser-exhaustion"],
)
def test_cli_syntax_without_line_has_relative_diagnostic(tree, payload):
    root, source, baseline = tree
    source.write_bytes(payload)
    baseline.write_bytes(b"[]")
    result = run_checker(root, baseline)
    assert result.returncode == 1
    assert "src/assetutilities/sample.py:?: invalid Python syntax" in result.stdout
    assert "Traceback" not in result.stderr
    assert str(root) not in result.stdout + result.stderr


@pytest.mark.parametrize("failure", [MemoryError, RecursionError])
@pytest.mark.parametrize("phase", ["parse", "compile"])
def test_parser_resource_errors_are_syntax_findings(
    checker, monkeypatch, failure, phase
):
    def exhausted(*args, **kwargs):
        raise failure

    if phase == "parse":
        monkeypatch.setattr(checker, "ast", SimpleNamespace(parse=exhausted))
    else:
        monkeypatch.setattr(checker, "compile", exhausted, raising=False)
    findings = checker.inspect_source(b"value = 1\n")
    assert len(findings) == 1
    assert findings[0]["rule"] == "syntax"
    assert findings[0]["fingerprint"] == "?"


@pytest.mark.parametrize("kind", ["file", "directory", "source-root"])
def test_non_link_reparse_points_are_scanned(checker, tree, monkeypatch, kind):
    root, source, _ = tree
    target = {"file": source, "directory": source.parent, "source-root": root / "src"}[
        kind
    ]
    original_lstat = Path.lstat

    def lstat(path, *args, **kwargs):
        result = original_lstat(path, *args, **kwargs)
        if path == target:
            return SimpleNamespace(
                st_mode=result.st_mode,
                st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
                st_reparse_tag=0x8000001B,
            )
        return result

    monkeypatch.setattr(Path, "lstat", lstat)
    findings = checker.scan_tree(root)
    assert len(findings) == 1
    assert findings[0]["path"] == "src/assetutilities/sample.py"
    assert findings[0]["rule"] == "print"


def test_resolved_source_escape_fails_closed(checker, tree, monkeypatch):
    root, source, _ = tree
    original_resolve = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == source:
            return root.parent / "outside.py"
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="escapes"):
        checker.scan_tree(root)


def test_link_diagnostic_names_relative_source(checker, tree, monkeypatch, capsys):
    root, source, baseline = tree
    baseline.write_bytes(b"[]")
    original_is_symlink = Path.is_symlink

    def is_symlink(path):
        return path == source or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", is_symlink)
    assert checker.main(["--root", str(root), "--baseline", str(baseline)]) == 1
    result = capsys.readouterr()
    assert "src/assetutilities/sample.py" in result.err
    assert "link" in result.err
    assert str(root) not in result.out + result.err


def test_unreadable_source_diagnostic_has_path_and_cause(
    checker, tree, monkeypatch, capsys
):
    root, source, baseline = tree
    baseline.write_bytes(b"[]")

    def denied(path):
        raise PermissionError(13, "permission denied", str(path))

    monkeypatch.setattr(Path, "read_bytes", denied)
    assert checker.main(["--root", str(root), "--baseline", str(baseline)]) == 1
    result = capsys.readouterr()
    assert "src/assetutilities/sample.py" in result.err
    assert "PermissionError" in result.err
    assert str(root) not in result.out + result.err


def test_missing_baseline_diagnostic_has_path_and_cause(tree):
    root, _, baseline = tree
    result = run_checker(root, baseline)
    assert result.returncode == 1
    assert "baseline.json" in result.stderr
    assert "FileNotFoundError" in result.stderr
    assert str(root) not in result.stdout + result.stderr
