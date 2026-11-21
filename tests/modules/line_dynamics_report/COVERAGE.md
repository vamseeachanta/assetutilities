# Formula coverage

Cache regression and formula interpretation are different evidence. Numeric
comparisons use relative tolerance 1e-9 and absolute tolerance 1e-12; text uses
exact equality. No tolerance was relaxed.

| Source group | Sheets | Formulas per sheet | Cache comparisons | Formula-text comparisons |
| --- | ---: | ---: | ---: | ---: |
| Layback summary | 1 | 12 | 12 | Not needed |
| Synthetic reports, neutral aliases case01 through case16 | 16 | 134 | 0 | 2,128 |
| Original dynamics reports, optional source checks | 16 | 1,070 | 0 | 17,104 per check |
| Hidden metadata and raw inputs | 21 | 0 | 0 | 0 |

The report source has 17,120 empty numeric `<v></v>` elements, one per formula.
Zero are missing; zero contain numbers, strings, or error values. With default
numeric cell type, an empty value element is unavailable calculation output,
not a cached empty string. Every report's compact cache record asserts 1,070
`empty_v` cells and an empty cached-value map. Tests do not skip this evidence.
The raw XML scanner distinguishes missing elements, empty numeric elements,
empty strings, text, numbers and errors independently of openpyxl's data-only
interpretation. The small summary source has twelve actual caches: all pass.

The fixture stores one row pattern (18 columns, repeated over 56 rows), plus
62 isolated formulas, once for all reports. Expansion reproduces all 1,070
formula addresses, texts and array ranges. A fresh source extraction proves
all 16 normalized sets identical, including the full formula SHA-256:
`64506bf6cec000cf1c41fa0fbf17b5f9e309212704125433395ad81d80fe3b24`.
Shared constants and all 448 blank helpers are also verified for each report.
All public reports share four hand-chosen synthetic rows with round values,
both current branches and negative directions. Original response rows are never
written to the report fixture. Expansion shortens table and extrema ranges for
synthetic inputs while preserving the original pattern for source checks.

The restricted formula interpreter checks G2, B9:S64 and H66:AA68 for every
source report: 1,069 outputs each, 17,104 total per check. Both source tests use
full original response rows in memory: one with sanitized filenames, one with
original filenames and sheet context. The public synthetic fixtures check 133
outputs each, 2,128 total.
G2 uses neutral sheet context in public fixtures and original context in the
direct-source comparison. B4 is excluded because its title prefix is identifying;
neutral title assembly has a separate assertion. Formula interpretation does
not establish agreement with independently calculated Excel values.

All tests run without source workbooks except the three read-only source
comparisons (two report checks and one summary check). Only those tests skip
when their optional source is absent.

Raw rows 58:60 and four raw sheets without reports are outside the formula
references. No formulas are excluded due to macros, external references or
text concatenation. Independent report caches, identifying title validation,
and the Input gaps in
[README.md](../../../src/assetutilities/line_dynamics_report/README.md) remain the limits.
