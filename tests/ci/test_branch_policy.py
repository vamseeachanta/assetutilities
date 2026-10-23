"""Branch policy expectations use explicit calendar dates and synthetic refs."""

import importlib.util
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "branch_policy", ROOT / "scripts/ci/branch_policy.py"
)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


@pytest.mark.parametrize("branch", ["202610", "fix/config", "feature/release-work"])
def test_current_month_and_topic_branches_are_valid(branch):
    policy.validate_branch(branch, date(2026, 10, 20))


@pytest.mark.parametrize("branch", ["202609", "202611", "202613", "main", "", "123"])
def test_stale_future_invalid_and_direct_main_branches_are_rejected(branch):
    with pytest.raises(ValueError, match="branch"):
        policy.validate_branch(branch, date(2026, 10, 20))


def test_year_boundary_uses_full_calendar_month():
    policy.validate_branch("202701", date(2027, 1, 1))
    with pytest.raises(ValueError):
        policy.validate_branch("202612", date(2027, 1, 1))


def test_audit_reports_stale_and_unpublished_without_mutation(monkeypatch):
    """Expected report follows literal refs, not elapsed-age thresholds.

    October is current; September is stale. A topic ref without an upstream
    needs publishing; the current monthly ref is ahead of its remote.
    """
    commands = []

    def refs(command, **kwargs):
        commands.append(command)
        return type(
            "Result",
            (),
            {
                "stdout": (
                    "refs/heads/202610\trefs/remotes/origin/202610\t[ahead 1]\n"
                    "refs/heads/202609\trefs/remotes/origin/202609\t\n"
                    "refs/heads/fix/config\t\t\n"
                    "refs/heads/archive/202609\t\t\n"
                    "refs/remotes/origin/202609\t\t\n"
                    "refs/remotes/origin/archive/202609\t\t\n"
                )
            },
        )()

    monkeypatch.setattr(policy.subprocess, "run", refs)
    report = policy.audit(ROOT, date(2026, 10, 20))
    assert report == {
        "current_month": "202610",
        "stale_monthly": ["refs/heads/202609", "refs/remotes/origin/202609"],
        "unpublished_local": [
            "refs/heads/202610",
            "refs/heads/archive/202609",
            "refs/heads/fix/config",
        ],
    }
    assert len(commands) == 1
    assert commands[0][1] == "for-each-ref"


def test_policy_checks_are_added_to_the_existing_gate():
    import yaml

    with (ROOT / ".github/workflows/tests.yml").open(
        encoding="utf-8", newline="\n"
    ) as stream:
        workflow = yaml.safe_load(stream)
    steps = workflow["jobs"]["gates"]["steps"]
    policy_step = next(
        step
        for step in steps
        if "scripts/ci/branch_policy.py --branch" in step.get("run", "")
    )
    assert policy_step["if"] == "github.event_name == 'pull_request'"
    assert policy_step["env"]["SOURCE_BRANCH"] == "${{ github.head_ref }}"
    # The domain matrix owns the contract suite; Gates must not run it twice.
    assert not any("pytest tests/ci" in step.get("run", "") for step in steps)


def test_daily_audit_is_read_only():
    import yaml

    with (ROOT / ".github/workflows/branch-audit.yml").open(
        encoding="utf-8", newline="\n"
    ) as stream:
        workflow = yaml.safe_load(stream)
    events = workflow.get("on", workflow.get(True))
    assert events["schedule"] == [{"cron": "0 9 * * *"}]
    assert workflow["permissions"] == {"contents": "read"}
    steps = workflow["jobs"]["audit"]["steps"]
    commands = [step["run"] for step in steps if "run" in step]
    assert commands == [
        "python scripts/ci/branch_policy.py --audit > branch-audit.json"
    ]
