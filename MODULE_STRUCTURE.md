# assetutilities Module Structure

Updated: 2026-04-27

This file is the current package map for `src/assetutilities/`. It is a
human-readable companion to `docs/maps/assetutilities-operator-map.md` and
`docs/registry/module-routing.yaml`.

## Directory Structure

```text
assetutilities/
+-- AGENTS.md
+-- README.md
+-- MODULE_STRUCTURE.md
+-- docs/
|   +-- README.md
|   +-- maps/
|   |   +-- assetutilities-operator-map.md
|   +-- registry/
|       +-- module-routing.yaml
+-- scripts/
|   +-- hygiene/
|       +-- check-source-hygiene.sh
+-- src/
|   +-- assetutilities/
|       +-- __init__.py
|       +-- __main__.py
|       +-- engine.py
|       +-- calculation.py
|       +-- math_helpers.py
|       +-- `agent_os/`
|       +-- `base_configs/`
|       +-- `calculations/`
|       +-- `cli/`
|       +-- `common/`
|       +-- `constants/`
|       +-- `devtools/`
|       +-- `modules/`
|       +-- `units/`
+-- tests/
```

## Package Areas

| Area | Role | Primary tests | Related docs |
|---|---|---|---|
| `agent_os/` | Agent OS command, specification, and cross-repo helpers. | `tests/bash-setup/`, targeted agent command tests when added | `docs/modules/agent-os/` |
| `base_configs/` | Shared base YAML configuration templates. | Config consumers under `tests/modules/` | `docs/README.md` |
| `calculations/` | Engineering calculations for casing, drilling risers, lifecycle cost, pipelines, and fatigue. | `tests/benchmarks/`, `tests/test_casing_grades.py`, calculation-focused tests | `docs/README.md` |
| `cli/` | Command-line and slash-command helper scripts. | `tests/bash-setup/` and CLI-specific tests when added | `docs/commands/` |
| `common/` | Common file, data, YAML, visualization, web scraping, logging, and validation helpers. | `tests/unit/test_common_*.py`, `tests/modules/` | `docs/modules/` |
| `constants/` | Casing grades, conversions, materials, and seawater constants. | `tests/unit/test_constants.py`, `tests/test_casing_grades.py` | `docs/README.md` |
| `devtools/` | Developer tooling for dependency modernization and command propagation. | `tests/unit/` or focused devtool tests when added | `src/assetutilities/devtools/README.md` |
| `modules/` | CSV, data exploration, Excel, PDF, YAML, zip, and test utility modules. | `tests/modules/`, `tests/unit/test_common_yml_utilities.py` | `docs/modules/` |
| `units/` | Units, quantities, policies, traceability, and domain registries. | `tests/unit/test_quantity.py`, `tests/unit/test_registry.py`, `tests/unit/test_traceability*.py` | `docs/README.md` |

## File Placement Rules

| Work type | Canonical location | Validation route |
|---|---|---|
| Shared helper code | `src/assetutilities/common/` | Add or update `tests/unit/test_common_*.py` or focused `tests/modules/` coverage. |
| Engineering calculations | `src/assetutilities/calculations/` | Add or update calculation tests and benchmark tests where appropriate. |
| Unit conversion behavior | `src/assetutilities/units/` | Add or update `tests/unit/test_quantity.py`, `tests/unit/test_registry.py`, or related unit tests. |
| Constants and lookup tables | `src/assetutilities/constants/` | Add or update constants-specific unit tests. |
| CLI and command helpers | `src/assetutilities/cli/` or `src/assetutilities/agent_os/` | Add focused CLI or bash-setup tests. |
| Developer tooling | `src/assetutilities/devtools/` | Add focused devtool tests and document user-facing behavior. |
| Canonical docs routing | `docs/README.md`, `docs/maps/`, `docs/registry/` | Run `tests/docs/test_assetutilities_routing_contract.py`. |
| Source hygiene | `.gitignore`, `scripts/hygiene/`, `tests/hygiene/` | Run `tests/hygiene/test_no_backup_artifacts_tracked.py` and `scripts/hygiene/check-source-hygiene.sh`. |

## Hygiene Rules

- Do not track `*.bak` or `*.orig` files.
- Do not treat broad docs inventories, generated reports, or raw reference
  folders as issue routing authority.
- Keep source, tests, and docs path changes reflected in
  `docs/maps/assetutilities-operator-map.md` and
  `docs/registry/module-routing.yaml`.
