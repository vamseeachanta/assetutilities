"""Check release boundaries from the actual YAML, following the PyPA guide."""

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def workflow():
    return yaml.safe_load(
        (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    )


def test_all_release_actions_are_pinned_to_release_commits():
    references = [
        step["uses"]
        for job in workflow()["jobs"].values()
        for step in job["steps"]
        if "uses" in step
    ]
    assert references
    for reference in references:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", reference), reference
    lines = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    for line in lines.splitlines():
        if re.match(r"\s*- uses:", line):
            assert re.search(r"@[0-9a-f]{40}\s+# v\d+\.\d+\.\d+\s*$", line), line


def test_dependabot_updates_github_actions():
    path = ROOT / ".github/dependabot.yml"
    assert path.is_file(), "Pinned release actions require dependency updates"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["version"] == 2
    assert any(
        update["package-ecosystem"] == "github-actions"
        and update["directory"] == "/"
        and update["schedule"]["interval"] == "weekly"
        for update in data["updates"]
    )


def test_release_build_disables_restored_uv_cache():
    setup = next(
        step
        for step in workflow()["jobs"]["build"]["steps"]
        if step.get("uses", "").startswith("astral-sh/setup-uv@")
    )
    assert setup.get("with", {}).get("enable-cache") is False


@pytest.fixture
def release_history(tmp_path):
    """Create complete synthetic history without borrowing caller Git objects."""
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }

    def git(*args, input=None):
        return subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            env=env,
            input=input,
            encoding="utf-8",
            capture_output=True,
            check=True,
        ).stdout.strip()

    git("init")
    tree = git("mktree", input="")
    parent = ""
    for message in ("base", "tip"):
        commit = git(
            "hash-object",
            "-t",
            "commit",
            "-w",
            "--stdin",
            input=(
                f"tree {tree}\n{parent}"
                "author Fixture <fixture> 0 +0000\n"
                "committer Fixture <fixture> 0 +0000\n"
                f"\n{message}\n"
            ),
        )
        parent = f"parent {commit}\n"
    git("update-ref", "HEAD", commit)
    return git, env


@pytest.mark.parametrize(
    ("release_ref", "main_ref", "expected_status"),
    [("HEAD", "HEAD", 0), ("HEAD^", "HEAD", 0), ("HEAD", "HEAD^", 1)],
)
def test_release_requires_main_ancestry(
    tmp_path, release_history, release_ref, main_ref, expected_status
):
    steps = workflow()["jobs"]["build"]["steps"]
    guards = [step for step in steps if step.get("name") == "Require release on main"]
    assert len(guards) == 1, "Release builds must reject commits outside main"
    guard = guards[0]
    checkout = next(
        step for step in steps if "actions/checkout@" in step.get("uses", "")
    )
    assert checkout["with"]["fetch-depth"] == 0
    assert steps.index(checkout) < steps.index(guard) < 2
    assert guard["env"] == {"RELEASE_COMMIT": "${{ github.sha }}"}
    git, env = release_history
    release = git("rev-parse", release_ref)
    main = git("rev-parse", main_ref)
    git("update-ref", "refs/remotes/origin/main", main)
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", guard["run"]],
        cwd=tmp_path,
        env=dict(env, RELEASE_COMMIT=release),
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert result.returncode == expected_status


def test_only_version_tags_trigger_release():
    data = workflow()
    assert data.get("on", data.get(True)) == {"push": {"tags": ["v*"]}}
    assert data["permissions"] == {"contents": "read"}
    assert data["concurrency"]["cancel-in-progress"] is False


def test_build_has_no_publishing_permission():
    build = workflow()["jobs"]["build"]
    assert "id-token" not in build.get("permissions", {})
    steps = build["steps"]
    checkout = next(
        step for step in steps if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["persist-credentials"] is False
    helper = next(step for step in steps if "build.sh" in step.get("run", ""))
    assert helper["env"] == {"RELEASE_TAG": "${{ github.ref_name }}"}
    assert helper["run"] == 'bash scripts/release/build.sh . dist "$RELEASE_TAG"'
    commands = [step.get("run") for step in steps]
    assert "python scripts/maintenance/check_wheel_package_data.py dist" in commands
    artifact = next(
        step
        for step in steps
        if step.get("uses", "").startswith("actions/upload-artifact@")
    )
    assert artifact["with"]["path"] == "dist/"
    assert artifact["with"]["if-no-files-found"] == "error"


def test_publisher_only_downloads_and_publishes_built_artifacts():
    data = workflow()
    publish = data["jobs"]["publish"]
    assert publish["needs"] == "build"
    assert (
        publish["if"]
        == "github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')"
    )
    assert publish["environment"]["name"] == "pypi"
    assert publish["permissions"] == {"id-token": "write"}
    download, upload = publish["steps"]
    assert download["uses"].startswith("actions/download-artifact@")
    assert upload["uses"].startswith("pypa/gh-action-pypi-publish@")
    build_artifact = next(
        step
        for step in data["jobs"]["build"]["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact@")
    )
    assert download["with"]["name"] == build_artifact["with"]["name"]
    assert download["with"]["path"] == "dist/"
    assert not upload.get("with", {}).get("skip-existing", False)
    assert "secrets." not in str(data)


def test_release_contract_is_run_by_existing_ci():
    data = yaml.safe_load(
        (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    )
    commands = [step.get("run") for step in data["jobs"]["gates"]["steps"]]
    assert "uv run python -m pytest tests/release" in commands
