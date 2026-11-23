"""Exercise array concatenation without writing into the fixture tree."""

import shutil
import sys
from pathlib import Path

import yaml


def test_file_run(tmp_path, monkeypatch):
    from assetutilities.engine import engine

    source = Path(__file__).parent
    input_name = "file_edit_concatenate_array.yml"
    inputs = yaml.safe_load((source / input_name).read_text(encoding="utf-8"))["input"][
        0
    ]
    expected_bytes = [
        b"".join((source / name).read_bytes() for name in group)
        for group in inputs["input_files"]
    ]
    content = inputs["batch"]["content"]
    shutil.copyfile(source / input_name, tmp_path / input_name)
    shutil.copytree(source / "concatenate", tmp_path / "concatenate")
    monkeypatch.setattr(sys, "argv", ["assetutilities"])
    monkeypatch.chdir(tmp_path)

    result = engine(str(tmp_path / input_name), root_folder=str(tmp_path))
    outputs = result["file_edit"]["output_filename"]
    assert outputs == [["no_load_09moors", "no_load_10moors"]]
    for label, expected in zip(outputs[0], expected_bytes):
        assert (tmp_path / (label + ".dat")).read_bytes() == expected
    batch = tmp_path / "file_edit_concatenate_array_0.bat"
    assert batch.is_file()
    assert batch.read_text(encoding="utf-8").splitlines() == [
        content + " " + str(tmp_path / label) for label in outputs[0]
    ]
