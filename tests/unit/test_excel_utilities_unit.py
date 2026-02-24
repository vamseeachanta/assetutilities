# ABOUTME: Unit tests for modules/excel_utilities/excel_utilities.py
# ABOUTME: Covers router, get_data stub, and _evaluate_simple_formula pure logic.

import pytest

# Skip the entire module if openpyxl or PIL are not available,
# since the module-level imports require them.
pytest.importorskip("openpyxl")
pytest.importorskip("PIL")

from assetutilities.modules.excel_utilities.excel_utilities import ExcelUtilities


# ---------------------------------------------------------------------------
# ExcelUtilities.__init__
# ---------------------------------------------------------------------------


class TestExcelUtilitiesInit:
    """ExcelUtilities can be instantiated without arguments."""

    def test_init_returns_instance(self):
        # Act
        eu = ExcelUtilities()

        # Assert
        assert isinstance(eu, ExcelUtilities)


# ---------------------------------------------------------------------------
# ExcelUtilities.get_data
# ---------------------------------------------------------------------------


class TestGetData:
    """ExcelUtilities.get_data is a pass stub — coverage only."""

    def test_get_data_returns_none(self):
        # Arrange
        eu = ExcelUtilities()
        cfg = {}

        # Act
        result = eu.get_data(cfg)

        # Assert — stub returns None
        assert result is None


# ---------------------------------------------------------------------------
# ExcelUtilities.router
# ---------------------------------------------------------------------------


class TestRouter:
    """ExcelUtilities.router dispatches on task key."""

    def test_router_returns_cfg(self):
        # Arrange
        eu = ExcelUtilities()
        cfg = {"task": "custom_calculation"}

        # Act
        result = eu.router(cfg)

        # Assert
        assert result is cfg

    def test_router_unknown_task_returns_cfg_unchanged(self):
        # Arrange
        eu = ExcelUtilities()
        cfg = {"task": "nonexistent_task"}

        # Act
        result = eu.router(cfg)

        # Assert — no matching branch but cfg returned
        assert result is cfg


# ---------------------------------------------------------------------------
# ExcelUtilities._evaluate_simple_formula — pure logic branch
# ---------------------------------------------------------------------------


class TestEvaluateSimpleFormula:
    """ExcelUtilities._evaluate_simple_formula pure-Python branches."""

    def test_non_string_input_returned_unchanged(self):
        # Arrange
        eu = ExcelUtilities()

        # Act
        result = eu._evaluate_simple_formula(42, wb=None)

        # Assert — non-string value is returned as-is
        assert result == 42

    def test_non_formula_string_returned_unchanged(self):
        # Arrange
        eu = ExcelUtilities()

        # Act
        result = eu._evaluate_simple_formula("plain_text", wb=None)

        # Assert
        assert result == "plain_text"

    def test_depth_limit_returns_none(self):
        # Arrange
        eu = ExcelUtilities()

        # Act — depth > 10 triggers early return
        result = eu._evaluate_simple_formula("=SOMETHING", wb=None, depth=11)

        # Assert
        assert result is None

    def test_formula_without_sheet_ref_returns_formula_string(self):
        # Arrange
        eu = ExcelUtilities()

        # Act — simple same-sheet ref like =B9 (no sheet ref, no parens)
        result = eu._evaluate_simple_formula("=B9", wb=None)

        # Assert — same-sheet refs are returned as-is
        assert result == "=B9"

    def test_formula_with_paren_returns_empty_string(self):
        # Arrange: formula with ( but no ! — falls through to return ""
        eu = ExcelUtilities()

        # Use a mock object that doesn't have sheetnames to avoid any attribute access
        class NoopWb:
            sheetnames = []

        # Act — a function-style formula with no sheet ref returns ""
        result = eu._evaluate_simple_formula("=SUM(A1:A10)", wb=NoopWb())

        # Assert
        assert result == ""

    def test_unknown_formula_returns_empty_string(self):
        # Arrange
        eu = ExcelUtilities()

        class NoopWb:
            sheetnames = []

        # Act — formula with ! but sheet not in workbook
        result = eu._evaluate_simple_formula("=unknownsheet!A1", wb=NoopWb())

        # Assert — sheet not found, returns "" via exception fallback
        assert result == ""
