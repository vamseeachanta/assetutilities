"""Repository audit examples are synthetic, with independent rule evaluations.

Dates and counts are test inputs, not retention recommendations. For the main
example, March precedes the supplied April cutoff and May follows it. Of three
repositories, only the idle one has no work; only that repository needs issue
routing review; only its merged, unprotected topic branch is a cleanup candidate.
Thus the hand-counted summary is (3 repositories, 1 consolidation review,
1 issue-routing review, 1 branch review). See the rules and source definitions in
docs/modules/repo_management/consolidation-audit.md.
"""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.devtools.repo_audit import audit_inventory, main, render_markdown


CUTOFF = "2026-04-01T00:00:00Z"
OBSERVED = "2026-06-01T00:00:00Z"


@pytest.fixture
def inventory():
    return {
        "observed_at": OBSERVED,
        "repositories": [
            {
                "name": "idle",
                "archived": False,
                "pushed_at": "2026-03-01T00:00:00Z",
                "open_issues": 0,
                "open_pull_requests": 0,
                "default_branch": "main",
                "branches_complete": True,
                "branches": [
                    {"name": "main"},
                    {
                        "name": "topic",
                        "protected": False,
                        "merged": True,
                        "committed_at": "2026-03-01T00:00:00Z",
                        "open_pull_requests": 0,
                    },
                ],
            },
            {
                "name": "tools",
                "archived": False,
                "pushed_at": "2026-05-01T00:00:00Z",
                "open_issues": 2,
                "open_pull_requests": 1,
                "default_branch": "main",
                "branches_complete": True,
                "branches": [],
            },
            {"name": "retired", "archived": True},
        ],
    }


def run(inventory, **kwargs):
    return audit_inventory(
        inventory, stale_before=CUTOFF, issue_repositories=["tools"], **kwargs
    )


def row(report, name="idle"):
    return next(item for item in report["repositories"] if item["name"] == name)


def test_three_slices_and_hand_counted_totals(inventory):
    report = run(inventory)
    assert report["summary"] == {
        "repositories": 3,
        "consolidation_reviews": 1,
        "issue_routing_reviews": 1,
        "branch_reviews": 1,
    }
    idle = row(report)
    assert idle["consolidation"]["status"] == "REVIEW_CONSOLIDATION"
    assert idle["issue_routing"]["status"] == "REVIEW_ROUTING"
    assert idle["branches"]["items"][0]["status"] == "KEEP"
    assert idle["branches"]["items"][1]["status"] == "REVIEW_DELETE"
    assert row(report, "tools")["consolidation"]["status"] == "KEEP"
    assert row(report, "retired")["consolidation"]["status"] == "ARCHIVED"


@pytest.mark.parametrize(
    "field,value",
    [("open_issues", 1), ("open_pull_requests", 1), ("pushed_at", CUTOFF)],
)
def test_pending_work_and_cutoff_equality_prevent_consolidation(
    inventory, field, value
):
    """Any pending work blocks review; equality is not strictly before cutoff."""
    inventory["repositories"][0][field] = value
    assert row(run(inventory))["consolidation"]["status"] == "KEEP"


def test_explicit_keep_overrides_inactivity(inventory):
    assert (
        row(run(inventory, keep_repositories=["idle"]))["consolidation"]["status"]
        == "KEEP"
    )


@pytest.mark.parametrize(
    "field", ["archived", "pushed_at", "open_issues", "open_pull_requests"]
)
def test_missing_repository_evidence_is_not_evaluated(inventory, field):
    inventory["repositories"][0].pop(field)
    assert row(run(inventory))["consolidation"]["status"] == "NOT_EVALUATED"


def test_issue_routing_checks_destinations_and_existing_backlog(inventory):
    inventory["repositories"][0]["open_issues"] = 2
    report = run(inventory)
    assert row(report)["issue_routing"]["status"] == "REVIEW_ROUTING"
    assert "2" in row(report)["issue_routing"]["reason"]
    assert row(report, "tools")["issue_routing"]["status"] == "OK"
    assert row(report, "retired")["issue_routing"]["status"] == "NOT_EVALUATED"


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("protected", True, "KEEP"),
        ("merged", False, "KEEP"),
        ("open_pull_requests", 1, "KEEP"),
        ("committed_at", CUTOFF, "KEEP"),
        ("protected", None, "NOT_EVALUATED"),
        ("merged", None, "NOT_EVALUATED"),
        ("open_pull_requests", None, "NOT_EVALUATED"),
        ("committed_at", None, "NOT_EVALUATED"),
    ],
)
def test_branch_safety_evidence(inventory, field, value, expected):
    inventory["repositories"][0]["branches"][1][field] = value
    assert row(run(inventory))["branches"]["items"][1]["status"] == expected


def test_missing_default_branch_blocks_cleanup(inventory):
    inventory["repositories"][0].pop("default_branch")
    assert all(
        item["status"] == "NOT_EVALUATED"
        for item in row(run(inventory))["branches"]["items"]
    )


