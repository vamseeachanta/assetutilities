"""Pin pull-request coverage and preserve the existing test gate contract."""

from pathlib import Path
import re

import pytest

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


def test_concurrency_cancels_pull_request_runs_only() -> None:
    """Push and dispatch runs get unique groups; only PR runs cancel."""
    concurrency = _workflow()["concurrency"]
    assert "github.run_id" in concurrency["group"]
    assert "github.event_name == 'pull_request' && github.ref" in concurrency["group"]
    assert (
        concurrency["cancel-in-progress"]
        == "${{ github.event_name == 'pull_request' }}"
    )


def _evaluate_expression(expression: str, context: dict) -> object:
    """Evaluate the workflow's equality and short-circuit expression subset."""
    expression = expression.strip()
    for operator in ("||", "&&", "=="):
        if operator in expression:
            left, right = expression.split(operator, 1)
            value = _evaluate_expression(left, context)
            if operator == "||":
                return value or _evaluate_expression(right, context)
            if operator == "&&":
                return value and _evaluate_expression(right, context)
            return value == _evaluate_expression(right, context)
    if expression.startswith("'") and expression.endswith("'"):
        return expression[1:-1]
    return context[expression]


def _concurrency_for(event: str, ref: str, run_id: str) -> tuple[str, bool]:
    """Evaluate the actual YAML group and cancellation for one event."""
    concurrency = _workflow()["concurrency"]
    context = {
        "github.workflow": "Tests",
        "github.event_name": event,
        "github.ref": ref,
        "github.run_id": run_id,
    }
    group = re.sub(
        r"\$\{\{(.*?)\}\}",
        lambda match: str(_evaluate_expression(match[1], context)),
        concurrency["group"],
    )
    cancel = concurrency["cancel-in-progress"]
    if isinstance(cancel, str):
        cancel = _evaluate_expression(
            cancel.removeprefix("${{").removesuffix("}}"), context
        )
    return group, cancel


def test_pull_request_concurrency_groups() -> None:
    """Runs of one PR share a group; distinct PRs remain independent."""
    first = _concurrency_for("pull_request", "refs/pull/1/merge", "101")
    repeat = _concurrency_for("pull_request", "refs/pull/1/merge", "102")
    other = _concurrency_for("pull_request", "refs/pull/2/merge", "103")
    assert first == repeat == ("Tests-refs/pull/1/merge", True)
    assert other == ("Tests-refs/pull/2/merge", True)
    assert first[0] != other[0]


@pytest.mark.parametrize("event", ["push", "workflow_dispatch", "schedule"])
def test_non_pull_request_runs_have_unique_groups(event: str) -> None:
    """Every non-PR event uses its run id without cancelling other runs."""
    first = _concurrency_for(event, "refs/heads/main", "101")
    second = _concurrency_for(event, "refs/heads/main", "102")
    assert first == ("Tests-101", False)
    assert second == ("Tests-102", False)
    assert first[0] != second[0]


def test_trigger_contract_runs_in_gates() -> None:
    """Run this contract even when the domain selector chooses only core tests."""
    commands = [step.get("run", "") for step in _workflow()["jobs"]["gates"]["steps"]]
    assert "uv run python -m pytest tests/workflows/test_ci_triggers.py" in commands
