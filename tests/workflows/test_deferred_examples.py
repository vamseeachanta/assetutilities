"""Exercise registry examples with all generated files isolated from the checkout."""

from pathlib import Path
import runpy
import shlex
import shutil
import subprocess
import sys

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
    source = ROOT / "examples/workflows" / basename
    if (source / "input_data").is_dir():
        shutil.copytree(
            source / "input_data",
            examples / basename / "input_data",
            ignore=shutil.ignore_patterns("*.pdf_page_*.pdf"),
        )
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
    assert row["test"] == registry["invocation"].format(input=row["input"])
    assert row["result"]["kind"] == "files"
    for output in row["outputs"]:
        assert (tmp_path / output).is_file()
    if basename == "read_pdf":
        for summary, text in zip(result["result"], ("alpha page", "beta page")):
            assert Path(summary["output_file"]).read_text().strip() == text
    elif basename == "edit_pdf":
        for page, text in ((1, "alpha page"), (2, "beta page")):
            reader = PdfReader(
                f"{examples}/edit_pdf/input_data/input.pdf_page_{page}-{page}.pdf"
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


@pytest.mark.parametrize("basename", ("read_pdf", "edit_pdf", "csv_utilities"))
def test_registry_invocation_needs_no_preparation(tmp_path, basename):
    """Run the registry invocation against only the example's shipped inputs."""
    source = ROOT / "examples/workflows" / basename
    destination = tmp_path / "examples/workflows" / basename
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("logs", "results", "outputs", "*.pdf_page_*.pdf"),
    )
    registry = yaml.safe_load(
        (ROOT / "docs/registry/workflows.yaml").read_text(encoding="utf-8")
    )
    row = next(row for row in registry["workflows"] if row["id"] == basename)
    command = shlex.split(registry["invocation"].format(input=row["input"]))
    assert command[:3] == ["uv", "run", "python"]
    completed = subprocess.run(
        [sys.executable, *command[3:]],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    for output in row["outputs"]:
        assert (tmp_path / output).is_file()


def test_optional_preparation_matches_and_preserves_inputs(tmp_path):
    prepare = runpy.run_path(
        str(ROOT / "examples/workflows/prepare_deferred_inputs.py")
    )["prepare"]
    prepare(tmp_path)
    inputs = (
        "read_pdf/input_data/input.pdf",
        "edit_pdf/input_data/input.pdf",
        "csv_utilities/input_data/input.csv",
    )
    for path in inputs:
        generated = tmp_path / path
        assert (
            generated.read_bytes() == (ROOT / "examples/workflows" / path).read_bytes()
        )
        generated.write_bytes(b"existing synthetic input\n")
    prepare(tmp_path)
    for path in inputs:
        assert (tmp_path / path).read_bytes() == b"existing synthetic input\n"