def test_incomplete_branch_listing_is_reported(inventory):
    inventory["repositories"][0]["branches_complete"] = False
    assert row(run(inventory))["branches"]["status"] == "NOT_EVALUATED"


@pytest.mark.parametrize(
    "field,value", [("protected", "false"), ("merged", 1), ("open_pull_requests", -1)]
)
def test_rejects_malformed_branch_evidence(inventory, field, value):
    inventory["repositories"][0]["branches"][1][field] = value
    with pytest.raises(ValueError):
        run(inventory)


def test_archived_or_unknown_repository_never_has_branch_candidates(inventory):
    for archived in (True, None):
        inventory["repositories"][0]["archived"] = archived
        assert row(run(inventory))["branches"]["items"][1]["status"] != "REVIEW_DELETE"


def test_requires_evidence_for_complete_listing_and_destinations(inventory):
    inventory["repositories"][0]["branches"] = None
    with pytest.raises(ValueError, match="branches_complete"):
        run(inventory)
    inventory["repositories"][0]["branches_complete"] = False
    inventory["repositories"][1]["archived"] = True
    with pytest.raises(ValueError, match="unarchived"):
        run(inventory)


def test_output_is_deterministic_and_markdown_escapes_labels(inventory):
    inventory["repositories"][0]["name"] = "idle|<b>"
    report = run(inventory)
    inventory["repositories"].reverse()
    assert run(inventory) == report
    rendered = render_markdown(report)
    assert "idle&#124;&lt;b&gt;" in rendered
    assert "idle|<b>" not in rendered


def test_normalizes_offsets_and_does_not_mutate_input(inventory):
    """03:00+03:00 equals midnight UTC, so it lies on the keep boundary."""
    inventory["repositories"][0]["pushed_at"] = "2026-04-01T03:00:00+03:00"
    before = copy.deepcopy(inventory)
    assert row(run(inventory))["consolidation"]["status"] == "KEEP"
    assert inventory == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("archived", "false"),
        ("open_issues", True),
        ("open_issues", -1),
        ("open_pull_requests", 0.5),
        ("pushed_at", "2026-03-01"),
        ("pushed_at", "2026-03-01T00:00:00"),
        ("pushed_at", "2026-07-01T00:00:00Z"),
        ("branches", {}),
        ("name", ""),
    ],
)
def test_rejects_invalid_repository_fields(inventory, field, value):
    inventory["repositories"][0][field] = value
    with pytest.raises(ValueError):
        run(inventory)


def test_rejects_duplicate_repository_or_branch_names(inventory):
    inventory["repositories"].append(copy.deepcopy(inventory["repositories"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        run(inventory)
    inventory["repositories"].pop()
    inventory["repositories"][0]["branches"].append({"name": "main"})
    with pytest.raises(ValueError, match="duplicate"):
        run(inventory)


@pytest.mark.parametrize(
    "issue_repositories", [[], ["absent"], ["tools", "tools"], "tools", None]
)
def test_requires_unambiguous_issue_destination(inventory, issue_repositories):
    with pytest.raises(ValueError):
        audit_inventory(
            inventory, stale_before=CUTOFF, issue_repositories=issue_repositories
        )


def test_cutoff_must_precede_observation(inventory):
    with pytest.raises(ValueError):
        audit_inventory(inventory, stale_before=OBSERVED, issue_repositories=["tools"])


def test_cli_json_and_markdown_are_read_only(inventory, tmp_path, capsys):
    source = tmp_path / "inventory.json"
    original = json.dumps(inventory)
    source.write_text(original, encoding="utf-8")
    args = [str(source), "--stale-before", CUTOFF, "--issue-repo", "tools"]
    assert main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["branch_reviews"] == 1
    assert main(args + ["--format", "markdown"]) == 0
    output = capsys.readouterr().out
    assert "REVIEW_CONSOLIDATION" in output
    assert "REVIEW_ROUTING" in output
    assert "REVIEW_DELETE" in output
    assert "NOT_EVALUATED" in output
    assert source.read_text(encoding="utf-8") == original
    assert list(tmp_path.iterdir()) == [source]


def test_cli_invalid_input_has_no_partial_report(tmp_path, capsys):
    source = tmp_path / "invalid.json"
    source.write_text('{"repositories":', encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main([str(source), "--stale-before", CUTOFF, "--issue-repo", "tools"])
    assert (
        error.value.code == 2
    )  # argparse error exit convention, Python library reference.
    assert capsys.readouterr().out == ""


def test_worked_example_through_module_entrypoint():
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "assetutilities.devtools.repo_audit",
            str(root / "examples/devtools/repo-audit.json"),
            "--stale-before",
            CUTOFF,
            "--issue-repo",
            "tools",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["summary"] == {
        "repositories": 3,
        "consolidation_reviews": 1,
        "issue_routing_reviews": 1,
        "branch_reviews": 1,
    }
