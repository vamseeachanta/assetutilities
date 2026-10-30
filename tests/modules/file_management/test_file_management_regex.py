"""Compare regex filtering with portable fixture-relative results."""

import shutil
import sys
from pathlib import Path

import yaml


def test_run_process(tmp_path, monkeypatch):
    from assetutilities.engine import engine

    source = Path(__file__).parent
    input_name = "test_file_management_regex.yml"
    snapshot = source / "results/test_file_management_regex_pytest.yml"
    expected = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    shutil.copyfile(source / input_name, tmp_path / input_name)
    shutil.copytree(source / "test_files", tmp_path / "test_files")
    monkeypatch.setattr(sys, "argv", ["assetutilities"])
    monkeypatch.chdir(tmp_path)

    result = engine(str(tmp_path / input_name), root_folder=str(tmp_path))
    obtained = {
        extension: sorted(Path(path).relative_to(tmp_path).as_posix() for path in paths)
        for extension, paths in result["file_management"]["input_files"].items()
    }
    assert obtained == {key: sorted(paths) for key, paths in expected.items()}
