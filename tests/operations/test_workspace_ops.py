"""Operational rules come from #122 and its ten child issues (2026 snapshot).

Counts below are hand counts of the explicitly listed requirements, rather than
values calculated by the implementation. Dates and references are synthetic
inputs; no operational retention or freshness threshold is assumed.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/operations/workspace_ops.py"
SPEC = importlib.util.spec_from_file_location("workspace_ops", SCRIPT)
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)

# Independent enumeration: the Children list in #122, retrieved in 2026.
CHILDREN = {
    "repositories": 35,
    "data": 33,
    "hardware": 36,
    "agents": 30,
    "meetings": 56,
    "knowledge": 38,
    "email": 39,
    "onboarding": 42,
    "process": 37,
    "marketing": 40,
}


def complete_record():
    return {
        "state": "complete",
        "responsible_role": "maintainer",
        "evidence_ref": "example:acceptance-record",
        "observed_on": "2026-10-19",
        "valid_until": "2026-10-21",
    }


def manifest(records=None):
    return {"as_of": "2026-10-20", "records": records or {}}


def test_inventory_reports_only_explicit_roots_and_immediate_children(tmp_path):
    """Hand count: one normal checkout + one worktree = two marker candidates."""
    (tmp_path / "library/.git").mkdir(parents=True)
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: ../metadata\n", encoding="utf-8")
    (tmp_path / "ordinary/nested/.git").mkdir(parents=True)
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*"))
    result = ops.inventory([tmp_path])
    assert result["repositories"] == [
        {"root_index": 0, "path": "library", "marker": "directory"},
        {"root_index": 0, "path": "worktree", "marker": "file"},
    ]
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")) == before


def test_inventory_accepts_a_checkout_as_the_root(tmp_path):
    (tmp_path / ".git").mkdir()
    assert ops.inventory([tmp_path])["repositories"] == [
        {"root_index": 0, "path": ".", "marker": "directory"}
    ]


def test_inventory_deduplicates_overlapping_roots(tmp_path):
    repo = tmp_path / "library"
    (repo / ".git").mkdir(parents=True)
    assert len(ops.inventory([tmp_path, repo, tmp_path])["repositories"]) == 1


def test_inventory_does_not_follow_child_or_marker_symlinks(tmp_path):
    outside = tmp_path / "outside"
    (outside / ".git").mkdir(parents=True)
    root = tmp_path / "root"
    root.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    (root / "fake").mkdir()
    (root / "fake/.git").symlink_to(outside / ".git", target_is_directory=True)
    assert ops.inventory([root])["repositories"] == []


def test_inventory_rejects_missing_or_file_root(tmp_path):
    with pytest.raises(ValueError, match="inventory root"):
        ops.inventory([tmp_path / "absent"])
    file = tmp_path / "file"
    file.touch()
    with pytest.raises(ValueError, match="inventory root"):
        ops.inventory([file])


def test_empty_manifest_cannot_claim_readiness():
    """#122 lists ten children: zero pass, zero fail, ten unevaluated."""
    report = ops.assess(manifest())
    assert {r["id"]: r["issue"] for r in report["checks"]} == CHILDREN
    assert report["summary"] == {"PASS": 0, "FAIL": 0, "NOT_EVALUATED": 10}
    assert report["overall"] == "NOT_EVALUATED"
    assert len(report["actions"]) == 10


def test_complete_current_records_pass_without_mutating_input():
    data = manifest({name: complete_record() for name in CHILDREN})
    before = copy.deepcopy(data)
    report = ops.assess(data)
    assert data == before
    assert report["overall"] == "PASS"
    assert report["summary"] == {"PASS": 10, "FAIL": 0, "NOT_EVALUATED": 0}
    assert report["actions"] == []


@pytest.mark.parametrize(
    "missing", ["responsible_role", "evidence_ref", "observed_on", "valid_until"]
)
def test_complete_without_supporting_evidence_is_not_evaluated(missing):
    record = complete_record()
    del record[missing]
    report = ops.assess(manifest({"repositories": record}))
    assert report["checks"][0]["status"] == "NOT_EVALUATED"
    assert missing in report["checks"][0]["reason"]


@pytest.mark.parametrize("state", ["pending", "blocked"])
def test_known_incomplete_work_is_a_failure_and_an_action(state):
    record = {
        "state": state,
        "responsible_role": "maintainer",
        "next_action": "Review the inventory.",
    }
    report = ops.assess(manifest({"repositories": record}))
    assert report["overall"] == "FAIL"
    assert report["actions"][0]["next_action"] == "Review the inventory."
    assert report["actions"][0]["responsible_role"] == "maintainer"


@pytest.mark.parametrize("expiry", ["2026-10-19", "2026-10-20"])
def test_expiry_is_exclusive(expiry):
    """At or after the supplied valid-until date, evidence needs a new review."""
    record = complete_record()
    record["valid_until"] = expiry
    report = ops.assess(manifest({"repositories": record}))
    assert report["checks"][0]["status"] == "NOT_EVALUATED"
    assert "expired" in report["checks"][0]["reason"]


