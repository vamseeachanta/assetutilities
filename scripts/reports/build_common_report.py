"""Build the common-module report from public inputs and actual library calls.

Rebuild: python scripts/reports/build_common_report.py
Dependencies: numpy, pandas, plotly, PyYAML (including package import dependencies).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from assetutilities.common.transform import Transform, TransformData  # noqa: E402

DESTINATION = ROOT / "docs/reports/modules/acommon"
REBUILD = "python scripts/reports/build_common_report.py"
SOURCE_URL = (
    "https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication811e2008.pdf"
)
# NIST SP 811 (2008), B.7.2: published length and rounding endpoints.
LENGTHS_FT = [35.5, 36, 36.5]
SCALE = 0.3048  # NIST SP 811 (2008), B.8, international foot to metre (exact).
SHIFT = 0  # Selected input: length conversion has no origin offset (B.3).
REVISION = {
    "revision": "1",
    "date": "2026-10-21",
    "changes": [
        "The data-transformation interface is described using a published length conversion.",
        "Arithmetic values and rounding bounds are separated from the reported measurement.",
        "Mutation, missing-column behaviour and the unassessed utility areas are identified.",
    ],
}


def example() -> dict:
    """Evaluate scalar, list, DataFrame and record-export routes without file I/O."""
    transformer = TransformData()
    scalar = transformer.linear({"data": LENGTHS_FT[1], "scale": SCALE, "shift": SHIFT})
    config = {"data": LENGTHS_FT.copy(), "scale": SCALE, "shift": SHIFT}
    listed = transformer.linear(config)
    frame = pd.DataFrame({"length": LENGTHS_FT})
    converted = Transform().get_transformed_df(
        [{"column": "length", "scale": SCALE, "shift": SHIFT}], frame
    )
    records = Transform().dataframe_to_dict(converted, {"orient": "records"})
    # This is a selected plotting resolution, not an engineering constant.
    chart_x = [LENGTHS_FT[0] + index / 20 for index in range(21)]
    chart_y = transformer.linear({"data": chart_x, "scale": SCALE, "shift": SHIFT})
    return {
        "inputs_ft": LENGTHS_FT.copy(),
        "scale_m_per_ft": SCALE,
        "shift_m": SHIFT,
        "scalar_m": scalar["data"],
        "list_m": listed["data"],
        "frame_m": converted["length"].tolist(),
        "records": records,
        "source_frame_ft": frame["length"].tolist(),
        "reported_m": format(scalar["data"], ".1f"),
        "chart_ft": chart_x,
        "chart_m": chart_y["data"],
    }


def existing_test_count() -> int:
    """Count the selected existing tests; this is inventory, not execution evidence."""
    source = ROOT / "tests/unit/test_common_data.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    names = {"TestTransformGetTransformedDf", "TestTransformDataLinear"}
    return sum(
        isinstance(method, ast.FunctionDef) and method.name.startswith("test_")
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name in names
        for method in node.body
    )


def number(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}".replace("-", "−")


def publication_data(value):
    """Round embedded arrays without changing the values returned by the library."""
    if isinstance(value, dict):
        return {key: publication_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [publication_data(item) for item in value]
    if isinstance(value, float):
        return round(value, 6)
    return value


def build() -> tuple[str, str]:
    data = example()
    # Inlined repository stylesheet; comment removal omits external attribution URLs
    # from the rendered asset. Its repository locator is recorded in section 9.2.
    css = (ROOT / "docs/sub_utilities/assets/style.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S).strip()
    css = "\n".join(line.rstrip() for line in css.splitlines())
    rows = "\n".join(
        f"<tr><td>{x:g}</td><td>{number(y)}</td><td>Reference 1, B.7.2; module call</td></tr>"
        for x, y in zip(data["inputs_ft"], data["list_m"])
    )
    changes = json.dumps([REVISION], ensure_ascii=False, indent=2) + "\n"
    change_data = changes.replace("<", "\\u003c")
    evidence = json.dumps(publication_data(data), ensure_ascii=False, sort_keys=True)
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Common module: data transformation analysis</title>
<style>{css}</style>
</head>
<body class="hs-doc"><main class="container">
<header><h1>Common module: data transformation analysis</h1>
<p>Draft for maintainer review</p></header>
<section id="summary"><h2>1 Executive Summary</h2>
<p>The common module is a collection of shared configuration, data, file and presentation utilities.
Analysis is performed to determine how a sourced length conversion is applied by its data-transformation interfaces;
key results are summarized below.</p>
<ul><li>Length values are converted using an explicit international-foot basis.
<ul><li>The published input of {data['inputs_ft'][1]:g} ft returns {number(data['scalar_m'])} m before reporting precision is applied.
The reported result is {data['reported_m']} m under the rounding treatment in Reference 1, B.7.2.</li></ul></li>
<li>Data handling is selected according to the required mutation behaviour.
<ul><li>The DataFrame route returns a copy; the scalar and list route replaces data in the supplied configuration.
Neither route applies a physical acceptance limit or checks the unit basis.</li></ul></li></ul>
</section>
<section aria-label="Revision history"><h2>Revision history</h2>
<table><thead><tr><th>Revision</th><th>Date</th><th>What changed and why</th></tr></thead>
<tbody><tr><td>{REVISION['revision']}</td><td>{REVISION['date']}</td>
<td>Initial description of the transformation contract, public calculation and limits of use.</td></tr></tbody></table>
</section>
<nav aria-label="Contents"><p>
<a href="#summary">1 Summary</a> · <a href="#introduction">2 Introduction</a> ·
<a href="#basis">3 Basis</a> · <a href="#method">4 Method</a> ·
<a href="#results">5 Results</a> · <a href="#validation">6 Validation</a> ·
<a href="#limits">7 Limits</a> · <a href="#recommendations">8 Recommendations</a> ·
<a href="#references">9 References</a> · <a href="#symbols">10 Symbols</a> ·
<a href="#appendix">Appendix</a></p></nav>
<section id="introduction"><h2>2 Introduction</h2>
<p>The common module is used to support application inputs, data preparation and output production.
The selected workflow is bounded to numerical scaling and record export, with the surrounding utilities listed separately.</p>
<p>A full report is provided because callable interfaces and existing tests are present. Public usage is documented for
the validation class and structured-report functions; the numerical transformation contract is described here and is exercised by existing tests.
This report assesses a data operation, rather than installation feasibility or structural performance.</p>
<h3>2.1 Workflow and interfaces</h3>
<p>Input values and conversion settings are supplied by the caller. The output unit is attached by the caller after conversion.</p>
<figure><pre aria-label="Data flow">Numeric length values in ft + explicit scale and shift
                     ↓
         Scalar or list configuration → linear → same configuration, data replaced
                     or
         DataFrame + column settings → transform → new DataFrame in m
                                                     ↓
                                               record export</pre>
<figcaption>Figure 2.1. Data flow and mutation boundary. A physical-system schematic is inapplicable to this software operation.</figcaption></figure>
<p>The scalar and list entry point is <code>TransformData.linear(cfg)</code>, which returns the supplied dictionary after replacing
<code>data</code>. Its keys are <code>data</code>, <code>scale</code> and <code>shift</code>.
The DataFrame entry point is <code>Transform.get_transformed_df(settings, frame)</code>;
each setting supplies <code>column</code>, <code>scale</code> and <code>shift</code>.
Record export is provided by <code>dataframe_to_dict(frame, {{"orient": "records"}})</code>, returning a list of row dictionaries for this orientation.</p>
</section>
<section id="basis"><h2>3 Design Data and Criteria</h2>
<p>The international foot is adopted from Reference 1, B.8. The published example and its rounding interval are taken from Reference 1, B.7.2.</p>
<p>The input is {data['inputs_ft'][1]:g} ft; the exact conversion scale is {data['scale_m_per_ft']} m/ft.
The selected shift is {data['shift_m']} m because length conversion preserves the origin.
The source discusses inputs from {data['inputs_ft'][0]:g} to {data['inputs_ft'][2]:g} ft as a rounding interval;
the endpoints are displayed as bounds, without assigning a probability distribution.</p>
<p>No structural, thermal, operational or instrument limit is specified.
Acceptance for this example is numerical agreement at displayed precision with the public conversion and agreement among the called interfaces.
The rounding bounds are not acceptance limits. Measurement uncertainty is not estimated from these bounds.</p>
</section>
<section id="method"><h2>4 Analysis Methodology</h2>
<p>An affine transformation is applied to each selected value. The scaling interpretation follows Reference 1, B.3;
an offset conversion is illustrated there by the Celsius relation in 4.2.1.1, but no temperature calculation is assessed here.</p>
<p><code>y = a x + b</code>, where <code>x</code> is the input numerical value in ft, <code>y</code> is the output numerical value in m,
<code>a</code> is the scale in m/ft and <code>b</code> is the shift in m.
For the selected length conversion, <code>y = {data['scale_m_per_ft']} x + {data['shift_m']}</code> (Reference 1, B.3 and B.8).</p>
<p>The same source inputs are passed to scalar, list and DataFrame calls. The DataFrame is then exported as row records.
The public reporting precision is applied separately from the transformation. Intermediate arithmetic is displayed to preserve the exact converted values
for the stated decimal inputs; it does not imply measurement precision.</p>
<h3>4.1 Executable use</h3>
<p>The following call is made in the report generator. The source dictionary is replaced in place by the scalar result.</p>
<pre><code>from assetutilities.common.transform import TransformData
cfg = {{"data": {data['inputs_ft'][1]:g}, "scale": {data['scale_m_per_ft']}, "shift": {data['shift_m']}}}
result = TransformData().linear(cfg)
length_m = result["data"]</code></pre>
</section>
<section id="results"><h2>5 Detailed Results</h2>
<p>The scalar conversion returns {number(data['scalar_m'])} m. The reported measurement is {data['reported_m']} m,
following Reference 1, B.7.2, and is kept separate from the arithmetic result.</p>
<p>The converted rounding bounds are {number(data['list_m'][0])} m and {number(data['list_m'][2])} m.
All displayed results, bounds and plot ordinates are produced by module calls. The per-case values are listed in Appendix A.1.</p>
<figure>
<label for="case-index">Inspect length conversion</label>
<input id="case-index" type="range" min="0" max="{len(data['chart_ft']) - 1}" value="{len(data['chart_ft']) // 2}" step="1">
<output id="chart-readout" aria-live="polite"></output>
<p><button id="zoom-chart" type="button">Zoom to centre</button>
<button id="reset-chart" type="button">Reset view</button>
<button id="toggle-bounds" type="button" aria-pressed="true">Show rounding bounds</button>
<button id="export-chart" type="button">Export chart</button></p>
<svg id="conversion-chart" viewBox="0 0 800 380" role="img" aria-label="Converted length in metres against input length in international feet" width="100%"></svg>
<figcaption>Figure 5.1. Converted length against input length. Hover or focus a point, or move the inspection control.
The dashed lines show the published rounding bounds. No acceptance limit is supplied.</figcaption>
</figure>
<noscript><p>Interactive inspection requires JavaScript. The full numerical results remain available in Appendix A.1.</p></noscript>
</section>
<section id="validation"><h2>6 Validation Evidence</h2>
<p>Existing transformation tests are held in the repository. Their selected inventory contains {existing_test_count()} tests across scalar, list and DataFrame behaviour;
the inventory is not a statement about whole-module coverage.</p>
<p>The existing assertions cover scale and shift, an absent target column and preservation of the original DataFrame.
The added report checks compare each generated value with fresh module calls and include hand-worked anchors at both rounding bounds and the published central input.
These comparisons establish the example calculation and the interfaces exercised; they do not qualify unrelated utilities.</p>
<p>The published example is a numerical reference, not experimental benchmark data.
No physical benchmark dataset is used in this report. An execution record is provided in Appendix A.3.</p>
</section>
<section id="limits"><h2>7 Limits of Use</h2>
<p>Unit selection and data validity are delegated to the caller. Missing target columns are silently skipped by the DataFrame transformation.</p>
<p>The scalar and list route mutates the configuration; repeat application converts already converted data again.
Its dispatch wrapper mutates the input and returns no result. The list branch requires an actual list;
tuples and arrays are not assessed by this example. The DataFrame route copies its input and preserves the target column name,
so the caller is responsible for labelling the output unit. Multiple settings for the same column are applied in sequence.</p>
<p>No finite-number, unit-dimension, uncertainty or engineering acceptance check is performed by these transformation methods.
Generic scale and shift settings are not a replacement for a unit registry.
Record export requires unambiguous column names; duplicate names return an empty dictionary in the inspected implementation.</p>
<h3>7.1 Not covered</h3>
<p>Configuration merging, path resolution, file copying and editing, spreadsheet and document operations, database access,
web retrieval, validation scoring, logging, plotting and geographic conversion are outside the assessed workflow.
Their presence is established by source inventory, without asserting their readiness.</p>
<p>Interpolation and inverse geographic conversion contain unimplemented methods in the transformation source.
The CSV reader wrapper returns an undefined name in the inspected source.
These interfaces are excluded from the example; the documented structured-report entry point is present but is not called here.</p>
</section>
<section id="recommendations"><h2>8 Recommendations</h2>
<p>Explicit unit and column checks are recommended before transformation. The method is selected according to whether configuration mutation is intended.</p>
<p>Use the exact international-foot conversion only when that input basis is established, and apply reporting precision after the arithmetic
(Reference 1, B.7.2 and B.8). Preserve the original readings and write the output unit alongside the converted data.
Reject absent target columns before the DataFrame call, because the implementation skips them.</p>
<p>The next bounded extension is a checked transformation adapter with declared input units, output units and required columns.
Its first acceptance cases are a missing column, a non-finite value and repeated conversion.
For the excluded CSV wrapper, return-value repair and a file-reading test are recommended before adoption;
the interpolation and inverse-geographic placeholders require implemented behaviour and tests before use.</p>
<p>No failing physical result is reported. Numerical agreement is limited to the selected reference and calls;
engineering limits require a separate, sourced acceptance basis.</p>
</section>
<section id="references"><h2>9 References</h2>
<p>The conversion basis is taken from an open institutional publication. Repository records identify interfaces and test assertions rather than establish physical conversion factors.</p>
<h3>9.1 Published reference</h3>
<p id="ref-1">Reference 1. NIST Special Publication 811, Guide for the Use of the International System of Units, 2008 edition:
4.2.1.1 (temperature offset relation), B.3 (conversion-factor use), B.7.2 (rounding converted values, published length example),
and B.8 (international-foot conversion). <a href="{SOURCE_URL}">Open publication</a>.
The conversion clauses are used; the publication's historical definitions of base units are not adopted as current definitions.</p>
<h3>9.2 Repository records and rebuild</h3>
<p>Calculation source: <code>src/assetutilities/common/transform.py</code>.
Compatibility exports: <code>src/assetutilities/common/data.py</code>.
Existing tests: <code>tests/unit/test_common_data.py</code>, classes <code>TestTransformGetTransformedDf</code> and <code>TestTransformDataLinear</code>.</p>
<p>Documented entry points: <code>src/assetutilities/common/validation.py</code> (class usage) and
<code>docs/modules/documentation/standard-report.md</code> (structured reports).
Excluded CSV implementation: <code>src/assetutilities/common/readers/csv_reader.py</code>.
Module inventory: <code>MODULE_STRUCTURE.md</code> and <code>docs/maps/assetutilities-operator-map.md</code>.</p>
<p>Presentation basis: the inlined stylesheet is copied from <code>docs/sub_utilities/assets/style.css</code>, with comments removed.
No existing page with the requested body class was found in the inspected documentation; <code>hs-doc</code> is applied here with the existing container layout.</p>
<p>Rebuild command: <code>{REBUILD}</code>.
Report checks: <code>python -m pytest tests/docs/test_common_module_report.py -q -p no:cacheprovider</code>.
The check compares fresh and committed structure after masking numerical payloads, then compares the payloads at displayed precision.
The calculation digest is checked separately and gives the rebuild command on mismatch.</p>
</section>
<section id="symbols"><h2>10 Acronyms and Symbols</h2>
<p>Symbols are defined for the selected length transformation. No domain-specific shorthand is required to interpret the result.</p>
<p><code>x</code>: input numerical length in ft; <code>y</code>: output numerical length in m;
<code>a</code>: scale in m/ft; <code>b</code>: shift in m.
The symbol ft denotes the international foot; m denotes the metre.
A DataFrame is a labelled table, and a record is a row represented as a dictionary.</p>
</section>
<section id="appendix"><h2>Appendix A Supporting Data and Review</h2>
<p>Per-case arithmetic, data provenance and pre-flight evidence are collected here. The rounding range is descriptive and has no pass or fail classification.</p>
<h3>A.1 Calculation and data register</h3>
<table id="example-table"><thead><tr><th>Input (ft)</th><th>Arithmetic output (m)</th><th>Source</th></tr></thead><tbody>
{rows}
</tbody></table>
<p>Input values and their rounding interpretation: Reference 1, B.7.2.
Conversion scale: Reference 1, B.8. Shift: selected as zero for an origin-preserving length conversion under B.3.
Plot sampling is a display choice; it does not add measured data.</p>
<p>Physical acceptance limit: NOT_EVALUATED, because none is supplied.
Instrument calibration and measurement uncertainty: NOT_EVALUATED, because neither is part of the public example.
No assumed engineering value is required. Application-specific limits remain required inputs for a separate engineering assessment.</p>
<h3>A.2 Review comments and changes</h3>
<p>Comments are attached to a section and kept in this page until exported. Select “Save beside report” to choose the report folder
in browsers that support folder access. Other browsers download the comment file; place it beside the report.
Import that file to continue reviewing. No server or account is used.</p>
<label for="comment-section">Section</label><select id="comment-section"></select>
<label for="comment-text">Comment</label><textarea id="comment-text" class="u-full-width"></textarea>
<button id="add-comment" type="button">Add comment</button>
<button id="save-comments" type="button">Save beside report</button>
<label for="load-comments">Import saved comments</label><input id="load-comments" type="file" accept="application/json,.json">
<p id="comment-status" role="status"></p><ul id="comments"></ul>
<details><summary>Engineering changes</summary><ul id="changes"></ul></details>
<h3>A.3 Pre-flight evidence</h3>
<p>The report checks exercise the published conversion, hand arithmetic, mutation and missing-column behaviour,
record export, chart bounds, references, public wording and rebuild structure.
Test execution totals and tool versions are recorded with the accompanying change description.
The source inventory establishes test presence only.</p>
<p>Browser execution and visual inspection are not performed by these checks. Comment export uses a permission-controlled folder selector
with a download fallback. Numerical and document checks do not establish browser rendering or physical adequacy.</p>
</section>
<script id="example-data" type="application/json">{evidence}</script>
<script id="change-data" type="application/json">{change_data}</script>
<script id="calculation-record" type="application/json">{json.dumps(calculation_record(), sort_keys=True)}</script>
<script>{JAVASCRIPT}</script>
</main></body></html>
"""
    return document, changes


