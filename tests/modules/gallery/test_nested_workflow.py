"""Regression coverage for metadata collection used by the gallery."""

import hashlib
import json
from pathlib import Path

from assetutilities.workflow_api import ResultLocator
from assetutilities.workflow_api.envelope import result_hash
from assetutilities.workflow_api.runner import extract_result


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
    (results / "example.yml").write_text("configuration dump")
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
    (outside / "unrelated.txt").write_text("unrelated")
    (results / "linked-file.txt").symlink_to(outside / "unrelated.txt")
    (results / "linked-directory").symlink_to(outside, target_is_directory=True)
    (results / "actual.txt").write_bytes(b"actual")
    cfg = {"Analysis": {"result_folder": str(results), "file_name": "example"}}
    payload, warnings = extract_result(cfg, ResultLocator(), str(tmp_path))
    assert not warnings
    assert [f["basename"] for f in payload["outputs"]] == ["actual.txt"]


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
