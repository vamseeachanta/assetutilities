"""Regression coverage for metadata collection used by the gallery."""

import hashlib
import json
from pathlib import Path

import pytest

from assetutilities.workflow_api import ResultLocator, runner
from assetutilities.workflow_api.envelope import result_hash
from assetutilities.workflow_api.runner import extract_result


@pytest.mark.parametrize("reader", ["registry", "example"])
def test_workflow_yaml_is_utf8(tmp_path, monkeypatch, reader):
    registry = tmp_path / "docs/registry/workflows.yaml"
    registry.parent.mkdir(parents=True)
    for source in (registry, tmp_path / "example.yml"):
        with source.open("w", encoding="utf-8", newline="\n") as output:
            output.write("label: · ×\n")
    original_open = open

    def locale_open(path, encoding=None):
        return original_open(path, encoding=encoding or "cp1252")

    monkeypatch.setattr(runner, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(runner, "open", locale_open, raising=False)
    if reader == "registry":
        cfg = runner.load_registry()
    else:
        cfg = runner.build_cfg({"basename": "synthetic", "input": "example.yml"}, None)
    assert cfg["label"] == "· ×"


def test_empty_results_warning_omits_temporary_root(tmp_path):
    cfg = {"Analysis": {"result_folder": str(tmp_path / "results")}}
    payload, warnings = extract_result(cfg, ResultLocator(), str(tmp_path))
    assert payload["outputs"] == []
    assert len(warnings) == 1
    assert "emitted no files" in warnings[0]
    assert str(tmp_path) not in warnings[0]


def test_unknown_workflow_uses_registry_relative_diagnostic():
    with pytest.raises(KeyError) as error:
        runner.resolve_registry_row("missing-example")
    assert "docs/registry/workflows.yaml" in str(error.value)
    assert str(runner._repo_root()) not in str(error.value)


def test_nested_output_metadata_excludes_configuration_dump(tmp_path):
    """Bytes b'chart' have length 5; hashlib independently supplies their digest.

    No rendered image is needed to test discovery. Both nested and top-level
    files must survive, while the configuration dump remains excluded.
    """
    results = tmp_path / "results"
    plot = results / "Plot"
    plot.mkdir(parents=True)
    (plot / "example.png").write_bytes(b"chart")
    (results / "summary.csv").write_bytes(b"summary")
    (results / "example.yml").write_bytes(b"configuration dump")
    cfg = {"Analysis": {"result_folder": str(results), "file_name": "example"}}
    payload, warnings = extract_result(cfg, ResultLocator(), str(tmp_path))
    assert not warnings
    assert payload["outputs"] == [
        {
            "basename": "example.png",
            "relative_path": "Plot/example.png",
            "sha256": hashlib.sha256(b"chart").hexdigest(),
            "size": 5,
        },
        {
            "basename": "summary.csv",
            "relative_path": "summary.csv",
            "sha256": hashlib.sha256(b"summary").hexdigest(),
            "size": 7,
        },
    ]


def test_nested_discovery_does_not_follow_symlinks(tmp_path):
    """Synthetic bytes outside the declared result tree must not be collected."""
    results = tmp_path / "results"
    results.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "unrelated.txt").write_bytes(b"unrelated")
    (results / "linked-file.txt").symlink_to(outside / "unrelated.txt")
    (results / "linked-directory").symlink_to(outside, target_is_directory=True)
    (results / "actual.txt").write_bytes(b"actual")
    cfg = {"Analysis": {"result_folder": str(results), "file_name": "example"}}
    payload, warnings = extract_result(cfg, ResultLocator(), str(tmp_path))
    assert not warnings
    assert [f["basename"] for f in payload["outputs"]] == ["actual.txt"]


def test_nested_discovery_rejects_resolved_escape(tmp_path, monkeypatch):
    """Emulate traversal through a directory reparse point on any platform."""
    results = tmp_path / "results"
    results.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "unrelated.txt").write_bytes(b"unrelated")
    (results / "linked-directory").symlink_to(outside, target_is_directory=True)
    actual = results / "actual.txt"
    actual.write_bytes(b"actual")
    escaped = results / "linked-directory/unrelated.txt"
    monkeypatch.setattr(Path, "rglob", lambda *_: iter([escaped, actual]))
    cfg = {"Analysis": {"result_folder": str(results)}}
    payload, warnings = extract_result(cfg, ResultLocator(), str(tmp_path))
    assert not warnings
    assert [f["relative_path"] for f in payload["outputs"]] == ["actual.txt"]


def test_nested_discovery_sorts_posix_relative_paths(tmp_path):
    """A separator sorts before '0' in POSIX order, but after it on Windows."""
    results = tmp_path / "results"
    (results / "a").mkdir(parents=True)
    for name in ("a0.txt", "a/child.txt", "a.txt"):
        (results / name).write_bytes(b"synthetic")
    cfg = {"Analysis": {"result_folder": str(results)}}
    payload, warnings = extract_result(cfg, ResultLocator(), str(tmp_path))
    assert not warnings
    assert [f["relative_path"] for f in payload["outputs"]] == [
        "a.txt",
        "a/child.txt",
        "a0.txt",
    ]


def test_duplicate_basenames_retain_distinct_relative_paths(tmp_path):
    """Identical bytes in different directories still identify distinct outputs."""
    results = tmp_path / "results"
    for directory in ("Tables", "Plot"):
        folder = results / directory
        folder.mkdir(parents=True)
        (folder / "result.dat").write_bytes(b"same")
    cfg = {"Analysis": {"result_folder": str(results)}}
    payload, warnings = extract_result(cfg, ResultLocator(), str(tmp_path))
    assert not warnings
    assert [f["basename"] for f in payload["outputs"]] == ["result.dat"] * 2
    assert [f["relative_path"] for f in payload["outputs"]] == [
        "Plot/result.dat",
        "Tables/result.dat",
    ]
    assert payload["outputs"][0] != payload["outputs"][1]


def test_directory_only_move_changes_result_hash(tmp_path):
    """Changing only the parent directory must change the result hash."""
    payloads = []
    for directory in ("Plot", "Tables"):
        root = tmp_path / directory
        results = root / "results"
        folder = results / directory
        folder.mkdir(parents=True)
        (folder / "result.dat").write_bytes(b"same")
        cfg = {"Analysis": {"result_folder": str(results)}}
        payload, warnings = extract_result(cfg, ResultLocator(), str(root))
        assert not warnings
        payloads.append(payload)
    assert result_hash(payloads[0]) != result_hash(payloads[1])


def test_result_paths_and_hash_ignore_injected_root(tmp_path):
    """Temporary roots and output order do not affect relative output identity."""
    payloads = []
    for name in ("first", "second"):
        root = tmp_path / name
        results = root / "results"
        (results / "Plot").mkdir(parents=True)
        (results / "Plot" / "result.dat").write_bytes(b"same")
        (results / "summary.csv").write_bytes(b"summary")
        cfg = {"Analysis": {"result_folder": str(results)}}
        payload, warnings = extract_result(cfg, ResultLocator(), str(root))
        assert not warnings
        assert str(root) not in json.dumps(payload)
        assert all(
            not Path(f["relative_path"]).is_absolute() for f in payload["outputs"]
        )
        payloads.append(payload)
    assert payloads[0] == payloads[1]
    payloads[1]["outputs"].reverse()
    assert result_hash(payloads[0]) == result_hash(payloads[1])
