# Offline domain tests and live-data opt-in

The default pytest selection excludes `live_data` and `pdf_integration` tests.
The web-scraping and download domains retain offline coverage while external
service checks require an explicit selection.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-19 | Add offline examples and live-data selection guidance to remove network-dependent quarantine entries. |

## Default and explicit selection

Run the domains without contacting external services:

```sh
uv run pytest tests/modules/web_scraping tests/modules/download_data
```

The expected result is four offline cases passing and three live cases
deselected. The default expression in `pytest.ini` is
`not live_data and not pdf_integration`. Mark new external-service tests with
`@pytest.mark.live_data`; keep offline tests unmarked.

To inspect the live selection without executing it:

```sh
uv run pytest tests/modules/web_scraping tests/modules/download_data --collect-only -m live_data
```

Removing `--collect-only` intentionally executes those live workflows. A command
line `-m` replaces the default expression, including its PDF exclusion; use a
complete expression when selecting another subset. This follows pytest's
[option precedence](https://docs.pytest.org/en/stable/example/simple.html#how-to-change-command-line-options-defaults)
and [marker selection](https://docs.pytest.org/en/stable/example/markers.html).

## Worked offline example

The executable example is
[`test_download_and_process_zip_mocked`](../../tests/modules/download_data/test_zip_offline.py).
Its inputs are an in-memory ZIP containing a directory `well_data/` and the
member `well_data/sample.csv`, with this synthetic content:

```csv
a,b
1,2
```

A fake HTTP response supplies the ZIP for
`https://example.invalid/APDRawData.zip`. The method checks HTTP status, skips
the directory member, reads the CSV, and writes it to pytest's temporary output
directory. The hand-derived filename is the archive stem, an underscore, the
member stem, and `.csv`: `APDRawData_sample.csv`. The answer is exactly that
file, with the same header and data row. These are synthetic test values, with
no physical units or engineering acceptance limits.

```sh
uv run pytest tests/modules/download_data/test_zip_offline.py
```

The companion failure case verifies that an HTTP error propagates without
writing output. Both cases reject unmocked HTTP requests. The router tests
replace both scraper backends and check that only the selected backend receives
the original configuration.

## Limits

This coverage establishes selection, routing and ZIP conversion behavior. It
does not establish external service availability or validate the live engine
configuration. The download router's list-versus-mapping URL shape and the
scraper's `input_settings` configuration remain separate defects. Live tests
can still fail until those defects are resolved.

The generic quarantine mechanism remains available for unrelated defects; the
network entries associated with
[issue 99](https://github.com/vamseeachanta/assetutilities/issues/99) are removed.
