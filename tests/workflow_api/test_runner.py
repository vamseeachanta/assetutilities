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
            snap[str(p)] = (st.st_size, st.st_mtime_ns)
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
    (results / "data_exploration_FST1.csv").write_text("a,b\n1,2\n")
    (results / "data_exploration.yml").write_text("Analysis: {}\n")  # the save_cfg dump
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
