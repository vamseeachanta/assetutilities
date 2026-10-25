"""Offline workflow examples; expected answers are independent of the routers.

All numbers below describe synthetic input sizes or one-based page positions,
not standards-derived engineering coefficients or acceptance limits.
"""

from pathlib import Path

import git
import pytest
import yaml
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from PyPDF2 import PdfReader

from assetutilities.engine import engine
from assetutilities.modules.pdf_utilities.read_pdf import ReadPDF


@pytest.fixture
def pdf_input(tmp_path):
    """Author two text pages; the expected text is the literal source string."""
    path = tmp_path / "input.pdf"
    with PdfPages(path) as pdf:
        for text in ("alpha page", "beta page"):
            figure = Figure()
            figure.text(0.1, 0.5, text)  # Synthetic drawing positions, not limits.
            pdf.savefig(figure)
    return path


def run_config(tmp_path, cfg):
    path = tmp_path / "input.yml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    result = engine(str(path))
    saved = yaml.safe_load((tmp_path / "results/input.yml").read_text())
    assert saved["basename"] == cfg["basename"]
    return result


def test_read_pdf_all_entries_are_serializable(tmp_path, pdf_input):
    """One-based pages 1 and 2 select authored alpha and beta respectively."""
    result = run_config(
        tmp_path,
        {
            "basename": "read_pdf",
            "library": "PyPDF2",
            "files": {
                "from_pdf": [
                    {"io": str(pdf_input), "page": 1, "label": "alpha"},
                    {"io": str(pdf_input), "page": 2, "label": "beta"},
                ]
            },
        },
    )
    assert len(result["result"]) == 2
    for summary, expected in zip(result["result"], ("alpha page", "beta page")):
        text = Path(summary["output_file"]).read_text(encoding="utf-8")
        assert text.strip() == expected
        assert summary["n_chars"] == len(text)
    yaml.safe_dump(result)


@pytest.mark.parametrize("page", [0, -1, 3, True, "1"])
def test_read_pdf_rejects_invalid_page(tmp_path, pdf_input, page):
    """The authored PDF has exactly two pages; valid positions are 1 and 2."""
    cfg = {
        "library": "PyPDF2",
        "files": {
            "from_pdf": [
                {"io": str(pdf_input), "page": page, "label": "invalid"},
            ]
        },
        "Analysis": {"result_folder": str(tmp_path / "out")},
    }
    with pytest.raises(ValueError, match="page"):
        ReadPDF().read_pdf(cfg)
    assert not (tmp_path / "out").exists()


def test_read_pdf_labels_cannot_escape_output(tmp_path, pdf_input):
    cfg = {
        "library": "PyPDF2",
        "files": {
            "from_pdf": [
                {"io": str(pdf_input), "page": 1, "label": "../../escape"},
            ]
        },
        "Analysis": {"result_folder": str(tmp_path / "out")},
    }
    summary = ReadPDF().read_pdf(cfg)[0]
    assert Path(summary["output_file"]).parent == tmp_path / "out"


def test_edit_pdf_page_contents(tmp_path, pdf_input):
    """Inclusive range [2,2] contains one page: the authored beta page."""
    run_config(
        tmp_path,
        {
            "basename": "edit_pdf",
            "library": "PyPDF2",
            "files": [{"io": str(pdf_input), "pages": [[2, 2]]}],
        },
    )
    reader = PdfReader(f"{pdf_input}_page_2-2.pdf")
    assert len(reader.pages) == 1
    assert reader.pages[0].extract_text().strip() == "beta page"


@pytest.mark.parametrize("encoding", [None, "latin1"])
def test_csv_normalization(tmp_path, encoding):
    """Header name,value + café,7 + tea,9 => two rows and two columns."""
    (tmp_path / "input.csv").write_bytes("name,value\ncafé,7\ntea,9\n".encode("latin1"))
    options = {"input_file": "input.csv"}
    if encoding:
        options["encoding"] = encoding
    result = run_config(
        tmp_path, {"basename": "csv_utilities", "csv_utilities": options}
    )
    outputs = result["csv_utilities"]["results"]
    assert (
        Path(outputs["normalized_file"]).read_text(encoding="utf-8")
        == "name,value\ncafé,7\ntea,9\n"
    )
    summary = yaml.safe_load(Path(outputs["summary_file"]).read_text())
    assert summary["n_rows"] == 2
    assert summary["n_columns"] == 2
    assert summary["columns"] == ["name", "value"]
    assert summary["encoding_used"] == "latin1"


def test_csv_alias_delimiter_and_limit(tmp_path):
    """A semicolon header and two rows, limited to one, yields café,7 only."""
    (tmp_path / "input.csv").write_text("name;value\ncafé;7\ntea;9\n", encoding="utf-8")
    result = run_config(
        tmp_path,
        {
            "basename": "csv_utilities",
            "csv_utilities": {
                "txt_file": "input.csv",
                "delimiter": ";",
                "nrows": 1,
            },
        },
    )
    path = result["csv_utilities"]["results"]["normalized_file"]
    assert Path(path).read_text(encoding="utf-8") == "name,value\ncafé,7\n"


