"""Executable evidence for the workflow API module report.

Rebuild: python scripts/reports/build_workflow_api_report.py
Integer byte lengths and counts are exact; no floating point tolerance is needed.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REBUILD = "python scripts/reports/build_workflow_api_report.py"
DESTINATION = ROOT / "docs/reports/modules/aworkflowapi"


@pytest.fixture(scope="module")
def builder():
    spec = importlib.util.spec_from_file_location(
        "workflow_module_report", ROOT / "scripts/reports/build_workflow_api_report.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def evidence(builder):
    return builder.calculate()


@pytest.fixture(scope="module")
def rebuilt(builder, evidence):
    return builder.render(evidence)


def embedded_data(page):
    match = re.search(
        r'<script id="report-data" type="application/json">(.*?)</script>', page, re.S
    )
    assert match, "The report needs its calculation evidence."
    return json.loads(match.group(1))


def test_hand_anchor_registered_file_count(evidence):
    # The public input declares FST1 and FST2. Each group writes one CSV:
    # one file + one file = 2 files; the configuration dump is excluded.
    assert evidence["example"]["file_count"] == 2


def test_hand_anchor_ascii_byte_length(evidence):
    # UTF-8 uses one byte for each ASCII letter: a + b + c = 1 + 1 + 1 = 3.
    assert evidence["anchors"]["ascii_bytes"] == 3


def test_hand_anchor_structured_byte_length(evidence):
    # Compact {"a":1}: braces 2 + quotes 2 + key 1 + colon 1 + digit 1 = 7.
    assert evidence["anchors"]["structured_bytes"] == 7


def test_hand_anchor_two_member_byte_length(evidence):
    # Compact {"a":1,"b":2}: braces 2 + two members of 5 + comma 1 = 13.
    assert evidence["anchors"]["two_member_bytes"] == 13


def test_module_consistency_for_every_worked_number(builder, evidence, rebuilt):
    from assetutilities.workflow_api import artifact, run_workflow

    fresh = run_workflow("data_exploration", verify_reproducible=True)
    assert fresh.status == "ok", fresh.warnings
    assert fresh.determinism["reproducible"] is True
    assert evidence["example"]["outputs"] == [
        item["basename"] for item in fresh.result["outputs"]
    ]
    assert evidence["example"]["file_count"] == len(fresh.result["outputs"])
    assert (
        evidence["anchors"]["ascii_bytes"]
        == artifact.physical_artifact(
            b"abc", media_type="text/plain", native_format="text"
        )["size_bytes"]
    )
    assert (
        evidence["anchors"]["structured_bytes"]
        == artifact.structured_artifact({"a": 1})["size_bytes"]
    )
    assert (
        evidence["anchors"]["two_member_bytes"]
        == artifact.structured_artifact({"b": 2, "a": 1})["size_bytes"]
    )
    assert evidence["curve"] == builder.byte_curve()
    values = builder.display_values(evidence)
    displayed = re.findall(r'data-number="([^"]+)"[^>]*>(\d+)</span>', rebuilt)
    assert {key for key, _ in displayed} == set(values)
    for key, value in displayed:
        assert int(value) == values[key], key


def test_rebuild_matches_committed_report(rebuilt):
    committed = (DESTINATION / "index.html").read_text(encoding="utf-8")
    # All embedded measurements are integer byte counts or counts. There are
    # no CPU-dependent floating point strings, timestamps or source revisions.
    assert committed == rebuilt, f"Report is stale; rebuild with: {REBUILD}"


def test_generator_writes_utf8_lf_to_requested_directory(
    builder, rebuilt, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "sys.argv", ["build_workflow_api_report.py", "--output-dir", str(tmp_path)]
    )
    builder.main()
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == rebuilt
    assert (
        json.loads((tmp_path / "changes.json").read_text(encoding="utf-8"))
        == builder.CHANGES
    )
    for path in tmp_path.iterdir():
        assert b"\r" not in path.read_bytes()


def test_source_inventory_failure_names_rebuild(evidence, rebuilt):
    stored = embedded_data((DESTINATION / "index.html").read_text(encoding="utf-8"))
    assert stored["source_digests"] == evidence["source_digests"], REBUILD
    assert stored["test_inventory"] == evidence["test_inventory"], REBUILD
    assert embedded_data(rebuilt) == evidence


def test_changes_panel_matches_companion_file(builder, rebuilt):
    changes = json.loads((DESTINATION / "changes.json").read_text(encoding="utf-8"))
    assert changes == builder.CHANGES
    assert changes["revision"] == "A"
    assert "change-panel" in rebuilt


class PageStructure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.h2_count = 0
        self.external_assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h2":
            self.h2_count += 1
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.links.append(attrs["href"][1:])
        if (tag == "script" and "src" in attrs) or (
            tag == "link" and attrs.get("rel") == "stylesheet"
        ):
            self.external_assets.append(attrs)


def test_single_file_sections_references_and_style(rebuilt):
    page = PageStructure()
    page.feed(rebuilt)
    assert page.h2_count == 10
    assert len(page.ids) == len(set(page.ids))
    assert set(page.links) <= set(page.ids)
    assert not page.external_assets
    assert '<body class="hs-doc">' in rebuilt
    assert "<h4" not in rebuilt
    assert "<b>" not in rebuilt and "<strong>" not in rebuilt
    assert "Draft for maintainer review" in rebuilt
    assert "showDirectoryPicker" in rebuilt
    assert "createWritable()" in rebuilt
    assert "comments.json" in rebuilt


def test_built_visible_text_register(rebuilt):
    visible = re.sub(r"<(script|style)\b.*?</\1>", "", rebuilt, flags=re.S)
    visible = re.sub(r"<[^>]*>", " ", visible)
    forbidden = r"\b(could|should|would|certified|compliant|validated)\b"
    assert not re.search(forbidden, visible, flags=re.I)
    assert "NOT_EVALUATED" in visible


def test_utf8_lf_and_house_stylesheet(builder, rebuilt):
    for path in (
        DESTINATION / "index.html",
        DESTINATION / "changes.json",
        DESTINATION / "house-style.css",
        ROOT / "scripts/reports/build_workflow_api_report.py",
        Path(__file__),
    ):
        content = path.read_bytes()
        content.decode("utf-8")
        assert b"\r" not in content, path.name
        assert all(line == line.rstrip(b" \t") for line in content.splitlines()), path.name
    assert (DESTINATION / "house-style.css").read_text(encoding="utf-8") in rebuilt


def test_unknown_workflow_is_reported_as_error():
    from assetutilities.workflow_api import run_workflow

    result = run_workflow("missing-report-example")
    assert result.status == "error"
    assert result.determinism["reproducible"] is None
    assert result.result == {}


def test_chart_and_comment_interactions_without_browser(rebuilt):
    """Exercise event handlers with a small DOM stand-in, without a browser."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable; the report interaction check needs Node.")
    script = re.findall(r"<script>(.*?)</script>", rebuilt, re.S)[-1]
    report_data = json.dumps(embedded_data(rebuilt))
    changes = re.search(
        r'<script id="change-data" type="application/json">(.*?)</script>',
        rebuilt,
        re.S,
    ).group(1)
    sections = re.findall(r'<section id="([^"]+)"><h2>(.*?)</h2>', rebuilt)
    harness = r"""
const assert = require("node:assert/strict");
class Element {
  constructor(tag) {this.tag = tag; this.children = []; this.events = {}; this.value = ""; this.textContent = ""; this.attrs = {};}
  setAttribute(key, value) {this.attrs[key] = value;}
  appendChild(child) {this.children.push(child); return child;}
  addEventListener(name, callback) {this.events[name] = callback;}
  replaceChildren() {this.children = [];}
}
const elements = new Map();
const element = id => {if (!elements.has(id)) elements.set(id, new Element(id)); return elements.get(id);};
const sectionData = SECTION_DATA;
const sectionElements = sectionData.map(([id, text]) => ({id:id,querySelector:() => ({textContent:text})}));
global.document = {
  getElementById:element,
  createElement:tag => new Element(tag),
  createElementNS:(namespace, tag) => new Element(tag),
  querySelectorAll:() => sectionElements
};
let saved = "";
let savedName = "";
let closed = false;
global.window = {showDirectoryPicker:async () => ({
  getFileHandle:async name => {savedName = name; return {
    createWritable:async () => ({write:async text => {saved = text;},close:async () => {closed = true;}})
  };}
})};
element("report-data").textContent = REPORT_DATA;
element("change-data").textContent = CHANGE_DATA;
"""
    harness = (
        harness.replace("SECTION_DATA", json.dumps(sections))
        .replace("REPORT_DATA", json.dumps(report_data))
        .replace("CHANGE_DATA", json.dumps(changes))
    )
    actions = r"""
const dots = element("byte-chart").children.filter(child => child.tag === "circle");
assert.equal(dots.length, data.curve.length);
dots.at(-1).events.click();
assert.match(element("chart-detail").textContent, /demand: 3 bytes/);
assert.match(element("chart-detail").textContent, /limit: NOT_EVALUATED/);
element("comment-section").value = "worked";
element("comment-text").value = "Check the example scope.";
element("comment-add").events.click();
assert.equal(element("comment-list").children.length, 1);
await element("comment-save").events.click();
assert.equal(savedName, "comments.json");
assert.equal(closed, true);
assert.equal(JSON.parse(saved).comments[0].text, "Check the example scope.");
await element("comment-load").events.change({target:{files:[{text:async () => saved}]}});
assert.match(element("comment-status").textContent, /loaded/);
await element("comment-load").events.change({target:{files:[{text:async () => "{}"}]}});
assert.match(element("comment-status").textContent, /not a comment file/);
global.window = {};
await element("comment-save").events.click();
assert.match(element("comment-status").textContent, /unavailable/);
console.log("Chart inspection and comment save/load checks passed.");
"""
    result = subprocess.run(
        [node],
        input="(async () => {\n"
        + harness
        + script
        + actions
        + "\n})().catch(error => {console.error(error);process.exitCode=1;});\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "save/load checks passed" in result.stdout
