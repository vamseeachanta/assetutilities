# assetutilities

> *Everyday complex engineering — made deterministically simple.*

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

Broad inventories under `docs/sub_*` are supporting material,
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

After syncing the dev tools, run `uv run pre-commit install`. Check
`git config --get core.hooksPath`: it must be unset, since a custom value silently
diverts Git away from installed hooks. The secret scanner reads the repo-local
`.gitleaks.toml`; the empty linter baseline is also in-repo at
`config/quality/bandit-baseline-assetutilities.json` and suppresses no findings.
The same secret scanner runs in CI on pull request changes.

Targeted routing and hygiene checks:

```bash
uv run python -m pytest tests/docs/test_assetutilities_routing_contract.py tests/hygiene/test_no_backup_artifacts_tracked.py
bash scripts/hygiene/check-source-hygiene.sh
```

Do not commit backup, cache, runtime, generated-result, or scratch wrapper files
as trusted source. In particular, `*.bak` and `*.orig` files are ignored and the
hygiene gate fails if they are tracked.

## Large and cold files

Large and cold non-source files live in a content-addressed cold-data store; see
`data-manifest/MANIFEST.tsv`. Original input data belongs in its owning private
repository. Client or project originals never go into this public repository.

Set `ACE_DATA_ROOT` to the data root for a local store, or set both `ACE_DATA_HOST`
and `ACE_DATA_ROOT` for an SSH-accessible store. No machine-specific defaults are
provided. Linux and Git Bash on Windows can use the same Python command:

```bash
python scripts/fetch_data.py --list
python scripts/fetch_data.py 'docs/sub_mathcad/*'
python scripts/fetch_data.py --all
python scripts/fetch_data.py --verify --all
```

Restoration verifies size and SHA-256 and refuses to overwrite tracked files.
With no reachable store, fetching prints a visible message and changes nothing.
Restored originals are ignored; compact fixtures occupy separate tracked paths.

Under the repository's lean-data rule, non-source files over 1 MB without code or test references move
to the store; referenced files unchanged for 90 days move with fetch on demand.
Files under 1 MB stay unless explicitly superseded, re-downloadable, or private.
The pre-commit hook blocks added files over 1,000 KB.
