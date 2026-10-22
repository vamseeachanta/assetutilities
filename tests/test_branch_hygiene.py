"""Branch decisions use explicit hand-derived set membership, not age guesses.

Fixture: main and topic/done have reachable tips; topic/open does not.
Subtracting protected/current branches leaves only topic/done for review.
The monthly example retains January and the preceding December across a year.
"""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts/git/branch_hygiene.py"
SPEC = importlib.util.spec_from_file_location("branch_hygiene", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_classification():
    refs = ["refs/heads/main", "refs/heads/topic/done", "refs/heads/topic/open"]
    result = module.classify(refs, refs[:2], "topic/open", "main")
    assert [row["status"] for row in result] == [
        "protected", "merged_review", "current"
    ]


def test_unmerged_is_preserved_and_default_names_protected():
    refs = [f"refs/heads/{name}" for name in ("main", "master", "develop", "topic")]
    result = module.classify(refs, [], None, "develop")
    assert [row["status"] for row in result] == [
        "protected", "protected", "protected", "unmerged"
    ]


def test_remote_names_and_symbolic_refs():
    refs = ["refs/remotes/origin/main", "refs/remotes/origin/topic"]
    result = module.classify(refs, refs, None, "origin/main")
    assert [row["status"] for row in result] == ["protected", "merged_review"]
    assert result[1]["ref"] == "refs/remotes/origin/topic"


@pytest.mark.parametrize("month,previous", [("202601", "202512"), ("202603", "202602")])
def test_month_retention(month, previous):
    # Calendar predecessor: January wraps to December of the preceding year.
    refs = [f"refs/heads/{name}" for name in (month, previous, "202401", "topic")]
    result = module.classify(refs, refs, None, "main", month)
    assert [row["monthly"] for row in result] == [
        "retained", "retained", "outside_window", "not_monthly"
    ]


@pytest.mark.parametrize("month", ["202600", "202613", "20261", "abcd01", "000001"])
def test_invalid_month(month):
    with pytest.raises(ValueError):
        module.classify([], [], None, "main", month)


def test_runner_clears_git_bindings(monkeypatch):
    tmp_path = Path("fixture")
    monkeypatch.setenv("GIT_DIR", "unrelated")
    monkeypatch.setenv("GIT_WORK_TREE", "unrelated")
    monkeypatch.setenv("GIT_COMMON_DIR", "unrelated")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    seen = {}

    def fake_run(args, **kwargs):
        seen.update(kwargs)
        assert args == ["git", "rev-parse", "--is-inside-work-tree"]
        return subprocess.CompletedProcess(args, 0, "true\n", "")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    assert module.git(tmp_path, "rev-parse", "--is-inside-work-tree") == "true"
    assert not any(key.startswith("GIT_") for key in seen["env"])
    assert seen["cwd"] == tmp_path
    assert seen["shell"] is False


def test_inspection_only_uses_read_commands(monkeypatch):
    tmp_path = Path("fixture")
    calls = []

    def fake_git(repo, *args):
        calls.append(args)
        if args[0] == "rev-parse":
            return "a" * 40
        if args[0] == "symbolic-ref":
            return "topic/open"
        if "--merged" in args:
            return "refs/heads/main\nrefs/heads/topic/done"
        return "refs/heads/main\t\nrefs/heads/topic/done\t\nrefs/heads/topic/open\t\nrefs/remotes/origin/HEAD\trefs/remotes/origin/main"

    monkeypatch.setattr(module, "git", fake_git)
    report = module.inspect(repo=tmp_path, base="main")
    assert len(report["branches"]) == 3
    assert report["base_commit"] == "a" * 40
    assert {call[0] for call in calls} == {"rev-parse", "symbolic-ref", "for-each-ref"}
    assert [row["status"] for row in report["branches"]] == [
        "protected", "merged_review", "current"
    ]


def test_detached_head(monkeypatch):
    tmp_path = Path("fixture")
    def fake_git(repo, *args):
        if args[0] == "symbolic-ref":
            raise module.GitError("symbolic-ref", 1)
        return "a" * 40 if args[0] == "rev-parse" else ""

    monkeypatch.setattr(module, "git", fake_git)
    assert module.inspect(tmp_path, "main")["current"] is None


def test_symbolic_ref_error_is_not_detached(monkeypatch):
    tmp_path = Path("fixture")
    def fake_git(repo, *args):
        if args[0] == "symbolic-ref":
            raise module.GitError("symbolic-ref", 128)
        return "a" * 40

    monkeypatch.setattr(module, "git", fake_git)
    with pytest.raises(module.GitError):
        module.inspect(tmp_path, "main")


def test_cli_json_and_findings_exit(monkeypatch, capsys):
    report = {"branches": [{"status": "merged_review"}]}
    monkeypatch.setattr(module, "inspect", lambda *args: report)
    assert module.main(["--base", "main"]) == 0
    assert json.loads(capsys.readouterr().out) == report
    assert module.main(["--base", "main", "--fail-on-findings"]) == 1


def test_cli_failure_is_redacted(monkeypatch, capsys):
    def fail(*args):
        raise OSError("sensitive environment details")

    monkeypatch.setattr(module, "inspect", fail)
    assert module.main(["--base", "main"]) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "sensitive" not in captured.err


def test_invalid_base_option():
    with pytest.raises(ValueError):
        module.inspect(Path("."), "--all")


@pytest.mark.parametrize("code", [1, 128])
def test_git_failure_does_not_expose_stderr(monkeypatch, code):
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess(args, code, "", "private details"))
    with pytest.raises(module.GitError) as caught:
        module.git(Path("fixture"), "for-each-ref")
    assert caught.value.returncode == code
    assert "private details" not in str(caught.value)


