"""Public conversion anchors, library consistency and report rebuild checks."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import pytest

from assetutilities.common.transform import Transform, TransformData

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "common_report_builder", ROOT / "scripts/reports/build_common_report.py"
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
REPORT = ROOT / "docs/reports/modules/acommon/index.html"
REBUILD = "Rebuild with: python scripts/reports/build_common_report.py"


def payload(document: str, name: str) -> dict:
    match = re.search(
        rf'<script id="{name}" type="application/json">(.*?)</script>', document, re.S
    )
    assert match, f"Missing {name}. {REBUILD}"
    return json.loads(match[1])


def test_hand_anchor_lower_rounding_bound():
    # NIST SP 811 (2008), B.7.2/B.8: y = x * 0.3048 + 0.
    # 35.5 * 3048 / 10000 = (35 * 3048 + 3048 / 2) / 10000
    # = (106680 + 1524) / 10000 = 10.8204 m; absolute tolerance 1e-12 m.
    assert builder.example()["list_m"][0] == pytest.approx(10.8204, abs=1e-12, rel=0)


def test_hand_anchor_published_example():
    # NIST SP 811 (2008), B.7.2/B.8: y = 36 * 0.3048 + 0.
    # (30 * 3048 + 6 * 3048) / 10000 = (91440 + 18288) / 10000
    # = 10.9728 m; B.7.2 reports 11.0 m. Absolute tolerance 1e-12 m.
    data = builder.example()
    assert data["scalar_m"] == pytest.approx(10.9728, abs=1e-12, rel=0)
    assert data["reported_m"] == "11.0"


def test_hand_anchor_upper_rounding_bound():
    # NIST SP 811 (2008), B.7.2/B.8: y = 36.5 * 0.3048 + 0.
    # (36 * 3048 + 3048 / 2) / 10000 = (109728 + 1524) / 10000
    # = 11.1252 m; absolute tolerance 1e-12 m.
    assert builder.example()["list_m"][2] == pytest.approx(11.1252, abs=1e-12, rel=0)


def test_committed_numbers_consistency_with_module_calls():
    """Consistency check: every example and chart output is compared with library calls."""
    data = payload(REPORT.read_text(encoding="utf-8"), "example-data")
    settings = {"scale": data["scale_m_per_ft"], "shift": data["shift_m"]}
    scalar = TransformData().linear({**settings, "data": data["inputs_ft"][1]})
    listed = TransformData().linear({**settings, "data": data["inputs_ft"].copy()})
    frame = Transform().get_transformed_df(
        [{**settings, "column": "length"}], pd.DataFrame({"length": data["inputs_ft"]})
    )
    chart = TransformData().linear({**settings, "data": data["chart_ft"].copy()})
    assert data["scalar_m"] == pytest.approx(scalar["data"], abs=1e-12, rel=0)
    assert data["list_m"] == pytest.approx(listed["data"], abs=1e-12, rel=0)
    assert data["frame_m"] == pytest.approx(frame["length"].tolist(), abs=1e-12, rel=0)
    assert data["chart_m"] == pytest.approx(chart["data"], abs=5e-5, rel=0)
    assert data["reported_m"] == format(scalar["data"], ".1f")
    records = Transform().dataframe_to_dict(frame, {"orient": "records"})
    for recorded, fresh in zip(data["records"], records):
        assert recorded["length"] == pytest.approx(fresh["length"], abs=1e-12, rel=0)
    assert data["source_frame_ft"] == data["inputs_ft"]


def assert_numeric_equal(actual, expected):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), REBUILD
        for key in expected:
            assert_numeric_equal(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected), REBUILD
        for left, right in zip(actual, expected):
            assert_numeric_equal(left, right)
    elif isinstance(expected, (int, float)):
        # Tolerance is half the last displayed metre digit; never compare raw float text.
        assert actual == pytest.approx(expected, abs=5e-5, rel=0), REBUILD
    else:
        assert actual == expected, REBUILD


def test_rebuild_matches_committed_structure_and_display_precision(tmp_path):
    document, changes = builder.build()
    fresh = tmp_path / "index.html"
    fresh.write_text(document, encoding="utf-8", newline="\n")
    committed = REPORT.read_text(encoding="utf-8")
    for name in ("example-data", "change-data", "calculation-record"):
        before, after = payload(committed, name), payload(document, name)
        if name == "example-data":
            assert_numeric_equal(before, after)
        else:
            assert before == after, REBUILD

    # Mask numeric serialization and source digest, while comparing all visible text and code.
    def mask(text):
        return re.sub(
            r'(<script id="(?:example-data|calculation-record)" type="application/json">).*?(</script>)',
            r"\1MASKED\2",
            text,
            flags=re.S,
        )

    assert mask(committed) == mask(fresh.read_text(encoding="utf-8")), REBUILD
    assert (REPORT.parent / "changes.json").read_text(
        encoding="utf-8"
    ) == changes, REBUILD


def test_cli_rebuild_uses_selected_destination(tmp_path):
    subprocess.run(
        [
            __import__("sys").executable,
            str(ROOT / "scripts/reports/build_common_report.py"),
            "--output-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    actual = payload(
        (tmp_path / "index.html").read_text(encoding="utf-8"), "example-data"
    )
    assert_numeric_equal(actual, builder.example())
    assert json.loads((tmp_path / "changes.json").read_text(encoding="utf-8")) == [
        builder.REVISION
    ]


def test_calculation_source_record_and_selected_test_inventory():
    document = REPORT.read_text(encoding="utf-8")
    assert (
        payload(document, "calculation-record") == builder.calculation_record()
    ), REBUILD
    assert builder.existing_test_count() == 5, REBUILD


def test_documented_mutation_and_missing_column_behaviour():
    config = {"data": [36], "scale": 0.3048, "shift": 0}
    assert TransformData().linear(config) is config
    assert config["data"] == pytest.approx([10.9728], abs=1e-12, rel=0)
    dispatch = {"type": "linear", "data": 36, "scale": 0.3048, "shift": 0}
    assert TransformData().get_transformed_data(dispatch) is None
    assert dispatch["data"] == pytest.approx(10.9728, abs=1e-12, rel=0)
    source = pd.DataFrame({"length": [36]})
    untouched = source.copy(deep=True)
    output = Transform().get_transformed_df(
        [{"column": "absent", "scale": 0.3048, "shift": 0}], source
    )
    pd.testing.assert_frame_equal(source, untouched)
    pd.testing.assert_frame_equal(output, source)
    assert output is not source
    duplicate = pd.DataFrame([[36, 36]], columns=["length", "length"])
    assert Transform().dataframe_to_dict(duplicate, {"orient": "records"}) == {}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.visible = [], [], []
        self.hidden = 0
        self.section_headings = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "a":
            self.links.append(attributes.get("href", ""))
        if tag in ("script", "style"):
            self.hidden += 1
        if tag == "h2":
            self.section_headings.append([])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)


def test_built_page_references_wording_bounds_and_table():
    document = REPORT.read_text(encoding="utf-8")
    page = Page()
    page.feed(document)
    assert len(page.ids) == len(set(page.ids))
    assert all(link[1:] in page.ids for link in page.links if link.startswith("#"))
    assert builder.SOURCE_URL in page.links
    assert '<body class="hs-doc">' in document
    assert len(re.findall(r"<h2>\d+ ", document)) == 10
    assert not re.search(
        r"<h[4-6]|<b>|<strong>|<script[^>]+src=|<link[^>]+stylesheet", document
    )
    text = " ".join(page.visible)
    assert "Draft for maintainer review" in text
    prohibited = [
        "own" + "er",
        "could",
        "should",
        "would",
        "jo" + "b",
        "fl" + "eet",
        "dis" + "patcher",
        "la" + "ne",
        "ses" + "sion",
    ]
    assert not re.search(r"\b(" + "|".join(prohibited) + r")\b", text, re.I)
    assert "No acceptance limit is supplied" in text
    assert 'id="toggle-bounds"' in document
    rows = re.search(
        r'<table id="example-table">.*?<tbody>(.*?)</tbody>', document, re.S
    )[1]
    cells = re.findall(r"<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", rows)
    data = payload(document, "example-data")
    assert len(cells) == len(data["inputs_ft"])
    for (x, y, source), expected_x, expected_y in zip(
        cells, data["inputs_ft"], data["list_m"]
    ):
        assert float(x) == expected_x
        assert float(y) == pytest.approx(expected_y, abs=5e-5, rel=0)
        assert "B.7.2" in source


def test_utf8_lf_and_publication_scan():
    paths = [
        REPORT,
        REPORT.parent / "changes.json",
        Path(builder.__file__),
        Path(__file__),
    ]
    # Construct forbidden directory markers so the check contains no such literal itself.
    markers = ["/" + "home" + "/", "/" + "mnt" + "/"]
    email = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
    for path in paths:
        raw = path.read_bytes()
        assert b"\r" not in raw, f"LF required: {path.name}"
        text = raw.decode("utf-8")
        assert all(marker not in text for marker in markers), path.name
        assert not email.search(text), path.name
    # Embedded calculation values are rounded; CPU-dependent tail digits are absent.
    document = REPORT.read_text(encoding="utf-8")
    numerical_payload = re.search(
        r'<script id="example-data" type="application/json">(.*?)</script>',
        document,
        re.S,
    )[1]
    assert not re.search(r"\d+\.\d{7,}", numerical_payload), REBUILD


def test_interactive_script_syntax_and_comment_round_trip(tmp_path):
    """Exercise the actual script with a minimal DOM; this is not browser validation."""
    document = REPORT.read_text(encoding="utf-8")
    script = re.search(r"<script>\s*(.*?)</script>", document, re.S)[1]
    # A DOM stub permits actual handlers to run without a browser or external dependencies.
    harness = r"""
