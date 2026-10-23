"""Exercise registry examples with all generated files isolated from the checkout."""

from pathlib import Path
import runpy
import shutil

import pytest
import yaml
from PyPDF2 import PdfReader

from assetutilities.engine import engine

ROOT = Path(__file__).resolve().parents[2]
NAMES = ("read_pdf", "edit_pdf", "csv_utilities", "text_analytics", "gitpython")


@pytest.mark.parametrize("basename", NAMES)
def test_registered_example(tmp_path, monkeypatch, basename):
    """Answers follow directly from authored pages, rows and set membership.

    Splitting two pages into singleton groups produces one page per file.
    CSV has two records and two named columns. Intersection of [alpha,beta]
    and [beta,gamma] contains beta only. Git facts depend on the checkout.
    """
    examples = tmp_path / "examples/workflows"
    prepare = runpy.run_path(
        str(ROOT / "examples/workflows/prepare_deferred_inputs.py")
    )["prepare"]
    prepare(examples)
    prepare(examples)  # Inputs must survive repeated preparation unchanged.
    destination = examples / basename / "input.yml"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "examples/workflows" / basename / "input.yml", destination)
    if basename == "gitpython":
        cfg = yaml.safe_load(destination.read_text())
        cfg["repos"] = [{"io": str(ROOT)}]
        destination.write_text(yaml.safe_dump(cfg))
    monkeypatch.chdir(tmp_path)
    result = engine(str(destination))
    assert result["basename"] == basename
    registry = yaml.safe_load((ROOT / "docs/registry/workflows.yaml").read_text())
    row = next(row for row in registry["workflows"] if row["id"] == basename)
    for output in row["outputs"]:
        assert (tmp_path / output).is_file()
    if basename == "read_pdf":
        for summary, text in zip(result["result"], ("alpha page", "beta page")):
            assert Path(summary["output_file"]).read_text().strip() == text
    elif basename == "edit_pdf":
        for page, text in ((1, "alpha page"), (2, "beta page")):
            reader = PdfReader(
                f"{examples}/read_pdf/outputs/input.pdf_page_{page}-{page}.pdf"
            )
            assert len(reader.pages) == 1
            assert reader.pages[0].extract_text().strip() == text
    elif basename == "csv_utilities":
        assert (
            Path(result["csv_utilities"]["results"]["normalized_file"]).read_text(
                encoding="utf-8"
            )
            == "name,value\ncafé,7\ntea,9\n"
        )
    elif basename == "text_analytics":
        assert result["text_analytics"]["summary"]["common"] == ["beta"]
    else:
        assert result["gitpython"]["repos"][0]["head"]