def test_git_read_only_with_inherited_write_flags(tmp_path, monkeypatch):
    """One authored commit => one log entry; flags cannot create another."""
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)
    repo_path = tmp_path / "repo"
    with git.Repo.init(repo_path) as repo:
        (repo_path / "tracked.txt").write_text("synthetic\n")
        repo.index.add(["tracked.txt"])
        commit = repo.index.commit("Synthetic read-only workflow test")
        repo.head.reference = commit  # Exercise the detached CI case.
        (repo_path / "untracked.txt").write_text("new\n")
        before = repo.head.commit.hexsha
        index_before = (repo_path / ".git/index").read_bytes()
        result = run_config(
            tmp_path,
            {
                "basename": "gitpython",
                "common_cfg": {"commit": True, "push": True, "clone": True},
                "repos": [{"io": "repo"}],
                "max_count": 1,
            },
        )
        report = yaml.safe_load(Path(result["gitpython"]["output_file"]).read_text())
        row = report["repos"][0]
        assert row["current_branch"] == "DETACHED"
        assert row["head"] == before
        assert row["is_dirty"] is True
        assert row["recent_commits"] == [{"sha": before, "subject": commit.summary}]
        assert "not supported" in report["write_operations"]
        assert repo.head.commit.hexsha == before
        assert (repo_path / ".git/index").read_bytes() == index_before
        assert not list(repo.remotes)


def test_git_unborn_repo_and_parent_search(tmp_path, monkeypatch):
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)
    with git.Repo.init(tmp_path / "repo"):
        (tmp_path / "repo/subdir").mkdir()
        result = run_config(
            tmp_path, {"basename": "gitpython", "repos": [{"io": "repo/subdir"}]}
        )
    row = result["gitpython"]["repos"][0]
    assert row["head"] is None
    assert row["recent_commits"] == []


def test_pdf_explicit_index_and_fallback(tmp_path, pdf_input):
    """Selecting entry 1 yields authored beta, with results beside the PDF."""
    summaries = ReadPDF().read_pdf(
        {
            "library": "PyPDF2",
            "files": {
                "from_pdf": [
                    {"io": str(pdf_input), "page": 1, "label": "same"},
                    {"io": str(pdf_input), "page": 2, "label": "same"},
                ]
            },
        },
        file_index=1,
    )
    assert len(summaries) == 1
    output = Path(summaries[0]["output_file"])
    assert output.parent == tmp_path / "results"
    assert output.read_text().strip() == "beta page"


def test_pdf_duplicate_labels_keep_both_pages(tmp_path, pdf_input):
    """Two entries share a label but must retain both authored page strings."""
    summaries = ReadPDF().read_pdf(
        {
            "library": "PyPDF2",
            "files": {
                "from_pdf": [
                    {"io": str(pdf_input), "page": 1, "label": "same"},
                    {"io": str(pdf_input), "page": 2, "label": "same"},
                ]
            },
        }
    )
    assert [Path(row["output_file"]).read_text().strip() for row in summaries] == [
        "alpha page",
        "beta page",
    ]


def test_table_workflow_is_serializable(monkeypatch):
    """A synthetic one-cell table serializes as its authored row, value 7."""
    import pandas as pd

    monkeypatch.setattr(
        ReadPDF, "from_pdf_tabula", lambda *args: [pd.DataFrame({"value": [7]})]
    )
    cfg = {"library": "tabula", "files": {"from_pdf": [{"io": "unused", "page": 1}]}}
    assert yaml.safe_load(yaml.safe_dump(ReadPDF().read_pdf(cfg))) == [[[{"value": 7}]]]


@pytest.mark.parametrize("library", ["tabula", "camelot"])
def test_table_timestamps_are_saved_as_native_values(tmp_path, monkeypatch, library):
    """Both table backends preserve dates and nulls in the saved workflow cfg."""
    from types import SimpleNamespace

    import pandas as pd

    table = pd.DataFrame(
        {"date": [pd.Timestamp("2026-01-02"), pd.NaT], "value": [7.0, float("nan")]}
    )
    tables = [table] if library == "tabula" else [SimpleNamespace(df=table)]
    monkeypatch.setattr(ReadPDF, f"from_pdf_{library}", lambda *args: tables)
    result = run_config(
        tmp_path,
        {
            "basename": "read_pdf",
            "library": library,
            "files": {"from_pdf": [{"io": "unused", "page": 1}]},
        },
    )
    expected = [
        [
            [
                {"date": "2026-01-02T00:00:00.000", "value": 7.0},
                {"date": None, "value": None},
            ]
        ]
    ]
    saved = yaml.safe_load((tmp_path / "results/input.yml").read_text(encoding="utf-8"))
    assert result["result"] == saved["result"] == expected


def test_csv_explicit_encoding_does_not_silently_fallback(tmp_path):
    (tmp_path / "input.csv").write_bytes("name\ncafé\n".encode("latin1"))
    with pytest.raises(UnicodeDecodeError):
        run_config(
            tmp_path,
            {
                "basename": "csv_utilities",
                "csv_utilities": {
                    "input_file": "input.csv",
                    "encoding": "utf-8",
                },
            },
        )


@pytest.mark.parametrize("max_count", [-1, True, "5"])
def test_git_invalid_log_limit(tmp_path, max_count):
    with pytest.raises(ValueError, match="max_count"):
        run_config(
            tmp_path, {"basename": "gitpython", "repos": [], "max_count": max_count}
        )
