"""Run registered offline examples twice, with all artifacts in temporary storage."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml
from PyPDF2 import PdfReader

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ["read_pdf", "edit_pdf", "csv_utilities", "text_analytics", "gitpython"]


@pytest.mark.parametrize("name", WORKFLOWS)
def test_registered_cli_example(name, tmp_path):
    """Expected outputs are hand-enumerated from each committed synthetic input.

    PDF pages contain their literal page numbers; the CSV has two data rows;
    set intersection is [blue, green], left-only [red], right-only [gold].
    Git values are environment-dependent, so only report shape is asserted.
    """
    base = Path("examples/workflows") / name
    example = tmp_path / base
    shutil.copytree(ROOT / base, example)
    input_file = example / "input.yml"
    if name == "gitpython":
        # The temporary example is outside a checkout: inspect this checkout instead.
        cfg = yaml.safe_load(input_file.read_text())
        cfg["repos"] = [{"io": str(ROOT)}]
        input_file.write_text(yaml.safe_dump(cfg))
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    for _ in range(2):  # Issue #91 acceptance criterion: repeatable outputs.
        subprocess.run(
            [sys.executable, "-m", "assetutilities", str(base / "input.yml")],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        saved = yaml.safe_load((example / "results/input.yml").read_text())
        assert saved["basename"] == name
        registry = yaml.safe_load((ROOT / "docs/registry/workflows.yaml").read_text())
        row = next(row for row in registry["workflows"] if row["id"] == name)
        assert all((tmp_path / output).is_file() for output in row["outputs"])
    if name == "read_pdf":
        assert "sample page 1" in (example / "results/read_pdf_first.txt").read_text()
        assert "sample page 4" in (example / "results/read_pdf_last.txt").read_text()
        assert [r["page"] for r in saved["result"]] == [1, 4]
    elif name == "edit_pdf":
        for start, stop in [(1, 2), (3, 4)]:
            pdf = PdfReader(example / f"data/sample.pdf_page_{start}-{stop}.pdf")
            assert len(pdf.pages) == 2
            assert f"sample page {start}" in pdf.pages[0].extract_text()
    elif name == "csv_utilities":
        report = yaml.safe_load(
            (example / "results/sample_latin1_summary.yml").read_text()
        )
        assert (report["n_rows"], report["n_columns"]) == (2, 2)
        assert report["encoding_used"] == "latin-1"
        assert (example / "results/sample_latin1_normalized.csv").read_text() == (
            "name,value\ncafé,2\ntea,3\n"
        )
    elif name == "text_analytics":
        report = yaml.safe_load(
            (example / "results/text_analytics_comparison.yml").read_text()
        )
        assert report["common"] == ["blue", "green"]
        assert report["only_in_set1"] == ["red"]
        assert report["only_in_set2"] == ["gold"]
    else:
        report = yaml.safe_load((example / "results/gitpython_report.yml").read_text())
        assert {"head", "current_branch", "is_dirty", "recent_commits"} <= (
            report["repositories"][0].keys()
        )
        assert report["write_operations"] == "skipped: write operations not supported"
