# Line-dynamics report and layback summary calculations

Pure Python reproductions of the formulas in `custom_calculation_polynomial.xlsx`
and `excel_to_image.xlsx`, with immutable input/output records. Source workbooks
are read only. No workbook, macro, licensed application, or external link is
needed by the calculation API. No engineering standard or clause is cited in
these workbooks; this conversion supplies no additional design rules.

## Source inventory and scope

| Source | Sheets | Formula cells | Usable cached results |
| --- | ---: | ---: | ---: |
| Layback summary | 1 | 12 | 12 |
| Dynamics reports | 37 | 17,120 | 0 |

The report source has one hidden metadata sheet, 20 raw data sheets, and 16
reports. All reports share the same 1,070 normalized formulas, including array
formula text and ranges. Four raw sheets have no report; raw rows 58:60 are
outside all report references. Both workbooks have zero defined names and
zero external links. Hidden metadata and unused cells are excluded.

`layback_summary.calculate_layback_summary` implements six labels and six
range extrema on Sheet1. The source has no polynomial equation or coefficient
table despite its filename. Inputs are sparse G7:L41 and blank layback cells
A7/A13/A19/A25/A31/A37. Only I/J/K have numeric values. Blank range entries are
`None`; extrema ignore blanks and return zero for an entirely blank range.
Concatenating a blank layback produces empty text. Lengths are m, angles degrees,
and tensions retain the source's `Te` notation.

`bending_report.calculate_bending_report` reduces raw rows 2:57, using columns B,
F, I:X. Outputs correspond to G2, B4, B9:S64 and H66:AA68. Inputs are
`DynamicsRow`, `ReportMetadata`, `ReportAllowables` and `DirectionConvention`.
Lengths are m, time s, angles degrees, speed m/s and loads/tensions kN; the
current factor is dimensionless. Callers supply inputs in these units.

Tp and Hs are the first four characters after those filename tokens. Tp uses
INT (floor); Hs stays text. Wave direction is `360 - direction + 90`, relative
heading is `wave direction - vessel heading`, and current speed is reference
speed times factor. Positive current uses `90 - direction`, with 360 added once
if negative; nonpositive current uses direction zero. Connection angle extrema
use `180 - declination extrema` with maximum/minimum reversed. Remaining
response columns are direct copies. There is no modulo operation or conversion
of load units in these formulas.

Summary extrema are independent and can describe different loading conditions.
T:AA helper columns are blank, producing zero extrema and zero direct-reference
allowables. Allowables are copied as values, without engineering acceptance
checks. F1 is labelled an override but no formula uses it. Callers supply a
`ReportMetadata.title_template` with `{prefix}`, `{step}` and
`{current_description}` fields. The title is `None` when no prefix is supplied.
An explicit sheet name supplies the context used by CELL("filename").

## Compact fixtures and publication

`fixtures/bending_reports.json` in the test folder stores one pattern: 18 row
formulas translated over rows 9:64, plus 62 isolated formulas. Shared constants,
448 source helper blanks (as a range), and the redacted title cell are represented
once. The original pattern expands to 1,070 formulas and 1,478 input references.
All reports share four hand-chosen synthetic rows with round values, positive,
zero and negative current speeds, and negative directions. Expansion shortens
the table, extrema ranges and helper blanks to those four rows: 134 formulas
and 126 input references. Both fixtures are under 20 kB. The report fixture retains
no original response rows. Its XML cache evidence describes the original source,
not the synthetic rows. The separate small summary fixture retains its twelve
cached results.

Source sheet identifiers are replaced by ordinal aliases; raw formula references
use `RAW`. Synthetic filenames contain only the Hs/Tp fields read by formulas.
Source paths, identifying title prefixes, and unused filename fields are omitted.
Public sheet context therefore uses neutral aliases. A direct-source test checks
all non-title formula results using the full original response rows, sheet context
and filenames in memory. Another source test checks the full data after filename
sanitization. Identifying metadata is never written to fixtures.

The extractor checks every source formula against expansion of the single
pattern, including array ranges, and verifies shared constants and blanks on
all 16 reports. The normalized SHA-256 is
`64506bf6cec000cf1c41fa0fbf17b5f9e309212704125433395ad81d80fe3b24`.

