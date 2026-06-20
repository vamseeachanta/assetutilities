# Design: Switch `engine.py` dispatch to a Registry Pattern

Issue: [#29](https://github.com/vamseeachanta/assetutilities/issues/29) — *tech debt | switch engine to registry design pattern*

Status: design / migration plan (no refactor performed here)

## 1. Context & motivation

`engine.engine()` routes a parsed config to the right module handler using a long
`if / elif` chain keyed on `basename`. The repo already contains a working
**registry design pattern** in `common/reportgen` (the `ReportWriterRegistry`),
which the issue calls out as "similar / same as what engine is doing": it reads a
class name from config, looks it up in a registry, instantiates it, and runs it.

This doc maps that existing, proven pattern onto the engine dispatch and gives an
ordered, low-risk migration. Every code reference below was verified against the
working tree before writing.

## 2. Current state — how `engine.py` dispatches today

File: `src/assetutilities/engine.py`.

The basename is extracted at `engine.py:36-41`:

```python
if "basename" in cfg:
    basename = cfg["basename"]
elif "meta" in cfg:
    basename = cfg["meta"]["basename"]
else:
    raise ValueError("basename not found in cfg")
```

Routing is a hardcoded `if / elif` chain over `basename`, `engine.py:55-114`. Each
branch follows one of two shapes:

- **Eager-imported handler** — the class is imported at module top
  (`engine.py:5-17`), instantiated, and its `router`/`run` method called. E.g.
  `visualization` (`engine.py:63-65`), `file_management` (`engine.py:66-67`),
  `text_analytics` (`engine.py:77-79`), `data_exploration` (`engine.py:86-87`),
  `web_scraping` (`engine.py:89-91`), `download_data` (`engine.py:93-95`),
  `yaml_utilities`/`yml_utilities` (`engine.py:97-98`), `reportgen`
  (`engine.py:100-104`), `zip_utilities` (`engine.py:105-107`),
  `csv_utilities` (`engine.py:109-111`).
- **Lazy-imported handler** — the class is imported *inside* the branch to defer a
  heavy/optional dependency. E.g. `excel_utilities` (`engine.py:55-62`),
  `gitpython` (`engine.py:71-76`), `word_utilities` (`engine.py:80-85`).

The unmatched case raises at `engine.py:113-114`:

```python
else:
    raise (Exception(f"Analysis for basename: {basename} not found. ... FAIL"))
```

### Pain points

1. **Open/closed violation.** Adding a module means editing the chain in `engine.py`
   — the file imports ~13 subsystems (`engine.py:5-17`) and must know every handler.
2. **Inconsistent handler contract.** Some branches reassign the result
   (`cfg_base = ws.router(cfg_base)`, `engine.py:91`) while others discard it
   (`viz_comp.visualization_router(cfg_base)`, `engine.py:65`; `fm.router(cfg_base)`,
   `engine.py:67`). The "return the updated cfg" contract is not enforced, so the
   post-dispatch `save_cfg` (`engine.py:120`) sometimes saves a stale `cfg_base`.
3. **Method-name drift.** Most handlers expose `router(cfg)`, but the entry point
   name varies: `excel_utility_router` (`engine.py:62`),
   `visualization_router` (`engine.py:65`), `run` (`reportgen`, `engine.py:104`).
   The chain hardcodes each name; there is no uniform interface.
4. **Alias handling is ad-hoc.** `yaml_utilities` and `yml_utilities` are handled by
   one branch with an `or` (`engine.py:97`); other aliases would need more `or`s.
5. **No introspection.** There is no way to ask "what basenames are supported?"
   without reading the chain; error messages can't list valid options.

## 3. Target pattern — the reportgen writer registry

File: `src/assetutilities/common/reportgen/writers.py`.

The registry is a class holding a name→class dict, `writers.py:11-29`:

```python
class ReportWriterRegistry:
    """Registry for report writer implementations"""

    _writers = {}

    @classmethod
    def register(cls, writer_name: str, writer_class: type) -> None:
        if not issubclass(writer_class, ReportWriter):
            raise TypeError(...)
        cls._writers[writer_name] = writer_class
        logging.info(f"Registered writer: {writer_name}")

    @classmethod
    def get_writer(cls, writer_name: str) -> Optional[type]:
        return cls._writers.get(writer_name)
```

Registration is an **import-time side effect** at the bottom of each writer module:
`writers.py:201-202` registers the built-ins, and
`doris_writers.py:145-146` registers `DorisMarkdownWriter` / `DorisDocxWriter`.

Resolution is config-driven in `reportgen.py`: the class name is read from config
(`reportgen.py:45`), validated (`reportgen.py:51`, which calls
`ReportWriter.validate_writer_class`, `writers.py:52-61`), looked up
(`reportgen.py:58`, `ReportWriterRegistry.get_writer`), instantiated
(`reportgen.py:60`), and later run via a uniform `flush()` method
(`reportgen.py:69-71`). When the configured class is missing/invalid it **falls
back** to defaults instead of crashing (`reportgen.py:46-47`, `74-82`).

### Pattern elements to carry over

| reportgen element | engine equivalent |
|---|---|
| key = `report_writer_class` from config (`reportgen.py:45`) | key = `basename` from cfg (`engine.py:36-41`) |
| `ReportWriterRegistry._writers` dict (`writers.py:14`) | `EngineRegistry._handlers` dict |
| `register(name, class)` (`writers.py:16-24`) | `register(basename, handler)` |
| `get_writer(name)` (`writers.py:26-29`) | `get_handler(basename)` |
| import-time registration (`writers.py:201-202`, `doris_writers.py:145-146`) | import-time / decorator registration per module |
| uniform `flush()` interface (`writers.py:47-50`) | uniform `router(cfg) -> cfg` interface |
| graceful fallback (`reportgen.py:46-47`) | explicit error listing known basenames |

### Caveat observed in the source pattern (avoid in engine)

`doris_writers.py` is **not imported anywhere** in `src/` (the package
`__init__` imports only `decorator`, `dom`, `reportgen` — see
`reportgen/__init__.py:5-7`), so its `register` calls at `doris_writers.py:145-146`
never execute, yet `tests/modules/reportgen/reportgen-cfg-20in-docx.yml:30`
configures `report_writer_class: "DorisDocxWriter"`. Pure import-side-effect
registration only works if something imports the module. The engine registry must
guarantee its handler modules are imported (eager-import barrel, or an explicit
registration module) so no handler is "registered but unreachable".

## 4. Mapping — concrete design for an `EngineRegistry`

New module: `src/assetutilities/engine_registry.py` (sibling of `engine.py`).

### 4.1 Handler contract

Normalize on the dominant shape already in the chain — a callable that takes the
configured cfg and returns the (possibly mutated) cfg:

```python
# handler signature
Handler = Callable[[dict], dict]   # (cfg_base) -> cfg_base
```

Most existing entry points already match (`router(cfg_base)`); the registry adapts
the few that differ (e.g. reportgen's `run` returns `None`) with a thin lambda that
returns `cfg_base` so the engine's post-dispatch `save_cfg` (`engine.py:120`) always
gets a real cfg. This *also fixes pain point #2* (some branches today discard the
return value).

### 4.2 Registration API

```python
class EngineRegistry:
    _handlers: dict[str, Handler] = {}

    @classmethod
    def register(cls, *basenames: str):
        """Decorator: register a handler under one or more basenames (aliases)."""
        def deco(fn: Handler) -> Handler:
            for name in basenames:
                if name in cls._handlers:
                    logging.warning(f"engine handler for '{name}' overridden")
                cls._handlers[name] = fn
            return fn
        return deco

    @classmethod
    def get_handler(cls, basename: str) -> Handler | None:
        return cls._handlers.get(basename)

    @classmethod
    def basenames(cls) -> list[str]:
        return sorted(cls._handlers)
```

Variadic `*basenames` subsumes the `yaml_utilities`/`yml_utilities` alias
(`engine.py:97`) cleanly (pain point #4). A `basenames()` accessor gives the
introspection the chain lacks (pain point #5).

### 4.3 Handler definitions (preserving lazy imports)

Each handler is a small adapter that keeps the *exact* current behavior, including
deferred imports for heavy/optional deps (`excel`, `gitpython`, `word`):

```python
@EngineRegistry.register("excel_utilities")
def _excel(cfg):
    from assetutilities.modules.excel_utilities.excel_utilities import ExcelUtilities
    return ExcelUtilities().excel_utility_router(cfg)

@EngineRegistry.register("yaml_utilities", "yml_utilities")
def _yaml(cfg):
    return wwyaml.router(cfg)

@EngineRegistry.register("reportgen")
def _reportgen(cfg):
    from assetutilities.common.reportgen import reportgen
    reportgen.run(cfg)          # returns None today (reportgen.py:92-97)
    return cfg                  # normalize to the (cfg) -> cfg contract
```

This deliberately mirrors the reportgen registry's import-time registration
(`writers.py:201-202`) — but to avoid the `doris_writers` "registered-but-not-
imported" trap (Section 3 caveat), the registration module(s) are imported by
`engine.py` itself (Section 5, step 2), so registration is guaranteed to run.

### 4.4 Dispatch in `engine.py`

The chain at `engine.py:55-114` collapses to:

```python
handler = EngineRegistry.get_handler(basename)
if handler is None:
    raise Exception(
        f"Analysis for basename: {basename} not found "
        f"(known: {EngineRegistry.basenames()}). ... FAIL"
    )
cfg_base = handler(cfg_base)
```

This preserves the existing failure mode (`engine.py:113-114`) while improving the
message, and always reassigns `cfg_base` (fixing pain point #2). Everything before
(`engine.py:27-53`) and after (`engine.py:116-121`) the chain is unchanged.

### 4.5 Backward compatibility

- Public signature `engine(inputfile, cfg, config_flag)` is unchanged.
- Every existing `basename` keeps the same observable behavior and the same
  handler call; only the *lookup mechanism* changes.
- The `else`-raise contract is preserved (same exception type, richer message).
- Lazy imports remain lazy, so optional-dependency footprint is unchanged.

## 5. Migration steps (ordered, each independently testable)

The strangler approach — introduce the registry **alongside** the chain, migrate
handlers one at a time, then delete the chain.

1. **Add `engine_registry.py`** with `EngineRegistry` (register/get/basenames).
   No engine change yet. Test: unit test register→get round-trip + alias + unknown
   returns `None`. *Risk: none (additive).*

2. **Add a `_register_handlers` step and import it from `engine.py`.** Define the
   handler functions (Section 4.3) in `engine_registry.py` (or a sibling
   `engine_handlers.py`) and ensure `engine.py` imports that module so registration
   runs — explicitly avoiding the `doris_writers` not-imported trap (Section 3).
   Test: `EngineRegistry.basenames()` lists all current basenames.

3. **Dual-path dispatch behind the chain.** In `engine.py`, *before* the `if/elif`,
   try `handler = EngineRegistry.get_handler(basename)`; if found, call it and skip
   the chain; else fall through to the existing chain. Migrate handlers by simply
   *populating* the registry — start with the lowest-risk ones (`yaml_utilities`,
   `csv_utilities`, `zip_utilities`). Test per-handler: run that basename's existing
   template/yaml fixture and diff output vs. pre-change.

4. **Migrate the remaining handlers**, one commit each, including the lazy-import
   trio (`excel_utilities`, `gitpython`, `word_utilities`) and `reportgen`
   (verify the `run`→`return cfg` adapter). After each, the matching test in
   `tests/modules/...` must still pass. *Risk: per-handler, isolated.*

5. **Flip to registry-only dispatch.** Replace the `if/elif` body
   (`engine.py:55-114`) with the lookup+raise from Section 4.4. Delete the now-dead
   eager imports that exist *only* to feed the chain (`engine.py:5-17`), keeping any
   still used elsewhere in the module. Test: full `tests/` suite green.

6. **Deprecate/remove the chain remnants & document.** Remove dual-path scaffolding,
   update module docs, and (optional) add a `basenames()`-driven smoke test that
   every template's `basename` resolves to a handler.

Each step is a small commit and individually revertible; the codebase stays green
throughout because the chain remains the fallback until step 5.

## 6. Risks & open questions

**Risks**

- **Import-side-effect registration not running** (the `doris_writers.py:145-146`
  trap). Mitigation: `engine.py` explicitly imports the registration module
  (step 2); a `basenames()` smoke test asserts coverage.
- **Return-contract normalization.** Branches that today discard the router result
  (`engine.py:65,67,69,76,79,85`) will now have their return value reassigned to
  `cfg_base`. If any router returns `None`, `save_cfg` (`engine.py:120`) could see
  `None`. Mitigation: adapters return `cfg` explicitly when the underlying method
  returns `None` (as shown for reportgen).
- **Heavy-import regression.** Moving an eager import into a handler (or vice versa)
  could change optional-dependency behavior. Mitigation: preserve each branch's
  current import locality exactly (lazy stays lazy — Section 4.3).
- **Hidden ordering dependence.** The chain is evaluated top-down; if any two
  basenames overlap today they'd be order-sensitive. None observed, but the
  registry's duplicate-key warning (Section 4.2) surfaces accidental collisions.

**Open questions**

1. Decorator-based registration (Section 4.2) vs. an explicit registration table —
   the reportgen pattern uses explicit `register(...)` calls (`writers.py:201-202`).
   Should engine match that style exactly for consistency, or adopt the decorator?
2. Should the handler contract be a bare callable, or a small ABC (mirroring
   `ReportWriter`, `writers.py:32-50`) to enforce a `router(cfg) -> cfg` method?
3. Should aliasing live in the registry (variadic `register`) or be normalized
   upstream when `basename` is read (`engine.py:36-41`)?
4. Out of scope but adjacent: fixing the reportgen `doris_writers` not-imported bug
   (Section 3) — track separately if not already covered.
