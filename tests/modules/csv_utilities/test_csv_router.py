"""CSV expectations are independent counts of the literal synthetic rows."""

from pathlib import Path

import pytest
import yaml

from assetutilities.modules.csv_utilities.csv_utilities_router import CSVUtilitiesRouter


@pytest.mark.parametrize("legacy", [False, True])
def test_encoding_fallback_and_alias(tmp_path, legacy):
    """Header name/value has 2 columns; cafe/accent and tea give 2 rows.

    Latin-1 byte e9 cannot decode as UTF-8, so the fallback must be latin-1.
    """
    source = tmp_path / "sample.csv"
    source.write_bytes("name,value\ncafé,2\ntea,3\n".encode("latin-1"))
    cfg = {
        "Analysis": {
            "analysis_root_folder": str(tmp_path),
            "result_folder": str(tmp_path / "out"),
        },
        "csv_utilities": {"txt_file" if legacy else "input_file": source.name},
    }
    result = CSVUtilitiesRouter().router(cfg)["csv_utilities"]["results"]
    summary = yaml.safe_load(Path(result["summary"]).read_text(encoding="utf-8"))
    assert summary["encoding_used"] == "latin-1"
    assert summary["n_rows"] == 2
    assert summary["n_columns"] == 2
    assert summary["columns"] == ["name", "value"]
    normalized = Path(result["normalized"]).read_text(encoding="utf-8")
    assert normalized == "name,value\ncafé,2\ntea,3\n"
    assert b"\r\n" not in Path(result["normalized"]).read_bytes()
    assert b"\r\n" not in Path(result["summary"]).read_bytes()


def test_explicit_encoding_delimiter_and_row_limit(tmp_path):
    """Two literal input rows truncated to the requested first row."""
    source = tmp_path / "sample.csv"
    source.write_text("name;value\nred;2\nblue;3\n", encoding="utf-8", newline="\n")
    cfg = {
        "Analysis": {"result_folder": str(tmp_path / "out")},
        "csv_utilities": {
            "input_file": str(source),
            "encoding": "utf-8",
            "delimiter": ";",
            "nrows": 1,
        },
    }
    rows = CSVUtilitiesRouter().router(cfg)["csv_utilities"]["results"]
    summary = yaml.safe_load(Path(rows["summary"]).read_text(encoding="utf-8"))
    assert summary["encoding_used"] == "utf-8"
    assert summary["n_rows"] == 1
    assert summary["delimiter"] == ";"
    assert "blue" not in Path(rows["normalized"]).read_text(encoding="utf-8")


def test_explicit_encoding_does_not_silently_fallback(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_bytes(b"name\n\xe9\n")
    cfg = {
        "Analysis": {"result_folder": str(tmp_path / "out")},
        "csv_utilities": {"input_file": str(source), "encoding": "utf-8"},
    }
    with pytest.raises(UnicodeDecodeError):
        CSVUtilitiesRouter().router(cfg)


@pytest.mark.parametrize(
    "options", [{}, {"input_file": ""}, {"txt_file": ""}, {"input_file": None}]
)
def test_missing_input_reports_required_aliases(tmp_path, options):
    cfg = {
        "Analysis": {"result_folder": tmp_path.as_posix()},
        "csv_utilities": options,
    }
    with pytest.raises(
        ValueError, match=r"^csv_utilities requires input_file \(or txt_file\)$"
    ):
        CSVUtilitiesRouter().router(cfg)
