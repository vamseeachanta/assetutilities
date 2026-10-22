# Logging with loguru

Application configuration calls `set_logging(cfg)`, which delegates to
`logging_setup.setup_logging(cfg)`. Both entry points configure one loguru
pipeline. Existing standard-library emitters are intercepted into that
pipeline and continue to reach the run log without changing their imports.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Unified setup | 2026-10-20 | Document the shared setup and one-way interception so native and legacy emitters write once. |
| 1 | 2026-10-22 | Identify format, propagation and level changes so existing consumers can migrate explicitly. |

## Run-log behavior

| Property | Behavior |
|---|---|
| File | `<Analysis.log_folder>/<Analysis.file_name>.log` |
| Mode | Overwrite when a run is configured |
| Format | Timestamp, logger name, level and message, using a twelve-hour clock |
| Level | `default.log_level`, defaulting to `INFO` |
| Console | Standard output |
| No-file mode | `Analysis.log_to_file: false`; no log folder is created |

Each emission is written once per destination. Reconfiguring logging replaces
previous sinks. The library configures the process-wide logging root, as the
previous setup did; independent concurrent logging configurations need separate
processes or caller-managed logging.

## Emit messages

```python
from assetutilities.common.logging_setup import logger

logger.info("Process START")
logger.info("Rows processed: {}", count)
```

Loguru uses brace formatting for positional arguments. Existing stdlib logging
calls keep their percent-format semantics through the interception handler.
Do not configure additional output sinks inside workflow handlers.

Exception-local diagnostics and expanded backtraces are disabled for configured
sinks. Applications must still avoid including confidential values in message
text or exception messages.

## Compatibility

`set_logging`, `setup_logging`, `logger`, `InterceptHandler` and
`PropagateHandler` remain importable. `PropagateHandler` is retained for external
callers, but the library setup does not install it: installing both bridge
directions would create a loop. Direct loguru imports use the same shared logger.
When loguru cannot be imported, the shim uses standard-library logging with the
same destinations, level and no-file behavior.

The shared setup changes three earlier behaviors:

- Run logs from `set_logging` contain human-readable lines rather than serialized
  loguru JSON. Update JSON readers or add a caller-managed loguru sink with
  `serialize=True` after configuration when structured output is required.
- Native loguru records no longer propagate into named stdlib handlers, including
  pytest's `caplog` handler. Capture them with a loguru sink. Stdlib emitters still
  reach the configured run log through interception; do not install both bridge
  directions on the same records.
- `default.log_level` must name a stdlib-recognized level. Replace loguru-only
  `TRACE` or `SUCCESS` with a stdlib level such as `DEBUG` or `INFO`. Unknown
  levels raise `ValueError` before sinks are reconfigured.

The tests check single writes from both APIs, level filtering, reconfiguration,
no-file mode, human-readable logs and the fallback. See
[the core example](modules/core-hardening.md) for a complete workflow.

Source: [Loguru migration guide](https://loguru.readthedocs.io/en/stable/resources/migration.html),
accessed 2026-10-20, including standard logging integration and exception diagnostics.