def test_observation_on_as_of_date_is_current():
    record = complete_record()
    record["observed_on"] = "2026-10-20"
    assert (
        ops.assess(manifest({"repositories": record}))["checks"][0]["status"] == "PASS"
    )


@pytest.mark.parametrize(
    "update",
    [
        {"observed_on": "2026-10-21"},
        {"observed_on": "2026-02-30"},
        {"observed_on": "20261019"},
        {"valid_until": "2026-10-18"},
        {"state": "ready"},
        {"evidence_ref": ["example:record"]},
        {"unexpected": True},
    ],
)
def test_invalid_records_are_rejected(update):
    record = complete_record()
    record.update(update)
    with pytest.raises(ValueError):
        ops.assess(manifest({"repositories": record}))


@pytest.mark.parametrize(
    "data",
    [
        [],
        {},
        {"as_of": "yesterday"},
        {"as_of": "2026-10-20", "records": []},
        {"as_of": "2026-10-20", "records": {"repository": {}}},
        {"as_of": "2026-10-20", "records": {"repositories": None}},
        {"as_of": "2026-10-20", "surprise": True},
    ],
)
def test_invalid_manifest_shapes_are_rejected(data):
    with pytest.raises(ValueError):
        ops.assess(data)


def test_worked_example_has_independently_counted_answer():
    """Two current complete records (repositories, agents), one pending (email),
    and seven omitted (data, hardware, meetings, knowledge, onboarding, process,
    marketing) give PASS=2, FAIL=1, NOT_EVALUATED=7, hence overall FAIL.
    """
    path = ROOT / "examples/operations/workspace-operations.json"
    report = ops.assess(json.loads(path.read_text(encoding="utf-8")))
    assert report["summary"] == {"PASS": 2, "FAIL": 1, "NOT_EVALUATED": 7}
    assert report["overall"] == "FAIL"
    assert len(report["actions"]) == 8


def test_markdown_escapes_evidence_and_role_text():
    record = complete_record()
    record["responsible_role"] = "maintainer|backup\nnext row"
    record["evidence_ref"] = "<example>&record|tail"
    text = ops.render_markdown(ops.assess(manifest({"repositories": record})))
    assert "maintainer\\|backup next row" in text
    assert "&lt;example&gt;&amp;record\\|tail" in text
    assert "Revision history" in text
    assert "NOT_EVALUATED" in text


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_assesses_example_and_uses_nonready_exit_status():
    result = run_cli("assess", ROOT / "examples/operations/workspace-operations.json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["overall"] == "FAIL"
    result = run_cli(
        "assess",
        ROOT / "examples/operations/workspace-operations.json",
        "--format",
        "markdown",
    )
    assert result.returncode == 1
    assert "## Actions" in result.stdout


def test_cli_complete_manifest_exits_successfully(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps(manifest({key: complete_record() for key in CHILDREN})))
    assert run_cli("assess", path).returncode == 0


@pytest.mark.parametrize(
    "raw",
    [
        '{"as_of":"2026-10-20","as_of":"2026-10-21"}',
        '{"as_of":"2026-10-20","records":{"email":{"state":NaN}}}',
        "not JSON",
    ],
)
def test_cli_invalid_input_is_reported_without_echoing_payload(tmp_path, raw):
    path = tmp_path / "input.json"
    path.write_text(raw, encoding="utf-8")
    result = run_cli("assess", path)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "invalid" in result.stderr
    assert raw not in result.stderr
    assert str(tmp_path) not in result.stderr


def test_cli_missing_file_does_not_echo_private_path(tmp_path):
    result = run_cli("assess", tmp_path / "absent.json")
    assert result.returncode == 2
    assert str(tmp_path) not in result.stderr


def test_cli_inventory_is_relative_and_read_only(tmp_path):
    (tmp_path / "library/.git").mkdir(parents=True)
    result = run_cli("inventory", tmp_path)
    assert result.returncode == 0
    assert json.loads(result.stdout)["repositories"][0]["path"] == "library"
    assert str(tmp_path) not in result.stdout


def test_markdown_renders_supplied_links_and_code_as_literal_text():
    record = complete_record()
    record["evidence_ref"] = "[record](example:record) `code` *text* \\|"
    text = ops.render_markdown(ops.assess(manifest({"repositories": record})))
    assert r"\[record\]\(example:record\) \`code\` \*text\* \\\|" in text


def test_cli_inventory_error_is_sanitized(tmp_path):
    result = run_cli("inventory", tmp_path / "unavailable")
    assert result.returncode == 2
    assert result.stdout == ""
    assert str(tmp_path) not in result.stderr


def test_cli_inventory_symlink_cycle_is_sanitized(tmp_path):
    loop = tmp_path / "loop"
    loop.symlink_to(loop)
    result = run_cli("inventory", loop)
    assert result.returncode == 2
    assert str(tmp_path) not in result.stderr