def calculation_record() -> dict:
    import hashlib

    path = "src/assetutilities/common/transform.py"
    # Normalize line endings so checkout policy does not alter the calculation identity.
    source = (ROOT / path).read_text(encoding="utf-8")
    return {
        "source": path,
        "digest": hashlib.sha256(source.encode("utf-8")).hexdigest(),
    }


JAVASCRIPT = r"""
"use strict";
const data = JSON.parse(document.getElementById("example-data").textContent);
const revisions = JSON.parse(document.getElementById("change-data").textContent);
const svg = document.getElementById("conversion-chart");
const control = document.getElementById("case-index");
let zoom = false, boundsVisible = true;
const download = (text, name, type) => {
  const url = URL.createObjectURL(new Blob([text], {type}));
  const link = document.createElement("a");
  link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
const svgNode = (name, attributes, text) => {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  svg.appendChild(node); return node;
};
function readout(index) {
  document.getElementById("chart-readout").textContent =
    `Length conversion; input ${data.chart_ft[index].toFixed(2)} ft; ` +
    `output ${data.chart_m[index].toFixed(4)} m; rounding bounds ` +
    `${data.list_m[0].toFixed(4)}–${data.list_m[2].toFixed(4)} m; acceptance limit not supplied.`;
}
function draw() {
  svg.replaceChildren();
  const first = zoom ? 5 : 0, last = zoom ? 15 : data.chart_ft.length - 1;
  const xmin = data.chart_ft[first], xmax = data.chart_ft[last];
  const ymin = data.chart_m[0], ymax = data.chart_m[data.chart_m.length - 1];
  const px = x => 100 + 580 * (x - xmin) / (xmax - xmin);
  const py = y => 290 - 240 * (y - ymin) / (ymax - ymin);
  svgNode("rect", {x: 0, y: 0, width: 800, height: 380, fill: "white"});
  svgNode("path", {d: "M100 40V300H690", stroke: "#333", fill: "none"});
  if (boundsVisible) {
    for (const value of [ymin, ymax]) {
      svgNode("path", {d: `M100 ${py(value)}H690`, stroke: "#555", "stroke-dasharray": "6 4"});
      svgNode("text", {x: 8, y: py(value) + 4, "font-size": 14}, value.toFixed(4));
    }
  }
  const points = data.chart_ft.slice(first, last + 1).map((x, i) => `${px(x)},${py(data.chart_m[first + i])}`);
  svgNode("polyline", {points: points.join(" "), fill: "none", stroke: "#1f77b4", "stroke-width": 2});
  for (let i = first; i <= last; i++) {
    const point = svgNode("circle", {cx: px(data.chart_ft[i]), cy: py(data.chart_m[i]), r: 5,
      fill: "#1f77b4", tabindex: 0, role: "img"});
    const label = `Length conversion; input ${data.chart_ft[i].toFixed(2)} ft; output ${data.chart_m[i].toFixed(4)} m; ` +
      `rounding bounds ${ymin.toFixed(4)}–${ymax.toFixed(4)} m; acceptance limit not supplied.`;
    point.setAttribute("aria-label", label);
    const title = document.createElementNS(svg.namespaceURI, "title"); title.textContent = label; point.appendChild(title);
    for (const event of ["mouseenter", "focus"]) point.addEventListener(event, () => {control.value = i; readout(i);});
  }
  svgNode("text", {x: 100, y: 325, "font-size": 14}, xmin.toFixed(2));
  svgNode("text", {x: 650, y: 325, "font-size": 14}, xmax.toFixed(2));
  svgNode("text", {x: 250, y: 365, "font-size": 16}, "Input length (international ft)");
  svgNode("text", {x: 100, y: 25, "font-size": 16}, "Converted length (m); dashed lines are rounding bounds");
  readout(Number(control.value));
}
control.addEventListener("input", () => readout(Number(control.value)));
document.getElementById("zoom-chart").addEventListener("click", () => {zoom = true; draw();});
document.getElementById("reset-chart").addEventListener("click", () => {zoom = false; draw();});
document.getElementById("toggle-bounds").addEventListener("click", event => {
  boundsVisible = !boundsVisible; event.target.setAttribute("aria-pressed", String(boundsVisible)); draw();
});
document.getElementById("export-chart").addEventListener("click", () => {
  const copy = svg.cloneNode(true); copy.setAttribute("xmlns", svg.namespaceURI);
  download(new XMLSerializer().serializeToString(copy), "length-conversion.svg", "image/svg+xml");
});
draw();
const sectionSelect = document.getElementById("comment-section");
const sectionNames = new Map();
for (const section of document.querySelectorAll("section[id]")) {
  const title = section.querySelector("h2").textContent;
  sectionNames.set(section.id, title);
  const option = document.createElement("option"); option.value = section.id; option.textContent = title;
  sectionSelect.appendChild(option);
}
let comments = [];
const status = text => {document.getElementById("comment-status").textContent = text;};
function showComments() {
  const list = document.getElementById("comments"); list.replaceChildren();
  for (const comment of comments) {
    const item = document.createElement("li");
    item.textContent = `${sectionNames.get(comment.section)}: ${comment.text}`; list.appendChild(item);
  }
}
document.getElementById("add-comment").addEventListener("click", () => {
  const input = document.getElementById("comment-text"), text = input.value.trim();
  if (!text) {status("Enter a comment before adding it."); return;}
  comments.push({section: sectionSelect.value, text}); input.value = ""; showComments();
  status("Comment added in memory. Save before closing this page.");
});
document.getElementById("save-comments").addEventListener("click", async () => {
  const text = JSON.stringify({revision: revisions[0].revision, comments}, null, 2) + "\n";
  try {
    if (window.showDirectoryPicker) {
      const folder = await window.showDirectoryPicker({mode: "readwrite"});
      const file = await folder.getFileHandle("common-module.comments.json", {create: true});
      const stream = await file.createWritable(); await stream.write(text); await stream.close();
      status("Comments saved in the selected folder.");
    } else {
      download(text, "common-module.comments.json", "application/json");
      status("Comments downloaded. Place the file beside the report.");
    }
  } catch (error) {status("Comments remain in memory. Save was cancelled or unavailable.");}
});
document.getElementById("load-comments").addEventListener("change", async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    const saved = JSON.parse(await file.text());
    if (saved.revision !== revisions[0].revision || !Array.isArray(saved.comments) ||
      saved.comments.some(item => !item || !sectionNames.has(item.section) || typeof item.text !== "string")) {
      throw new Error("Invalid comment file");
    }
    comments = saved.comments; showComments(); status("Saved comments imported; existing in-memory comments replaced.");
  } catch (error) {status("Comment file was not accepted; existing comments are unchanged.");}
});
for (const revision of revisions) {
  for (const change of revision.changes) {
    const item = document.createElement("li"); item.textContent = `Revision ${revision.revision}: ${change}`;
    document.getElementById("changes").appendChild(item);
  }
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    args = parser.parse_args()
    document, changes = build()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "index.html").write_text(
        document, encoding="utf-8", newline="\n"
    )
    (args.output_dir / "changes.json").write_text(
        changes, encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
