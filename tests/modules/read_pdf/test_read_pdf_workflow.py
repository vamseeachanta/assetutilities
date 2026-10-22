"""Synthetic PDF examples; expectations follow directly from fixture text."""

from pathlib import Path

import pytest
import yaml
from PyPDF2 import PdfReader

from assetutilities.modules.pdf_utilities.read_pdf import ReadPDF

SAMPLE = (
    Path(__file__).resolve().parents[3] / "examples/workflows/read_pdf/data/sample.pdf"
)


def test_extract_all_entries(tmp_path):
    """Page 1 contains 'sample page 1'; page 4 contains 'sample page 4'.

    These strings are the literal inputs used to generate the synthetic PDF.
    The expected character count is independently len(the written text).
    """
    cfg = {
        "library": "PyPDF2",
        "Analysis": {"result_folder": str(tmp_path)},
        "files": {
            "from_pdf": [
                {"io": str(SAMPLE), "page": 1, "label": "first"},
                {"io": str(SAMPLE), "page": 4, "label": "last"},
            ]
        },
    }
    result = ReadPDF().read_pdf(cfg)
    assert [r["page"] for r in result] == [1, 4]
    for entry in result:
        text = Path(entry["output_file"]).read_text(encoding="utf-8")
        assert f"sample page {entry['page']}" in text
        assert entry["n_chars"] == len(text)
    assert yaml.safe_load(yaml.safe_dump(result)) == result
    assert len(PdfReader(SAMPLE).pages) == 4


def test_output_path_does_not_require_same_drive(tmp_path, monkeypatch):
    """Extraction must not relativize output against the working directory."""

    def different_drives(*args, **kwargs):
        raise ValueError("paths are on different drives")

    monkeypatch.setattr("os.path.relpath", different_drives)
    cfg = {
        "library": "PyPDF2",
        "Analysis": {"result_folder": tmp_path.as_posix()},
        "files": {"from_pdf": [{"io": SAMPLE.as_posix(), "page": 1}]},
    }
    result = ReadPDF().read_pdf(cfg)
    output = tmp_path / "read_pdf_file_1.txt"
    assert result[0]["output_file"] == output.as_posix()
    assert "sample page 1" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize("page", [0, -1, 5, True, "1"])
def test_invalid_page_rejected(tmp_path, page):
    """A four-page input admits integer YAML page numbers 1 through 4 only."""
    cfg = {
        "library": "PyPDF2",
        "Analysis": {"result_folder": str(tmp_path)},
        "files": {"from_pdf": [{"io": str(SAMPLE), "page": page}]},
    }
    with pytest.raises(ValueError, match="page"):
        ReadPDF().read_pdf(cfg)


def test_safe_unique_labels_and_fallback(tmp_path):
    """Two equal labels must produce two files under the input's results dir."""
    source = tmp_path / "sample.pdf"
    source.write_bytes(SAMPLE.read_bytes())
    cfg = {
        "library": "PyPDF2",
        "files": {
            "from_pdf": [
                {"io": str(source), "page": 1, "label": "../../same"},
                {"io": str(source), "page": 2, "label": "../../same"},
            ]
        },
    }
    rows = ReadPDF().read_pdf(cfg)
    outputs = [Path(r["output_file"]).resolve() for r in rows]
    assert outputs[0] != outputs[1]
    assert all(p.parent == tmp_path / "results" for p in outputs)


def test_blank_page_has_empty_text(tmp_path):
    """A synthetic page without text objects has exactly zero characters."""
    from PyPDF2 import PdfWriter

    source = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)  # Synthetic geometry, not a limit.
    with source.open("wb") as stream:
        writer.write(stream)
    rows = ReadPDF().read_pdf(
        {"library": "PyPDF2", "files": {"from_pdf": [{"io": str(source), "page": 1}]}}
    )
    assert rows[0]["n_chars"] == 0


@pytest.mark.parametrize("library", ["tabula", "camelot"])
def test_optional_table_dispatch_stays_serializable(library):
    """A synthetic one-cell table must survive a safe YAML round trip."""
    from types import SimpleNamespace
    from unittest.mock import patch
    import pandas as pd

    frame = pd.DataFrame({"synthetic": ["value"]})
    tables = [SimpleNamespace(df=frame)] if library == "camelot" else [frame]
    method = "from_pdf_camelot" if library == "camelot" else "from_pdf_tabula"
    cfg = {"library": library, "files": {"from_pdf": [{"io": "unused", "page": 1}]}}
    with patch.object(ReadPDF, method, return_value=tables) as handler:
        result = ReadPDF().read_pdf(cfg)
    handler.assert_called_once_with(cfg, 0)
    assert result == [{"tables": [[{"synthetic": "value"}]]}]
    assert yaml.safe_load(yaml.safe_dump(result)) == result
