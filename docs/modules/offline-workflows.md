# Offline PDF, CSV, text and Git workflows

These five registered CLI workflows replace the deferred handlers in issue #91.
Each example uses synthetic data or inspects the current checkout. Run the commands
from the repository root; generated files are excluded from version control.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| Initial | 2026-10-19 | Added worked examples for the newly usable offline workflows. |

## PDF extraction and splitting

```sh
uv run python -m assetutilities examples/workflows/read_pdf/input.yml
uv run python -m assetutilities examples/workflows/edit_pdf/input.yml
```

The four-page `data/sample.pdf` contains the literal text
`AssetUtilities read_pdf sample page N` for each page number. Its synthetic
geometry and page count are example inputs, not engineering acceptance limits.
The fixture was generated with matplotlib's `PdfPages`: each iteration creates a
figure, places that string with `fig.text`, saves it and closes it. The two examples
share the fixture in `examples/workflows/read_pdf/data/sample.pdf`.
PDF creation and modification timestamps were omitted.

`read_pdf` specifies `library: PyPDF2` and a complete `files.from_pdf` list with
`io`, `page` and optional `label` per entry. The example requests pages 1 and 4.
YAML page numbers are one-based: page `p` selects `reader.pages[p - 1]`.
Each selected page is extracted to UTF-8 text; the answer is the corresponding
literal fixture string in `results/read_pdf_first.txt` and
`results/read_pdf_last.txt`. The returned `result` contains label, page,
`output_file` and `n_chars`, with no reader or DataFrame objects.

PDF input paths resolve against the process working directory. Text outputs use
`Analysis.result_folder`; direct callers without it get `results/` beside the PDF.
Returned text paths retain the configured directory and use forward slashes.
Labels are sanitized and duplicate labels receive suffixes.
A blank page produces empty text. Invalid
page types and out-of-range pages raise `ValueError`.

`edit_pdf` selects inclusive ranges `[1, 2]` and `[3, 4]`. Independent enumeration
gives two pages per output, containing the original first/second and third/fourth
page strings respectively. The existing splitter writes beside the input:
`examples/workflows/read_pdf/data/sample.pdf_page_1-2.pdf` and
`examples/workflows/read_pdf/data/sample.pdf_page_3-4.pdf`.

Method source: [PyPDF2 3.0.0, Extract Text from a PDF](https://pypdf2.readthedocs.io/en/3.0.0/user/extract-text.html).
The one-based YAML convention and inclusive splitter ranges follow the issue #91
implementation plan (2026-07-06) and `EditPDF.from_pdf_PyPDF2` respectively.
Text extraction is not OCR; scanned pages are not evaluated for text recognition.
Tabula and Camelot remain optional table backends and require their own dependencies;
the examples exercise neither Java nor native table extraction.

## CSV normalization

```sh
uv run python -m assetutilities examples/workflows/csv_utilities/input.yml
```

The Latin-1 input is exactly:

```csv
name,value
café,2
tea,3
```

`csv_utilities.input_file` resolves relative to `Analysis.analysis_root_folder`
(the input YAML directory); legacy `txt_file` is an accepted alias. The router
uses `pandas.read_csv`, with a comma delimiter by default and optional `nrows`.
Without `encoding`, it tries UTF-8 and retries Latin-1 only on `UnicodeDecodeError`.
An explicit encoding is honored without fallback. Normalized output is UTF-8,
comma-delimited, with a header and no index column.

The independent answer is two data rows and two columns (`name`, `value`).
The accent's Latin-1 byte cannot decode as UTF-8, so `encoding_used` is `latin-1`.
Outputs are `results/sample_latin1_normalized.csv` and
`results/sample_latin1_summary.yml`; the summary echoes the input, encoding,
delimiter, row/column counts and column names. `csv_utilities.results` holds paths.

Method source: [pandas 2.2.3, read_csv](https://pandas.pydata.org/pandas-docs/version/2.2.3/reference/api/pandas.read_csv.html).
The fallback policy follows the issue #91 implementation plan (2026-07-06).
Latin-1 fallback is not an encoding detector; set `encoding` explicitly when known.
CSV parsing retains pandas' type inference and missing-value interpretation;
normalization is not a byte-preserving archival conversion.

## Ordered set comparison

```sh
uv run python -m assetutilities examples/workflows/text_analytics/input.yml
```

Inputs are `data.set1: [red, blue, red, green]` and
`data.set2: [green, gold, blue, gold]`. Both must be lists of strings.
For sets A and B, the method computes A intersection B, A minus B and B minus A.
Results retain first occurrence order from their respective input lists and remove
duplicates. Hand enumeration gives:

| Result | Answer | Count |
|---|---|---|
| `common` | `[blue, green]` | 2 |
| `only_in_set1` | `[red]` | 1 |
| `only_in_set2` | `[gold]` | 1 |

The raw input sizes are four and four, including duplicates. Results, unique
counts and raw sizes go to `results/text_analytics_comparison.yml` and
`cfg.text_analytics`. Direct callers must supply `Analysis.result_folder`.
Comparison is exact and case-sensitive; no fuzzy matching or document reading occurs.

Method source: [Python 3.11, Set Types](https://docs.python.org/3.11/library/stdtypes.html#set-types-set-frozenset).
Order and deduplication follow the issue #91 implementation plan (2026-07-06).

## Read-only Git inspection

```sh
uv run python -m assetutilities examples/workflows/gitpython/input.yml
```

Each `repos` entry has an `io` path, resolved relative to the input YAML directory.
The example uses `.`; parent-directory discovery finds the containing checkout.
`results/gitpython_report.yml` contains branch, HEAD, dirty state (including
untracked files) and at most five recent commit identifiers/subjects per repository.
The five-entry bound is the issue #91 implementation plan's explicit output policy
(2026-07-06), not an engineering limit. Detached HEADs report `DETACHED`; an unborn
branch has a null HEAD and an empty history. Actual branch and history values vary.

The workflow never commits, pushes or clones, including when legacy merged
`common_cfg` flags request these operations. The report records
`skipped: write operations not supported`. Source: [GitPython 3.1.43 tutorial](https://gitpython.readthedocs.io/en/3.1.43/tutorial.html).
Reports can include repository history subjects; inspect their contents before sharing.

## Validation and scope

`tests/workflows/test_deferred_workflows.py` runs every example through the real
CLI twice, checks each registry-listed output, and safely loads the saved YAML.
It copies example inputs to temporary storage so generated outputs stay outside
the checkout; the Git copy inspects the checkout through an explicit path.
Focused module tests cover invalid/blank PDF pages, duplicate labels, CSV alias,
encoding and row limits, duplicate/empty text sets, and Git HEAD states.

These are CLI examples. Sandboxed `workflow_api.run_workflow` execution of these
new examples is not qualified here; legacy PDF splitting still writes beside its
input. `web_scraping` and `download_data` remain deferred until an offline-fixture
strategy is defined. No licensed solver or external service is used by the examples.
