# assetutilities Operator Map

Canonical routing map for common `assetutilities` issue work. This map is the
human-readable companion to `docs/registry/module-routing.yaml`.

| Module | Source path | Tests path | Related docs path | Typical issue labels | Key dependencies |
|---|---|---|---|---|---|
| `agent_os` | `src/assetutilities/agent_os/` | `tests/bash-setup/`, focused agent command tests when added | `docs/modules/agent-os/`, `docs/commands/` | `cat:automation`, `domain:repo-organization` | CLI helpers, cross-repo command conventions |
| `base_configs` | `src/assetutilities/base_configs/` | Config consumer tests under `tests/modules/` | `docs/README.md` | `cat:configuration`, `cat:maintenance` | YAML utilities, common file loading |
| `calculations` | `src/assetutilities/calculations/` | `tests/benchmarks/`, calculation-focused tests | `docs/README.md` | `cat:engineering-calculations`, `cat:engineering` | constants, units, common data helpers |
| `cli` | `src/assetutilities/cli/` | `tests/bash-setup/`, focused CLI tests when added | `docs/commands/` | `cat:automation`, `cat:harness` | agent_os, devtools |
| `common` | `src/assetutilities/common/` | `tests/unit/test_common_*.py`, `tests/modules/` | `docs/modules/` | `cat:engineering`, `cat:data-pipeline` | pandas, YAML, file system, visualization dependencies |
| `constants` | `src/assetutilities/constants/` | `tests/unit/test_constants.py`, `tests/test_casing_grades.py` | `docs/README.md` | `cat:engineering-calculations`, `cat:maintenance` | units, calculations |
| `devtools` | `src/assetutilities/devtools/` | focused devtool tests when added | `src/assetutilities/devtools/README.md` | `cat:maintenance`, `cat:harness` | pyproject, CLI entry points |
| `modules` | `src/assetutilities/modules/` | `tests/modules/`, related unit tests | `docs/modules/` | `cat:data-pipeline`, `cat:automation` | common helpers, pandas, Excel/YAML/zip dependencies |
| `units` | `src/assetutilities/units/` | `tests/unit/test_quantity.py`, `tests/unit/test_registry.py`, `tests/unit/test_traceability*.py` | `docs/README.md` | `cat:engineering-calculations`, `cat:engineering-methodology` | constants, sympy, pint-style quantity behavior |
| `workflow_api` | `src/assetutilities/workflow_api/` | `tests/workflow_api/` | `docs/README.md` | `cat:automation`, `cat:data-pipeline` | workflow engine, identity, artifact and publication helpers |

## Source-Hygiene Routing

Backup artifacts, local scratch scripts, cache files, generated reports, and
runtime files must not become routing authority. Use:

- `.gitignore` for ignore rules.
- `scripts/hygiene/check-source-hygiene.sh` for deterministic validation.
- `tests/hygiene/test_no_backup_artifacts_tracked.py` for pytest coverage.

## Structured report output

P6 Word and PDF output is implemented in
`src/assetutilities/common/reportgen/standard.py`, tested in
`tests/modules/reportgen/test_standard_report.py`, and documented in
`docs/modules/documentation/standard-report.md`. The neutral input example is
`examples/workflows/reportgen/standard-report.json`.

## Package release tooling

Release helpers live in `scripts/release/`, with tests in `tests/release/`
and setup and reuse instructions in `docs/sub_release/pypi.md`. The publishing
workflow is `.github/workflows/release.yml`.
