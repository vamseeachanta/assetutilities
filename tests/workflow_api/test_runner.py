# ABOUTME: Tests for run_workflow + ResultLocator + extract_result (#3282).
# ABOUTME: Engine-backed tests consume the #3297 embed path (engine(embed=True)).
"""Runner, locator, registry, and side-effect-freeness tests.

Engine-backed tests call the #3297 embed path. They run from the repo root
(the data_exploration example reads csv paths relative to cwd).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from assetutilities.workflow_api import (
    ResultEnvelope,
    ResultLocator,
    build_cfg,
    run_workflow,
)
from assetutilities.workflow_api.runner import (
    extract_result,
    load_registry,
    resolve_registry_row,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = REPO_ROOT / "examples" / "workflows" / "data_exploration"


def _snapshot(path: Path) -> dict:
    snap = {}
    for p in sorted(path.rglob("*")):
        if p.is_file():
            st = p.stat()
            snap[p.as_posix()] = (st.st_size, st.st_mtime_ns)
    return snap


# --- registry / schema (no engine) -----------------------------------------

def test_registry_schema_v2_invocation_and_optional_result():
    reg = load_registry()
    assert reg["schema_version"] == 2
    assert reg["invocation"] == "uv run python -m assetutilities {input}"
    assert len(reg["workflows"]) == 9
    de = resolve_registry_row("data_exploration")
    assert de["result"]["kind"] == "files"


def test_build_cfg_merges_params_over_example():
    row = resolve_registry_row("data_exploration")
    cfg = build_cfg(row, {"type": {"df_basic_statistics": {"flag": False}}})
    assert cfg["basename"] == "data_exploration"
    # params win over the example value (which was flag: True)
    assert cfg["type"]["df_basic_statistics"]["flag"] is False
    # untouched example keys survive
    assert cfg["data"]["type"] == "csv"


# --- locator unit (no engine) ----------------------------------------------

def test_locator_from_row_defaults_to_files():
    assert ResultLocator.from_row(None).kind == "files"
    assert ResultLocator.from_row({"result": {"kind": "in_memory", "key": "k"}}).kind == "in_memory"


def test_locator_in_memory_missing_key_warns_not_silent():
    loc = ResultLocator(kind="in_memory", key="absent_key")
    payload, warns = extract_result({"basename": "x"}, loc, "/nonexistent")
    assert payload["value"] is None
    assert warns and "absent_key" in warns[0]


def test_locator_files_emits_no_files_warns(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    cfg_base = {"Analysis": {"result_folder": str(results), "file_name": "x"}}
    payload, warns = extract_result(cfg_base, ResultLocator(kind="files"), str(tmp_path))
    assert payload == {"kind": "files", "outputs": []}
    assert warns and "no files" in warns[0]


def test_extract_result_excludes_cfg_dump(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    (results / "data_exploration_FST1.csv").write_text("a,b\n1,2\n", encoding="utf-8", newline="\n")
    (results / "data_exploration.yml").write_text("Analysis: {}\n", encoding="utf-8", newline="\n")  # the save_cfg dump
    cfg_base = {"Analysis": {"result_folder": str(results), "file_name": "data_exploration"}}
    payload, _ = extract_result(cfg_base, ResultLocator(kind="files"), str(tmp_path))
    names = {f["basename"] for f in payload["outputs"]}
    assert names == {"data_exploration_FST1.csv"}
    assert "data_exploration.yml" not in names


# --- error envelopes (no engine) -------------------------------------------

def test_run_workflow_unknown_id_error_envelope():
    env = run_workflow("nope_not_a_workflow")
    assert isinstance(env, ResultEnvelope)
    assert env.status == "error"
    assert env.warnings and "nope_not_a_workflow" in env.warnings[0]
    assert env.determinism["result_hash"] is None


# --- engine-backed (embed path) --------------------------------------------

def test_run_workflow_by_id_returns_envelope():
    env = run_workflow("data_exploration")
    assert env.status == "ok", env.warnings
    assert env.result["kind"] == "files"
    names = sorted(f["basename"] for f in env.result["outputs"])
    assert names == ["data_exploration_FST1.csv", "data_exploration_FST2.csv"]
    assert env.provenance["input_hash"]
    assert env.determinism["result_hash"]
    assert env.determinism["reproducible"] is None  # default unchecked


def test_extract_result_globs_injected_root_real_filenames():
    # The emitted names are the cfg-derived data_exploration_*.csv, NOT the
    # registry's documentary input_FST*.csv, and the cfg-dump is excluded.
    env = run_workflow("data_exploration")
    names = {f["basename"] for f in env.result["outputs"]}
    assert all(n.startswith("data_exploration_") and n.endswith(".csv") for n in names)
    assert "data_exploration.yml" not in names
    assert not any(n.startswith("input_") for n in names)


def test_run_workflow_writes_nothing_outside_tempdir():
    before = _snapshot(EXAMPLE_DIR)
    cwd_logs_before = (REPO_ROOT / "logs").exists()
    env = run_workflow("data_exploration")
    after = _snapshot(EXAMPLE_DIR)
    assert env.status == "ok", env.warnings
    assert before == after, "embed run mutated the repo example dir"
    assert not (EXAMPLE_DIR / "results").exists()
    # No new logs dir under the repo root from this call.
    assert (REPO_ROOT / "logs").exists() == cwd_logs_before
    # No stray temp roots left behind.
    leftover = [d for d in os.listdir("/tmp") if d.startswith("auwf_")]
    assert leftover == [], f"tempdirs not cleaned: {leftover}"


def test_reproducible_computed_true_on_double_run():
    env = run_workflow("data_exploration", verify_reproducible=True)
    assert env.status == "ok", env.warnings
    assert env.determinism["reproducible"] is True


def test_extract_result_includes_nested_plot(tmp_path):
    """Plot writers emit below Plot; hashes must include the actual bytes."""
    import hashlib

    from assetutilities.workflow_api.runner import ResultLocator, extract_result

    results = tmp_path / "results"
    plot = results / "Plot" / "curve.png"
    plot.parent.mkdir(parents=True)
    plot.write_bytes(b"synthetic image bytes")
    (results / "run.yml").write_text("runtime configuration", encoding="utf-8", newline="\n")
    payload, warnings = extract_result(
        {"Analysis": {"result_folder": str(results), "file_name": "run"}},
        ResultLocator(),
        str(tmp_path),
    )
    assert not warnings
    assert payload["outputs"] == [
        {
            "basename": "Plot/curve.png",
            "size": len(b"synthetic image bytes"),
            "sha256": hashlib.sha256(b"synthetic image bytes").hexdigest(),
        }
    ]


def test_extract_result_preserves_relative_paths_for_duplicate_names(tmp_path):
    from assetutilities.workflow_api.runner import ResultLocator, extract_result

    for folder in ("Data", "Plot"):
        directory = tmp_path / "results" / folder
        directory.mkdir(parents=True)
        (directory / "same.txt").write_text(folder, encoding="utf-8", newline="\n")
    payload, warnings = extract_result({}, ResultLocator(), str(tmp_path))
    assert not warnings
    assert [row["basename"] for row in payload["outputs"]] == [
        "Data/same.txt", "Plot/same.txt"
    ]


@pytest.mark.parametrize("directory", [False, True])
def test_extract_result_rejects_linked_outputs(tmp_path, directory):
    results = tmp_path / "results"
    results.mkdir()
    target = tmp_path / "target"
    if directory:
        target.mkdir()
        (target / "answer.txt").write_text("answer", encoding="utf-8", newline="\n")
    else:
        target.write_text("answer", encoding="utf-8", newline="\n")
    (results / "linked").symlink_to(target, target_is_directory=directory)
    with pytest.raises(ValueError, match="link"):
        extract_result({}, ResultLocator(), str(tmp_path))


def test_extract_result_rejects_result_directory_outside_run(tmp_path):
    root = tmp_path / "run"
    root.mkdir()
    outside = tmp_path / "results"
    outside.mkdir()
    (outside / "answer.txt").write_text("answer", encoding="utf-8", newline="\n")
    cfg = {"Analysis": {"result_folder": str(outside)}}
    with pytest.raises(ValueError, match="escapes"):
        extract_result(cfg, ResultLocator(), str(root))


def test_extract_result_rejects_linked_result_directory(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "answer.txt").write_text("answer", encoding="utf-8", newline="\n")
    (tmp_path / "results").symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="link"):
        extract_result({}, ResultLocator(), str(tmp_path))


def test_extract_result_missing_directory_warns(tmp_path):
    payload, warnings = extract_result({}, ResultLocator(), str(tmp_path))
    assert payload == {"kind": "files", "outputs": []}
    assert warnings and "no files" in warnings[0]


@pytest.mark.parametrize("name", ["results", "results/linked", "results/answer.txt"])
@pytest.mark.parametrize("target_exists", [False, True])
def test_extract_result_rejects_reparse_points(
    tmp_path, monkeypatch, name, target_exists
):
    import stat
    from types import SimpleNamespace

    results = tmp_path / "results"
    (results / "linked").mkdir(parents=True)
    (results / "answer.txt").write_text("answer", encoding="utf-8", newline="\n")
    reparse = tmp_path / name
    original_lstat = Path.lstat
    original_exists = Path.exists

    def lstat(path, *args, **kwargs):
        observed = original_lstat(path, *args, **kwargs)
        if path == reparse:
            return SimpleNamespace(
                st_mode=observed.st_mode,
                st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
            )
        return observed

    monkeypatch.setattr(Path, "lstat", lstat)
    if not target_exists:
        monkeypatch.setattr(
            Path, "exists", lambda path: False if path == reparse else original_exists(path)
        )
    with pytest.raises(ValueError, match="link"):
        extract_result({}, ResultLocator(), str(tmp_path))


def test_extract_result_rejects_unreadable_subdirectory(tmp_path, monkeypatch):
    results = tmp_path / "results"
    denied = results / "unreadable"
    denied.mkdir(parents=True)
    (results / "answer.txt").write_text("answer", encoding="utf-8", newline="\n")
    original_scandir = os.scandir

    def scandir(path):
        if Path(path) == denied:
            raise PermissionError("synthetic traversal failure")
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir)
    with pytest.raises(ValueError, match="Cannot read"):
        extract_result({}, ResultLocator(), str(tmp_path))
