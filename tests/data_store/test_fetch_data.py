"""Offline checks for manifest-based data restoration."""

import hashlib
import importlib.util
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "fetch_data.py"


@pytest.fixture
def fetch():
    assert SCRIPT.exists(), "fetch utility has not been implemented"
    spec = importlib.util.spec_from_file_location("fetch_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repository(tmp_path, monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("ACE_DATA_HOST", raising=False)
    monkeypatch.delenv("ACE_DATA_ROOT", raising=False)
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "data-manifest").mkdir()
    store = tmp_path / "store"
    payload = b"column\n1\n2\n"
    digest = hashlib.sha256(payload).hexdigest()
    blob = store / "data/assetutilities/blobs/sha256" / digest[:2] / (digest + ".csv")
    blob.parent.mkdir(parents=True)
    blob.write_bytes(payload)
    manifest = root / "data-manifest/MANIFEST.tsv"
    manifest.write_text(
        "# offline fixture\npath\tbytes\tsha256\tdisposition\tblob\tredownloadable\tsecond_copy\n"
        f"fixtures/data.csv\t{len(payload)}\t{digest}\tMOVE\tblobs/sha256/{digest[:2]}/{digest}.csv\tfalse\ttest-copy\n"
        f"fixtures/original.csv\t{len(payload)}\t{digest}\tSHRINK-ORIGINAL\tblobs/sha256/{digest[:2]}/{digest}.csv\tfalse\ttest-copy\n"
        f"outputs/old.csv\t{len(payload)}\t{digest}\tDELETE-SUPERSEDED\t-\tfalse\tnot-required\n",
        encoding="utf-8",
    )
    return root, store, blob, payload


def test_restore_glob_and_verify(fetch, repository, monkeypatch):
    root, store, _, payload = repository
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["fixtures/*.csv"], root) == 0
    assert (root / "fixtures/data.csv").read_bytes() == payload
    assert (root / "fixtures/original.csv").read_bytes() == payload
    assert not (root / "outputs/old.csv").exists()
    assert fetch.main(["--verify", "--all"], root) == 0


def test_corrupt_blob_preserves_existing_file(fetch, repository, monkeypatch):
    root, store, blob, _ = repository
    target = root / "fixtures/data.csv"
    target.parent.mkdir()
    target.write_bytes(b"existing")
    blob.write_bytes(b"corrupt")
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["fixtures/data.csv"], root) == 1
    assert target.read_bytes() == b"existing"
    assert list(target.parent.iterdir()) == [target]


def test_unavailable_store_is_noop(fetch, repository, monkeypatch, capsys):
    root, _, _, _ = repository
    monkeypatch.setenv("ACE_DATA_ROOT", str(root / "missing-store"))
    assert fetch.main(["--all"], root) == 0
    assert "unavailable" in capsys.readouterr().out.lower()
    assert not (root / "fixtures").exists()


def test_tracked_destination_is_protected(fetch, repository, monkeypatch):
    root, store, _, _ = repository
    target = root / "fixtures/data.csv"
    target.parent.mkdir()
    target.write_bytes(b"tracked")
    subprocess.run(["git", "-C", str(root), "add", "fixtures/data.csv"], check=True)
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["fixtures/data.csv"], root) == 1
    assert target.read_bytes() == b"tracked"


@pytest.mark.parametrize(
    "unsafe",
    [
        "../escape.csv",
        "/escape.csv",
        "dir/../escape.csv",
        "C:/escape.csv",
        "dir\\escape.csv",
    ],
)
def test_manifest_rejects_unsafe_paths(fetch, repository, monkeypatch, unsafe):
    root, store, _, _ = repository
    manifest = root / "data-manifest/MANIFEST.tsv"
    manifest.write_text(manifest.read_text().replace("fixtures/data.csv", unsafe))
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["--all"], root) == 1
    assert not (root / "fixtures").exists()


def test_symlink_parent_is_rejected(fetch, repository, monkeypatch, tmp_path):
    root, store, _, _ = repository
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "fixtures").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["fixtures/data.csv"], root) == 1
    assert list(outside.iterdir()) == []


def test_missing_blob_fails_when_store_exists(fetch, repository, monkeypatch):
    root, store, blob, _ = repository
    blob.unlink()
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["fixtures/data.csv"], root) == 1


def test_list_needs_no_store(fetch, repository, capsys):
    root, _, _, _ = repository
    assert fetch.main(["--list"], root) == 0
    output = capsys.readouterr().out
    assert "fixtures/data.csv" in output
    assert "outputs/old.csv" not in output


def test_verify_detects_modified_restored_file(fetch, repository, monkeypatch):
    root, store, _, _ = repository
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["fixtures/data.csv"], root) == 0
    (root / "fixtures/data.csv").write_bytes(b"changed")
    assert fetch.main(["--verify", "fixtures/data.csv"], root) == 1


def test_remote_option_host_rejected(fetch, repository, monkeypatch):
    root, _, _, _ = repository
    monkeypatch.setenv("ACE_DATA_ROOT", "store")
    monkeypatch.setenv("ACE_DATA_HOST", "-invalid")
    assert fetch.main(["--all"], root) == 1


def test_fetch_command_exists():
    assert SCRIPT.exists(), "fetch command is missing"


