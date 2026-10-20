"""Citation formatting contracts from issue #79; all fixtures are synthetic.

Expected strings are assembled by hand: look up the bound revision, then join
code, revision, optional section prefixed with §, and optional page prefixed
with p. in square brackets. Locators are formatting examples, not assertions
about standard contents. No engineering constants or acceptance limits apply.
"""

import copy
import hashlib
import re
from pathlib import Path

import pytest
import yaml
from bs4 import BeautifulSoup
from docx import Document

from assetutilities.common.reportgen import ReportGenerator, run
from assetutilities.common.reportgen.citations import (
    DISCLOSURE_TEXT,
    build_disclosure_section,
    build_provenance_section,
    parse_references,
    render_citation,
)
from assetutilities.common.reportgen.dom import DocumentDOM
from assetutilities.common.reportgen.writers import DefaultMDWriter
from assetutilities.workflow_api import envelope


@pytest.fixture(autouse=True)
def reset_dom():
    DocumentDOM._instance = None
    yield
    DocumentDOM._instance = None


@pytest.fixture
def config(tmp_path):
    return {
        "important_paths": {"project_root": str(tmp_path), "outputs_path": "outputs"},
        "report_details": {
            "name": "Citation example",
            "project_name": "Synthetic example",
            "project_num": "example",
            "engineer": "TBD",
            "reviewer": "TBD",
            "date": "not issued",
            "target_file_stub": "report",
            "target_report_type": "md",
        },
        "references": [
            {"code_id": "DNV-OS-E301", "publisher": "DNV", "revision": "example"}
        ],
        "sections_L1": [
            {
                "name": "Results",
                "paragraphs": [[{"type": "citation", "code_id": "DNV-OS-E301"}]],
                "sections_L2": [
                    {
                        "name": "Detail",
                        "paragraphs": [
                            [{"type": "citation", "code_id": "DNV-OS-E301"}]
                        ],
                    }
                ],
            }
        ],
    }


def test_parse_references_copies_and_defaults(config):
    original = copy.deepcopy(config)
    refs = parse_references(config)
    assert refs == [{**config["references"][0], "source_sibling": "generic"}]
    refs[0]["revision"] = "changed"
    assert config == original
    assert parse_references({}) == []


@pytest.mark.parametrize(
    "references",
    [
        None,
        {},
        "standard",
        [None],
        [{}],
        [{"code_id": "", "revision": "example"}],
        [{"code_id": "DNV-OS-E301", "revision": ""}],
        [{"code_id": "DNV-OS-E301", "revision": 2018}],
        [{"code_id": "DNV-OS-E301", "revision": "example", "publisher": []}],
    ],
)
def test_invalid_references_fail_closed(references):
    with pytest.raises(ValueError, match="references"):
        parse_references({"references": references})


@pytest.mark.parametrize("extension", ["md", "docx", "html"])
@pytest.mark.parametrize("field", ["code_id", "publisher", "revision"])
@pytest.mark.parametrize(
    "line_break",
    [
        "\r",
        "\n",
        "\r\n",
        "\v",
        "\f",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x85",
        "\u2028",
        "\u2029",
    ],
    ids=["cr", "lf", "crlf", "vt", "ff", "fs", "gs", "rs", "nel", "ls", "ps"],
)
def test_multiline_references_fail_before_output(
    config, tmp_path, extension, field, line_break
):
    config["references"][0][field] = f"Example{line_break}metadata"
    config["sections_L1"] = []
    config["report_details"].update(
        target_report_type=extension, timestamped_filename=False
    )
    with pytest.raises(ValueError, match=rf"references.*{field}"):
        run(config)
    assert not list(tmp_path.iterdir())


def test_duplicate_bindings_are_ambiguous(config):
    config["references"] *= 2
    with pytest.raises(ValueError, match="Duplicate"):
        parse_references(config)


@pytest.mark.parametrize(
    "locator,expected",
    [
        ({}, "[DNV-OS-E301 example]"),
        ({"section": "example-clause"}, "[DNV-OS-E301 example §example-clause]"),
        ({"page": "example-page"}, "[DNV-OS-E301 example p.example-page]"),
        (
            {"section": "example-clause", "page": "example-page"},
            "[DNV-OS-E301 example §example-clause p.example-page]",
        ),
    ],
)
def test_render_citation(config, locator, expected):
    assert (
        render_citation({"code_id": "DNV-OS-E301", **locator}, parse_references(config))
        == expected
    )


