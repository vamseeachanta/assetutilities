"""Tag checks use literal metadata and independent string concatenation."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def validator():
    spec = importlib.util.spec_from_file_location(
        "validate_release", ROOT / "scripts/release/validate_release.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("version", ["1.2.3", "1.2.3rc1", "1.2.3.post1"])
def test_exact_tag_and_version(validator, tmp_path, version):
    """For each literal version, expected tag is the literal 'v' plus version."""
    (tmp_path / "pyproject.toml").write_text(f'[project]\nversion = "{version}"\n')
    assert validator.validate(tmp_path, "v" + version, tmp_path / "dist") == version


@pytest.mark.parametrize(
    "metadata",
    [
        "[project]\ndynamic = ['version']\n",
        "[project]\nversion = ''\n",
        "[project]\nversion = 123\n",
        "[project]\nversion = '1.2.3'\ndynamic = ['version']\n",
        "[project]\nversion = [\n",
        "[build-system]\nrequires = []\n",
        'project = "invalid"\n',
    ],
)
def test_invalid_or_dynamic_metadata_rejected(validator, tmp_path, metadata):
    (tmp_path / "pyproject.toml").write_text(metadata)
    with pytest.raises(ValueError):
        validator.validate(tmp_path, "v1.2.3", tmp_path / "dist")


def test_output_file_rejected(validator, tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n')
    output = tmp_path / "dist"
    output.write_text("retained")
    with pytest.raises(ValueError):
        validator.validate(tmp_path, "v1.2.3", output)
    assert output.read_text() == "retained"


def test_missing_metadata_rejected(validator, tmp_path):
    with pytest.raises(ValueError):
        validator.validate(tmp_path, "v1.2.3", tmp_path / "dist")
