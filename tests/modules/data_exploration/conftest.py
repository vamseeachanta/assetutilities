import hashlib
from pathlib import Path
import shutil
import tempfile

import pytest
import yaml

from assetutilities.engine import engine


FIXTURE_DIR = Path(__file__).parent


def _file_digests(directory):
    return {
        path.relative_to(directory): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


@pytest.fixture(autouse=True)
def preserve_repository_files():
    """Reject fixture edits and generated files beside the committed inputs."""
    repo_root = FIXTURE_DIR.parent.parent.parent
    directories = (FIXTURE_DIR, repo_root / "results", repo_root / "logs")
    before = {directory: _file_digests(directory) for directory in directories}
    yield
    assert {directory: _file_digests(directory) for directory in directories} == before


@pytest.fixture
def prepare_data_exploration_run(tmp_path):
    """Copy only the small inputs, with a fresh root for every invocation."""

    def prepare(input_file):
        source = FIXTURE_DIR / input_file
        run_root = Path(tempfile.mkdtemp(prefix=source.stem + "-", dir=tmp_path))
        csv_dir = run_root / "csv"
        csv_dir.mkdir()
        for csv_file in sorted((FIXTURE_DIR / "csv").glob("*.csv")):
            shutil.copyfile(csv_file, csv_dir / csv_file.name)

        config = yaml.safe_load(source.read_text(encoding="utf-8"))
        for group in config["data"]["groups"]:
            group["file_name"] = str(csv_dir / Path(group["file_name"]).name)
        if config["data"]["type"] == "file_management":
            config["file_management"]["input_directory"] = str(csv_dir)

        prepared_input = run_root / source.name
        prepared_input.write_text(yaml.safe_dump(config), encoding="utf-8")
        return prepared_input

    return prepare


@pytest.fixture
def data_exploration_run(prepare_data_exploration_run):
    def run(input_file):
        return engine(str(prepare_data_exploration_run(input_file)))

    return run