def test_unbound_citation_fails_before_output(config, tmp_path):
    config.pop("references")
    with pytest.raises(ValueError, match="Unbound"):
        run(config)
    assert not list(tmp_path.rglob("*.out.*"))


def test_disclosure_is_standardized():
    expected = (
        "Citations in this report reference an internal engineering-standards "
        "index by code identifier and revision. The full text of each cited "
        "standard is not included and must be obtained from the respective "
        "publisher. This report does not reproduce copyrighted standard content."
    )
    assert DISCLOSURE_TEXT == expected
    assert build_disclosure_section().paragraphs == [
        {"type": "text", "content": expected}
    ]


def test_provenance_uses_shared_helpers(monkeypatch):
    """SHA-256 expected value hashes literal canonical JSON independently."""
    monkeypatch.setattr(
        envelope,
        "code_version",
        lambda name: {
            "package_version": "example-version",
            "git_sha": "example-revision",
        },
    )
    monkeypatch.setattr(envelope, "utc_now_iso", lambda: "example-UTC")
    content = build_provenance_section({"purpose": "example"}).paragraphs[0]["content"]
    digest = hashlib.sha256(b'{"purpose": "example"}').hexdigest()
    for expected in ("example-version", "example-revision", "example-UTC", digest):
        assert expected in content


@pytest.mark.parametrize(
    "has_refs,flag,expected",
    [
        (True, None, True),
        (True, False, False),
        (True, True, True),
        (False, None, False),
        (False, False, False),
        (False, True, True),
    ],
)
def test_provenance_opt_in_and_out(config, has_refs, flag, expected):
    if not has_refs:
        config.pop("references")
        config["sections_L1"] = []
    if flag is not None:
        config["provenance"] = flag
    generator = ReportGenerator()
    generator.initialize_from_config(config)
    names = [s.name for s in generator.dom.sections]
    assert ("Provenance" in names) is expected
    assert ("References" in names) is has_refs
    assert ("Disclosure" in names) is has_refs


@pytest.mark.parametrize("extension", ["md", "docx", "html"])
def test_all_writer_positions_and_appendices(config, tmp_path, extension):
    config["report_details"].update(
        target_report_type=extension, timestamped_filename=False
    )
    generator = ReportGenerator()
    generator.initialize_from_config(config)
    generator.dom.first_section.paragraphs.append(
        {"type": "citation", "code_id": "DNV-OS-E301"}
    )
    generator.flush_report()
    target = tmp_path / "outputs" / f"report.out.{extension}"
    if extension == "docx":
        doc = Document(target)
        content = "\n".join(p.text for p in doc.paragraphs)
        content += "\n" + "\n".join(
            c.text for t in doc.tables for r in t.rows for c in r.cells
        )
    else:
        content = target.read_text(encoding="utf-8")
    assert content.count("[DNV-OS-E301 example]") == 3
    for expected in ("References", "Disclosure", "Provenance", DISCLOSURE_TEXT):
        assert expected in content
    assert str(tmp_path) not in content
    if extension == "html":
        assert '<span class="citation">[DNV-OS-E301 example]</span>' in content
        assert "<table>" in content
        assert "http" not in content.lower()


def test_html_escapes_headings_text_citations_and_table_cells(config, tmp_path):
    config["report_details"].update(
        target_report_type="html", timestamped_filename=False
    )
    config["report_details"]["name"] = "<script>heading &</script>"
    config["references"][0]["revision"] = "<script>revision &</script>"
    config["sections_L1"][0]["paragraphs"].append(
        [
            "<script>text &</script>",
            {
                "type": "markdown_table",
                "content": "| <tag> |\n|---|\n| <script>cell &</script> |",
            },
        ]
    )
    run(config)
    content = (tmp_path / "outputs/report.out.html").read_text(encoding="utf-8")
    assert "<script>" not in content
    for value in ("heading", "revision", "text", "cell"):
        assert f"&lt;script&gt;{value} &amp;&lt;/script&gt;" in content
    assert "&lt;tag&gt;" in content


