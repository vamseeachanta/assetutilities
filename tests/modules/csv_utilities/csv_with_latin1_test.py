"""Regression for the legacy txt_file input and Latin-1 fixture."""

from pathlib import Path
import shutil

import yaml

from assetutilities.engine import engine


def test_run_process(tmp_path):
    directory = Path(__file__).parent
    cfg = yaml.safe_load((directory / "csv_with_latin1.yml").read_text())
    source = directory / cfg["csv_utilities"]["txt_file"]
    shutil.copyfile(source, tmp_path / source.name)
    input_file = tmp_path / "input.yml"
    input_file.write_text(yaml.safe_dump(cfg))
    result = engine(str(input_file))
    outputs = result["csv_utilities"]["results"]
    assert Path(outputs["normalized"]).is_file()
    summary = yaml.safe_load(Path(outputs["summary"]).read_text())
    assert summary["encoding_used"] == "latin1"
    assert summary["n_rows"] > 0
    assert summary["n_columns"] == len(summary["columns"])
