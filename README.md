# assetutilities

Shared engineering utilities for project configuration, file and YAML handling,
data processing, engineering calculations, unit conversions, visualization, and
automation workflows.

## Canonical Routing

Start with these maintained routing surfaces before changing code:

| Surface | Purpose |
|---|---|
| `AGENTS.md` | Worker entry point, commands, and issue-work boundaries. |
| `docs/README.md` | Canonical docs entry point and issue routing table. |
| `docs/maps/assetutilities-operator-map.md` | Module-by-module source, test, and docs map. |
| `docs/registry/module-routing.yaml` | Machine-readable module routing registry. |
| `MODULE_STRUCTURE.md` | Current package structure under `src/assetutilities/`. |

Broad inventories under `docs/ref/` and `docs/sub_*` are supporting material,
not routing authority. Confirm final paths through the canonical surfaces above.

## Package Layout

The package lives under `src/assetutilities/`.

| Area | Typical work |
|---|---|
| `engine.py`, `calculation.py`, `math_helpers.py` | Top-level orchestration, calculation dispatch, and math helpers. |
| `agent_os/` | Agent OS command and cross-repo integration helpers. |
| `base_configs/` | Shared YAML configuration templates. |
| `calculations/` | Engineering calculations such as riser, pipeline, fatigue, and lifecycle routines. |
| `cli/` | Command-line and slash-command helpers. |
| `common/` | File management, data, YAML, visualization, web scraping, and general shared helpers. |
| `constants/` | Materials, casing grades, seawater, and conversion constants. |
| `devtools/` | Developer command wrappers and modernization helpers. |
| `modules/` | Higher-level utility modules such as CSV, Excel, PDF, YAML, and zip helpers. |
| `units/` | Unit conversion, quantity, policy, traceability, and domain unit registries. |

## Development

Use `uv` for local commands:

```bash
uv sync --group dev
uv run python -m pytest tests
```

Targeted routing and hygiene checks:

```bash
uv run python -m pytest tests/docs/test_assetutilities_routing_contract.py tests/hygiene/test_no_backup_artifacts_tracked.py
bash scripts/hygiene/check-source-hygiene.sh
```

Do not commit backup, cache, runtime, generated-result, or scratch wrapper files
as trusted source. In particular, `*.bak` and `*.orig` files are ignored and the
hygiene gate fails if they are tracked.
