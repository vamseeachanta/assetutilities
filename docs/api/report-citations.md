# Report citation binding

Reports bind opaque standard identifiers to declared editions. This public
binding layer reads no private index and copies no standards text. A rendered
citation establishes a document binding; it does not establish source access,
validity of an equation or permission to reproduce content.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| 1 | 2026-10-20 | Standardized reference bindings and disclosure across report outputs. |
| 2 | 2026-10-22 | Rejected blank locations and invalid pages, unified missing publishers, and excluded output paths from input hashes. |

## Template inventory

| Active surface | Binding and output |
|---|---|
| `examples/workflows/reportgen/input.yml` | Inline section definitions; Markdown, Word and self-contained HTML |
| `common/reportgen/dom.py` and `writers.py` | Shared document model, default writers and registered writer variants |
| `tests/modules/reportgen/*.yml` | Legacy report configurations; retain their existing formatting and content |
| `examples/workflows/reportgen/standard-report.json` and `common/reportgen/standard.py` | Structured Word/PDF layout; same top-level references and inline citation metadata |
| `docs/modules/documentation/standard-report.md` | Structured report layout instructions |

Calculation reports, design bases, vetting reports and tension reports can use
this same binding shape in their section definitions. Dedicated schemas for those
subjects are not asserted by this inventory. Archived documents and generated
sample reports are not templates to republish.

## Binding pattern

```yaml
references:
  - code_id: NIST-SP-811
    publisher: NIST
    revision: "2008"
    source_sibling: generic
sections_L1:
  - name: Method
    paragraphs:
      - [{type: citation, code_id: NIST-SP-811, section: "4.3, table 5"}]
```

The example renders `[NIST-SP-811 2008 §4.3, table 5]`. `page` is optional and
renders with a `p.` prefix. When supplied, it must be a positive integer or a
string containing a positive integer. Supplied sections must not be blank; no
page or clause is invented. Identifiers and revisions must be nonempty strings.
Duplicate identifiers and unbound inline citations fail before a report file is
created. Unknown private slugs are not silently treated as resolved.

`source_sibling: generic` carries the public binding's origin convention. It is
metadata only and does not locate a directory. `code_id`, `publisher`,
`revision`, `section` and `source_sibling` are the fields supported by this
repository's binding layer. Supply reviewed source metadata for each method;
the binding itself does not qualify that method.

For structured reports, declare the same top-level `references` and put
`{type: citation, code_id: ..., section: ...}` after the opening paragraph in a
section's `blocks`. The References section receives a metadata table and the
disclosure. Word and its derived PDF contain the same citation text.

## Appendix and disclosure

References render as Code / Publisher / Revision. An omitted or blank publisher
renders as `Not supplied` in every format. Reports with bindings include:

> Citations in this report reference an internal engineering-standards index by
> code identifier and revision. The full text of each cited standard is not
> included and must be obtained from the respective publisher. This report does
> not reproduce copyrighted standard content.

Legacy section-based reports also append package version, Git SHA, input hash
and generation time from the workflow provenance helpers. The input hash excludes
the `important_paths` output-location mapping and the workflow helper's volatile
keys; changing report content still changes the hash. No filesystem paths
are emitted in those provenance rows. Provenance defaults on when references
exist; `provenance: false` suppresses it and `provenance: true` enables it without
references. Structured reports retain their deterministic revision-based metadata.

For HTML, select `report_details.target_report_type: html`. Text and table cells
are escaped; CSS is inline. `timestamped_filename: false` selects a deterministic
filename; the default timestamped naming remains available.

Run the [worked example](library-gallery.md) and the reportgen tests to inspect
synthetic inputs and output. No private resolver or licensed text is required.
