# PDF, CSV, text comparison and repository workflows

The five formerly deferred basenames have offline examples. PDF and CSV inputs
are authored by a small Python generator; no sample data files are committed.
No engineering coefficients or acceptance limits are used.

## Revision history

| Revision | Date | Change and reason |
| --- | --- | --- |
| Initial | 2026-10-19 | Add worked examples for the newly implemented registry workflows. |

## Run the examples

From the repository root, prepare synthetic inputs:

```sh
uv run python examples/workflows/prepare_deferred_inputs.py
uv run python -m assetutilities examples/workflows/read_pdf/input.yml
uv run python -m assetutilities examples/workflows/edit_pdf/input.yml
uv run python -m assetutilities examples/workflows/csv_utilities/input.yml
uv run python -m assetutilities examples/workflows/text_analytics/input.yml
uv run python -m assetutilities examples/workflows/gitpython/input.yml
```

Preparation preserves existing files and writes only under the examples'
ignored `outputs/` directories. Other generated results and logs are ignored.
The PDF paths resolve from the process working directory, as in the existing
PDF API. CSV and Git paths resolve from the input YAML directory. Each example
replaces the legacy base configuration's complete input lists.

## Inputs, method and answer

| Workflow | Input | Method | Expected answer |
| --- | --- | --- | --- |
| `read_pdf` | Authored PDF pages containing `alpha page` and `beta page` | Extract one-based pages 1 and 2 independently | Two UTF-8 text files containing those respective strings |
| `edit_pdf` | The same PDF; inclusive ranges `[1,1]` and `[2,2]` | Copy each selected page | Two single-page PDFs containing `alpha page` and `beta page` respectively |
| `csv_utilities` | Latin-1 text `name,value`, then `café,7` and `tea,9` | Try UTF-8; on decode failure retry Latin-1; write UTF-8 without a dataframe index | Two records, two columns (`name`, `value`), with the accented text preserved |
| `text_analytics` | `[alpha,beta,alpha]` and `[beta,gamma]` | Ordered unique intersection and differences | Common `[beta]`; first only `[alpha]`; second only `[gamma]`; raw input sizes 3 and 2 |
| `gitpython` | Current checkout, at most 5 recent commits | Read branch, HEAD, porcelain status and log | YAML report with checkout-dependent facts; write operations explicitly skipped |

All expected counts follow by enumeration of the displayed synthetic input.
The CSV numeric strings are arbitrary demonstration records, not engineering
input or sourced material. The Git log length is a configurable display choice.

`read_pdf` returns a list of YAML-serializable summaries (`label`, `page`,
`output_file`, `n_chars`). Output names include the input entry index to avoid
collisions when labels repeat; label punctuation is replaced with underscores.
An explicit `file_index` still selects a single entry and returns a one-item
list. Invalid page positions raise `ValueError` before writing output. Without
`Analysis.result_folder`, direct PDF calls write beside the PDF under `results/`.

CSV accepts legacy `txt_file` as an alias for `input_file`, optional `delimiter`,
`encoding`, and `nrows`. An explicit encoding is honored; fallback occurs only
when encoding is omitted. Summaries record the encoding actually used, delimiter,
column names, row count and source. Parse errors are reported without retrying.

Text inputs must be lists of strings. Duplicate entries count toward the raw
input sizes but appear once in comparison results, preserving first occurrence.
All comparisons are computed regardless of legacy `analysis.match/subset` flags.

Git reports support detached HEADs, unborn repositories, and repository
subdirectories. `max_count` must be a nonnegative integer; zero requests no log.
Legacy `common_cfg.commit/push/clone` flags never enable writes. Optional Git
locks are disabled during status collection to preserve index bytes. Reports
contain repository facts and commit subjects; review them before sharing.

## Sources and limits

- [PyPDF2 3.0.0: Extract Text from a PDF](https://pypdf2.readthedocs.io/en/3.0.0/user/extract-text.html)
  describes indexed page extraction and the limitations of PDF text recovery.
- [pandas: read_csv API](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html)
  defines delimiter, encoding and row-limit options.
- [GitPython: tutorial](https://gitpython.readthedocs.io/en/stable/tutorial.html)
  describes repository discovery, detached HEAD and commit iteration.
- [Git: environment variables](https://git-scm.com/docs/git#Documentation/git.txt-codeGITOPTIONALLOCKScode)
  defines disabling optional operations such as index refresh.

PDF extraction is text-only, without OCR. Tabula and Camelot remain optional
backends; neither Java nor native table extraction is exercised by these
examples. Direct table-backend helpers keep their dataframe/table return types;
workflow dispatch converts them to records for configuration serialization.
Git operations that mutate a repository and network-backed scraping/download
workflows remain outside this change.
