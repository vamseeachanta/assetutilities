"""Pin pull-request coverage and preserve the existing test gate contract."""

from pathlib import Path
import os
import re
import shutil
import subprocess

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


def test_pull_request_activity_types_include_retargeting() -> None:
    """Retargeting must start fresh gates; leaving draft must start them too."""
    workflow = _workflow()
    events = workflow.get("on", workflow.get(True))
    assert events["pull_request"] == {
        "types": ["opened", "synchronize", "reopened", "edited", "ready_for_review"]
    }


def test_draft_pull_requests_skip_every_job() -> None:
    """Drafts do not queue gate jobs; ready_for_review runs them."""
    draft_skip = (
        "(github.event_name != 'pull_request' || "
        "github.event.pull_request.draft == false)"
    )
    for job_id, job in _workflow()["jobs"].items():
        assert str(job.get("if", "")).startswith(draft_skip), job_id


def test_edit_events_cannot_skip_jobs_or_steps() -> None:
    """An edit must not replace failing checks with skipped checks."""
    for job in _workflow()["jobs"].values():
        for node in [job, *job.get("steps", [])]:
            condition = str(node.get("if", ""))
            assert not re.search(r"github\.event\.(action|changes)\b", condition)


@pytest.mark.parametrize(
    "job_id,checkout_index",
    [
        (job_id, index)
        for job_id, job in _workflow()["jobs"].items()
        for index, step in enumerate(job.get("steps", []))
        if step.get("uses", "").startswith("actions/checkout@")
    ],
)
def test_checkouts_build_current_base_merge(job_id: str, checkout_index: int) -> None:
    """Every checkout must build and guard a merge of the current base and head."""
    steps = _workflow()["jobs"][job_id]["steps"]
    checkout = steps[checkout_index]
    merge = steps[checkout_index + 1]
    assert merge["if"] == "github.event_name == 'pull_request'"
    assert merge["id"] == "local_merge"
    assert merge["env"] == {
        "BASE_REF": "${{ github.event.pull_request.base.ref }}",
        "BASE_URL": "${{ github.event.pull_request.base.repo.clone_url }}",
        "PR_HEAD_SHA": "${{ github.event.pull_request.head.sha }}",
        "EVENT_BASE_SHA": "${{ github.event.pull_request.base.sha }}",
    }
    assert checkout["with"]["ref"] == (
        "${{ github.event.pull_request.head.sha || github.sha }}"
    )
    assert checkout["with"]["repository"] == (
        "${{ github.event.pull_request.head.repo.full_name || github.repository }}"
    )
    script = merge["run"]
    for fragment in (
        'git fetch --no-tags "$BASE_URL"',
        'git merge --no-ff --no-edit "$PR_HEAD_SHA"',
        "git cat-file -p HEAD",
        "${#parents[@]}",
        "${parents[0]}",
        "${parents[1]}",
        'echo "tip=$tip" >> "$GITHUB_OUTPUT"',
        "event_base=$EVENT_BASE_SHA",
        "exit 1",
    ):
        assert fragment in script
    assert "${{" not in script
    assert script.count("$EVENT_BASE_SHA") == 1


