"""Check release boundaries from the actual YAML, following the PyPA guide."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def workflow():
    return yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())


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
    assert upload["uses"] == "pypa/gh-action-pypi-publish@release/v1"
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
    data = yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text())
    commands = [step.get("run") for step in data["jobs"]["gates"]["steps"]]
    assert "uv run python -m pytest tests/release" in commands
