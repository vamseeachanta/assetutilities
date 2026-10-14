"""Read-back and reproducibility contracts for the P6 report output path."""

import copy
import json
import shutil
from pathlib import Path
from zipfile import ZipFile

import pytest
from docx import Document
from PyPDF2 import PdfReader


SAMPLE = Path(__file__).parents[3] / "examples/workflows/reportgen/standard-report.json"


def api():
    from assetutilities.common.reportgen import standard

    return standard


def sample():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_word_structure_and_readback(tmp_path):
    module = api()
    data = sample()
    target = module.write_docx(data, tmp_path / "report.docx")
    doc = Document(target)
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert headings[:3] == ["1 Executive Summary", "Revision history", "Contents"]
    expected = [f"{i} {name}" for i, name in enumerate(module.SECTIONS, 1)]
    assert [h for h in headings if h in expected] == expected
    assert headings.index("2 Introduction") > headings.index("Contents")
    assert "3.7 Load cases" in headings
    assert "9.1 Published references" in headings
    assert "9.2 Internal references" in headings
    assert "Appendix A – Supporting evidence" in headings
    history = doc.tables[0]
    assert [[c.text for c in r.cells] for r in history.rows] == [
        ["Revision", "Date", "What changed and why"],
        ["1", "2026-10-14", "First issue of the synthetic layout example."],
    ]
    assert history.rows[-1].cells[0].text == data["revision"]
    result = doc.tables[1]
    table = data["sections"][4]["blocks"][1]
    assert [c.text for c in result.rows[0].cells] == table["columns"]
    assert [[c.text for c in r.cells] for r in result.rows[1:]] == table["rows"]
    assert "Table 5.1 – Synthetic readings" in [p.text for p in doc.paragraphs]
    section = doc.sections[0]
    assert abs(section.page_width.mm - 210) < 0.1
    assert abs(section.left_margin.mm - 18) < 0.1
    assert doc.styles["Normal"].font.size.pt == 11
    with ZipFile(target) as archive:
        xml = archive.read("word/document.xml").decode()
        assert "tblHeader" in xml
        assert 'w:anchor="section_3"' in xml
        assert 'w:name="section_3"' in xml


def test_word_is_byte_identical_and_does_not_mutate_input(tmp_path):
    module = api()
    data = sample()
    original = copy.deepcopy(data)
    first = module.write_docx(data, tmp_path / "first.docx")
    second = module.write_docx(data, tmp_path / "second.docx")
    assert first.read_bytes() == second.read_bytes()
    assert data == original


@pytest.mark.parametrize(
    "change",
    [
        "revision",
        "sections",
        "design",
        "references",
        "empty",
        "deep",
        "rows",
        "ragged",
        "date",
        "type",
    ],
)
def test_invalid_report_is_rejected_before_writing(tmp_path, change):
    module = api()
    data = sample()
    if change == "revision":
        data["revision"] = "2"
    elif change == "sections":
        data["sections"].reverse()
    elif change == "design":
        data["sections"][2]["subsections"].pop()
    elif change == "references":
        data["sections"][8]["subsections"].pop()
    elif change == "empty":
        data["sections"][1]["blocks"] = []
    elif change == "deep":
        data["sections"][2]["subsections"][0]["subsections"] = [{}]
    elif change == "rows":
        data["sections"][4]["blocks"][1]["rows"] *= 16
    elif change == "ragged":
        data["sections"][4]["blocks"][1]["rows"] = [["missing column"]]
    elif change == "date":
        data["revisions"][0]["date"] = "invalid"
    else:
        data["sections"][0]["blocks"] = [{"type": "unknown"}]
    target = tmp_path / "invalid.docx"
    with pytest.raises(ValueError):
        module.write_docx(data, target)
    assert not target.exists()


def test_revision_history_preserves_earlier_records(tmp_path):
    module = api()
    data = sample()
    earlier = copy.deepcopy(data["revisions"])
    data["revision"] = "2"
    data["revisions"].append(
        {
            "revision": "2",
            "date": "2026-10-15",
            "change": "Added a second synthetic reading.",
        }
    )
    doc = Document(module.write_docx(data, tmp_path / "revision.docx"))
    assert [c.text for c in doc.tables[0].rows[1].cells] == list(earlier[0].values())
    assert doc.tables[0].rows[-1].cells[0].text == "2"


def test_converter_requires_installed_tool(tmp_path, monkeypatch):
    module = api()
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="LibreOffice"):
        module.convert_pdf(
            tmp_path / "source.docx", tmp_path / "report.pdf", tmp_path / "scratch"
        )