def test_merge_checkout_contract_is_nonempty_and_api_independent() -> None:
    """The contract cannot silently disappear or depend on computed merges."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "actions/checkout@" in text
    assert "merge_commit_sha" not in text
    assert "gh api" not in text
    assert not re.search(r"\[\[.*(?:base\.sha|EVENT_BASE_SHA)", text)


def _git(directory: Path, *arguments: str) -> str:
    """Run fixture Git commands without inherited repository bindings."""
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    return subprocess.check_output(
        ["git", *arguments], cwd=directory, env=env, text=True, stderr=subprocess.STDOUT
    ).strip()


def _commit(directory: Path, branch: str, filename: str, content: str) -> str:
    """Import synthetic fixture data without changing any configured identity."""
    message = "Update fixture content\n\nCo-Authored-By: Codex <noreply@openai.com>\n"
    parent = _git(
        directory, "for-each-ref", "--format=%(objectname)", f"refs/heads/{branch}"
    )
    stream = (
        f"commit refs/heads/{branch}\n"
        "committer Fixture <fixture> 1 +0000\n"
        f"data {len(message.encode())}\n{message}"
        + (f"from {parent}\n" if parent else "")
        + f"M 100644 inline {filename}\ndata {len(content.encode())}\n{content}\n"
    )
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    subprocess.run(
        ["git", "fast-import", "--quiet"],
        cwd=directory,
        env=env,
        input=stream,
        text=True,
        capture_output=True,
        check=True,
    )
    return _git(directory, "rev-parse", branch)


def _merge_fixture(root: Path, case: str) -> tuple[Path, str, str, str, str]:
    """Create a bare base repository and a detached runner checkout."""
    origin = root / "origin.git"
    _git(root, "init", "--bare", str(origin))
    event_base = _commit(origin, "main", "base.txt", "original\n")
    _git(origin, "branch", "feature", event_base)
    filename = "base.txt" if case == "conflict" else "feature.txt"
    head = _commit(origin, "feature", filename, "feature\n")
    if case == "shallow":
        for index in range(6):
            _commit(origin, "main", "history.txt", f"{index}\n")
    if case != "descendant":
        _commit(origin, "main", "base.txt", "current base\n")
    tip = _git(origin, "rev-parse", "main")
    runner = root / "runner"
    url = origin.as_uri()
    _git(root, "clone", "--depth=1", "--branch=feature", url, str(runner))
    _git(runner, "checkout", "--detach", head)
    return runner, url, head, tip, event_base


@pytest.mark.parametrize(
    "case", ["moved", "conflict", "shallow", "descendant", "no-api"]
)
def test_local_merge_behaviour(tmp_path: Path, case: str) -> None:
    """Execute the shipped script against real histories, including stale events."""
    runner, url, head, tip, event_base = _merge_fixture(tmp_path, case)
    merge = next(
        step
        for step in _workflow()["jobs"]["gates"]["steps"]
        if step.get("id") == "local_merge"
    )
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(
        BASE_REF="main",
        BASE_URL=url,
        PR_HEAD_SHA=head,
        EVENT_BASE_SHA=event_base,
        GITHUB_OUTPUT=str(tmp_path / "output"),
    )
    if case == "no-api":
        binaries = tmp_path / "bin"
        binaries.mkdir()
        for name in ("git", "sed"):
            (binaries / name).symlink_to(shutil.which(name))
        env["PATH"] = str(binaries)
        assert shutil.which("gh", path=env["PATH"]) is None
        assert shutil.which("curl", path=env["PATH"]) is None
    result = subprocess.run(
        ["/bin/bash", "-e", "-o", "pipefail", "-c", merge["run"]],
        cwd=runner,
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
    )
    if case == "conflict":
        assert result.returncode != 0
        assert "::error::" in result.stdout
        assert "tested=" not in result.stdout
        assert _git(runner, "rev-parse", "HEAD") == tip
        assert not (runner / ".git" / "MERGE_HEAD").exists()
        return
    assert result.returncode == 0, result.stdout + result.stderr
    parents = _git(runner, "show", "-s", "--format=%P", "HEAD").split()
    assert parents == [tip, head]
    tested = _git(runner, "rev-parse", "HEAD")
    tree = _git(runner, "rev-parse", "HEAD^{tree}")
    assert (
        f"tested={tested} first_parent={tip} second_parent={head} "
        f"tip={tip} event_base={event_base} tree={tree}"
    ) in result.stdout
    assert (tmp_path / "output").read_text() == f"tip={tip}\n"
    if case == "shallow":
        assert _git(runner, "merge-base", tip, head) == event_base
