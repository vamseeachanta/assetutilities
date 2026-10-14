# Structured Word and PDF reports

The opt-in P6 formatter extends `assetutilities.common.reportgen`. It uses
`python-docx` to write Word and an installed LibreOffice to convert that document
to PDF. No dependency or system package is added. Legacy Markdown and Word
writers retain their existing input and output behavior.

The layout basis is *Engineering reporting conventions*, proposed revision P6,
13 October 2026, Table 2.1 and presentation rules 2, 4 and 6. The inspected template
blob is `4e13d6ded9b029351e33c45e394d6b1316cf7466` in the standards repository.
This is a layout subset, not an assertion of engineering compliance.

## Input and use

The synthetic input is
`examples/workflows/reportgen/standard-report.json`. It contains invented text
and readings with no physical qualification. Its `revisions` array is the
revision record; the renderer never invents a history entry. A re-issue appends a
record and changes `revision` to match its last entry. Earlier records must be
retained by the caller. The formatter checks chronological dates, unique revision
identifiers and agreement with the latest record; it cannot detect a caller
rewriting a previous issue without an archived earlier record.

```sh
uv run python -m assetutilities.common.reportgen.standard \
  examples/workflows/reportgen/standard-report.json \
  --output "$REPORT_OUTPUT/sample.docx" \
  --pdf "$REPORT_OUTPUT/sample.pdf" --scratch "$REPORT_SCRATCH"
```

Both destination folders are caller-selected. Without `--pdf`, LibreOffice is
not required. The library functions are `write_docx(report, destination)` and
`convert_pdf(source, destination, scratch)`. Conversion accepts trusted DOCX
only; it does not inspect arbitrary untrusted office documents.

The existing `reportgen.run(config)` also accepts `reporting_standard: P6`, with
`report` containing the structured input. `report_details.target_report_type`
is `docx` or `pdf`, and `target_file_stub` controls the deterministic basename.
`important_paths.project_root` and `outputs_path` choose the output folder.
PDF additionally requires `scratch_path`. This route emits `stub.out.docx`
and, for PDF output, `stub.out.pdf`.

## Layout and validation

All ten sections are required in P6 order. Design Data contains its seven
prescribed subsections; References contains Published references and Internal
references. Each section and subsection opens with supplied text. State
inapplicability and its reason in that text rather than omitting a section.
At most two numbered heading levels are accepted. Optional appendices follow
Section 10 and use letters in input order. The contents list links to the section
bookmarks without requiring a Word field refresh.

Text blocks are strings. A table block has `type: table`, `caption`, `columns`
and rectangular `rows`. All cells are strings: the caller supplies engineering
precision, units and any qualified comparison. Captions appear below tables,
numbered by section or appendix. Rows repeat the header on continuation pages
and avoid splitting individual rows. Tables use borders and fixed equal column
widths within the page margins. Tables above fifteen data rows are rejected in
numbered sections except Design Data, References and Acronyms and Symbols; move
supporting results into an appendix and supply the body conclusion separately.
The formatter does not invent a chart or reduce a table's font to force one-page
output. Long words, oversized rows and pagination require inspection in the
recipient's renderer.

The report begins with its title, document number and an Internal cover mark,
then the summary, revision history and contents. Revision information appears
only in the history table. A4 page size and Arial are explicit layout choices;
P6 does not prescribe either. The 11-point body type and 18 mm margins follow the
template's print styling. Body text is regular weight; table headers and headings
retain structural emphasis. The default internal mark avoids implying that
format validation qualifies a report for external issue.

## Reproducibility and limits

Word core dates come from the newest revision date. ZIP entry order and dates
are fixed. Rebuilding the same input with the same library versions produces
byte-identical DOCX files, without discarding report content.

PDF conversion uses a separate retained LibreOffice profile and output folder
under the supplied scratch directory. The final PDF omits volatile creation and
modification metadata, XMP metadata and trailer identifiers; page content is
cloned. Native conversion output and logs remain in scratch. PDF bytes and font
pagination are only reproducible with the same converter and font environment.
An error is raised if the converter is missing, fails or produces no PDF.
The PDF integration test requires installed LibreOffice and is not silently
skipped. Local conversion could not start: `ERROR: no valid pipe path found.`
PDF read-back, link retention and repeat-build equality therefore remain
unverified for the installed converter.

Markdown ingestion, CSV-to-spreadsheet export, one-page table fitting, equations,
figures, charts, arbitrary cross-references and citation resolution are outside
this input contract. The formatter does not evaluate title semantics, source
rights, physical results, validation evidence or engineering adequacy. Citation
binding, disclosure and provenance for the broader template inventory remain
open in #79; this output backend alone does not complete that issue.
