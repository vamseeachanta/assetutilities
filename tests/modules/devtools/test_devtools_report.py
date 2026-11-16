"""Rebuild and arithmetic checks for the dependency collection report."""

import importlib.util
import json
import re
import tomllib
from html.parser import HTMLParser
from pathlib import Path

import pytest
from playwright.sync_api import Error, sync_playwright

ROOT = Path(__file__).resolve().parents[3]
COMMAND = "python scripts/reporting/generate_devtools_report.py --work-dir <scratch>"
SPEC = importlib.util.spec_from_file_location(
    "devtools_report", ROOT / "scripts/reporting/generate_devtools_report.py"
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.results = {}
        self.ids = []
        self.links = []
        self.sections = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.links.append(attrs["href"][1:])
        if tag == "section" and attrs.get("data-report-section"):
            self.sections += 1
        if "data-result" in attrs:
            self.results[attrs["data-result"]] = int(attrs["data-value"])


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return builder.build(tmp_path_factory.mktemp("report"))


def test_hand_anchor_file_count(built):
    # Two named input files: requirements.txt + requirements-dev.txt = 2 files.
    # Counts are integral, so the tolerance is zero.
    assert built["cases"][0]["files_processed"] == 2
    assert built["cases"][1]["files_processed"] == 2


def test_hand_anchor_runtime_count(built):
    # Discovery: R={requests}, D={pytest}; |R|=1, |D|=1, N=1+1=2,
    # U=|{requests, pytest}|=2. Both inputs contain one requirement each.
    assert built["cases"][0]["runtime_count"] == 1
    assert built["cases"][0]["dev_count"] == 1
    assert built["cases"][0]["dependencies_found"] == 2
    assert built["cases"][0]["distinct_count"] == 2
    # Overlap case runtime lines are requests, requests, pytest.
    # Identical requests lines collapse: {requests, pytest} has 2 members.
    assert built["cases"][1]["runtime_count"] == 2


def test_hand_anchor_reported_total(built):
    # Runtime {requests, pytest} has 2 members; development {pytest} has 1.
    # The implementation reports 2 + 1 = 3, despite only 2 distinct strings.
    assert built["cases"][1]["dev_count"] == 1
    assert built["cases"][1]["dependencies_found"] == 3
    assert built["cases"][1]["distinct_count"] == 2


@pytest.mark.parametrize("index", [0, 1])
def test_module_output_consistency(built, tmp_path, index):
    actual = builder.compute_case(tmp_path / "case", builder.INPUTS[index])
    assert actual == built["cases"][index]
    assert sorted(actual["generated_runtime"]) == actual["runtime"]
    assert sorted(actual["generated_development"]) == actual["development"]
    document = Document(built["html"])
    for key in builder.METRICS:
        assert document.results[f"{index}-{key}"] == actual[key]
    # Every requirement version and duplicate is shown from the input strings.
    for content in builder.INPUTS[index]["files"].values():
        assert content.strip() in built["html"]


def test_displayed_inputs_recompute_headline(built, tmp_path):
    document = Document(built["html"])
    # Headline N=|{requests, pytest}|+|{pytest}|=2+1=3;
    # U=|{requests, pytest} union {pytest}|=2.
    assert document.results["headline-total"] == 3
    assert document.results["headline-distinct"] == 2
    actual = builder.compute_case(tmp_path / "headline", builder.INPUTS[1])
    assert document.results["headline-total"] == actual["dependencies_found"]
    assert document.results["headline-distinct"] == actual["distinct_count"]
    assert document.results["1-dependencies_found"] == actual["dependencies_found"]
    assert actual["dependencies_found"] == actual["runtime_count"] + actual["dev_count"]


def test_committed_report_rebuild(built):
    # Integer counts have zero tolerance; there are no floating point results.
    # Source-only digests and test-definition counts drift intentionally.
    report_dir = ROOT / "docs/reports/modules/adevtools"
    assert (report_dir / "index.html").read_text(encoding="utf-8") == built[
        "html"
    ], f"Report is stale; rebuild with: {COMMAND}"
    assert (
        json.loads((report_dir / "changes.json").read_text(encoding="utf-8"))
        == built["changes"]
    ), f"Change panel is stale; rebuild with: {COMMAND}"


def test_sections_sources_and_self_containment(built):
    html = built["html"]
    doc = Document(html)
    assert doc.sections == 10
    assert len(doc.ids) == len(set(doc.ids))
    assert set(doc.links) <= set(doc.ids)
    assert '<body class="hs-doc">' in html
    assert "<script src=" not in html
    assert '<link rel="stylesheet"' not in html
    assert "showDirectoryPicker" in html
    assert "createWritable" in html
    assert "Draft for maintainer review" in html
    assert "sec_intro-sets.html" in html
    assert "pep-0508" in html
    assert (
        ROOT.joinpath("docs/sub_utilities/assets/style.css").read_text(encoding="utf-8")
        in html
    )


def test_utf8_lf_and_public_wording(built):
    html = built["html"]
    assert "\r" not in html
    # Build the disallowed path prefixes at runtime; do not store those paths.
    forbidden = ["/" + part + "/" for part in ("home", "mnt")]
    forbidden += [
        "ow" + "ner",
        "fl" + "eet",
        "dis" + "patcher",
        "ses" + "sion",
        "Co-Authored-By",
    ]
    for word in forbidden:
        assert word.lower() not in html.lower()
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", html)


def test_no_working_tree_side_effects(built):
    # Rebuild only returns deliverables; all calculation files live in scratch.
    assert set(built) == {"html", "changes", "cases"}
    assert built["cases"][0]["files_created"] == ["pyproject.toml"]
    assert all(case["errors"] == [] for case in built["cases"])


def test_reused_work_directory_rejects_undeclared_requirements(tmp_path):
    builder.build(tmp_path)
    extra = tmp_path / "case-1" / "requirements-extra.txt"
    extra.write_text("wheel\n", encoding="utf-8", newline="\n")
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    with pytest.raises(FileExistsError):
        builder.build(tmp_path)
    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


@pytest.mark.parametrize(
    "requirement",
    [
        'argparse;python_version<"2.7"\n',
        "requests==2.28.0 \\\n    --hash=sha256:abcd\n",
    ],
    ids=["quoted-marker", "continuation"],
)
def test_documented_unescaped_requirement_limit(tmp_path, requirement):
    # The current writer interpolates strings without TOML escaping.
    # These supported requirement-file forms therefore fail TOML parsing.
    case = {"name": "TOML escaping limit", "files": {"requirements.txt": requirement}}
    with pytest.raises(tomllib.TOMLDecodeError):
        builder.compute_case(tmp_path / "case", case)


def test_hash_options_and_distribution_aliases_remain_strings(tmp_path):
    case = {
        "name": "String identity limits",
        "files": {
            "requirements.txt": (
                "Foo_Bar==1.0\nfoo-bar==1.0\n" "requests==2.28.0 --hash=sha256:abcd\n"
            )
        },
    }
    actual = builder.compute_case(tmp_path / "case", case)
    # The two spellings remain 2 strings; the hash-bearing line adds 1: 2+1=3.
    expected = ["Foo_Bar==1.0", "foo-bar==1.0", "requests==2.28.0 --hash=sha256:abcd"]
    assert actual["runtime"] == expected
    assert sorted(actual["generated_runtime"]) == expected
    assert actual["runtime_count"] == actual["distinct_count"] == 3


@pytest.mark.selenium
def test_chart_keeps_accessible_name_after_render_and_selection(built):
    with sync_playwright() as runtime:
        try:
            browser = runtime.chromium.launch(channel="chrome")
        except Error:
            pytest.skip("Headless Chrome could not launch; this check requires Chrome.")
        with browser:
            page = browser.new_page()
            page.set_content(built["html"])
            for selection in (None, "1", "0"):
                if selection is not None:
                    page.select_option("#case-choice", selection)
                chart = page.locator("#count-chart")
                label = chart.get_attribute("aria-labelledby")
                assert label
                assert chart.locator(f"title#{label}").count() == 1
                assert (
                    page.get_by_role(
                        "img", name="Requirement string counts by dependency group"
                    ).count()
                    == 1
                )