const vm = require("node:vm"), assert = require("node:assert/strict");
class Element {
  constructor(id="") { this.id=id; this.children=[]; this.events={}; this.attributes={};
    this.value=""; this.textContent=""; this.namespaceURI="http://www.w3.org/2000/svg"; }
  setAttribute(k,v) {this.attributes[k]=v;}
  appendChild(c) {this.children.push(c);}
  replaceChildren() {this.children=[];}
  addEventListener(k,v) {this.events[k]=v;}
  querySelector() {return {textContent: this.id};}
  click() {this.clicked=true;}
}
const ids = new Map();
const get = id => {if (!ids.has(id)) ids.set(id,new Element(id)); return ids.get(id);};
get("example-data").textContent=JSON.stringify(INPUT_DATA);
get("change-data").textContent=JSON.stringify(INPUT_CHANGES);
get("case-index").value="10"; get("comment-section").value="summary";
const sections=[new Element("summary"),new Element("results")];
const context={document:{getElementById:get, createElement:()=>new Element(),
  createElementNS:()=>new Element(),querySelectorAll:()=>sections},
  window:{}, URL:{createObjectURL:()=>"blob:example",revokeObjectURL:()=>{}},
  Blob, setTimeout:fn=>fn()};
vm.createContext(context); vm.runInContext(SCRIPT,context);
assert.match(get("chart-readout").textContent,/10\.9728/);
get("comment-text").value="Check the unit basis.";
get("add-comment").events.click();
assert.equal(get("comments").children[0].textContent,"summary: Check the unit basis.");
let saved="";
context.window.showDirectoryPicker=async()=>({getFileHandle:async name=>{
  assert.equal(name,"common-module.comments.json");
  return {createWritable:async()=>({write:async text=>{saved=text;},close:async()=>{}})};
}});
(async()=>{
  await get("save-comments").events.click();
  assert.equal(JSON.parse(saved).comments[0].text,"Check the unit basis.");
  get("load-comments").events.change({target:{files:[{text:async()=>saved}]}});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(get("comments").children.length,1);
  const bad=JSON.stringify({revision:"1",comments:[{section:"missing",text:"bad"}]});
  await get("load-comments").events.change({target:{files:[{text:async()=>bad}]}});
  assert.equal(get("comments").children.length,1);
  assert.match(get("comment-status").textContent,/not accepted/);
  context.window.showDirectoryPicker=async()=>{throw new Error("cancelled");};
  await get("save-comments").events.click();
  assert.match(get("comment-status").textContent,/remain in memory/);
  get("toggle-bounds").events.click({target:get("toggle-bounds")});
  assert.equal(get("toggle-bounds").attributes["aria-pressed"],"false");
  get("zoom-chart").events.click(); get("reset-chart").events.click();
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
    harness = (
        "const INPUT_DATA="
        + json.dumps(payload(document, "example-data"))
        + ";\n"
        + "const INPUT_CHANGES="
        + json.dumps(payload(document, "change-data"))
        + ";\n"
        + "const SCRIPT="
        + json.dumps(script)
        + ";\n"
        + harness
    )
    path = tmp_path / "report-interactions.cjs"
    path.write_text(harness, encoding="utf-8", newline="\n")
    result = subprocess.run(
        ["node", str(path)], capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 0, result.stderr
