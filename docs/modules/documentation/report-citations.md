# Report citation bindings

`reportgen` binds inline citations to declared standard identifiers in Markdown,
Word and self-contained HTML. It appends References, Disclosure and, by default,
Provenance. This is a document formatting contract; it does not resolve private
content or qualify an engineering calculation.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| A | 2026-10-19 | Documented citation bindings and a worked formatting example for consistent report references. |

## Template inventory

| Existing surface | Purpose and binding pattern |
|---|---|
| `examples/workflows/reportgen/input.yml` | Runnable generic report template. Top-level `references` binds identifiers; citation paragraphs render in the body; appendices and disclosure are automatic. |
| `src/assetutilities/base_configs/modules/reportgen/reportgen.yml` | Legacy engine defaults. Citation binding is opt-in through the input configuration; the existing fixture is unchanged. |
| `tests/modules/reportgen/*.yml` | Legacy report configurations and layout examples. Inputs without bindings retain their section structure and default timestamped filenames. |
| `src/assetutilities/common/reportgen/writers.py` | Default Markdown, Word and HTML layouts; all support citation paragraphs in the opening section, main sections and subsections. |
| Registered custom writers in `src/assetutilities/common/reportgen/` | Separate presentation implementations. They have not been extended; use a default writer for citation paragraphs. |
| `src/assetutilities/common/reportgen/standard.py` | Separate structured Word/PDF layout documented in [standard-report.md](standard-report.md). Its explicit published/internal reference sections retain their existing schema; automatic citation binding is not wired to this route. |
| `modules/reporting/templates/plotly_report_template.py` | Standalone chart report helper outside the registered `reportgen` workflow. Its reference integration is deferred. |

There are no separate registered calculation-report, design-basis, vetting-report
or mooring-tension templates in this workflow. Each can use the same binding
pattern: declare all identifiers in `references`, place citation paragraphs next
to the relevant method or result, and retain the generated appendices. This
change adds no domain-specific engineering criteria or report layouts.

## Input contract

```yaml
references:
  - code_id: DNV-OS-E301
    publisher: DNV
    revision: "example-revision"
    source_sibling: generic

sections_L1:
  - name: Method
    paragraphs:
      - [{type: citation, code_id: DNV-OS-E301,
          section: example-clause, page: example-page}]
```

The top-level configuration block is the template's frontmatter binding.
`code_id` is the wiki slug/join key, not a URL or local path. Each reference
requires nonempty string `code_id` and `revision`. Optional `publisher`, `title`
and `source_sibling` must be nonempty strings when supplied; `source_sibling`
defaults to `generic`. It is retained for contract alignment but is not rendered
or used to access a private repository. Bind only one revision per identifier in
one document; duplicate identifiers and unbound citations raise `ValueError`.

Citation paragraphs have `type: citation`, `code_id`, and optional `section` and
`page` locators. The example renders as
`[DNV-OS-E301 example-revision §example-clause p.example-page]`. Missing locators
are omitted. These are inline citation labels, not linked footnote objects.
No section or page is inferred. Reference identifiers and locators are author
inputs; their existence, correctness and source access are not validated here.

The generated References appendix lists Code, Publisher and Revision in input
order, including references not cited in the body. Disclosure uses this exact
text:

> Citations in this report reference an internal engineering-standards index by code identifier and revision. The full text of each cited standard is not included and must be obtained from the respective publisher. This report does not reproduce copyrighted standard content.

The internal resolver is unavailable to report recipients. References confer no
access or reproduction rights; the full standard must be acquired separately.

## Provenance and output

Provenance uses `workflow_api.envelope.code_version`, `input_hash` and
`utc_now_iso`. It records Package version, Git SHA, Input sha256 and Generated
(UTC), with `unavailable` for missing version information. It never renders
configuration paths. Callers remain responsible for paths or sensitive content
they put into report text and metadata. The shared hash excludes its documented
volatile keys; other configuration fields, including supplied paths, affect the
hash without being printed. A hash is provenance, not source validation.

| References declared | `provenance` option | Provenance appended |
|---|---|---|
| Nonempty | absent or `true` | Yes |
| Nonempty | `false` | No |
| Empty or absent | absent or `false` | No |
| Empty or absent | `true` | Yes |

Set `report_details.target_report_type: html` for a single HTML file with inline
CSS and escaped headings, text, citations and table cells. The writer adds no
scripts, remote styles or fonts. Supplied text is preserved as text, including
any author-supplied URLs. Set `report_details.timestamped_filename: false` to
write `{stub}.out.{ext}`; otherwise the existing timestamped name is retained.
Stable names do not make provenance timestamps or Word files byte deterministic.
Regenerating a stable name replaces the previous output at that location.

## Worked formatting example

Input: [the workflow example](../../../examples/workflows/reportgen/input.yml)
declares `DNV-OS-E301` revision `2018-07` and `OCIMF-MEG4` revision `2018`.
These metadata strings come from the issue #79 example; no engineering value
is taken from those standards. No clause or page is asserted without a checked
source.

Method: for each citation, match `code_id` to a declared reference, read its
revision, and join the identifier and revision inside square brackets. Append
the reference table, standardized disclosure and shared provenance fields.

Answer: `[DNV-OS-E301 2018-07]` and `[OCIMF-MEG4 2018]` appear in Results,
followed by References, Disclosure and Provenance. The report includes revision
history after its opening summary. It demonstrates formatting rather than an
engineering calculation; no equations, coefficients or acceptance limits apply.

Run from the repository root:

```sh
uv run python -m assetutilities examples/workflows/reportgen/input.yml
```

The default output is a timestamped Markdown file in the example's outputs
directory. Tests redirect all output to their temporary directory and read back
Markdown, Word and HTML without committing generated reports.

## Basis and limits

The basis is issue #79 and its implementation plan dated 2026-07-06; field names
align with `workspace-hub:.claude/rules/calc-citation-contract.md` and
`workspace-hub:docs/standards/calc-output-citation.md`. The OCIMF MEG3/MEG4 pilot
establishes the identifier/revision binding pattern; its private corpus is not
reproduced or queried. The DNV calculation pilot and private-index validation
remain separate concerns. The current codes/standards routing rule governs
rights independently of repository visibility.

Tests in `tests/modules/reportgen/test_citation_binding.py` derive expected
labels by hand in the module docstring and independently hash literal canonical
JSON for provenance. They check invalid input, ambiguous binding, all writer
positions, escaping, optional provenance, legacy output and repeated runs.

Later slices: custom presentation writers, structured Word/PDF citation mapping,
standalone chart reports and private resolver integration. No private source
text, standard-derived numeric data or new dependencies are included.
