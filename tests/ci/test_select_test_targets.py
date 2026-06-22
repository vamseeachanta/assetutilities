# ABOUTME: Drift guard for the PR-gate test selector.
# ABOUTME: Fails if any tests/modules/<module> stops being selected, or routing regresses.

"""Tests for scripts/ci/select_test_targets.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "ci"))

from select_test_targets import (  # noqa: E402
    ALWAYS_XDIST,
    _has_tests,
    select,
    to_matrix,
)


def _modules() -> list[str]:
    base = REPO_ROOT / "tests" / "modules"
    return sorted(
        d.name for d in base.iterdir() if d.is_dir() and d.name != "__pycache__"
    )


def _modules_with_tests() -> list[str]:
    base = REPO_ROOT / "tests" / "modules"
    return sorted(
        d.name
        for d in base.iterdir()
        if d.is_dir() and d.name != "__pycache__" and _has_tests(d)
    )


def test_core_change_runs_full_tree():
    r = select(["pyproject.toml"], REPO_ROOT)
    assert r["scope"] == "full"


def test_uvlock_change_is_core():
    assert select(["uv.lock"], REPO_ROOT)["scope"] == "full"


def test_selector_self_change_is_core():
    assert select(["scripts/ci/select_test_targets.py"], REPO_ROOT)["scope"] == "full"


def test_module_change_is_module_scoped_not_full():
    r = select(["tests/modules/calculations/test_x.py"], REPO_ROOT)
    assert r["scope"] == "modules"
    assert "tests/modules/calculations" in r["xdist"]
    # the always-on cross-cutting set is always present
    assert all(t in r["xdist"] for t in ALWAYS_XDIST if (REPO_ROOT / t).is_dir())


def test_src_module_change_maps_to_test_home():
    """A change under a src module that has a tests/modules home is scoped."""
    if (REPO_ROOT / "tests/modules/csv_utilities").is_dir():
        r = select(["src/assetutilities/modules/csv_utilities/foo.py"], REPO_ROOT)
        assert r["scope"] == "modules"
        assert "tests/modules/csv_utilities" in r["xdist"]


def test_noncode_only_change_skips_full_tree():
    for path in ("reports/x.html", "notebooks/demo.ipynb", "README.md", "docs/x.md"):
        r = select([path], REPO_ROOT)
        assert r["scope"] == "skip", path
        # skip still runs the cheap always-on set, never module/full dirs
        assert r["xdist"] == [t for t in ALWAYS_XDIST if (REPO_ROOT / t).is_dir()]


def test_config_repo_structure_routes_to_its_contract():
    r = select(["config/repo_structure.yml"], REPO_ROOT)
    assert r["scope"] == "modules"
    if (REPO_ROOT / "tests/repo_structure").is_dir():
        assert "tests/repo_structure" in r["xdist"]


@pytest.mark.parametrize("module", _modules())
def test_every_module_is_selected(module):
    """Drift guard: a change under any tests/modules/<module> must be
    module-scoped and pull in that module's dir (no module silently regresses
    to full/skip)."""
    r = select([f"tests/modules/{module}/test_smoke.py"], REPO_ROOT)
    assert r["scope"] == "modules"
    assert f"tests/modules/{module}" in r["xdist"]


# --- Matrix-emitter (domain fan-out) tests ---


def _names(m: dict) -> set[str]:
    return {s["name"] for s in m["include"]}


def test_matrix_is_never_empty_on_skip():
    """Docs-only change still yields the always-on shard (matrix never empty)."""
    m = to_matrix(["README.md"], REPO_ROOT)
    assert m["scope"] == "skip"
    assert m["include"], "matrix must never be empty (CI matrix would error)"
    assert _names(m) == {"_always"}


def test_matrix_module_scope_one_shard_per_domain():
    m = to_matrix(
        [
            "tests/modules/calculations/test_a.py",
            "tests/modules/excel_utilities/test_b.py",
        ],
        REPO_ROOT,
    )
    assert m["scope"] == "modules"
    names = _names(m)
    assert "_always" in names
    assert "modules-calculations" in names and "modules-excel_utilities" in names


def test_matrix_full_scope_fans_out_every_module_with_tests():
    """A core change fans out to one shard per tests/modules/<domain> that has
    tests; pure support / empty stub dirs are excluded to avoid empty shards."""
    m = to_matrix(["uv.lock"], REPO_ROOT)
    assert m["scope"] == "full"
    names = _names(m)
    base = REPO_ROOT / "tests" / "modules"
    for module in _modules():
        if _has_tests(base / module):
            assert f"modules-{module}" in names, f"{module} missing from full matrix"
        else:
            assert f"modules-{module}" not in names, f"{module} is an empty shard"


def test_matrix_shards_have_required_fields():
    m = to_matrix(["uv.lock"], REPO_ROOT)
    for shard in m["include"]:
        assert set(shard) >= {"name", "targets", "mode"}
        assert shard["mode"] in {"xdist", "seq"}
        assert shard["targets"].strip()


def test_matrix_targets_only_existing_dirs_in_module_scope():
    m = to_matrix(["tests/modules/visualization/test_x.py"], REPO_ROOT)
    for shard in m["include"]:
        for tgt in shard["targets"].split():
            assert (REPO_ROOT / tgt).exists(), f"{tgt} does not exist"