## Raw XML cache evidence

All 17,120 report formula cells contain `<v></v>` after `<f>`. Each has no `t`
attribute, so the cell uses the default numeric type. The value element has zero
content: there is no calculated numeric result. These cells are neither cached
Excel empty strings (`t="str"`) nor cached errors (`t="e"`). Counting value
elements alone therefore overstates available cached results. Openpyxl returns
`None` for these empty numeric elements. None of the report value elements are
absent; none contain nonempty values or errors.

Tests assert this evidence for every report and inspect the original XML when
the source is available. A small synthetic XML example guards the distinction
between absent elements, empty numeric elements, cached empty strings, numeric
results, text results, and errors. There are no missing-cache skips. An
independent restricted formula interpreter checks 133 outputs per synthetic report
and 1,069 per original report; these are formula-consistency comparisons, not
Excel cache regressions. B4 is excluded because its identifying input is redacted;
neutral title assembly is
tested separately. All twelve summary results are compared with original caches.
Numeric tolerances remain relative 1e-9 and absolute 1e-12; text equality is exact.
See [COVERAGE.md](../../../tests/modules/line_dynamics_report/COVERAGE.md).

## Input gaps

- Sheet1 A7/A13/A19/A25/A31/A37: layback distances are blank. Keep `None`; do
  not infer distances from adjacent response data.
- Sheet1 G7:H41 and L7:L41: tension, departure-angle and allowable-radius inputs
  are blank. Preserve the source's zero-extrema semantics. No polynomial
  coefficients or equation are provided.
- Sheet1 G5/I5/J5: tension unit `Te` has no defined force conversion. Keep the
  notation; do not assume a conversion.
- Every report N3/O3/Q3: labelled allowable values 11.3 m / 6.9 m / 118 kN have
  no cited design basis. All four `ReportAllowables` arguments are required
  caller inputs. P3's clearance criterion `>0` also lacks a stated basis.
- Every report C9:C64/G9:G64 and L9:M64: the angle literals 360, 90 and 180
  lack a convention reference. Preserve `DirectionConvention` defaults;
  callers must confirm the intended coordinate convention.
- Filename field width four and sheet-label width six are source literals,
  named `FILENAME_VALUE_CHARACTERS` and `REPORT_STEP_CHARACTERS`. No alternative
  naming specification is supplied.
- Report S8 says `[kNm]`, while S9:S64 copies raw X2:X57, labelled minimum
  layspan tension. Preserve `layspan_tension_min_kn` values in kN; the unit
  label conflict remains unresolved.
- Report D2 is identifying title metadata and is redacted. A caller must supply
  `ReportMetadata.title_prefix` and `title_template` to reproduce B4 privately;
  no title template is assumed.
- CELL("filename") requires explicit sheet context. Original report caches
  contain empty numeric value elements, so cached-value validation remains
  unavailable for these 17,120 formulas.

## Test and regeneration commands

Run tests from the repository root:

```bash
python -m pytest --confcutdir=tests/modules/line_dynamics_report tests/modules/line_dynamics_report
```

The plain repository command fails before collection with pytest 9.2.0 because
`tests/conftest.py` implements the removed `path` argument:

```text
hookimpl definition: pytest_ignore_collect(path, config)
Argument(s) {'path'} are declared in the hookimpl but can not be found in the hookspec
```

`--confcutdir` bypasses that parent hook; the repository's pytest.ini still
supplies imports, markers, warning filters and default options.
The optional source checks skip only when their workbook is absent.

Regenerate the layback fixture from the repository root, without saving a workbook:

```bash
python tests/modules/line_dynamics_report/extract_cached_values.py --output-dir tests/modules/line_dynamics_report/fixtures
```

The report fixture's synthetic rows are maintained by hand. This command leaves
`bending_reports.json` unchanged; full report data is checked only in memory by
the optional source tests.

## What remains

Obtain an independently approved, calculated copy for report cache regression;
keep the original source unchanged. Confirm the allowable basis, direction
conventions, Te meaning, missing polynomial inputs/equation, and minimum-tension
unit label. There is no evidence for inventing extra reports or a polynomial
algorithm. The conversion remains partial in Excel cached-value validation.
