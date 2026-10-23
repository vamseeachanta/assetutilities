"""Exercise Cartesian concatenation without writing into the fixture tree."""

import itertools
import shutil
import sys
from pathlib import Path

import yaml


def test_file_run(tmp_path, monkeypatch):
    from assetutilities.engine import engine

    source = Path(__file__).parent
    input_name = "file_edit_concatenate_2d_array.yml"
    inputs = yaml.safe_load((source / input_name).read_text(encoding="utf-8"))["input"][
        0
    ]
    expected_bytes = [
        b"".join((source / name).read_bytes() for name in group)
        for group in itertools.product(*inputs["input_files"])
    ]
    content = inputs["batch"]["content"]
    labels = ["D_no_tug_000MPH000WD_10moors", "D_no_tug_100MPH000WD_10moors"]
    shutil.copyfile(source / input_name, tmp_path / input_name)
    shutil.copytree(
        source / "concatenate",
        tmp_path / "concatenate",
        ignore=shutil.ignore_patterns("dats"),
    )
    monkeypatch.setattr(sys, "argv", ["assetutilities"])
    monkeypatch.chdir(tmp_path)

    engine(str(tmp_path / input_name), root_folder=str(tmp_path))
    output_dir = tmp_path / inputs["output_dir"]
    assert sorted(path.stem for path in output_dir.glob("*.dat")) == labels
    for label, expected in zip(labels, expected_bytes):
        assert (output_dir / (label + ".dat")).read_bytes() == expected
    batch = tmp_path / "file_edit_concatenate_2d_array_0.bat"
    assert batch.read_text(encoding="utf-8").splitlines() == [
        content + " " + str(output_dir / label) for label in labels
    ]