def test_remote_restore_quotes_paths(fetch, repository, monkeypatch):
    root, store, blob, payload = repository
    monkeypatch.setenv("ACE_DATA_ROOT", "remote store's root")
    monkeypatch.setenv("ACE_DATA_HOST", "destination")
    original_run = subprocess.run
    commands = []

    def exchange(command, **kwargs):
        if command[0] != "ssh":
            return original_run(command, **kwargs)
        commands.append(command)
        if command[-1].startswith("cat -- "):
            kwargs["stdout"].write(blob.read_bytes())
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(fetch.subprocess, "run", exchange)
    assert fetch.main(["fixtures/data.csv"], root) == 0
    assert (root / "fixtures/data.csv").read_bytes() == payload
    assert commands[0][-1] == "test -d " + fetch.shlex.quote("remote store's root")
    assert commands[1][-1].startswith("cat -- '")


def test_unreachable_remote_noop(fetch, repository, monkeypatch):
    root, _, _, _ = repository
    monkeypatch.setenv("ACE_DATA_ROOT", "unavailable-store")
    monkeypatch.setenv("ACE_DATA_HOST", "destination")
    original_run = subprocess.run

    def exchange(command, **kwargs):
        if command[0] != "ssh":
            return original_run(command, **kwargs)
        return subprocess.CompletedProcess(command, 255, b"", b"")

    monkeypatch.setattr(fetch.subprocess, "run", exchange)
    assert fetch.main(["--all"], root) == 0
    assert not (root / "fixtures").exists()


@pytest.mark.parametrize(
    "relative,suffix",
    [("fixtures/plain", ""), ("fixtures/.csv", ""), ("fixtures/data.CSV", ".csv")],
)
def test_blob_extension_matches_layout(fetch, relative, suffix):
    digest = "0" * 64
    row = {"path": relative, "sha256": digest}
    assert fetch.blob_relative(row).endswith(digest + suffix)


def test_unavailable_store_does_not_inspect_destinations(fetch, repository):
    root, _, _, _ = repository
    target = root / "fixtures/data.csv"
    target.parent.mkdir()
    target.write_bytes(b"tracked")
    subprocess.run(["git", "-C", str(root), "add", "fixtures/data.csv"], check=True)
    assert fetch.main(["--all"], root) == 0
    assert target.read_bytes() == b"tracked"


def test_restore_dot_leading_file_without_extension(fetch, repository, monkeypatch):
    root, store, blob, payload = repository
    digest = hashlib.sha256(payload).hexdigest()
    blob.rename(blob.with_name(digest))
    manifest = root / "data-manifest/MANIFEST.tsv"
    manifest.write_text(
        manifest.read_text()
        .replace("fixtures/data.csv", "fixtures/.hidden")
        .replace(f"{digest}.csv", digest, 1)
    )
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["fixtures/.hidden"], root) == 0
    assert (root / "fixtures/.hidden").read_bytes() == payload


def test_public_manifest_records_placement_and_copy_status():
    import csv

    root = SCRIPT.parents[1]
    manifest = root / "data-manifest/MANIFEST.tsv"
    with manifest.open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(
            (line for line in stream if not line.startswith("#")), delimiter="\t"
        )
        assert rows.fieldnames == [
            "path",
            "bytes",
            "sha256",
            "disposition",
            "blob",
            "redownloadable",
            "second_copy",
        ]
        for row in rows:
            if row["disposition"] in {"MOVE", "SHRINK-ORIGINAL"}:
                assert row["blob"].startswith("blobs/sha256/")
                assert row["redownloadable"] == "false"
                assert row["second_copy"] == "verified-2026-10-11;not-rechecked"
            else:
                assert row["blob"] == "-"
                assert row["second_copy"] == "not-required"


@pytest.mark.parametrize(
    "selection", [["fixtures/data.csv"], ["--all"], ["--verify", "--all"]]
)
def test_require_store_unavailable_preserves_files(
    fetch, repository, capsys, selection
):
    root, _, _, _ = repository
    target = root / "fixtures/data.csv"
    target.parent.mkdir()
    target.write_bytes(b"existing")
    before = {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    assert fetch.main(["--require-store", *selection], root) != 0
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == (
        "Data store unavailable; set ACE_DATA_ROOT or ACE_DATA_HOST with ACE_DATA_ROOT. No files changed.\n"
    )
    after = {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    assert after == before
    assert not (root / "fixtures/original.csv").exists()


def test_require_store_available_restores_and_verifies(fetch, repository, monkeypatch):
    root, store, _, payload = repository
    monkeypatch.setenv("ACE_DATA_ROOT", str(store))
    assert fetch.main(["--require-store", "--all"], root) == 0
    assert (root / "fixtures/data.csv").read_bytes() == payload
    assert (root / "fixtures/original.csv").read_bytes() == payload
    assert fetch.main(["--require-store", "--verify", "--all"], root) == 0


def test_require_store_list_needs_no_store(fetch, repository, capsys):
    root, _, _, _ = repository
    assert fetch.main(["--require-store", "--list"], root) == 0
    output = capsys.readouterr()
    assert "fixtures/data.csv" in output.out
    assert output.err == ""