def test_default_filename_remains_timestamped(config):
    generator = ReportGenerator()
    generator.initialize_from_config(config)
    writer = DefaultMDWriter(generator.dom)
    assert re.fullmatch(r"report\.\d{6}-\d{6}\.out\.md", writer.target_file)


def test_reinitialization_drops_citations_and_appendices(config):
    generator = ReportGenerator()
    generator.initialize_from_config(config)
    config.pop("references")
    config["sections_L1"] = [{"name": "Legacy", "paragraphs": [["Uncited text"]]}]
    generator.initialize_from_config(config)
    assert generator.dom.references == []
    assert [s.name for s in generator.dom.sections] == ["Legacy"]


def test_legacy_markdown_is_unchanged(config, tmp_path):
    """Expected Markdown is written out from the legacy layout, independently."""
    config.pop("references")
    config["report_details"]["timestamped_filename"] = False
    config["sections_L1"] = [
        {
            "name": "Legacy",
            "paragraphs": [["Uncited text"]],
            "sections_L2": [{"name": "Notes", "paragraphs": [["Detail"]]}],
        }
    ]
    run(config)
    assert (tmp_path / "outputs/report.out.md").read_text(encoding="utf-8") == (
        "# Citation example\n"
        "| | |\n|:--|--:|\n"
        "| Project Name | Synthetic example |\n"
        "| Project # | example |\n| Engineer | TBD |\n"
        "| Checker | TBD |\n| Date | not issued |\n\n"
        "## Legacy\nUncited text\n### Notes\nDetail\n"
    )


@pytest.mark.parametrize(
    "path", sorted(Path(__file__).parent.glob("*.yml")), ids=lambda p: p.stem
)
def test_legacy_configurations_gain_no_automatic_sections(path):
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    generator = ReportGenerator()
    generator.initialize_from_config(cfg)
    assert generator.dom.references == []
    assert [s.name for s in generator.dom.sections] == [
        s["name"] for s in cfg.get("sections_L1", [])
    ]


@pytest.mark.parametrize("extension", ["md", "docx", "html"])
def test_reference_metadata_and_escaped_table_pipes_roundtrip(
    config, tmp_path, extension
):
    config["references"] = [
        {
            "code_id": "EXAMPLE-A",
            "publisher": "Example | publisher",
            "revision": "edition-A",
            "title": "Example title",
            "source_sibling": "generic",
        },
        {"code_id": "EXAMPLE-B", "revision": "edition-B"},
    ]
    config["sections_L1"] = []
    config["report_details"].update(
        target_report_type=extension, timestamped_filename=False
    )
    run(config)
    target = tmp_path / "outputs" / f"report.out.{extension}"
    if extension == "md":
        table = target.read_text(encoding="utf-8").split("## References\n")[1]
        assert table.split("## Disclosure\n")[0].strip().splitlines() == [
            "| Code | Publisher | Revision |",
            "| --- | --- | --- |",
            r"| EXAMPLE-A | Example \| publisher | edition-A |",
            "| EXAMPLE-B |  | edition-B |",
        ]
    else:
        if extension == "docx":
            table = Document(target).tables[1]
            rows = [[cell.text for cell in row.cells] for row in table.rows]
        else:
            document = BeautifulSoup(target.read_text(encoding="utf-8"), "html.parser")
            table = document.find("h2", string="References").find_next_sibling("table")
            rows = [
                [cell.get_text() for cell in row.find_all(["th", "td"])]
                for row in table.find_all("tr")
            ]
        assert rows == [
            ["Code", "Publisher", "Revision"],
            ["EXAMPLE-A", "Example | publisher", "edition-A"],
            ["EXAMPLE-B", "", "edition-B"],
        ]


def test_example_runs_with_outputs_in_scratch(tmp_path):
    path = Path(__file__).parents[3] / "examples/workflows/reportgen/input.yml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    config["important_paths"]["project_root"] = str(tmp_path)
    run(config)
    content = next(tmp_path.rglob("*.out.md")).read_text(encoding="utf-8")
    for expected in (
        "DNV-OS-E301",
        "OCIMF-MEG4",
        "## References",
        "## Disclosure",
        "## Provenance",
    ):
        assert expected in content
    assert str(tmp_path) not in content
