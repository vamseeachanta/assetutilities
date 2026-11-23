# Plan: Complete loguru migration in set_logging (#28)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/28
- Tier: T2 (medium, in-scope; tech debt with concrete acceptance)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #28 calls for switching from Python's stdlib `logging` to `loguru`,
keeping color-coded output and richer diagnostic context, while preserving
the existing log-file behavior.

State on `main`:

- `pyproject.toml` already declares `loguru>=0.7.0,<1.0.0`.
- `src/assetutilities/common/set_logging.py` imports both `logging` and
  `loguru.logger` but the actual handler/formatter wiring is still on
  stdlib `logging.basicConfig` — the migration is half-done.
- Issue body checkboxes are all checked but the source contradicts the
  closure claim, so this plan re-opens the actual migration.

In-scope: rewrite `set_logging.py` so loguru is the single sink, log files
land in `cfg["Analysis"]["log_folder"]` with the same naming, and stdlib
`logging` calls in the rest of the codebase are routed via an
`InterceptHandler` so we don't have to rewrite every callsite at once.

Out-of-scope: changing the `cfg` schema for log levels; per-module log
level overrides; structured JSON logging.

## Plan

1. **Audit callers.** `git grep -nE "import logging|from logging|logger ?="`
   under `src/` to enumerate every callsite. Note which ones expect a
   `logging.Logger` instance and which already use the loguru `logger`.
2. **Rewrite `set_logging.py`.**
   - Remove `logging.basicConfig` entirely.
   - Configure `loguru.logger.remove()` then `loguru.logger.add(...)` for
     (a) stderr with color, (b) the `<log_folder>/<file_name>.log` file
     with rotation = `10 MB` and retention = `10 files`.
   - Install an `InterceptHandler(logging.Handler)` that forwards stdlib
     records into loguru, then `logging.basicConfig(handlers=[InterceptHandler()], level=0)`
     so legacy `logging.getLogger(...)` callers are captured transparently.
   - Map `cfg["default"]["log_level"]` to a loguru level string.
3. **Update `engine.py` and other entrypoints.** Replace `import logging`
   + `logger = logging.getLogger(__name__)` with `from loguru import logger`
   in the few hot-path entrypoints. Leave deeper callers on stdlib for
   now (the InterceptHandler covers them).
4. **Add a test.** `tests/unit/test_common_set_logging.py` already exists —
   extend it to assert: (a) calling `set_logging` creates the log file,
   (b) a stdlib `logging.getLogger("foo").info("x")` line lands in that
   file, (c) the loguru `logger.info("y")` line also lands in that file.
5. **Update docs.** Refresh `docs/sub_logging/logging.md` and
   `docs/sub_python/logging/logging.md` with the new pattern; remove
   stale stdlib-`logging` examples.
6. **Open PR.** Run full test suite locally; ensure no regression in
   `tests/`.

## Acceptance criteria

- [ ] `set_logging.py` uses loguru as the sole sink; no `logging.basicConfig`.
- [ ] Stdlib `logging` calls anywhere in `src/assetutilities/` still write
      to the configured log file (via InterceptHandler).
- [ ] `tests/unit/test_common_set_logging.py` covers both loguru and
      stdlib paths, both green.
- [ ] `docs/sub_logging/logging.md` reflects the loguru-first pattern.
- [ ] `uv run python -m pytest tests -q` green on PR branch.
- [ ] Issue #28 closed referencing merge commit.

## Open questions

- Rotation/retention defaults: `10 MB` / `10 files` is a guess. Confirm
  with maintainer or pull from any existing convention before merge.
- Do downstream repos (digitalmodel, energydata) rely on a specific log
  format string? If yes, mirror it in the loguru sink format.
