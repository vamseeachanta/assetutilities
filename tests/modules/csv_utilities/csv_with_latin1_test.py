"""Legacy txt_file alias stays supported without writing tracked test output."""

from pathlib import Path

import yaml

from assetutilities.engine import engine


def test_run_process(tmp_path):
    """A header and one authored row give one record with two columns."""
    source = tmp_path / "input.csv"
    source.write_bytes("name,value\ncafé,7\n".encode("latin1"))
    config = tmp_path / "input.yml"
    config.write_text(
        yaml.safe_dump(
            {
                "basename": "csv_utilities",
                "csv_utilities": {
                    "txt_file": "input.csv",
                    "encoding": "latin1",
                    "delimiter": ",",
                },
            }
        )
    )
    result = engine(str(config))
    outputs = result["csv_utilities"]["results"]
    assert Path(outputs["normalized_file"]).read_text() == "name,value\ncafé,7\n"
    summary = yaml.safe_load(Path(outputs["summary_file"]).read_text())
    assert (summary["n_rows"], summary["n_columns"]) == (1, 2)
