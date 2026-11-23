# ABOUTME: Loguru-based logging setup shim for assetutilities (issue #28).
# ABOUTME: Reproduces the existing run-log FILE behavior; lazy-imports loguru with a stdlib fallback.
"""Loguru-based logging setup shim.

This module is the forward-looking replacement for the stdlib `logging`
configuration performed by ``common.set_logging.set_logging``. It exposes a
single :data:`logger` object and a :func:`setup_logging` function that
reproduces *exactly* the run-log file the repo writes today:

* file path  : ``<log_folder>/<file_name>.log``
* file mode  : ``w`` (truncate/overwrite per run — matches ``logging.basicConfig(filemode="w")``)
* line format: ``MM/DD/YYYY HH:MM:SS AM - <name> - <LEVEL> - <message>``
  (the human-readable format the stdlib handler wrote, *not* loguru's default)
* level      : driven by ``cfg["default"]["log_level"]``

Backward compatibility / no hard dependency on import
-----------------------------------------------------
``loguru`` is declared in ``pyproject.toml`` and is the intended runtime
dependency. However, importing this module must never fail if loguru happens
to be absent (e.g. a stripped test environment). We therefore:

* import loguru lazily inside :func:`setup_logging` (not at module import), and
* fall back to a thin stdlib-``logging`` shim (:data:`logger`) that supports the
  same ``.info()/.debug()/...`` call surface when loguru is unavailable.

Existing ``logging``-based code keeps working: loguru records are propagated
back into the stdlib hierarchy via a ``PropagateHandler`` (re-used from
``set_logging``) so module-level ``logging.getLogger(__name__)`` loggers still
emit. This module does not remove or alter ``set_logging``; both can coexist
during the migration.
"""

from __future__ import annotations

import logging
import os
import sys

# Human-readable run-log line format (mirrors the stdlib handler in set_logging).
# loguru uses {time}/{level}/{message}; map the stdlib format onto loguru tokens.
_STDLIB_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_STDLIB_DATEFMT = "%m/%d/%Y %I:%M:%S %p"
_LOGURU_FILE_FORMAT = (
    "{time:MM/DD/YYYY hh:mm:ss A} - {name} - {level} - {message}"
)


def _resolve_log_file(cfg: dict) -> str:
    """Return the run-log file path from cfg, creating the log folder.

    Mirrors ``set_logging``: ``<cfg['Analysis']['log_folder']>/<file_name>.log``.
    """
    analysis = cfg["Analysis"]
    log_folder = analysis["log_folder"]
    os.makedirs(log_folder, exist_ok=True)
    return os.path.join(log_folder, analysis["file_name"] + ".log")


def _resolve_level(cfg: dict) -> str:
    """Return the upper-cased log level string from cfg (default INFO)."""
    return str(cfg.get("default", {}).get("log_level", "INFO")).upper()


class _StdlibLoggerShim:
    """Minimal stdlib-backed fallback exposing a loguru-like call surface.

    Only used when ``loguru`` cannot be imported. Supports the common level
    methods plus ``bind`` (returns self) so callers can use ``logger.info(...)``
    identically whether or not loguru is installed.
    """

    def __init__(self, name: str = "assetutilities") -> None:
        self._log = logging.getLogger(name)

    def bind(self, **_kwargs):  # loguru API parity — no-op binding
        return self

    def debug(self, msg, *a, **k):
        self._log.debug(msg, *a, **k)

    def info(self, msg, *a, **k):
        self._log.info(msg, *a, **k)

    def warning(self, msg, *a, **k):
        self._log.warning(msg, *a, **k)

    def error(self, msg, *a, **k):
        self._log.error(msg, *a, **k)

    def exception(self, msg, *a, **k):
        self._log.exception(msg, *a, **k)

    def critical(self, msg, *a, **k):
        self._log.critical(msg, *a, **k)


def _make_logger():
    """Return the loguru logger if available, else a stdlib shim.

    Imported lazily so module import never requires loguru.
    """
    try:
        from loguru import logger as _loguru_logger  # noqa: PLC0415
    except Exception:  # pragma: no cover - exercised only without loguru
        return _StdlibLoggerShim()
    return _loguru_logger


# Module-level logger: loguru when present, stdlib shim otherwise.
logger = _make_logger()

# Whether the active ``logger`` is a real loguru logger.
LOGURU_AVAILABLE = not isinstance(logger, _StdlibLoggerShim)


def _configure_stdlib_fallback(logfilename: str, level: str) -> None:
    """Configure stdlib logging to write the run-log file (loguru absent path)."""
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=_STDLIB_FILE_FORMAT,
        datefmt=_STDLIB_DATEFMT,
        filename=logfilename,
        filemode="w",
        force=True,
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def setup_logging(cfg: dict):
    """Configure loguru (or a stdlib fallback) to write the repo run-log file.

    Reproduces the run-log path/format/overwrite behavior of
    ``common.set_logging.set_logging`` so downstream consumers see the same
    ``<log_folder>/<file_name>.log`` output.

    Parameters
    ----------
    cfg:
        Application config dict. Must contain ``cfg["Analysis"]["log_folder"]``
        and ``cfg["Analysis"]["file_name"]``. ``cfg["default"]["log_level"]`` is
        optional (defaults to ``INFO``).

    Returns
    -------
    The same ``cfg`` (for call-site parity with ``set_logging``).
    """
    level = _resolve_level(cfg)
    logfilename = _resolve_log_file(cfg)

    if not LOGURU_AVAILABLE:
        # No loguru: write the run-log via stdlib so behavior is preserved.
        _configure_stdlib_fallback(logfilename, level)
        logger.info("Logging started successfully (stdlib fallback) ...")
        return cfg

    # Reset stdlib root handlers so the human-readable file format is the one
    # loguru writes (avoids the prior double-write of a JSON-serialized file).
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger.remove()
    # Console sink (colorized by loguru when attached to a TTY).
    logger.add(sys.stdout, level=level)
    # Run-log FILE sink — human-readable, overwrite per run (mode="w").
    logger.add(
        logfilename,
        level=level,
        format=_LOGURU_FILE_FORMAT,
        mode="w",
    )

    # Keep stdlib-`logging`-based modules working during the migration:
    # propagate loguru records into the stdlib hierarchy.
    from assetutilities.common.set_logging import PropagateHandler  # noqa: PLC0415

    logger.add(PropagateHandler(), format="{message}")

    logger.info("Logging started successfully ...")
    return cfg