def test_cli_no_findings(monkeypatch, capsys):
    monkeypatch.setattr(module, "inspect", lambda *args: {"branches": []})
    assert module.main(["--base", "main", "--fail-on-findings"]) == 0
    assert json.loads(capsys.readouterr().out) == {"branches": []}


def test_monthly_policy_never_changes_reachability():
    refs = ["refs/heads/202401", "refs/heads/202601"]
    report = module.classify(refs, [], None, "main", "202601")
    assert [row["status"] for row in report] == ["unmerged", "unmerged"]
    assert [row["monthly"] for row in report] == ["outside_window", "retained"]


def test_current_branch_wins_over_merged():
    refs = ["refs/heads/topic"]
    assert module.classify(refs, refs, "topic", "main")[0]["status"] == "current"


def test_full_base_ref_is_protected():
    refs = ["refs/heads/integration"]
    assert module.classify(refs, refs, None, refs[0])[0]["status"] == "protected"


def test_base_failure_stops_inspection(monkeypatch):
    calls = []

    def fail(repo, *args):
        calls.append(args)
        raise module.GitError(args[0], 128)

    monkeypatch.setattr(module, "git", fail)
    with pytest.raises(module.GitError):
        module.inspect(Path("fixture"), "missing")
    assert len(calls) == 1


@pytest.fixture
def git_repository(tmp_path):
    repo = tmp_path / "repository"
    repo.mkdir()
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }

    def run_git(*args, input=None):
        return subprocess.run(
            ["git", *args], cwd=repo, env=environment,
            input=input.encode("utf-8") if input is not None else None,
            capture_output=True, check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout.decode("utf-8").strip()

    run_git("init", "--initial-branch=main")
    tree = run_git("hash-object", "-w", "-t", "tree", "--stdin", input="")
    # Build the fixture commit without requiring or changing Git identity settings.
    commit = run_git(
        "hash-object", "-w", "-t", "commit", "--stdin",
        input=f"tree {tree}\nauthor Fixture <> 0 +0000\n"
              "committer Fixture <> 0 +0000\n\nInitial fixture\n",
    )
    run_git("update-ref", "refs/heads/main", commit)
    return repo, run_git


@pytest.mark.parametrize("base,base_ref", [
    ("integration", "refs/heads/integration"),
    ("heads/integration", "refs/heads/integration"),
    ("refs/heads/integration", "refs/heads/integration"),
    ("origin/integration", "refs/remotes/origin/integration"),
    ("remotes/origin/integration", "refs/remotes/origin/integration"),
    ("refs/remotes/origin/integration", "refs/remotes/origin/integration"),
])
def test_inspection_protects_resolved_base(git_repository, base, base_ref, capsys):
    repo, run_git = git_repository
    commit = run_git("rev-parse", "HEAD")
    run_git("update-ref", base_ref, commit)
    commands = [("status", "--porcelain"), ("rev-parse", "HEAD"),
                ("for-each-ref", "--format=%(refname) %(objectname)")]
    before = [run_git(*args) for args in commands]

    report = module.inspect(repo, base)

    assert report["base"] == base
    assert report["base_commit"] == commit
    assert {row["ref"]: row["status"] for row in report["branches"]} == {
        "refs/heads/main": "protected", base_ref: "protected",
    }
    assert module.main([
        "--repo", repo.as_posix(), "--base", base, "--fail-on-findings",
    ]) == 0
    assert json.loads(capsys.readouterr().out) == report
    assert [run_git(*args) for args in commands] == before


@pytest.mark.parametrize("base", ["HEAD", "HEAD~0", "HEAD^{commit}", "commit_id"])
def test_commit_expression_does_not_protect_unrelated_refs(git_repository, base):
    repo, run_git = git_repository
    commit = run_git("rev-parse", "HEAD")
    run_git("update-ref", "refs/heads/topic", commit)
    if base == "commit_id":
        base = commit

    report = module.inspect(repo, base)

    assert report["base_commit"] == commit
    assert {row["ref"]: row["status"] for row in report["branches"]} == {
        "refs/heads/main": "protected", "refs/heads/topic": "merged_review",
    }
