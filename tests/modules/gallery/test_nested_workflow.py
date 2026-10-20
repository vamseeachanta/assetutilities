"""Regression coverage for metadata collection used by the gallery."""

import hashlib

from assetutilities.workflow_api import ResultLocator
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
            "sha256": hashlib.sha256(b"chart").hexdigest(),
            "size": 5,
        },
        {
            "basename": "summary.csv",
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
