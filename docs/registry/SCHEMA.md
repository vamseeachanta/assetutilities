# AssetUtilities workflow registry schema (`schema_version: 2`)

> Canonical schema-of-record: `workspace-hub/docs/standards/WORKFLOW_REGISTRY_SCHEMA.md`
> (workspace-hub#3295). This file is the assetutilities-local companion. It documents the
> `result:` descriptor owned by workspace-hub#3282 and the invocation/resolver contract.

`docs/registry/workflows.yaml` declares `schema_version: 2` — one documented **additive
superset** (no v3 bump). Adding optional/reserved fields is backward-compatible, so rows
that omit them still validate.

## Reference resolver

`deckhand/src/deckhand/capability_smoke.py` is the **reference resolver** for this registry.
It reads the top-level `invocation:` key (`capability_smoke.py:231`) and performs
**`{input}`-only** substitution (`capability_smoke.py:232`) — it never substitutes `{pkg}`.
Therefore `invocation` MUST embed the literal package name.

## Top-level keys

| Key | Required | Notes |
|---|---|---|
| `schema_version` | yes | integer literal `2`. |
| `invocation` | yes | `"uv run python -m assetutilities {input}"` exactly. Embeds the literal package name; `{input}`-only substitution. |
| `repo`, `issue` | no | legacy/optional metadata. |
| `workflows` | yes | list of workflow rows. |

## Workflow row fields

| Field | Required | Notes |
|---|---|---|
| `id` | yes | unique workflow id. |
| `basename` | yes | engine dispatch key. |
| `input` | yes | example input path (preserved per workspace-hub#3284 discovery). |
| `outputs` | yes | **documentary** CLI-path filenames — see "Result location" below. |
| `test` | yes | the runnable example command. |
| `runtime` | recommended | `fast`/`offline`/… ; `requires-license` carries the license-gate (workspace-hub#3284). |
| `version`/`status`/`latest` | optional | Deckhand routing triple (absent ⇒ `1`/`stable`/latest). |
| `result` | optional | **#3282-owned** result-location descriptor (below). |
| `request_schema`/`response_schema` | reserved | structured (untyped) slots **reserved by workspace-hub#3295**; no `str` invariant; not populated here. |

## Result location (`result:` descriptor — workspace-hub#3282)

```yaml
result:
  kind: files          # "files" (default) | "in_memory"
  key: <cfg key>       # for kind: in_memory — cfg[key] is the payload
  outputs: [...]       # for kind: files — DOCUMENTARY count/reference only
```

- **`kind: files`** (default) — `run_workflow` discovers the **actually emitted** files by
  **globbing the injected embed root** (`<root_folder>/results/`), NOT by matching the row's
  `outputs:` names. The embed-path `file_name` is **cfg-derived** (e.g. `data_exploration` →
  `data_exploration_FST1.csv`), so the real emitted names differ from the registry's CLI-path
  `outputs:` (`input_FST*.csv`). The `save_cfg` cfg-dump `<file_name>.yml` is excluded from the
  emitted-file list and the content hash. `outputs:` degrades to an expected-count cross-check.
- **`kind: in_memory`** — the payload is `cfg[key]`. **Supported but currently unexercised**:
  all registry rows are file-writing (`cfg[basename]` holds paths/echoes input, not data), so
  no row sets `kind: in_memory` yet.

## Determinism / provenance fields (disclaimer)

The envelope determinism fields (`input_hash`, `result_hash`, `reproducible`,
`provenance.code_version`) are computed by `assetutilities.workflow_api` (#3282) at runtime —
they are NOT registry fields. The golden-determinism harness + volatile-field spec are
workspace-hub#3283 (deferred to Wave 2).
