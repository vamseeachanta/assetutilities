"""Inclusive page ranges have hand-enumerated text and page-count answers."""

from pathlib import Path
import shutil

from PyPDF2 import PdfReader

from assetutilities.modules.pdf_utilities.edit_pdf import EditPDF


def test_split_ranges(tmp_path):
    """[1,2] selects pages 1 and 2; [3,4] selects pages 3 and 4: two each."""
    sample = (
        Path(__file__).resolve().parents[3]
        / "examples/workflows/read_pdf/data/sample.pdf"
    )
    source = tmp_path / "sample.pdf"
    shutil.copyfile(sample, source)
    EditPDF().edit_pdf({"files": [{"io": str(source), "pages": [[1, 2], [3, 4]]}]})
    for start, stop in [(1, 2), (3, 4)]:
        reader = PdfReader(f"{source}_page_{start}-{stop}.pdf")
        assert len(reader.pages) == 2
        assert f"sample page {start}" in reader.pages[0].extract_text()
        assert f"sample page {stop}" in reader.pages[1].extract_text()
