# assetutilities Docs

This is the canonical documentation entry point for issue routing in
`assetutilities`. Use it with `AGENTS.md`, `README.md`,
`MODULE_STRUCTURE.md`, `docs/maps/assetutilities-operator-map.md`, and
`docs/registry/module-routing.yaml`.

## Issue Routing Table

| Issue type | Source path | Tests path | Docs path |
|---|---|---|---|
| calculations | `src/assetutilities/calculations/`, `src/assetutilities/calculation.py` | `tests/benchmarks/`, focused calculation tests | `docs/README.md`, `docs/maps/assetutilities-operator-map.md` |
| file and YAML utilities | `src/assetutilities/common/`, `src/assetutilities/modules/yml_utilities/` | `tests/unit/test_common_*.py`, `tests/modules/yml_utilities/` | `docs/modules/`, `docs/modules/yml_utilities/` |
| unit conversion | `src/assetutilities/units/`, `src/assetutilities/constants/` | `tests/unit/test_quantity.py`, `tests/unit/test_registry.py`, `tests/unit/test_constants.py` | `docs/README.md`, `docs/registry/module-routing.yaml` |
| CLI and agent commands | `src/assetutilities/cli/`, `src/assetutilities/agent_os/` | `tests/bash-setup/`, focused CLI tests when added | `docs/commands/`, `docs/modules/agent-os/` |
| data processing and exploration | `src/assetutilities/modules/data_exploration/`, `src/assetutilities/common/data*.py` | `tests/modules/data_exploration/`, common data unit tests | `docs/modules/` |
| visualization | `src/assetutilities/common/visualization*.py` | `tests/unit/test_visualization*.py`, `tests/modules/visualization/` | `docs/modules/visualization/` |
| developer tooling | `src/assetutilities/devtools/`, `scripts/` | focused devtool or script tests | `src/assetutilities/devtools/README.md` |

## Curated Routing Surfaces

These files are trusted routing surfaces:

- `AGENTS.md`
- `README.md`
- `docs/README.md`
- `MODULE_STRUCTURE.md`
- `docs/maps/assetutilities-operator-map.md`
- `docs/registry/module-routing.yaml`
- `scripts/hygiene/check-source-hygiene.sh`

Use these surfaces to choose source, tests, and docs paths for issue work.

## Raw Inventory And Supporting Material

The following paths are raw inventory or supporting references. They can help
with discovery, but they are not final routing authority:

- `docs/ref/`
- `docs/sub_data/`
- `docs/sub_hardware/`
- generated test result directories under `tests/modules/**/results/`

If raw inventory conflicts with a curated routing surface, follow the curated
surface and update it if it is stale.

## Hygiene Rules

- Do not track `*.bak` or `*.orig` files.
- Do not add cache, runtime, generated-result, or local scratch files to trusted
  routing surfaces.
- Run `bash scripts/hygiene/check-source-hygiene.sh` before pushing routing or
  source-hygiene changes.
- Run `uv run python -m pytest tests/docs/test_assetutilities_routing_contract.py tests/hygiene/test_no_backup_artifacts_tracked.py`
  for focused validation.
