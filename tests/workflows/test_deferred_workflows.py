"""Run registered offline examples twice, with all artifacts in temporary storage."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml
from PyPDF2 import PdfReader
from git import Repo

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ["read_pdf", "edit_pdf", "csv_utilities", "text_analytics", "gitpython"]


@pytest.mark.parametrize("name", ["read_pdf", "csv_utilities", "gitpython"])
def test_workflow_text_writes_support_python39(name, tmp_path, monkeypatch):
    """Valid workflows must write outputs with Python 3.9's pathlib signature."""
    from assetutilities.engine import engine

    def python39_write_text(path, data, encoding=None, errors=None):
        # Python 3.9 has no newline keyword on Path.write_text; keep real I/O.
        with path.open("w", encoding=encoding, errors=errors, newline="\n") as stream:
            return stream.write(data)

    monkeypatch.setattr(Path, "write_text", python39_write_text)
    base = Path("examples/workflows") / name
    shutil.copytree(ROOT / base, tmp_path / base)
    if name == "gitpython":
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
            monkeypatch.delenv(key, raising=False)
        Repo.init(tmp_path).close()
    monkeypatch.chdir(tmp_path)
    engine((base / "input.yml").as_posix())

    registry = yaml.safe_load(
        (ROOT / "docs/registry/workflows.yaml").read_text(encoding="utf-8")
    )
    row = next(row for row in registry["workflows"] if row["id"] == name)
    assert row["outputs"]
    for output in row["outputs"]:
        data = (tmp_path / output).read_bytes()
        assert data.decode("utf-8")
        assert b"\r" not in data


@pytest.mark.parametrize("name", WORKFLOWS)
def test_registered_cli_example(name, tmp_path, monkeypatch):
    """Expected outputs are hand-enumerated from each committed synthetic input.

    PDF pages contain their literal page numbers; the CSV has two data rows;
    set intersection is [blue, green], left-only [red], right-only [gold].
    Git values are environment-dependent, so only report shape is asserted.
    """
    base = Path("examples/workflows") / name
    example = tmp_path / base
    shutil.copytree(ROOT / base, example)
    input_file = example / "input.yml"
    if name == "edit_pdf":
        cfg = yaml.safe_load(input_file.read_text(encoding="utf-8"))
        fixture = Path(cfg["files"][0]["io"])
        source = tmp_path / fixture
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / fixture, source)
    elif name == "gitpython":
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
            monkeypatch.delenv(key, raising=False)
        # Inspect a disposable repository discovered from the example subdirectory.
        Repo.init(tmp_path).close()
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
        saved = yaml.safe_load(
            (example / "results/input.yml").read_text(encoding="utf-8")
        )
        assert saved["basename"] == name
        registry = yaml.safe_load(
            (ROOT / "docs/registry/workflows.yaml").read_text(encoding="utf-8")
        )
        row = next(row for row in registry["workflows"] if row["id"] == name)
        assert all((tmp_path / output).is_file() for output in row["outputs"])
    if name == "read_pdf":
        assert "sample page 1" in (example / "results/read_pdf_first.txt").read_text(
            encoding="utf-8"
        )
        assert "sample page 4" in (example / "results/read_pdf_last.txt").read_text(
            encoding="utf-8"
        )
        assert [r["page"] for r in saved["result"]] == [1, 4]
    elif name == "edit_pdf":
        for start, stop in [(1, 2), (3, 4)]:
            pdf = PdfReader(f"{source.as_posix()}_page_{start}-{stop}.pdf")
            assert len(pdf.pages) == 2
            assert f"sample page {start}" in pdf.pages[0].extract_text()
    elif name == "csv_utilities":
        report = yaml.safe_load(
            (example / "results/sample_latin1_summary.yml").read_text(encoding="utf-8")
        )
        assert (report["n_rows"], report["n_columns"]) == (2, 2)
        assert report["encoding_used"] == "latin-1"
        normalized = (example / "results/sample_latin1_normalized.csv").read_text(
            encoding="utf-8"
        )
        assert normalized == "name,value\ncafé,2\ntea,3\n"
    elif name == "text_analytics":
        report = yaml.safe_load(
            (example / "results/text_analytics_comparison.yml").read_text(
                encoding="utf-8"
            )
        )
        assert report["common"] == ["blue", "green"]
        assert report["only_in_set1"] == ["red"]
        assert report["only_in_set2"] == ["gold"]
    else:
        report = yaml.safe_load(
            (example / "results/gitpython_report.yml").read_text(encoding="utf-8")
        )
        assert {"head", "current_branch", "is_dirty", "recent_commits"} <= (
            report["repositories"][0].keys()
        )
        assert report["write_operations"] == "skipped: write operations not supported"
