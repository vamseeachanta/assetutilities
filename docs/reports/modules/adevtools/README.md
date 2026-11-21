# Devtools dependency collection analysis

[index.html](index.html) contains the generated analysis;
[changes.json](changes.json) supplies its change panel.

## Plan-lite

- Reporting scope: demonstrate requirement-file discovery, string collection and
  configuration generation on two controlled examples. Explain duplicate and
  cross-group counts, parser limits and input preservation.
- Validation approach: compare all ten table values and both headline counts
  with literal arithmetic, compare generated dependency arrays with the collected
  sets, and rebuild the committed HTML and change panel exactly. Run the devtools
  and CI-selector tests, including report-input routing and reused-directory
  regressions. The Playwright check tests the chart's accessible name after
  rendering and both selections when Google Chrome can launch.
- Acceptance limits: counts and rebuild comparisons require exact equality.
  Evidence covers the supplied input strings and the chart-name check only.
  Package resolution, installation acceptance, performance, comment saving and
  other browsers remain unevaluated. Quoted markers and continuation lines can
  produce invalid TOML; hash options and alternate package spellings remain
  literal strings.

## Rebuild and checks

Use Python 3.11 or later. Supply a new directory outside the checkout for each
rebuild; existing case directories are rejected to preserve their contents.

```sh
python scripts/reporting/generate_devtools_report.py --work-dir <fresh-scratch>
```

The focused checks require pytest, pytest-asyncio and Playwright. The browser
check also requires Google Chrome; a launch error is reported as a skip and does
not establish browser acceptance.

```sh
python -m pytest tests/modules/devtools tests/ci/test_select_test_targets.py -q -rA -p no:cacheprovider --basetemp=<fresh-test-scratch>
```

A local pass does not replace a completed hosted devtools check. Test totals and
browser availability belong in the validation record for the tested revision.
