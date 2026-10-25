"""Skip expensive draft checks while preserving ready checks and their names."""

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
WORKFLOW_PATHS = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
SNAPSHOT = json.loads(
    Path(__file__).with_name("workflow_job_names.json").read_text(encoding="utf-8")
)
DRAFT_GUARD = (
    "github.event_name != 'pull_request' || github.event.pull_request.draft == false"
)
# Dependency installs, documentation builds and the domain matrix are expensive.
HEAVY_JOBS = [
    ("docs.yml", "docs"),
    ("pdf-integration.yml", "pdf-integration"),
    ("tests.yml", "gates"),
    ("tests.yml", "domain-tests"),
]
PULL_REQUEST_TYPES = {"opened", "synchronize", "reopened", "ready_for_review"}


def _workflow(path: Path) -> dict:
    # BaseLoader preserves the Actions event key 'on' instead of treating it as bool.
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_workflow_inventory_is_preserved() -> None:
    """Deleting a workflow must fail even when no file remains to parametrize."""
    assert {path.name for path in WORKFLOW_PATHS} == set(SNAPSHOT)


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda path: path.name)
def test_workflow_and_job_names_are_preserved(path: Path) -> None:
    """Pin workflow names, job ids and explicit check names from the base tree."""
    workflow = _workflow(path)
    assert {
        "name": workflow.get("name"),
        "jobs": {job_id: job.get("name") for job_id, job in workflow["jobs"].items()},
    } == SNAPSHOT[path.name]


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda path: path.name)
def test_pull_request_types_include_readiness(path: Path) -> None:
    """Ready events start checks; existing extra activity types remain valid."""
    triggers = _workflow(path)["on"]
    assert ("pull_request" in triggers) == (path.name != "pages.yml")
    if "pull_request" in triggers:
        assert PULL_REQUEST_TYPES <= set(
            (triggers["pull_request"] or {}).get("types", [])
        )


@pytest.mark.parametrize("filename,job_id", HEAVY_JOBS)
def test_heavy_jobs_skip_draft_pull_requests(filename: str, job_id: str) -> None:
    """The exact guard permits ready requests and every non-PR event."""
    job = _workflow(WORKFLOWS / filename)["jobs"][job_id]
    assert job.get("if") == DRAFT_GUARD, f"{filename}:{job_id} lacks draft guard"


@pytest.mark.parametrize(
    "guard", [None, DRAFT_GUARD + " || true"], ids=["missing", "weakened"]
)
def test_invalid_draft_guard_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: str | None
) -> None:
    """Exercise the live policy assertion against corrupted workflow copies."""
    workflow = _workflow(WORKFLOWS / "docs.yml")
    job = workflow["jobs"]["docs"]
    if guard is None:
        job.pop("if")
    else:
        job["if"] = guard
    (tmp_path / "docs.yml").write_text(
        yaml.safe_dump(workflow), encoding="utf-8", newline="\n"
    )
    monkeypatch.setitem(globals(), "WORKFLOWS", tmp_path)

    with pytest.raises(AssertionError, match=r"docs\.yml:docs lacks draft guard"):
        test_heavy_jobs_skip_draft_pull_requests("docs.yml", "docs")


@pytest.mark.parametrize("renamed", ["workflow", "job-id", "check-name"])
def test_renamed_workflow_or_check_is_rejected(tmp_path: Path, renamed: str) -> None:
    """The snapshot assertion must reject workflow, job id and check name drift."""
    workflow = _workflow(WORKFLOWS / "docs.yml")
    if renamed == "workflow":
        workflow["name"] = "Renamed workflow"
    elif renamed == "job-id":
        workflow["jobs"]["renamed"] = workflow["jobs"].pop("docs")
    else:
        workflow["jobs"]["docs"]["name"] = "Renamed check"
    path = tmp_path / "docs.yml"
    path.write_text(yaml.safe_dump(workflow), encoding="utf-8", newline="\n")

    with pytest.raises(AssertionError):
        test_workflow_and_job_names_are_preserved(path)


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=lambda path: path.name)
def test_manual_runs_remain_available(path: Path) -> None:
    assert "workflow_dispatch" in _workflow(path)["on"]


def test_short_source_hygiene_job_remains_active_on_drafts() -> None:
    """The short hygiene and secret checks continue to run on draft requests."""
    job = _workflow(WORKFLOWS / "source-hygiene.yml")["jobs"]["source-hygiene"]
    assert "if" not in job


def test_draft_policy_runs_in_ci_gates() -> None:
    """Keep this policy enforced even when the domain selector picks no tests."""
    steps = _workflow(WORKFLOWS / "tests.yml")["jobs"]["gates"]["steps"]
    assert "uv run python -m pytest tests/workflows/test_ci_draft_policy.py" in [
        step.get("run", "") for step in steps
    ]
