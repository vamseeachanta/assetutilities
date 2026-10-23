"""One logging pipeline for native loguru and legacy stdlib emitters.

Both setup_logging and set_logging configure this pipeline. Stdlib records
flow into loguru; no reverse propagation sink is installed, avoiding loops and
multiple writes. Without loguru, a stdlib fallback preserves the run-log API.
"""

from __future__ import annotations

import logging
import os
import sys

# Human-readable run-log line format (mirrors the stdlib handler in set_logging).
# loguru uses {time}/{level}/{message}; map the stdlib format onto loguru tokens.
_STDLIB_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_STDLIB_DATEFMT = "%m/%d/%Y %I:%M:%S %p"
_LOGURU_FILE_FORMAT = "{time:MM/DD/YYYY hh:mm:ss A} - {name} - {level} - {message}"


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
        from loguru import logger as _loguru_logger
    except ImportError:  # pragma: no cover - exercised only without loguru
        return _StdlibLoggerShim()
    return _loguru_logger


# Module-level logger: loguru when present, stdlib shim otherwise.
logger = _make_logger()

# Whether the active ``logger`` is a real loguru logger.
LOGURU_AVAILABLE = not isinstance(logger, _StdlibLoggerShim)


def _reset_root_handlers():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        if getattr(handler, "_assetutilities_handler", False):
            handler.close()


def _configure_stdlib_fallback(logfilename, level: str) -> None:
    """Configure one stdlib sink per destination when loguru is absent."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if logfilename is not None:
        handlers.append(logging.FileHandler(logfilename, mode="w", encoding="utf-8"))
    for handler in handlers:
        handler._assetutilities_handler = True
    logging.basicConfig(
        level=level,
        format=_STDLIB_FILE_FORMAT,
        datefmt=_STDLIB_DATEFMT,
        handlers=handlers,
        force=True,
    )


def setup_logging(cfg: dict):
    """Write each message once to stdout and optionally the configured run log.

    Analysis.log_to_file defaults to True. False creates no log directory.
    Reconfiguration replaces earlier sinks and truncates the current run log.
    Exception-local diagnostics are disabled so logs do not expose local values.
    """
    level = _resolve_level(cfg)
    numeric_level = logging.getLevelName(level)
    if numeric_level == f"Level {level}":
        raise ValueError(f"Invalid log level: {level}")
    level = logging.getLevelName(numeric_level)
    logfilename = (
        _resolve_log_file(cfg) if cfg["Analysis"].get("log_to_file", True) else None
    )
    _reset_root_handlers()

    if not LOGURU_AVAILABLE:
        _configure_stdlib_fallback(logfilename, level)
        logger.info("Logging started successfully (stdlib fallback) ...")
        return cfg

    logger.remove()
    # Loguru migration guide, "Replacing exception()": disable traceback
    # expansion and variable inspection for application run logs.
    sink_options = {"level": level, "backtrace": False, "diagnose": False}
    logger.add(sys.stdout, **sink_options)
    if logfilename is not None:
        logger.add(
            logfilename,
            format=_LOGURU_FILE_FORMAT,
            mode="w",
            encoding="utf-8",
            **sink_options,
        )

    # One-way interception follows Loguru's standard logging integration.
    from assetutilities.common.set_logging import InterceptHandler

    intercept = InterceptHandler()
    intercept._assetutilities_handler = True
    logging.root.addHandler(intercept)
    logging.root.setLevel(numeric_level)
    logger.info("Logging started successfully ...")
    return cfg