def test_converter_reports_failure_without_publishing_output(tmp_path, monkeypatch):
    module = api()
    source = module.write_docx(sample(), tmp_path / "source.docx")
    monkeypatch.setattr(module.shutil, "which", lambda name: "libreoffice")

    class Result:
        returncode = 1

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: Result())
    with pytest.raises(RuntimeError, match="conversion failed"):
        module.convert_pdf(source, tmp_path / "report.pdf", tmp_path / "scratch")
    assert not (tmp_path / "report.pdf").exists()


def test_pdf_readback_and_byte_identical_builds(tmp_path):
    module = api()
    assert shutil.which("libreoffice"), "PDF integration requires installed LibreOffice"
    source = module.write_docx(sample(), tmp_path / "source.docx")
    first = module.convert_pdf(source, tmp_path / "first.pdf", tmp_path / "scratch")
    second = module.convert_pdf(source, tmp_path / "second.pdf", tmp_path / "scratch")
    assert first.read_bytes() == second.read_bytes()
    reader = PdfReader(first)
    text = "\n".join(page.extract_text() for page in reader.pages)
    for expected in (
        "Executive Summary",
        "Revision history",
        "First issue",
        "Synthetic readings",
        "Supporting evidence",
    ):
        assert expected in text
    assert all(abs(float(p.mediabox.width) - 595.3) < 1 for p in reader.pages)


def test_existing_entry_point_routes_standard_report(tmp_path):
    from assetutilities.common.reportgen.reportgen import run

    run(
        {
            "reporting_standard": "P6",
            "report": sample(),
            "report_details": {
                "target_report_type": "docx",
                "target_file_stub": "standard",
            },
            "important_paths": {
                "project_root": str(tmp_path),
                "outputs_path": "outputs",
            },
        }
    )
    assert (tmp_path / "outputs/standard.out.docx").is_file()


def test_summary_subsections_are_not_lost(tmp_path):
    module = api()
    data = sample()
    data["sections"][0]["subsections"] = [
        {"name": "Decision basis", "blocks": ["Only the layout can be used."]}
    ]
    doc = Document(module.write_docx(data, tmp_path / "summary.docx"))
    paragraphs = [p.text for p in doc.paragraphs]
    assert "1.1 Decision basis" in paragraphs
    assert paragraphs.index("Only the layout can be used.") < paragraphs.index(
        "Revision history"
    )


def test_appendix_subsections_cannot_have_third_level(tmp_path):
    module = api()
    data = sample()
    data["sections"][4]["subsections"] = [
        {"name": "Evidence", "blocks": ["Supporting data."], "subsections": []}
    ]
    data["sections"][4]["subsections"][0]["blocks"] += [
        copy.deepcopy(data["sections"][4]["blocks"][1])
    ]
    data["sections"][4]["subsections"][0]["blocks"][1]["rows"] *= 16
    with pytest.raises(ValueError, match="appendix"):
        module.write_docx(data, tmp_path / "long.docx")


def test_malformed_sections_raise_value_error(tmp_path):
    module = api()
    data = sample()
    data["sections"][0] = "invalid"
    with pytest.raises(ValueError):
        module.write_docx(data, tmp_path / "malformed.docx")


def test_summary_table_limit_applies(tmp_path):
    module = api()
    data = sample()
    table = copy.deepcopy(data["sections"][4]["blocks"][1])
    table["rows"] *= 16
    data["sections"][0]["blocks"].append(table)
    with pytest.raises(ValueError, match="appendix"):
        module.write_docx(data, tmp_path / "summary.docx")


def test_pdf_normalization_preserves_pages_and_links(tmp_path, monkeypatch):
    from PyPDF2 import PdfWriter
    from PyPDF2.generic import DecodedStreamObject, NameObject

    module = api()
    source = module.write_docx(sample(), tmp_path / "input.docx")
    monkeypatch.setattr(module.shutil, "which", lambda name: "libreoffice")

    def convert(command, **kwargs):
        output = Path(command[command.index("--outdir") + 1]) / "input.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        writer.add_metadata(
            {"/CreationDate": "random time", "/ModDate": "another time"}
        )
        metadata = DecodedStreamObject()
        metadata.set_data(b"volatile XMP data")
        writer._root_object[NameObject("/Metadata")] = writer._add_object(metadata)
        with output.open("wb") as stream:
            writer.write(stream)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(module.subprocess, "run", convert)
    result = module.convert_pdf(source, tmp_path / "report.pdf", tmp_path / "scratch")
    reader = PdfReader(result)
    assert len(reader.pages) == 1
    assert "/Metadata" not in reader.trailer["/Root"]
    assert "/CreationDate" not in reader.metadata
    assert "/ModDate" not in reader.metadata
