"""Pin PDF workflow event coverage and cancellation policy."""

import re
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2] / ".github/workflows/pdf-integration.yml"
)


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _evaluate_expression(expression: str, context: dict) -> object:
    """Evaluate the equality and short-circuit subset used by concurrency."""
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
    concurrency = _workflow()["concurrency"]
    context = {
        "github.workflow": "PDF integration",
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
    """Superseded runs share a group only within one pull request."""
    first = _concurrency_for("pull_request", "refs/pull/1/merge", "101")
    repeat = _concurrency_for("pull_request", "refs/pull/1/merge", "102")
    other = _concurrency_for("pull_request", "refs/pull/2/merge", "103")
    assert first == repeat == ("PDF integration-refs/pull/1/merge", True)
    assert other == ("PDF integration-refs/pull/2/merge", True)
    assert first[0] != other[0]


@pytest.mark.parametrize("action", ["ready_for_review", "converted_to_draft"])
def test_readiness_transitions_cancel_previous_runs(action: str) -> None:
    """Readiness changes must cancel earlier runs of the same pull request."""
    workflow = _workflow()
    events = workflow.get("on", workflow.get(True))
    assert action in events["pull_request"]["types"]
    # Both actions retain the pull_request event name and the same merge ref.
    previous = _concurrency_for("pull_request", "refs/pull/1/merge", "101")
    transition = _concurrency_for("pull_request", "refs/pull/1/merge", "102")
    assert previous == transition == ("PDF integration-refs/pull/1/merge", True)


@pytest.mark.parametrize("event", ["push", "workflow_dispatch"])
def test_non_pull_request_runs_have_unique_groups(event: str) -> None:
    """Three quick runs cannot replace each other's pending work."""
    runs = [_concurrency_for(event, "refs/heads/main", str(i)) for i in range(3)]
    assert runs == [(f"PDF integration-{i}", False) for i in range(3)]


def test_pull_request_activity_types_include_retargeting() -> None:
    events = _workflow().get("on", _workflow().get(True))
    assert events["pull_request"] == {
        "branches": ["main"],
        "types": [
            "opened",
            "synchronize",
            "reopened",
            "edited",
            "ready_for_review",
            "converted_to_draft",
        ],
    }
    assert events["push"]["branches"] == ["main"]
    assert "workflow_dispatch" in events


def test_trigger_contract_runs_in_pdf_job() -> None:
    commands = [
        step.get("run", "") for step in _workflow()["jobs"]["pdf-integration"]["steps"]
    ]
    assert (
        "uv run python -m pytest tests/workflows/test_pdf_integration_triggers.py"
        in commands
    )
