# Logging migration to loguru (issue #28)

assetutilities is moving from Python's stdlib `logging` to
[loguru](https://loguru.readthedocs.io/) for color-coded console output and
richer diagnostic context, **without changing the run-log files** the library
writes today.

## What ships

- **`src/assetutilities/common/logging_setup.py`** — the loguru-based setup
  shim. Exposes a `logger` and `setup_logging(cfg)`.
- **`src/assetutilities/engine.py`** — first module migrated as proof
  (`logging.info(...)` → `logger.info(...)`).
- This guide for converting the remaining ~33 modules.

`common/set_logging.py` is **unchanged** and still wired into
`ApplicationManager`; loguru and stdlib `logging` coexist during the migration.

## Run-log preservation (the non-negotiable part)

Issue #28 requires loguru messages to land in the existing default run-log
files. The shim reproduces the exact behavior of the legacy stdlib handler:

| Property   | Legacy (`set_logging`)                                  | Shim (`logging_setup.setup_logging`)         |
|------------|---------------------------------------------------------|----------------------------------------------|
| File path  | `<Analysis.log_folder>/<Analysis.file_name>.log`        | identical                                    |
| File mode  | `filemode="w"` (overwrite per run)                      | `mode="w"`                                   |
| Line format| `%(asctime)s - %(name)s - %(levelname)s - %(message)s`<br>datefmt `%m/%d/%Y %I:%M:%S %p` | loguru `{time:MM/DD/YYYY hh:mm:ss A} - {name} - {level} - {message}` (same shape) |
| Level      | `cfg["default"]["log_level"]`                           | identical                                    |
| Console    | `StreamHandler(sys.stdout)`                             | `logger.add(sys.stdout)` (loguru colorizes)  |

The shim also re-attaches `set_logging.PropagateHandler` so records flow back
into the stdlib hierarchy — modules still using `logging.getLogger(__name__)`
keep emitting into the same run log while they are migrated.

## No hard dependency on import

`loguru` is declared in `pyproject.toml` (`loguru>=0.7.0,<1.0.0`). Even so, the
shim **imports loguru lazily** and falls back to a stdlib-backed `logger`
(`_StdlibLoggerShim`) if loguru is missing, so `import logging_setup` never
breaks and tests run without the dependency. `LOGURU_AVAILABLE` reports which
path is active.

## How to migrate a module

1. Replace the stdlib import:
   ```python
   import logging
   ```
   with the shim:
   ```python
   from assetutilities.common.logging_setup import logger
   ```
2. Convert call sites (the API is the same):
   - `logging.info(msg)`     → `logger.info(msg)`
   - `logging.debug(msg)`    → `logger.debug(msg)`
   - `logging.warning(msg)`  → `logger.warning(msg)`
   - `logging.error(msg)`    → `logger.error(msg)`
   - `logging.exception(msg)`→ `logger.exception(msg)`
   - `logging.getLogger(__name__)` → just use the shared `logger`
     (loguru has a single global logger; per-module logger objects are not
     needed). The record's module/function context is captured automatically.
3. **Do not** call `logging.basicConfig(...)` in migrated modules. Run-log
   configuration is centralized in `setup_logging(cfg)` /
   `ApplicationManager`.
4. loguru uses brace-style lazy formatting; f-strings keep working, so
   `logger.info(f"{x}")` is fine. For lazy args you may also use
   `logger.info("value={}", x)`.
5. Run that module's tests.

## Migration order suggestion

Start with leaf/entry modules that only *emit* logs (done: `engine.py`), then
modules that *configure* logging. Once all emitters use `logger`,
`set_logging.set_logging` can be replaced by `logging_setup.setup_logging` at
the single call site in `ApplicationManager`, and `set_logging` retired.

## What is left

All other modules under `src/` still importing `logging` (see
`grep -rl "import logging" src/`). They keep working unchanged thanks to the
`PropagateHandler` bridge; migrate them incrementally using the steps above.
