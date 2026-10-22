"""Build the devtools report from public API calls on disposable input copies.

Usage: python scripts/reporting/generate_devtools_report.py --work-dir <scratch>
Only the final HTML and change-panel JSON are written to the report directory.
Calculation inputs and generated configuration stay in the supplied directory.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import tomllib
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from assetutilities.devtools import DependencyModernizer  # noqa: E402

REPORT_DIR = ROOT / "docs/reports/modules/adevtools"
SOURCE = ROOT / "src/assetutilities/devtools/modernize_deps.py"
INPUTS = (
    {
        "name": "Documented discovery example",
        "files": {
            "requirements.txt": "requests==2.28.0\n",
            "requirements-dev.txt": "pytest\n",
        },
    },
    {
        "name": "Duplicate and group overlap example",
        "files": {
            "requirements.txt": "requests==2.28.0\nrequests==2.28.0\npytest\n",
            "requirements-dev.txt": "pytest\n",
        },
    },
)
METRICS = (
    "files_processed",
    "runtime_count",
    "dev_count",
    "dependencies_found",
    "distinct_count",
)
LABELS = (
    "Files processed",
    "Runtime requirement strings",
    "Development requirement strings",
    "Reported requirement count",
    "Distinct strings across groups",
)
CHANGES = {
    "revision": "A",
    "date": "2026-10-21",
    "changes": [
        {
            "section": "Dependency collection",
            "description": "Initial analysis distinguishes grouped requirement counts from distinct strings and package resolution.",
        },
        {
            "section": "Limits and recommendations",
            "description": "File-presence checks are separated from installation acceptance; controlled-copy use is specified.",
        },
    ],
}


def compute_case(work_dir: Path, case: dict) -> dict:
    """Call the documented class; leave all input and output copies in scratch."""
    work_dir.mkdir(parents=True, exist_ok=True)
    for name, content in case["files"].items():
        (work_dir / name).write_text(content, encoding="utf-8", newline="\n")
    modernizer = DependencyModernizer(work_dir, backup=False)
    modernizer.collect_all_dependencies()
    modernizer.create_pyproject_toml()
    configuration = tomllib.loads(
        (work_dir / "pyproject.toml").read_text(encoding="utf-8")
    )
    return {
        "name": case["name"],
        "files_processed": modernizer.report["files_processed"],
        "runtime_count": len(modernizer.dependencies),
        "dev_count": len(modernizer.dev_dependencies),
        "dependencies_found": modernizer.report["dependencies_found"],
        "distinct_count": len(modernizer.dependencies | modernizer.dev_dependencies),
        "runtime": sorted(modernizer.dependencies),
        "development": sorted(modernizer.dev_dependencies),
        "generated_runtime": configuration["project"]["dependencies"],
        "generated_development": configuration["project"]["optional-dependencies"][
            "dev"
        ],
        "files_created": modernizer.report["files_created"],
        "errors": modernizer.report["errors"],
    }


def build(work_dir: Path) -> dict:
    """Return the single-file report and the matching change panel."""
    cases = [
        compute_case(work_dir / f"case-{i}", case) for i, case in enumerate(INPUTS)
    ]
    tests = ast.parse(
        (ROOT / "tests/modules/devtools/test_devtools_coverage.py").read_text(
            encoding="utf-8"
        )
    )
    test_count = sum(
        isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        for node in ast.walk(tests)
    )
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    # Reuse the existing documentation stylesheet, omitting its attribution header.
    css = (
        "/* Grid"
        + (ROOT / "docs/sub_utilities/assets/style.css")
        .read_text(encoding="utf-8")
        .split("/* Grid", 1)[1]
    )
    inputs_html = "\n".join(
        f'<details open><summary>{escape(case["name"])}</summary>'
        + "".join(
            f"<p>{escape(name)}</p><pre>{escape(content)}</pre>"
            for name, content in case["files"].items()
        )
        + "</details>"
        for case in INPUTS
    )
    rows = "\n".join(
        f'<tr><td>{escape(case["name"])}</td><td>{label}</td>'
        f'<td data-result="{i}-{key}" data-value="{case[key]}">{case[key]}</td>'
        '<td>Computed example; Ref A and Ref C</td></tr>'
        for i, case in enumerate(cases)
        for key, label in zip(METRICS, LABELS)
    )
    outputs = "\n".join(
        f'<p>{escape(case["name"])}: runtime output '
        f'<code>{escape(json.dumps(case["generated_runtime"]))}</code>; '
        f'development output <code>{escape(json.dumps(case["generated_development"]))}</code>.</p>'
        for case in cases
    )
    changes_json = json.dumps(CHANGES, ensure_ascii=False, indent=2)
    cases_json = json.dumps(cases, ensure_ascii=False, sort_keys=True)
    html = Template("""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Devtools dependency collection analysis</title>
