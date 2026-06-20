# ABOUTME: Tests for common/logging_setup.py — the loguru-based logging shim (issue #28).
# ABOUTME: Verifies run-log path/format preservation (loguru) and the stdlib fallback path.

import importlib
import logging

import pytest

from assetutilities.common import logging_setup


def _cfg(log_folder, level="INFO", file_name="run"):
    return {
        "default": {"log_level": level},
        "Analysis": {"log_folder": str(log_folder), "file_name": file_name},
    }


class TestModuleSurface:
    """The shim imports without loguru and exposes the expected names."""

    def test_logger_and_setup_exist(self):
        assert hasattr(logging_setup, "logger")
        assert callable(logging_setup.setup_logging)
        assert hasattr(logging_setup, "LOGURU_AVAILABLE")

    def test_logger_has_level_methods(self):
        for name in ("debug", "info", "warning", "error", "exception", "critical"):
            assert callable(getattr(logging_setup.logger, name))


class TestRunLogPreservation:
    """setup_logging writes the same run-log file the repo writes today."""

    def test_returns_cfg(self, tmp_path):
        cfg = _cfg(tmp_path / "logs")
        assert logging_setup.setup_logging(cfg) is cfg

    def test_creates_log_folder_and_file(self, tmp_path):
        pytest.importorskip("loguru")
        log_folder = tmp_path / "logs"
        cfg = _cfg(log_folder, file_name="myrun")
        logging_setup.setup_logging(cfg)
        logging_setup.logger.info("hello run-log")
        # loguru flushes on emit; the file lives at <log_folder>/<file_name>.log
        expected = log_folder / "myrun.log"
        assert expected.exists()
        # Clean up loguru sinks so other tests are not affected.
        logging_setup.logger.remove()
        content = expected.read_text(encoding="utf-8", errors="ignore")
        assert "hello run-log" in content

    def test_loguru_file_line_format_is_human_readable(self, tmp_path):
        pytest.importorskip("loguru")
        log_folder = tmp_path / "logs"
        cfg = _cfg(log_folder, file_name="fmt")
        logging_setup.setup_logging(cfg)
        logging_setup.logger.info("format check")
        logging_setup.logger.remove()
        line = (log_folder / "fmt.log").read_text(encoding="utf-8").strip()
        # Format: "MM/DD/YYYY HH:MM:SS AM/PM - <name> - INFO - <message>"
        assert " - INFO - format check" in line


class TestStdlibFallback:
    """When loguru is unavailable the shim still writes the run-log via stdlib."""

    def test_fallback_logger_writes_run_log(self, tmp_path, monkeypatch):
        # Force the no-loguru code path.
        monkeypatch.setattr(logging_setup, "LOGURU_AVAILABLE", False)
        monkeypatch.setattr(
            logging_setup, "logger", logging_setup._StdlibLoggerShim()
        )
        log_folder = tmp_path / "logs"
        cfg = _cfg(log_folder, file_name="fallback")
        try:
            logging_setup.setup_logging(cfg)
            logging_setup.logger.info("fallback run-log")
            expected = log_folder / "fallback.log"
            assert expected.exists()
            # Flush stdlib handlers, then read.
            for h in logging.root.handlers:
                h.flush()
            content = expected.read_text(encoding="utf-8", errors="ignore")
            assert "fallback run-log" in content
        finally:
            for h in logging.root.handlers[:]:
                logging.root.removeHandler(h)

    def test_stdlib_shim_bind_returns_self(self):
        shim = logging_setup._StdlibLoggerShim()
        assert shim.bind(user="x") is shim


def test_module_reimports_cleanly():
    # Re-importing must not raise (lazy loguru import lives inside setup_logging).
    importlib.reload(logging_setup)
