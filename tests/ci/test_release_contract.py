"""Release validation with independently constructed package metadata."""

import importlib.util
import io
import re
import shlex
import tarfile
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "validate_release", ROOT / "scripts/ci/validate_release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def _source(tmp_path):
    """Synthetic version strings exercise exact equality, not version arithmetic."""
    (tmp_path / "pyproject.toml").write_text(
        '# café\n[project]\nname="assetutilities"\nversion="1.2.3"\n',
        encoding="utf-8",
        newline="\n",
    )
    package = tmp_path / "src/assetutilities"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '# café\n__version__ = "1.2.3"\n', encoding="utf-8", newline="\n"
    )
    return tmp_path


def _distributions(path, name="assetutilities", version="1.2.3"):
    path.mkdir()
    metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n\n".encode()
    # Core Metadata specification 2.1: Name and Version are required headers.
    with zipfile.ZipFile(path / "assetutilities-1.2.3-py3-none-any.whl", "w") as wheel:
        wheel.writestr("assetutilities-1.2.3.dist-info/METADATA", metadata)
    with tarfile.open(path / "assetutilities-1.2.3.tar.gz", "w:gz") as archive:
        member = tarfile.TarInfo("assetutilities-1.2.3/PKG-INFO")
        member.size = len(metadata)
        archive.addfile(member, io.BytesIO(metadata))


def test_source_and_artifacts_match_tag(tmp_path):
    root = _source(tmp_path)
    _distributions(root / "dist")
    assert release.validate_source(root, "v1.2.3") == "1.2.3"
    release.validate_distributions(root / "dist", "1.2.3")


@pytest.mark.parametrize("tag", ["1.2.3", "v1.2.4", "v1.2.3-extra", ""])
def test_wrong_tag_is_rejected(tmp_path, tag):
    with pytest.raises(ValueError, match="tag"):
        release.validate_source(_source(tmp_path), tag)


def test_source_version_drift_is_rejected(tmp_path):
    root = _source(tmp_path)
    (root / "src/assetutilities/__init__.py").write_text(
        '__version__ = "old"\n', encoding="utf-8", newline="\n"
    )
    with pytest.raises(ValueError, match="__version__"):
        release.validate_source(root)


@pytest.mark.parametrize(
    "name,version", [("wrong", "1.2.3"), ("assetutilities", "1.2.4")]
)
def test_artifact_metadata_drift_is_rejected(tmp_path, name, version):
    _distributions(tmp_path / "dist", name, version)
    with pytest.raises(ValueError, match="metadata"):
        release.validate_distributions(tmp_path / "dist", "1.2.3")


def test_missing_distribution_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="wheel.*sdist"):
        release.validate_distributions(tmp_path, "1.2.3")


def test_uv_output_directory_ignore_file_is_allowed(tmp_path):
    _distributions(tmp_path / "dist")
    (tmp_path / "dist/.gitignore").write_text("*\n", encoding="utf-8", newline="\n")
    release.validate_distributions(tmp_path / "dist", "1.2.3")


def test_unexpected_distribution_file_is_rejected(tmp_path):
    _distributions(tmp_path / "dist")
    (tmp_path / "dist/unexpected.txt").write_text(
        "unexpected", encoding="utf-8", newline="\n"
    )
    with pytest.raises(ValueError, match="wheel.*sdist"):
        release.validate_distributions(tmp_path / "dist", "1.2.3")


def test_release_workflow_has_isolated_publish_permissions():
    with (ROOT / ".github/workflows/release.yml").open(
        encoding="utf-8", newline="\n"
    ) as stream:
        workflow = yaml.safe_load(stream)
    events = workflow.get("on", workflow.get(True))
    assert events["push"] == {"tags": ["v*"]}
    assert "workflow_dispatch" in events
    assert workflow["permissions"] == {"contents": "read"}
    build = workflow["jobs"]["build"]
    publish = workflow["jobs"]["publish"]
    assert "id-token" not in build.get("permissions", {})
    assert publish["permissions"] == {"id-token": "write"}
    assert publish["environment"] == "pypi"
    assert publish["needs"] == "build"
    assert "github.event_name == 'push'" in publish["if"]
    assert "github.ref_type == 'tag'" in publish["if"]
    commands = "\n".join(step.get("run", "") for step in build["steps"])
    assert "git merge-base --is-ancestor HEAD origin/main" in commands
    assert "scripts/ci/validate_release.py" in commands
    assert "check_wheel_package_data.py" in commands
    assert "twine check --strict" in commands
    assert any(
        step.get("uses", "").startswith("pypa/gh-action-pypi-publish@")
        for step in publish["steps"]
    )


def test_release_actions_are_pinned_with_version_comments():
    with (ROOT / ".github/workflows/release.yml").open(
        encoding="utf-8", newline="\n"
    ) as stream:
        uses = [line.strip() for line in stream if "uses:" in line]
    assert len(uses) == 6
    for line in uses:
        assert re.search(r"@[0-9a-f]{40} # v\d+\.\d+\.\d+$", line), line


def test_release_tool_requirements_are_exact_versions():
    with (ROOT / ".github/workflows/release.yml").open(
        encoding="utf-8", newline="\n"
    ) as stream:
        workflow = yaml.safe_load(stream)
    requirements = []
    uv_step = next(
        step
        for step in workflow["jobs"]["build"]["steps"]
        if step.get("uses", "").startswith("astral-sh/setup-uv@")
    )
    assert uv_step["with"]["version"] == "0.13.1"
    for step in workflow["jobs"]["build"]["steps"]:
        tokens = shlex.split(step.get("run", ""))
        requirements.extend(
            tokens[index + 1] for index, token in enumerate(tokens) if token == "--with"
        )
    assert requirements
    assert all(re.fullmatch(r"[\w-]+==\d+\.\d+\.\d+", r) for r in requirements)
    assert "pytest==8.4.2" in requirements
    assert "twine==6.2.0" in requirements


def test_source_reads_binary_toml_and_utf8_python(tmp_path, monkeypatch):
    root = _source(tmp_path)
    path_open = Path.open

    def explicit_open(path, mode="r", *args, **kwargs):
        if path.name == "pyproject.toml":
            assert mode == "rb"
        elif path.name == "__init__.py":
            assert kwargs.get("encoding") == "utf-8"
            assert kwargs.get("newline") == "\n"
        return path_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", explicit_open)
    assert release.validate_source(root, "v1.2.3") == "1.2.3"
