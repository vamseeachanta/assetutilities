"""Numerical anchors and delivery checks for the units module report."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/reports/build_units_report.py"
REPORT = ROOT / "docs/reports/modules/aunits/units-report.html"
REBUILD = "uv run python scripts/reports/build_units_report.py"


@pytest.fixture(scope="module")
def builder():
    assert BUILDER.is_file(), f"Report generator missing; implement {BUILDER.name}"
    spec = importlib.util.spec_from_file_location("units_report", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hand_anchor_pressure(builder):
    # NIST SP 811 (2008), Table 5: kilo = 1000.
    # p = 101.325 kPa * 1000 Pa/kPa = 101325 Pa; relative tolerance 1e-12.
    assert builder.calculate()["values"]["pressure_pa"] == pytest.approx(
        101325, rel=1e-12
    )


def test_hand_anchor_force(builder):
    # OpenStax University Physics 1 (2016), 14.1 Eq. 14.3: F = p*A.
    # 101.325 kPa * 4.0 m^2 = 405.300 kN = 405.3 kN; tolerance 1e-12.
    assert builder.calculate()["values"]["force_kn"] == pytest.approx(405.3, rel=1e-12)


def test_hand_anchor_length(builder):
    # NIST SP 811 (2008), Table 5: milli = 0.001.
    # Guide thickness = 25.0 mm * 0.001 m/mm = 0.025 m; tolerance 1e-12.
    assert builder.calculate()["values"]["thickness_m"] == pytest.approx(
        0.025, rel=1e-12
    )


def test_module_consistency_checks(builder):
    from assetutilities.units import TrackedQuantity

    data = builder.calculate()
    values = data["values"]
    pressure = TrackedQuantity(values["pressure_kpa"], "kPa")
    area = TrackedQuantity(values["area_m2"], "m**2")
    force = pressure * area
    assert values["pressure_pa"] == pytest.approx(pressure.to("Pa").magnitude)
    assert values["force_n"] == pytest.approx(force.to("N").magnitude)
    assert values["force_kn"] == pytest.approx(force.to("kN").magnitude)
    assert values["thickness_m"] == pytest.approx(
        TrackedQuantity(values["thickness_mm"], "mm").to("m").magnitude
    )
    for point in data["curve"]:
        assert point["force_kn"] == pytest.approx(
            (pressure * TrackedQuantity(point["area_m2"], "m**2")).to("kN").magnitude,
            rel=1e-12,
        )
    assert data["audit"]["outputs"]["force"]["magnitude"] == values["force_kn"]
    assert data["audit"]["outputs"]["force"]["unit"] == "kilonewton"


def test_displayed_inputs_recompute_headline(builder):
    data = builder.calculate()
    display = builder.display_values(data)
    assert float(display["pressure_kpa"]) * float(display["area_m2"]) == (
        pytest.approx(float(display["force_kn"]), abs=0.00001)
    )


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.numbers = []
        self.active_number = None
        self.in_example = False
        self.example_text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if "href" in attributes:
            self.links.append(attributes["href"])
        if attributes.get("id") == "worked-example":
            self.in_example = True
        if "data-value" in attributes:
            self.active_number = attributes["data-value"]

    def handle_endtag(self, tag):
        if tag == "span":
            self.active_number = None
        if tag == "section":
            self.in_example = False

    def handle_data(self, text):
        if self.active_number:
            self.numbers.append((self.active_number, text))
        elif self.in_example:
            self.example_text.append(text)


def test_every_worked_number_matches_module(builder):
    parser = ReportParser()
    parser.feed(builder.render_report())
    values = builder.calculate()["values"]
    assert {name for name, _ in parser.numbers} == set(values)
    for name, value in parser.numbers:
        assert float(value) == pytest.approx(values[name], rel=1e-12, abs=1e-12)
    # Exclude the section number; all other example numbers must use data-value.
    prose = " ".join(parser.example_text).replace("6 Worked example", "")
    assert not re.search(r"\d", prose), prose


def test_tolerant_rebuild_and_source_freshness(builder, tmp_path):
    builder.build(tmp_path)
    fresh = (tmp_path / REPORT.name).read_text(encoding="utf-8")
    committed = REPORT.read_text(encoding="utf-8")

    # Embedded values are rounded; volatile audit timestamps are excluded.
    # Compare numerical payloads tolerantly, then mask them for text comparison.
    def payload(html):
        match = re.search(
            r'<script id="report-data" type="application/json">(.*?)</script>',
            html,
            re.S,
        )
        return json.loads(match.group(1))

    saved, current = payload(committed), payload(fresh)
    assert saved["source_digests"] == current["source_digests"], REBUILD
    assert saved["values"] == pytest.approx(current["values"], rel=1e-12), REBUILD
    assert saved["curve"] == current["curve"], REBUILD  # Display-rounded points.
    assert saved["versions"] == current["versions"], REBUILD

    def compare_audit(saved_record, current_record):
        if isinstance(current_record, dict):
            assert saved_record.keys() == current_record.keys(), REBUILD
            for key, value in current_record.items():
                compare_audit(saved_record[key], value)
        elif isinstance(current_record, list):
            assert len(saved_record) == len(current_record), REBUILD
            for saved_item, current_item in zip(saved_record, current_record):
                compare_audit(saved_item, current_item)
        elif isinstance(current_record, (int, float)):
            assert saved_record == pytest.approx(current_record, rel=1e-12), REBUILD
        else:
            assert saved_record == current_record, REBUILD

    compare_audit(saved["audit"], current["audit"])
    mask = r'(<script id="report-data" type="application/json">).*?(</script>)'
    assert re.sub(mask, r"\1MASKED\2", committed, flags=re.S) == re.sub(
        mask, r"\1MASKED\2", fresh, flags=re.S
    ), REBUILD
    assert (tmp_path / "changes.json").read_text(encoding="utf-8") == (
        REPORT.parent / "changes.json"
    ).read_text(encoding="utf-8"), REBUILD
    assert b"\r" not in (tmp_path / REPORT.name).read_bytes()
    assert b"\r" not in (tmp_path / "changes.json").read_bytes()


def test_structure_sources_and_public_wording(builder):
    html = builder.render_report()
    parser = ReportParser()
    parser.feed(html)
    assert 'class="hs-doc doc"' in html
    assert len(re.findall(r"<h2>\d+ ", html)) == 10
    assert not re.search(r"<h[4-6][ >]", html)
    assert len(parser.ids) == len(set(parser.ids))
    for link in parser.links:
        if link.startswith("#"):
            assert link[1:] in parser.ids
        elif not link.startswith("https://"):
            assert (REPORT.parent / link).resolve().is_file(), link
    assert "Draft for maintainer review" in html
    assert "NOT_EVALUATED" in html
    assert "101.325" in html and "405.3" in html
    assert "2008" in html and "2016" in html and "14.3" in html
    assert "<strong>" not in html and "<b>" not in html
    for pattern in (
        r"\b(owner|lane|seat|session|Codex|Claude|hostname)\b",
        r"/(home|mnt|tmp)/",
    ):
        assert not re.search(pattern, html, re.I), pattern
    for tag in re.findall(r"<(?:script|link|img)\b[^>]*>", html):
        assert not re.search(r"(?:src|href)=", tag), tag


def test_change_panel_and_comment_save(builder, tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for the comment interaction check")
    html = builder.render_report()
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert len(scripts) == 1
    script = tmp_path / "interaction.js"
    payload = re.search(
        r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S
    ).group(1)
    harness = "const initialData = " + payload + ";\n" + JS_HARNESS
    script.write_text(
        harness + scripts[0] + "\ncheckInteractions();\n",
        encoding="utf-8",
        newline="\n",
    )
    result = subprocess.run(
        [node, str(script)],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_report_assets_use_explicit_text_encoding():
    for path in (BUILDER, Path(__file__)):
        text = path.read_text(encoding="utf-8")
        for call in ast.walk(ast.parse(text)):
            if not isinstance(call, ast.Call) or not isinstance(
                call.func, ast.Attribute
            ):
                continue
            if call.func.attr not in {"read_text", "write_text"}:
                continue
            keywords = {
                item.arg: ast.literal_eval(item.value) for item in call.keywords
            }
            assert keywords.get("encoding") == "utf-8"
            if call.func.attr == "write_text":
                assert keywords.get("newline") == "\n"


JS_HARNESS = r"""
const assert = require("node:assert/strict");
const elements = {};
let written = "";
let closed = false;
let downloaded = false;
const events = {};
function element() {
  return {
    value: "", textContent: "", children: [], handlers: {},
    addEventListener(name, callback) { this.handlers[name] = callback; },
    replaceChildren() { this.children = []; },
    appendChild(child) { this.children.push(child); },
    click() { downloaded = true; }
  };
}
const points = [0, 1].map(index => Object.assign(element(), {dataset: {point: String(index)}}));
global.document = {
  getElementById(id) { return elements[id] ??= element(); },
  createElement() { return element(); },
  querySelectorAll() { return points; }
};
document.getElementById("report-data").textContent = JSON.stringify(initialData);
global.window = {
  addEventListener(name, callback) { events[name] = callback; },
  async showSaveFilePicker(options) {
    assert.equal(options.suggestedName, "units-report.comments.json");
    return { async createWritable() {
      return { async write(text) { written = text; }, async close() { closed = true; } };
    }};
  }
};
async function checkInteractions() {
  const click = id => elements[id].handlers.click();
  document.getElementById("comment-section").value = "Worked example";
  document.getElementById("comment-text").value = "<img src=x onerror=alert(1)>";
  click("add-comment");
  assert.equal(elements["comments-list"].children[0].textContent,
    "Worked example: <img src=x onerror=alert(1)>");
  await click("save-comments");
  assert.equal(JSON.parse(written).comments[0].section, "Worked example");
  assert.equal(JSON.parse(written).comments[0].text, "<img src=x onerror=alert(1)>");
  assert.equal(closed, true);
  assert.match(elements["save-status"].textContent, /saved/);
  elements["comment-text"].value = "Second note";
  click("add-comment");
  window.showSaveFilePicker = async () => { throw {name: "AbortError"}; };
  await click("save-comments");
  assert.match(elements["save-status"].textContent, /cancelled/);
  assert.equal(elements["comments-list"].children.length, 2);
  let prevented = false;
  events.beforeunload({preventDefault() { prevented = true; }});
  assert.equal(prevented, true);
  delete window.showSaveFilePicker;
  await click("save-comments");
  assert.equal(downloaded, true);
  assert.match(elements["save-status"].textContent, /not been confirmed/);
  await elements["load-comments"].handlers.change({target: {files: [{async text() {return "{}";}}]}});
  assert.match(elements["save-status"].textContent, /Save the current/);
  // Mark the outstanding comments as saved through the direct-save path.
  window.showSaveFilePicker = async () => ({async createWritable() {
    return {async write() {}, async close() {}};
  }});
  await click("save-comments");
  await elements["load-comments"].handlers.change({target: {files: [{async text() {return "{}";}}]}});
  assert.match(elements["save-status"].textContent, /not a comment file/);
  const loaded = JSON.stringify({document: "Units module analysis", revision: "A",
    comments: [{section: "Basis and Criteria", text: "Loaded note"}]});
  await elements["load-comments"].handlers.change({target: {files: [{async text() {return loaded;}}]}});
  assert.equal(elements["comments-list"].children.length, 1);
  assert.match(elements["comments-list"].children[0].textContent, /Loaded note/);
  points[1].handlers.focus();
  assert.match(elements["chart-detail"].textContent, /area 1.0 m²; demand 101.325 kN/);
  assert.match(elements["chart-detail"].textContent, /not evaluated/);
}
"""