<style>$css</style></head>
<body class="hs-doc"><main class="container">
<header><h1>Devtools dependency collection analysis</h1>
<p>Draft for maintainer review</p><p>Revision A · 2026-10-21</p></header>
<nav aria-label="Contents"><p>
<a href="#summary">Executive summary</a> · <a href="#introduction">Introduction</a> ·
<a href="#basis">Basis</a> · <a href="#method">Methodology</a> ·
<a href="#interface">Inputs and outputs</a> · <a href="#example">Worked example</a> ·
<a href="#validation">Validation</a> · <a href="#recommendations">Recommendations</a> ·
<a href="#references">References</a> · <a href="#appendix">Appendix</a></p></nav>
<section id="summary" data-report-section="1"><h2>1. Executive summary</h2>
<p>Devtools is a repository maintenance module. Analysis is performed to determine how requirement files are collected and written as dependency configuration; key results are summarized below.</p>
<ul><li>Dependency collection is demonstrated on controlled input copies.
<ul><li>For the overlap example, <span data-result="headline-total" data-value="$reported">$reported</span> grouped requirement entries are reported from <span data-result="headline-distinct" data-value="$distinct">$distinct</span> distinct strings; overlap between groups is counted in both groups.</li>
<li>Use the output as a configuration draft requiring review, rather than as evidence of a working installation.</li></ul></li>
<li>Operational acceptance is bounded by file-presence checks.
<ul><li>No package resolution, installation test or throughput limit is established by the computed examples.</li>
<li>Review the configuration and retain input copies before any cleanup is enabled.</li></ul></li></ul>
<h3>Revision history</h3><table><thead><tr><th>Revision</th><th>Date</th><th>Change and reason</th></tr></thead>
<tbody><tr><td>A</td><td>2026-10-21</td><td>Initial dependency collection analysis to explain the count basis and acceptance boundary.</td></tr></tbody></table>
</section>
<section id="introduction" data-report-section="2"><h2>2. Introduction</h2>
<p>Repository maintenance is provided through dependency modernization, command propagation and structure organization. The dependency collection and configuration-generation subworkflow is evaluated here using the documented public class.</p>
<p>Requirements discovery, parsing, set accumulation and configuration output are covered in full for plain requirement lines. The complete modernization wrapper also creates configuration and setup files, replaces the root requirements file and removes other requirement files; that wrapper is outside the computed example because input preservation is required.</p>
<h3>Not covered</h3><p>Command distribution, generated command execution, structural file moves, concurrency, generated setup-script execution and real package installation are not evaluated. The existing documentation describes these facilities; it does not supply measured performance or installation benchmark results.</p>
</section>
<section id="basis" data-report-section="3"><h2>3. Basis and acceptance criteria</h2>
<p>The count basis is taken from finite-set cardinality and the implementation's distinction between dependency groups. Acceptance of the demonstrated subworkflow is assessed by exact integer counts and equality between the collected strings and parsed configuration output.</p>
<p>A requirement string is treated as a set member. This is a string-level model: different version constraints for the same distribution remain different members, and dependency compatibility is not solved. The public dependency grammar defines names, version constraints, direct references and environment markers; the implementation is a line filter rather than a complete grammar parser. See <a href="#ref-c">Ref C</a>.</p>
<p>No engineering operating limit or empirical performance limit is defined for these counts. An absent limit is recorded as NOT_EVALUATED; a count is not used as an acceptance threshold.</p>
</section>
<section id="method" data-report-section="4"><h2>4. Methodology and theory</h2>
<p>Matched input files are deduplicated by path and parsed into runtime and development sets. Empty lines, comment lines and lines beginning with a hyphen are ignored; trailing hash comments are removed, and development classification is based on the filename containing “dev” or “test”.</p>
<p>Let F be the set of matched file paths, Rᵢ the runtime strings read from file i, and Dᵢ the development strings read from file i. The accumulated sets are R = ⋃ Rᵢ and D = ⋃ Dᵢ. The file count is |F|, where vertical bars denote cardinality. Set union and cardinality follow <a href="#ref-b">Ref B</a>, third edition, section 0.3, “Sets”.</p>
<p>The implementation's reported count is N = |R| + |D|. A distinct-string count is U = |R ∪ D|. Set membership and union follow <a href="#ref-b">Ref B</a>; addition of the group sizes is the implementation's reporting convention, not a package-resolution equation. R, D, F, N and U have no physical units; displayed count units are files or requirement strings.</p>
<figure><svg viewBox="0 0 900 150" role="img" aria-labelledby="flow-title flow-description" width="100%">
<title id="flow-title">Dependency collection data flow</title>
<desc id="flow-description">Controlled requirements copies enter the parser, runtime and development string sets are accumulated, and configuration is generated. Package resolution and installation lie outside the boundary.</desc>
<rect x="10" y="20" width="230" height="80" fill="none" stroke="currentColor"/>
<text x="20" y="50">Requirements input copies</text><text x="20" y="80">Plain lines and filenames</text>
<path d="M240 60 H300 M290 50 L300 60 L290 70" fill="none" stroke="currentColor"/>
<rect x="300" y="20" width="270" height="80" fill="none" stroke="currentColor"/>
<text x="310" y="50">Parser → runtime and dev sets</text><text x="310" y="80">No dependency solver</text>
<path d="M570 60 H630 M620 50 L630 60 L620 70" fill="none" stroke="currentColor"/>
<rect x="630" y="20" width="250" height="80" fill="none" stroke="currentColor"/>
<text x="640" y="50">Configuration draft</text><text x="640" y="80">Review before installation</text>
<text x="10" y="135">Boundary: local file processing; no physical system or solver model applies.</text></svg>
<figcaption>Figure A. Software data flow and evaluation boundary.</figcaption></figure>
</section>
<section id="interface" data-report-section="5"><h2>5. Inputs and outputs</h2>
<p>A repository-directory path and a backup flag are accepted by the public DependencyModernizer class. Requirement discovery and collection are called explicitly, followed by configuration generation on the controlled directory.</p>
<p>The collection methods return through object state: runtime and development string sets are accumulated, and a report dictionary records files processed, dependencies found, files created, files removed and errors. Configuration generation writes project metadata and sorted dependencies. Existing metadata is read only when the optional configuration parser is importable; unsupported existing fields are not generally preserved.</p>
<p>The worked calls disable backup because original input strings are supplied separately and remain intact. The complete modernization wrapper defaults to backups, but its backup list is narrower than its recursive cleanup search. A complete external input copy is required before cleanup is accepted.</p>
</section>
<section id="example" data-report-section="6"><h2>6. Worked example</h2>
<p>The public requirements-discovery example is evaluated by calling DependencyModernizer, collect_all_dependencies and create_pyproject_toml. An explicit extension introduces a duplicate runtime line and a requirement appearing in both groups to expose the count semantics.</p>
<p>The first input reproduces the requirement strings documented in the existing discovery test, including the exact requests version. The second is an illustrative extension, not a package-selection recommendation. Ref A identifies the input record.</p>
$inputs_html
<p>The generated project configuration is parsed as data. Its dependency arrays are shown without editing the returned strings.</p>
$outputs
<p>Counts are provided in Table A and in the interactive Figure B. Every displayed count is inserted from the module state, and the distinct-string comparison is obtained from the returned sets.</p>
<label for="case-choice">Example selection</label><select id="case-choice"><option value="0">Documented discovery example</option><option value="1">Duplicate and group overlap example</option></select>
<figure><svg id="count-chart" viewBox="0 0 900 220" width="100%" role="img" aria-labelledby="chart-title">
<title id="chart-title">Requirement string counts by dependency group</title></svg>
<figcaption>Figure B. Requirement strings against dependency group for the selected example. Hover or focus a bar for case, component, demand, limit and units. No limit is defined.</figcaption></figure>
<noscript><p>Interactive selection requires JavaScript; all example counts are also provided in Table A.</p></noscript>
</section>
<section id="validation" data-report-section="7"><h2>7. Validation evidence</h2>
<p>The existing devtools test file contains $test_count test definitions, covering construction, requirement discovery, backup behavior and repository discovery. These tests provide unit-level evidence; no installation, solver, field-data or performance benchmark is established by them.</p>
<p>The report tests include hand-counted anchors for discovered files, deduplicated runtime strings and the summed group count. Additional consistency checks call the module again, compare every displayed count with its returned state, and rebuild the committed report and change panel. Integer counts are compared exactly, with zero tolerance; no floating-point text is compared.</p>
<p>The generated configuration's runtime and development arrays are compared with the accumulated sets. That comparison establishes string preservation for these inputs; acceptance of a build environment remains NOT_EVALUATED. The presence-only validation method in the complete wrapper does not parse configuration or install packages.</p>
</section>
<section id="recommendations" data-report-section="8"><h2>8. Key findings, limits and recommendations</h2>
<p>String collection is demonstrated for the supplied plain-line inputs, while package resolution and installation remain outside the evidence. Operational use is bounded by parser completeness, metadata preservation and cleanup scope.</p>
<p>Review requirement includes, editable lines, direct references, hash fragments and conflicting version constraints before modernization. Hyphen-prefixed lines are skipped and hash content is stripped, so a full dependency grammar is not implemented. Use the grammar in <a href="#ref-c">Ref C</a> as the acceptance basis for a future parser test suite.</p>
<p>Preserve a complete input copy, inspect the generated configuration and test installation in an isolated environment before enabling cleanup. The rationale is the observed difference between recursive cleanup and the fixed backup list, together with the current file-presence-only validation described in <a href="#ref-a">Ref A</a>.</p>
<p>Interpret the reported total as grouped string counts. For an inventory of distinct strings, use the union of the returned sets; for an inventory of installable distributions, perform package resolution separately. No timing result, worker-count recommendation or scalability threshold is inferred from this analysis.</p>
</section>
<section id="references" data-report-section="9"><h2>9. References and evidence locators</h2>
<p>Public sources are identified for the mathematical basis and the dependency grammar. Repository evidence is separated from external references so implementation behavior is not treated as a standard.</p>
<h3>9.1 Public sources</h3>
<p id="ref-b">Ref B. Discrete Mathematics: An Open Introduction, third edition, section 0.3, “Sets”: set membership, union and cardinality. <a href="https://discrete.openmathbooks.org/dmoi3/sec_intro-sets.html">Open textbook section</a>. The source was read for this analysis.</p>
<p id="ref-c">Ref C. Python Enhancement Proposal 508, final specification, “Grammar” and “Complete Grammar”: dependency strings, version constraints and markers. <a href="https://peps.python.org/pep-0508/">Public specification</a>. The source was read for this analysis; no numeric package limits are taken from it.</p>
<h3>9.2 Repository evidence and rebuild</h3>
<p id="ref-a">Ref A. Public API and usage: <code>src/assetutilities/devtools/README.md</code>, “Python API Usage”; exports: <code>src/assetutilities/devtools/__init__.py</code>; implementation: <code>src/assetutilities/devtools/modernize_deps.py</code>. Existing inputs and tests: <code>tests/modules/devtools/test_devtools_coverage.py</code>, especially <code>test_find_requirements_files_happy_path</code>.</p>
<p>Related implementations reviewed for scope: <code>src/assetutilities/devtools/cli.py</code>, <code>src/assetutilities/devtools/propagate_commands.py</code> and <code>src/assetutilities/devtools/organize_structure.py</code>. Presentation basis: <code>docs/sub_utilities/assets/style.css</code>, inlined below its attribution header. No existing house-style report exemplar was found in this repository.</p>
<p>Calculation-source digest (SHA-256): <code>$digest</code>. The digest covers only the dependency implementation; it identifies the calculation text, not a successful installation.</p>
<p>Rebuild: <code>python scripts/reporting/generate_devtools_report.py --work-dir &lt;scratch&gt;</code>. Checks: <code>python -m pytest tests/reports/test_devtools_report.py tests/modules/devtools -p no:cacheprovider</code>. Use a compatible pytest release and direct coverage output to scratch. Rebuild messages name this command when source content or the existing test-definition count changes.</p>
</section>
<section id="appendix" data-report-section="10"><h2>10. Appendix</h2>
<p>Outstanding evidence and document controls are recorded here. The data register distinguishes absent measurements from example inputs.</p>
<h3>10.1 Computed values, data register and pre-flight</h3>
<table id="table-a"><caption>Table A. Computed example counts</caption><thead><tr><th>Example</th><th>Quantity</th><th>Count</th><th>Source</th></tr></thead><tbody>$rows</tbody></table>
<table><thead><tr><th>Item</th><th>Status</th><th>Basis or next action</th></tr></thead><tbody>
<tr><td>Requirement strings</td><td>Documented example and labelled extension.</td><td>Ref A; full input strings appear in the worked example.</td></tr>
<tr><td>Performance limit and installation acceptance</td><td>NOT_EVALUATED.</td><td>No benchmark or installation campaign is included.</td></tr>
<tr><td>Physical model and operating envelope</td><td>Not applicable.</td><td>This is file-processing software.</td></tr>
<tr><td>Assumed engineering data</td><td>None.</td><td>No missing coefficient or limit has been substituted.</td></tr>
<tr><td>Document style exemplar</td><td>Unavailable in the inspected repository.</td><td>Existing documentation stylesheet is reused with the requested document body class.</td></tr>
<tr><td>Pre-flight checks</td><td>Defined in the rebuild test.</td><td>Section count, links, input precision, integer anchors, result consistency, self-containment and public wording are checked.</td></tr>
<tr><td>Browser interaction</td><td>NOT_EVALUATED.</td><td>No browser automation is included; comments and chart code require browser acceptance testing.</td></tr>
</tbody></table>
<h3>10.2 Engineering changes</h3><div id="change-panel"></div>
<h3>10.3 Review comments</h3><p>Choose a section, enter a comment and add it to the list. Save beside this document by selecting its containing folder when supported. Otherwise download the comments file and place it beside the HTML. Comments are held in this page until saved; closing the page discards unsaved comments.</p>
<label for="comment-section">Section</label><select id="comment-section"></select>
<label for="comment-text">Comment</label><textarea id="comment-text" rows="4" cols="60"></textarea>
<p><button id="add-comment" type="button">Add comment</button> <button id="save-comments" type="button">Save comments</button></p>
<p id="save-status" role="status"></p><ol id="comments"></ol>
</section>
<script id="example-data" type="application/json">$cases_json</script>
<script id="changes-data" type="application/json">$changes_json</script>
<script>
const cases = JSON.parse(document.getElementById('example-data').textContent);
const changeData = JSON.parse(document.getElementById('changes-data').textContent);
const panel = document.getElementById('change-panel');
for (const change of changeData.changes) {
  const p = document.createElement('p');
  p.textContent = change.section + ': ' + change.description;
  panel.appendChild(p);
}
const ns = 'http://www.w3.org/2000/svg';
function drawChart() {
  const item = cases[Number(document.getElementById('case-choice').value)];
  const chart = document.getElementById('count-chart');
  chart.replaceChildren();
  const groups = [['Runtime', item.runtime_count], ['Development', item.dev_count],
    ['Reported total', item.dependencies_found], ['Distinct union', item.distinct_count]];
  const scale = Math.max(...cases.map(c => c.dependencies_found));
  groups.forEach(([name, value], index) => {
    const y = 20 + index * 45;
    const label = document.createElementNS(ns, 'text');
    label.setAttribute('x', '10'); label.setAttribute('y', y + 22);
    label.textContent = name; chart.appendChild(label);
    const bar = document.createElementNS(ns, 'rect');
    bar.setAttribute('x', '210'); bar.setAttribute('y', y);
    bar.setAttribute('width', String(value / scale * 550)); bar.setAttribute('height', '30');
    bar.setAttribute('fill', '#33C3F0'); bar.setAttribute('tabindex', '0');
    const text = item.name + '; component: ' + name + '; demand: ' + value +
      '; limit: not defined; units: requirement strings';
    bar.setAttribute('aria-label', text);
    const title = document.createElementNS(ns, 'title'); title.textContent = text;
    bar.appendChild(title); chart.appendChild(bar);
    const count = document.createElementNS(ns, 'text');
    count.setAttribute('x', String(220 + value / scale * 550));
    count.setAttribute('y', y + 22); count.textContent = String(value); chart.appendChild(count);
  });
  const axis = document.createElementNS(ns, 'text');
  axis.setAttribute('x', '210'); axis.setAttribute('y', '215');
  axis.textContent = 'Count (requirement strings); no acceptance limit is defined.';
  chart.appendChild(axis);
}
document.getElementById('case-choice').addEventListener('change', drawChart);
drawChart();
const comments = [];
const sectionPicker = document.getElementById('comment-section');
for (const section of document.querySelectorAll('section[data-report-section]')) {
  const option = document.createElement('option'); option.value = section.id;
  option.textContent = section.querySelector('h2').textContent; sectionPicker.appendChild(option);
}
document.getElementById('add-comment').addEventListener('click', () => {
  const field = document.getElementById('comment-text');
  if (!field.value.trim()) return;
  const comment = {section: sectionPicker.value, text: field.value.trim()};
  comments.push(comment);
  const li = document.createElement('li'); li.textContent = comment.section + ': ' + comment.text;
  document.getElementById('comments').appendChild(li); field.value = '';
  document.getElementById('save-status').textContent = 'Unsaved comments.';
});
document.getElementById('save-comments').addEventListener('click', async () => {
  const name = 'devtools-comments.json';
  const content = JSON.stringify({revision: changeData.revision, comments}, null, 2) + '\\n';
  const status = document.getElementById('save-status');
  try {
    if ('showDirectoryPicker' in window) {
      const directory = await window.showDirectoryPicker({mode: 'readwrite'});
      const handle = await directory.getFileHandle(name, {create: true});
      const writable = await handle.createWritable(); await writable.write(content); await writable.close();
      status.textContent = 'Comments saved in the selected folder.';
    } else {
      const url = URL.createObjectURL(new Blob([content], {type: 'application/json'}));
      const link = document.createElement('a'); link.href = url; link.download = name; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = 'Comments downloaded. Place the file beside the HTML document.';
    }
  } catch (error) { status.textContent = 'Comments were not saved. ' + error.message; }
});
</script></main></body></html>
""").substitute(
        css=css,
        inputs_html=inputs_html,
        outputs=outputs,
        rows=rows,
        test_count=test_count,
        digest=digest,
        cases_json=cases_json,
        changes_json=changes_json,
        reported=cases[1]["dependencies_found"],
        distinct=cases[1]["distinct_count"],
    )
    return {"html": html, "changes": CHANGES, "cases": cases}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    scratch = args.work_dir.resolve()
    if scratch == ROOT or ROOT in scratch.parents:
        parser.error("--work-dir must be outside the repository")
    result = build(scratch)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "index.html").write_text(
        result["html"], encoding="utf-8", newline="\n"
    )
    (args.output_dir / "changes.json").write_text(
        json.dumps(result["changes"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("Built dependency collection report and change panel.")


if __name__ == "__main__":
    main()
