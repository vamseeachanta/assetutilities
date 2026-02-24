# ABOUTME: Tests for common/set_logging.py — PropagateHandler and InterceptHandler.
# ABOUTME: Covers the handler classes without invoking the full set_logging() I/O path.

import logging
import tempfile

import pytest

from assetutilities.common.set_logging import InterceptHandler, PropagateHandler


class TestPropagateHandler:
    """PropagateHandler.emit routes records through the standard logging hierarchy."""

    def test_propagate_handler_is_logging_handler(self):
        # Assert
        assert issubclass(PropagateHandler, logging.Handler)

    def test_emit_does_not_raise_for_info_record(self):
        # Arrange
        handler = PropagateHandler()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        # Act / Assert — should not raise
        handler.emit(record)

    def test_emit_does_not_raise_for_warning_record(self):
        # Arrange
        handler = PropagateHandler()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="warning message",
            args=(),
            exc_info=None,
        )

        # Act / Assert
        handler.emit(record)

    def test_emit_does_not_raise_for_error_record(self):
        # Arrange
        handler = PropagateHandler()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="error message",
            args=(),
            exc_info=None,
        )

        # Act / Assert
        handler.emit(record)

    def test_emit_passes_record_to_named_logger(self):
        # Arrange
        handler = PropagateHandler()
        captured = []

        target_logger = logging.getLogger("capture_test_logger")
        mock_handler = logging.handlers_memory = None

        class CapturingHandler(logging.Handler):
            def emit(self, record):
                captured.append(record.getMessage())

        cap = CapturingHandler()
        target_logger.addHandler(cap)
        target_logger.propagate = False

        record = logging.LogRecord(
            name="capture_test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="captured msg",
            args=(),
            exc_info=None,
        )

        try:
            # Act
            handler.emit(record)

            # Assert
            assert "captured msg" in captured
        finally:
            target_logger.removeHandler(cap)
            target_logger.propagate = True


class TestInterceptHandler:
    """InterceptHandler bridges standard logging to loguru."""

    def test_intercept_handler_is_logging_handler(self):
        # Assert
        assert issubclass(InterceptHandler, logging.Handler)

    def test_emit_does_not_raise_for_info_record(self):
        # Arrange
        handler = InterceptHandler()
        record = logging.LogRecord(
            name="test.intercept",
            level=logging.INFO,
            pathname="test_file.py",
            lineno=42,
            msg="intercept test",
            args=(),
            exc_info=None,
        )

        # Act / Assert — should not raise
        handler.emit(record)

    def test_emit_handles_debug_level(self):
        # Arrange
        handler = InterceptHandler()
        record = logging.LogRecord(
            name="test.intercept",
            level=logging.DEBUG,
            pathname="test_file.py",
            lineno=1,
            msg="debug message",
            args=(),
            exc_info=None,
        )

        # Act / Assert
        handler.emit(record)

    def test_emit_handles_unknown_level_name_gracefully(self):
        # Arrange — use a numeric level that loguru may not recognise by name
        handler = InterceptHandler()
        record = logging.LogRecord(
            name="test.intercept",
            level=logging.CRITICAL,
            pathname="test_file.py",
            lineno=5,
            msg="critical message",
            args=(),
            exc_info=None,
        )

        # Act / Assert
        handler.emit(record)
