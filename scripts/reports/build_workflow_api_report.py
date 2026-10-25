"""Build a single-file workflow API module report from actual module calls.

Rebuild from the repository root:
    python scripts/reports/build_workflow_api_report.py

The execution environment needs the repository's engine dependencies. Outputs
and source fingerprints are deterministic; runtime timestamps and source-control
revision identifiers are deliberately excluded from the document evidence.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "docs/reports/modules/aworkflowapi"
REBUILD = "python scripts/reports/build_workflow_api_report.py"
sys.path.insert(0, str(ROOT / "src"))

from assetutilities.workflow_api import artifact, run_workflow  # noqa: E402

CHANGES = {
    "document": "Workflow API module analysis",
    "revision": "A",
    "date": "2026-10-22",
    "changes": [
        {
            "section": "3 to 7",
            "change": "The registered CSV workflow and stored-byte examples are calculated through the module.",
            "reason": "Execution evidence is separated from acceptance of engineering results.",
        },
        {
            "section": "8",
            "change": "Input-file identity, serialization differences and publication boundaries are identified.",
            "reason": "Repeat equality alone does not establish a durable calculation record.",
        },
    ],
}


def physical(data: bytes) -> dict:
    return artifact.physical_artifact(
        data, media_type="text/plain", native_format="text"
    )


def byte_curve() -> list[dict]:
    """Measure stored ASCII prefixes; there is no implied performance envelope."""
    data = b"abc"
    return [
        {"characters": count, "bytes": physical(data[:count])["size_bytes"]}
        for count in range(len(data) + 1)
    ]


def calculate() -> dict:
    envelope = run_workflow("data_exploration", verify_reproducible=True)
    if envelope.status != "ok" or envelope.warnings:
        # Runtime diagnostics can include local paths. They are not copied into
        # report artifacts or terminal output by this generator.
        raise RuntimeError("The registered example failed or emitted warnings.")
    if envelope.determinism["reproducible"] is not True:
        raise RuntimeError("The registered example did not return equal repeat hashes.")
    source_files = sorted((ROOT / "src/assetutilities/workflow_api").rglob("*.py"))
    source_files += [
        ROOT / "src/assetutilities/engine.py",
        ROOT / "src/assetutilities/modules/data_exploration/data_exploration.py",
    ]
    inventory = {}
    for path in sorted((ROOT / "tests/workflow_api").glob("test_*.py")):
        if path.name == "test_module_report.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        inventory[path.relative_to(ROOT).as_posix()] = sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return {
        "example": {
            "workflow": envelope.workflow_id,
            "status": envelope.status,
            "file_count": len(envelope.result["outputs"]),
            "outputs": [item["basename"] for item in envelope.result["outputs"]],
            "repeat_equal": envelope.determinism["reproducible"],
        },
        "anchors": {
            "ascii_bytes": physical(b"abc")["size_bytes"],
            "structured_bytes": artifact.structured_artifact({"a": 1})["size_bytes"],
            "two_member_bytes": artifact.structured_artifact({"b": 2, "a": 1})[
                "size_bytes"
            ],
        },
        "curve": byte_curve(),
        "test_inventory": inventory,
        "source_digests": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in source_files
        },
    }


def display_values(data: dict) -> dict:
    return {
        "file_count": data["example"]["file_count"],
        **data["anchors"],
        "test_definitions": sum(data["test_inventory"].values()),
        "test_files": len(data["test_inventory"]),
    }


def number(key: str, values: dict) -> str:
    return f'<span data-number="{key}">{values[key]}</span>'


def render(data: dict) -> str:
    values = display_values(data)
    replacements = {
        "STYLE": (DESTINATION / "house-style.css").read_text(encoding="utf-8"),
        "DATA": json.dumps(data, ensure_ascii=False, sort_keys=True),
        "CHANGES": json.dumps(CHANGES, ensure_ascii=False, sort_keys=True),
        "OUTPUTS": ", ".join(
            f"<code>{escape(name)}</code>" for name in data["example"]["outputs"]
        ),
        "INVENTORY": "\n".join(
            f"<tr><td><code>{escape(path)}</code></td><td>{count}</td>"
            "<td>Source definition count; parameter expansions are excluded.</td></tr>"
            for path, count in data["test_inventory"].items()
        ),
        "DIGESTS": "\n".join(
            f"<tr><td><code>{escape(path)}</code></td><td><code>{digest}</code></td></tr>"
            for path, digest in data["source_digests"].items()
        ),
    }
    replacements.update({key.upper(): number(key, values) for key in values})
    return Template(PAGE).substitute(replacements)


PAGE = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Workflow API module analysis</title>
<style>$STYLE</style>
<style>
pre,td code{white-space:pre-wrap;overflow-wrap:anywhere} pre{padding:12px;background:var(--bg)}
svg{width:100%;height:auto} svg text{font:14px sans-serif;fill:var(--ink)}
button,input,select,textarea{font:inherit} button{cursor:pointer;padding:5px 10px}
textarea{display:block;width:100%;min-height:90px} .review{border:1px solid var(--line);padding:14px}
.chart-point{fill:var(--brand);cursor:pointer} .chart-point:focus{stroke:var(--accent);stroke-width:4}
.diagram{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.diagram span{border:1px solid var(--line);background:var(--bg);padding:12px}
</style></head>
<body class="hs-doc"><main class="wrap">
<header><div class="kicker">Engineering software · module analysis</div>
<h1>Workflow API module analysis</h1>
<p class="sub">Draft for maintainer review</p>
<p>Revision A · 22 October 2026</p></header>

<section id="summary"><h2>1 Executive summary</h2>
<p>The workflow application programming interface is an in-process execution and evidence interface.
Analysis is performed to determine how a registered calculation is called and which evidence is returned;
key results are summarized below.</p>
<ul><li>Run the public CSV example through the typed interface.
<ul><li>The registered example returns $FILE_COUNT output files and equal output hashes on repetition.
This equality is limited to the executed example and its current environment.</li></ul></li>
<li>Inspect returned status and warnings before consuming output metadata.
<ul><li>Content hashing is distinguished from engineering acceptance. No physical acceptance limit is supplied by this interface.</li></ul></li>
<li>Select explicit records when durable identity or publication is required.
<ul><li>The envelope alone does not freeze input-file bytes or enforce a clean source revision.</li></ul></li></ul>
<h3>Revision history</h3>
<table><thead><tr><th>Revision</th><th>Date</th><th>Change and cause</th></tr></thead>
<tbody><tr><td>A</td><td>22 October 2026</td><td>The callable workflow and evidence boundaries are documented to support integration decisions.</td></tr></tbody></table>
</section>

<section id="purpose"><h2>2 Purpose and system boundary</h2>
<p>A workflow configuration is dispatched through the existing calculation engine.
A result envelope is returned so that calling software is separated from command-line execution.</p>
<p>The main path is <code>run_workflow</code>. Registry resolution, configuration merging,
temporary output discovery and hashing are provided by that path. Identity, input admission,
artifact, output, metric and publication contracts are supplied as additional interfaces;
they are not automatically applied by the runner. <a href="#source-runner">[4]</a></p>
<figure><div class="diagram" role="img" aria-label="Configuration enters the registry resolver and engine. Temporary files are inspected, hashed and removed. A result envelope returns file metadata to the caller.">
<span>Caller configuration</span> → <span>Registry and engine</span> →
<span>Temporary files → metadata</span> → <span>Result envelope</span></div>
<figcaption>Software data flow. The temporary directory is removed by the runner; the returned file list is metadata, rather than a persistent download location.</figcaption></figure>
<p>A physical geometry, mesh or structural boundary condition is not represented by this interface.
Such inputs belong to the selected calculation and are outside this software diagram.</p>
</section>

<section id="basis"><h2>3 Basis and theory</h2>
<p>Stored-byte identity is formed by hashing the bytes supplied to the artifact interface.
The hash algorithm is specified externally; the composition of workflow records is specified by the implementation.</p>
<h3>Stored bytes and canonical serialization</h3>
<p class="eq"><var>d</var> = SHA-256(<var>B</var>)</p>
<p><var>B</var> denotes the stored byte sequence and <var>d</var> its content digest.
SHA-256 is specified by FIPS 180-4, August 2015, sections 5.1.1 and 6.2.
Compression is descriptive metadata and is not decoded before hashing by the artifact interface.
Hash equality is evidence of byte agreement under that digest, rather than a mathematical proof that collisions are impossible.
<a href="#ref-fips">[1]</a> <a href="#source-artifact">[4]</a></p>
<p>For the small integer objects used here, compact JSON punctuation and ordered keys are used.
Whitespace, key sorting and UTF-8 generation are described in RFC 8785, June 2020,
sections 3.2.1, 3.2.3 and 3.2.4. UTF-8 encoding for ASCII characters is specified in
RFC 3629, November 2003, section 3. <a href="#ref-jcs">[2]</a> <a href="#ref-utf8">[3]</a></p>
<p>The identity serializer differs from RFC 8785 for general data: Unicode normalization is applied,
and decimal values are rendered without the RFC's required number conversion rules.
RFC conformance is therefore not claimed. The ASCII integer examples do not exercise these differences.
<a href="#ref-jcs">[2]</a> <a href="#source-identity">[4]</a></p>
<h3>Runner evidence and acceptance criteria</h3>
<p>Runner input hashing serializes configuration after removing volatile top-level settings.
Runner result hashing serializes the sorted output-name and file-digest pairs.
These operations use the envelope serializer, separately from the identity serializer.
Repeat equality means the result hashes from separate executions compare equal.
The documented example is accepted here only when its status is <code>ok</code>, warnings are absent,
and the opt-in repeat check returns true. These are software criteria, with no engineering capacity interpretation.
<a href="#source-envelope">[4]</a> <a href="#source-runner">[4]</a></p>
</section>

<section id="interface"><h2>4 Inputs and outputs</h2>
<p>A registered workflow identifier or a complete configuration dictionary is supplied by the caller.
The returned envelope is inspected before downstream use.</p>
<h3>Caller inputs</h3>
<p><code>workflow_id</code> selects a registry entry. <code>params</code> recursively overrides its loaded example
configuration. <code>cfg</code> supplies a full configuration and takes precedence over registry example loading;
in that branch, <code>params</code> is not merged. The workflow identifier still labels the envelope.
<code>verify_reproducible</code> defaults to false; setting it to true requests a fresh repeat execution.
Relative CSV paths in the documented example are resolved from the repository root.
<a href="#source-runner">[4]</a></p>
<h3>Envelope outputs</h3>
<p><code>status</code> is <code>ok</code> or <code>error</code>. A successful file result contains
basenames, byte sizes and content digests. Provenance contains a best-effort code version,
configuration hash, time and standards list; the runner does not populate engineering standards.
Determinism contains the result hash and a repeat flag that is null unless requested.
Confidence remains null. Warnings contain discovery discrepancies or caught error text.
Unknown identifiers and caught exceptions return error envelopes. <a href="#source-envelope">[4]</a></p>
<p>Only direct files in the resolved result directory are discovered. The saved configuration dump is excluded.
Registry output names are documentary: their count is cross-checked when declared, but the actual filenames are used.
An empty file list can accompany an <code>ok</code> status and a warning; status alone is insufficient.
<a href="#source-runner">[4]</a></p>
</section>

<section id="worked"><h2>5 Worked public workflow example</h2>
<p>The registered descriptive-statistics example is executed by calling the module.
Its repository sample CSV groups are processed without a physical design interpretation.</p>
<pre><code>from assetutilities.workflow_api import run_workflow

result = run_workflow("data_exploration", verify_reproducible=True)
assert result.status == "ok"
assert not result.warnings
assert result.determinism["reproducible"] is True
print(len(result.result["outputs"]))</code></pre>
<p>The module returns $FILE_COUNT output files. Each declared input group generates its own statistics file;
the saved configuration dump is omitted by the locator. The repeat flag is true because the separate
executions return equal content-based result hashes. Output locations and basenames are recorded in section 9.2.
<a href="#source-example">[4]</a></p>
<p>Numeric statistics are not carried in the envelope: the returned payload lists output metadata.
Access to the generated CSV values requires an output capture or persistence mechanism before temporary cleanup.
No coefficient from the sample CSV files is interpreted as a physical performance limit.</p>
</section>

<section id="bytes"><h2>6 Stored-byte worked anchors</h2>
<p>Small byte sequences and structured objects are passed to the artifact constructors.
The returned byte counts are checked against hand-counted punctuation and ASCII characters.</p>
<p>The stored ASCII sequence <code>abc</code> returns $ASCII_BYTES bytes.
The object <code>{"a":1}</code> returns $STRUCTURED_BYTES bytes.
The object supplied as <code>{"b":2,"a":1}</code> is stored as
<code>{"a":1,"b":2}</code> and returns $TWO_MEMBER_BYTES bytes.
These byte counts are module outputs; their hand calculations are supplied with the report tests.
<a href="#ref-jcs">[2]</a> <a href="#ref-utf8">[3]</a> <a href="#source-artifact">[4]</a></p>
<figure><svg id="byte-chart" viewBox="0 0 640 260" role="img" aria-label="Stored bytes against ASCII prefix length. Points are selectable by keyboard or pointer."></svg>
<figcaption>Stored byte length against ASCII prefix length. Select a point for its case, component,
demand, limit status and units. No maximum artifact size is enforced by this constructor;
an operational size limit is NOT_EVALUATED. This chart is not a throughput benchmark.</figcaption></figure>
<p id="chart-detail" aria-live="polite">Select a chart point to inspect its measured byte count.</p>
<noscript><p>Interactive inspection requires JavaScript. The worked byte counts are stated in the preceding paragraph.</p></noscript>
</section>

<section id="evidence"><h2>7 Validation evidence</h2>
<p>Existing tests are mapped to their software contracts.
The map is a source inventory, rather than a statement of engineering accuracy or an executed test count.</p>
<p>The existing suite contains $TEST_DEFINITIONS test definitions in $TEST_FILES files,
counted from source before parameter expansion. Envelope round-tripping, hash sensitivity,
registry merging, real engine execution, temporary-output isolation and opt-in repeat equality are exercised.
Artifact tests cover byte integrity and storage-location binding. Identity and input tests cover explicit
record membership and rejection of inadmissible inputs. <a href="#source-tests">[5]</a></p>
<p>Output and metric tests cover publication-surface restrictions, definitions and population eligibility.
Publication tests use an in-memory port and a mocked external adapter. Those tests do not demonstrate
live service access, credential configuration or successful external publication. No timing benchmark
or field measurement is included in the cited workflow example. <a href="#source-tests">[5]</a></p>
<p>The report checks add literal hand-count anchors and consistency checks against fresh module calls.
Counts are exact integers; floating point tolerances are unnecessary for the reported measurements.
Only stable counts and names are embedded for the CSV example, so environment-sensitive CSV formatting
and runtime timestamps are not presented as portable byte digests. <a href="#source-rebuild">[5]</a></p>
</section>

<section id="limits"><h2>8 Findings, limits and recommendations</h2>
<p>Execution repeatability is demonstrated for the included example by the returned repeat flag.
Durable input identity and physical acceptance remain separate responsibilities.</p>
<h3>Limits of use</h3>
<p>The runner configuration hash includes CSV path strings, rather than the referenced file bytes.
Volatile top-level configuration settings are removed from that hash, even though changing a default setting
can change execution. Provenance does not establish a clean source revision or an environment pin.
Relative example paths require the repository context. The embedded engine path redirects ordinary outputs,
but it is not a security sandbox for arbitrary configurations or plugins. <a href="#source-runner">[4]</a></p>
<p>The separate identity gate accepts caller-supplied cleanliness and revision evidence; it does not inspect
the working tree itself. Its serializer is not general RFC 8785 conformance evidence.
The architecture contract referred to by module docstrings is absent from the current checkout;
implementation and tests are the available local contract evidence. <a href="#source-identity">[4]</a></p>
<h3>Recommendations</h3>
<p>Inspect status, warnings and expected outputs together, and request the repeat check for calculations that need
repeat evidence. Materialize referenced input bytes and record explicit schema and environment evidence before
using the separate identity and publication contracts. Capture output bytes before cleanup when persistent results
are required. Test non-ASCII and decimal interoperability before exchanging canonical records with other implementations.
These actions address the implementation boundaries described above. <a href="#source-runner">[4]</a>
<a href="#source-identity">[4]</a> <a href="#ref-jcs">[2]</a></p>
<p>Supply the selected engineering method, input units, acceptance criteria and method-specific validation
before treating a successful software status as acceptance of a physical design. No safety factor,
capacity threshold or operating envelope is supplied or inferred by this report.</p>
<h3>Not covered</h3>
<p>Live publication, promotion recovery, metric population design, external credentials and the other registered
engine routes are inventoried through tests but are not worked examples here. No external publication is performed.</p>
</section>

<section id="references"><h2>9 References and source register</h2>
<p>Public standards and repository records are identified for the claims made above.
Source locations and calculation fingerprints are collected here.</p>
<h3>9.1 Public documents</h3>
<ol class="refs"><li id="ref-fips"><a href="https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf">FIPS 180-4, Secure Hash Standard, August 2015</a>,
sections 5.1.1 and 6.2. Open copy read on 22 October 2026; HTTP status 200. Used for the stored-byte hash algorithm.</li>
<li id="ref-jcs"><a href="https://www.rfc-editor.org/rfc/rfc8785">RFC 8785, JSON Canonicalization Scheme, June 2020</a>,
sections 3.1 and 3.2.1 to 3.2.4. Open copy read on 22 October 2026; HTTP status 200.
Used for compact JSON, sorting, encoding and the stated interoperability differences.</li>
<li id="ref-utf8"><a href="https://www.rfc-editor.org/rfc/rfc3629">RFC 3629, UTF-8, November 2003</a>,
section 3, encoding table. Open copy read on 22 October 2026; HTTP status 200. Used for ASCII byte counting.</li></ol>
<h3>9.2 Repository evidence and locations</h3>
<table><thead><tr><th>Record</th><th>Location</th><th>Use</th></tr></thead><tbody>
<tr id="source-runner"><td>[4] Public interface and runner</td><td><code>src/assetutilities/workflow_api/__init__.py</code><br><code>src/assetutilities/workflow_api/runner.py</code></td><td>Entry point, overrides, temporary cleanup and output discovery.</td></tr>
<tr id="source-envelope"><td>[4] Envelope</td><td><code>src/assetutilities/workflow_api/envelope.py</code></td><td>Input and result hashes; provenance and repeat semantics.</td></tr>
<tr id="source-artifact"><td>[4] Artifacts</td><td><code>src/assetutilities/workflow_api/artifact.py</code></td><td>Physical and structured byte counts, integrity and storage binding.</td></tr>
<tr id="source-identity"><td>[4] Identity and related contracts</td><td><code>src/assetutilities/workflow_api/identity.py</code><br><code>src/assetutilities/workflow_api/inputs.py</code><br><code>src/assetutilities/workflow_api/output_contract.py</code><br><code>src/assetutilities/workflow_api/metrics.py</code><br><code>src/assetutilities/workflow_api/publication/</code></td><td>Separate admission, identity, metric and publication requirements.</td></tr>
<tr id="source-example"><td>[4] Public example</td><td><a href="../../../../examples/workflows/data_exploration/input.yml">examples/workflows/data_exploration/input.yml</a><br><code>docs/registry/workflows.yaml</code></td><td>Documented sample CSV groups and registry entry.</td></tr>
<tr><td>[4] Returned basenames</td><td>$OUTPUTS</td><td>Computed file list; persistent locations are not returned.</td></tr>
<tr id="source-tests"><td>[5] Existing tests</td><td><code>tests/workflow_api/</code></td><td>Source inventory follows; pass counts are supplied separately with check results.</td></tr>
<tr id="source-rebuild"><td>[5] Report checks and rebuild</td><td><code>tests/workflow_api/test_module_report.py</code><br><code>python scripts/reports/build_workflow_api_report.py</code></td><td>Hand anchors, module consistency, rebuild comparison and visible-text checks.</td></tr>
<tr><td>House-style exemplar</td><td>Companion calculation documentation: <code>docs/api/cfd/turbulent-flat-plate-verification.html</code> and <code>docs/api/_assets/brand.css</code></td><td>The established palette and layout are copied and inlined. No matching house-style page exists in this repository at the report basis. The body uses <code>hs-doc</code>.</td></tr>
</tbody></table>
<details><summary>Existing test definitions by source file</summary>
<table><thead><tr><th>File</th><th>Definitions</th><th>Source</th></tr></thead><tbody>$INVENTORY</tbody></table></details>
<details><summary>Calculation source fingerprints</summary><p>The digests cover module and calculation source files,
rather than test files or document formatting. A changed fingerprint requires rebuilding the report.</p>
<table><thead><tr><th>Calculation source</th><th>SHA-256</th></tr></thead><tbody>$DIGESTS</tbody></table></details>
</section>

<section id="appendix"><h2>10 Appendix: data register and review</h2>
<p>Unspecified application requirements are recorded separately from the worked software inputs.
Comments are attached to report sections and saved as a companion file.</p>
<h3>Data register and quality checks</h3>
<table><thead><tr><th>Item</th><th>Basis or state</th><th>Effect</th><th>Source</th></tr></thead><tbody>
<tr><td>Registered workflow</td><td>Public repository example</td><td>File count is calculated by the runner.</td><td>Section 9.2, public example.</td></tr>
<tr><td>Byte inputs</td><td>Explicit ASCII and integer-object inputs</td><td>Counts are exact and hand-checkable.</td><td>Section 6 and reference [3].</td></tr>
<tr><td>Physical units and design acceptance</td><td>NOT_EVALUATED; required from the selected calculation</td><td>No physical operating limit is inferred.</td><td>Section 8.</td></tr>
<tr><td>Operational size and performance limit</td><td>NOT_EVALUATED; required from the consuming application</td><td>No throughput or memory-capacity claim is made.</td><td>Section 6.</td></tr>
<tr><td>Application suitability</td><td>ASSUMED - to be confirmed: the registered example represents the intended integration pattern.</td><td>Application-specific coverage is required before use beyond this example.</td><td>Sections 5 and 8.</td></tr>
</tbody></table>
<p>Quality checks cover hand-counted anchors, fresh module consistency, report rebuild equality, internal reference
targets, source inventory, UTF-8 encoding and LF line endings. The page contains its styles and interactive code;
no remote chart library is loaded. Full application testing and external-service testing are outside the report checks.</p>
<details id="change-panel"><summary>Engineering changes</summary><div id="change-content"></div></details>
<h3>Section comments</h3>
<div class="review"><label for="comment-section">Section</label><select id="comment-section"></select>
<label for="comment-text">Comment text</label><textarea id="comment-text"></textarea>
<p><button id="comment-add" type="button">Add comment</button>
<button id="comment-save" type="button">Save comments beside report</button>
<button id="comment-download" type="button">Download comments</button></p>
<label for="comment-load">Load saved comments</label><input id="comment-load" type="file" accept="application/json">
<p id="comment-status" aria-live="polite">Comments remain in this page until saved. Select the report folder when saving;
otherwise download the companion comments file and place it beside this HTML.</p>
<ol id="comment-list"></ol></div>
</section>
<footer>Workflow API module analysis · Draft for maintainer review</footer>
</main>
<script id="report-data" type="application/json">$DATA</script>
<script id="change-data" type="application/json">$CHANGES</script>
<script>
"use strict";
const data = JSON.parse(document.getElementById("report-data").textContent);
const changeData = JSON.parse(document.getElementById("change-data").textContent);
const chart = document.getElementById("byte-chart");
const ns = "http://www.w3.org/2000/svg";
function svgElement(tag, attrs, text) {
  const element = document.createElementNS(ns, tag);
  for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, value);
  if (text !== undefined) element.textContent = text;
  chart.appendChild(element);
  return element;
}
svgElement("path", {d:"M70 25V210H600", fill:"none", stroke:"currentColor"});
svgElement("text", {x:260,y:250}, "Input prefix (characters)");
svgElement("text", {x:10,y:18}, "Stored bytes");
const extent = Math.max(...data.curve.map(point => point.characters));
for (const point of data.curve) {
  const x = 70 + point.characters / extent * 500;
  const y = 210 - point.bytes / extent * 170;
  svgElement("text", {x:x-4,y:232}, String(point.characters));
  svgElement("text", {x:43,y:y+5}, String(point.bytes));
  const detail = "Case: ASCII prefix " + point.characters + "; component: stored artifact; demand: " +
    point.bytes + " bytes; limit: NOT_EVALUATED; units: bytes.";
  const dot = svgElement("circle", {cx:x,cy:y,r:7,tabindex:0,role:"button",class:"chart-point","aria-label":detail});
  const title = document.createElementNS(ns, "title"); title.textContent = detail; dot.appendChild(title);
  const inspect = () => {document.getElementById("chart-detail").textContent = detail;};
  dot.addEventListener("focus", inspect); dot.addEventListener("mouseenter", inspect);
  dot.addEventListener("click", inspect);
  dot.addEventListener("keydown", event => {if (["Enter", " "].includes(event.key)) {event.preventDefault(); inspect();}});
}
for (const entry of changeData.changes) {
  const p = document.createElement("p");
  p.textContent = "Sections " + entry.section + ": " + entry.change + " " + entry.reason;
  document.getElementById("change-content").appendChild(p);
}
const sections = Array.from(document.querySelectorAll("main > section"));
const selector = document.getElementById("comment-section");
for (const section of sections) {
  const option = document.createElement("option"); option.value = section.id;
  option.textContent = section.querySelector("h2").textContent; selector.appendChild(option);
}
let comments = [];
function status(text) {document.getElementById("comment-status").textContent = text;}
function refreshComments() {
  const list = document.getElementById("comment-list"); list.replaceChildren();
  for (const entry of comments) {
    const item = document.createElement("li"); item.textContent = entry.section + ": " + entry.text; list.appendChild(item);
  }
}
function commentsText() {
  return JSON.stringify({document:changeData.document,revision:changeData.revision,comments:comments}, null, 2) + "\n";
}
document.getElementById("comment-add").addEventListener("click", () => {
  const input = document.getElementById("comment-text"); const text = input.value.trim();
  if (!text) {status("Enter a comment before adding it."); return;}
  comments.push({section:selector.value,text:text}); input.value = ""; refreshComments();
  status("Comment added. Save the companion file to preserve it.");
});
document.getElementById("comment-save").addEventListener("click", async () => {
  if (!window.showDirectoryPicker) {status("Folder saving is unavailable. Download comments and place the file beside this HTML."); return;}
  try {
    const directory = await window.showDirectoryPicker({mode:"readwrite"});
    const file = await directory.getFileHandle("comments.json", {create:true});
    const writable = await file.createWritable(); await writable.write(commentsText()); await writable.close();
    status("Comments saved in the selected report folder.");
  } catch (error) {status("Comments were not saved. Select a writable report folder or use Download comments.");}
});
document.getElementById("comment-download").addEventListener("click", () => {
  const url = URL.createObjectURL(new Blob([commentsText()], {type:"application/json;charset=utf-8"}));
  const link = document.createElement("a"); link.href = url; link.download = "comments.json"; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000); status("Place the downloaded comments file beside this HTML.");
});
document.getElementById("comment-load").addEventListener("change", async event => {
  const file = event.target.files[0]; if (!file) return;
  try {
    const saved = JSON.parse(await file.text());
    const valid = saved.document === changeData.document && saved.revision === changeData.revision &&
      Array.isArray(saved.comments) && saved.comments.every(entry => entry && typeof entry.text === "string" &&
        sections.some(section => section.id === entry.section));
    if (!valid) throw new Error("Invalid comment document");
    comments = saved.comments; refreshComments(); status("Saved comments loaded.");
  } catch (error) {status("The selected file is not a comment file for this report revision.");}
});
</script></body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    args = parser.parse_args()
    data = calculate()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "index.html").open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        output.write(render(data))
    with (args.output_dir / "changes.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        output.write(json.dumps(CHANGES, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
