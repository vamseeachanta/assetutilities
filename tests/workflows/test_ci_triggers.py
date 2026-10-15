"""Pin pull-request coverage and preserve the existing test gate contract."""

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github/workflows/tests.yml"


def _workflow() -> dict:
    """Read the workflow with YAML 1.1 event-key handling."""
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_pull_requests_allow_every_base_branch() -> None:
    """Every base branch must receive the test gates."""
    workflow = _workflow()
    events = workflow.get("on", workflow.get(True))
    assert "pull_request" in events
    trigger = events["pull_request"] or {}
    assert "branches" not in trigger
    assert "branches-ignore" not in trigger


def test_push_branches_remain_main_only() -> None:
    """Keep feature-branch pushes from duplicating pull-request runs."""
    workflow = _workflow()
    events = workflow.get("on", workflow.get(True))
    assert events["push"]["branches"] == ["main"]


def test_existing_gate_jobs_are_preserved() -> None:
    """Keep the gate ids and explicit check names stable."""
    assert {key: job.get("name") for key, job in _workflow()["jobs"].items()} == {
        "gates": "Gates",
        "domain-tests": None,
    }


def test_existing_concurrency_is_preserved() -> None:
    """Pin the existing concurrency without changing cancellation behavior."""
    assert _workflow()["concurrency"] == {
        "group": "${{ github.workflow }}-${{ github.ref }}",
        "cancel-in-progress": True,
    }


def test_trigger_contract_runs_in_gates() -> None:
    """Run this contract even when the domain selector chooses only core tests."""
    commands = [step.get("run", "") for step in _workflow()["jobs"]["gates"]["steps"]]
    assert "uv run python -m pytest tests/workflows/test_ci_triggers.py" in commands
# Exercise incremental selection against a stacked pull-request base.
