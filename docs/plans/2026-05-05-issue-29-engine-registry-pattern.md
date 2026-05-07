# Plan: Switch engine.py to registry design pattern (#29)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/29
- Tier: T2 (medium, in-scope, refactor with downstream blast radius)
- Repo: assetutilities
- Status: plan-review

## Context

`src/assetutilities/engine.py` is the dispatcher used by all assetutilities
YAML-driven runs. Today it is a long if/elif chain that imports each
module and calls a hard-coded entrypoint based on `basename`. Issue #29
notes that another internal project (reportgen / writers.py / doris_writer.py
by Siva) uses a registry pattern: writer class names are read from a YAML
config, the registry resolves the class, the `run()` method is invoked.

Goal: refactor `engine.py` so handlers are looked up via a registry. New
modules register themselves; `engine` no longer needs to know each
basename in advance.

In-scope: introduce a `Registry` (dict of basename → callable) plus a
decorator-based registration API; convert the current if/elif handlers
to registered entries; preserve the public signature
`engine(inputfile=None, cfg=None, config_flag=True) -> dict`.

Out-of-scope: changing the YAML schema; changing how downstream repos
import `engine`; entry-point–based plugin discovery (defer).

## Plan

1. **Inventory current handlers.** Read `src/assetutilities/engine.py`
   end-to-end and catalog every `if basename == "..."` branch with the
   target module + callable. Output the catalog as a table in the PR
   description.
2. **Add `src/assetutilities/registry/handler_registry.py`.** Implement a
   small class with `.register(basename: str)` decorator + `.dispatch(basename, cfg)`
   resolver + `__contains__`. Keep it dict-backed; no fancy lookup.
3. **Register existing handlers.** For each catalogued handler, add a
   thin module-level call (or decorator on the handler function) that
   registers it. Modules already imported lazily inside if/elif branches
   should remain lazily imported — register a callable that performs
   the import on first dispatch, to preserve startup cost.
4. **Replace dispatcher.** Rewrite the if/elif body of `engine()` as a
   single `cfg_base = registry.dispatch(basename, cfg_base)` call.
   Raise `KeyError` with a clear message listing registered basenames
   when the basename is unknown.
5. **Add tests.** New `tests/unit/test_engine_registry.py` covering:
   register + dispatch happy path; unknown basename raises with helpful
   message; lazy import is not triggered until dispatch.
6. **Smoke-test downstream.** Run a representative basename end-to-end
   (e.g., `csv_utilities` or `yml_utilities`) via an existing
   integration test under `tests/`. No behavior change expected.
7. **Open PR.** Document the registry contract in
   `docs/modules/engine_registry.md` and link from the module-routing doc.

## Acceptance criteria

- [ ] `engine.py` body is reduced to config + `registry.dispatch(...)` and
      no longer contains the if/elif chain.
- [ ] All previously supported basenames still dispatch correctly
      (verified by existing integration tests).
- [ ] Unknown basename raises `KeyError` with a list of registered
      handlers in the message.
- [ ] `tests/unit/test_engine_registry.py` green; full suite green.
- [ ] Public `engine(inputfile, cfg, config_flag)` signature unchanged;
      no downstream repo edits required.
- [ ] Issue #29 closed referencing merge commit.

## Open questions

- Should registration happen at import time (current modules `__init__.py`)
  or via an explicit `register_all()` called once at engine startup?
  Default: explicit `register_all()` to keep import side-effects bounded.
- How do we handle two modules trying to register the same basename?
  Default: `register` raises `ValueError` on collision; can override with
  `replace=True` for tests.
