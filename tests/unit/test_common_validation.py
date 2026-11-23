# ABOUTME: Tests for common/validation.py — DataValidator class.
# ABOUTME: Covers validate_dataframe, generate_report, and helper methods.

import pandas as pd
import pytest

from assetutilities.common.validation import DataValidator


# ---------------------------------------------------------------------------
# DataValidator — validate_dataframe
# ---------------------------------------------------------------------------


class TestDataValidatorEmptyDataFrame:
    """Tests for empty DataFrame input."""

    def test_empty_df_returns_invalid(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame()

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["valid"] is False

    def test_empty_df_quality_score_zero(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame()

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["quality_score"] == 0.0

    def test_empty_df_has_issue_message(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame()

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert len(result["issues"]) > 0


class TestDataValidatorValidDataFrame:
    """Tests for clean DataFrames that should pass validation."""

    def test_clean_df_is_valid(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["valid"] is True

    def test_clean_df_high_quality_score(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["quality_score"] == pytest.approx(100.0)

    def test_clean_df_no_issues(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"x": [1, 2, 3]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["issues"] == []

    def test_result_has_total_rows(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["total_rows"] == 5

    def test_result_has_total_columns(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["total_columns"] == 3


class TestDataValidatorRequiredFields:
    """Tests for required_fields validation."""

    def test_missing_required_field_makes_invalid(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"name": ["Alice", "Bob"]})

        # Act
        result = validator.validate_dataframe(df, required_fields=["id"])

        # Assert
        assert result["valid"] is False

    def test_missing_required_field_reduces_quality_score(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"name": ["Alice"]})

        # Act
        result = validator.validate_dataframe(df, required_fields=["id"])

        # Assert
        assert result["quality_score"] < 100.0

    def test_all_required_fields_present_passes(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})

        # Act
        result = validator.validate_dataframe(df, required_fields=["id", "name"])

        # Assert
        assert result["valid"] is True

    def test_empty_required_fields_list_does_not_fail(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"id": [1]})

        # Act
        result = validator.validate_dataframe(df, required_fields=[])

        # Assert
        assert result["valid"] is True


class TestDataValidatorMissingData:
    """Tests for missing data detection."""

    def test_high_missing_data_is_invalid(self):
        # Arrange
        validator = DataValidator()
        # 50% missing — well above 30% threshold
        df = pd.DataFrame({"a": [1, None, None, None, None]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result["valid"] is False

    def test_no_missing_data_no_missing_entry_in_result(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert result.get("missing_data", {}) == {}

    def test_missing_data_percentages_recorded(self):
        # Arrange
        validator = DataValidator()
        # 2 out of 4 missing = 50%
        df = pd.DataFrame({"a": [1, None, None, None], "b": [1, 2, 3, 4]})

        # Act
        result = validator.validate_dataframe(df)

        # Assert
        assert "missing_data" in result
        assert "a" in result["missing_data"]
        assert result["missing_data"]["a"] == pytest.approx(0.75)

    def test_quality_score_floored_at_zero(self):
        # Arrange
        validator = DataValidator()
        # Massive missing data + missing required fields => score would go negative
        df = pd.DataFrame({"col": [None, None, None, None]})

        # Act
        result = validator.validate_dataframe(df, required_fields=["id", "name", "x"])

        # Assert
        assert result["quality_score"] >= 0.0


class TestDataValidatorDuplicates:
    """Tests for duplicate detection via unique_field."""

    def test_duplicate_unique_field_reduces_score(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"id": [1, 1, 2], "val": ["a", "b", "c"]})

        # Act
        result = validator.validate_dataframe(df, unique_field="id")

        # Assert
        assert result["quality_score"] < 100.0

    def test_no_duplicates_full_score_maintained(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})

        # Act
        result = validator.validate_dataframe(df, unique_field="id")

        # Assert
        assert result["quality_score"] == pytest.approx(100.0)

    def test_unique_field_not_in_df_skipped(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, 2]})

        # Act — 'id' is not in df; should not raise
        result = validator.validate_dataframe(df, unique_field="id")

        # Assert: no duplicate issues added
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# DataValidator — _check_missing_data
# ---------------------------------------------------------------------------


class TestCheckMissingData:
    """Tests for _check_missing_data helper method."""

    def test_no_missing_returns_empty_dict(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        # Act
        result = validator._check_missing_data(df)

        # Assert
        assert result == {}

    def test_partial_missing_returns_percentage(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, None], "b": [3, 4]})

        # Act
        result = validator._check_missing_data(df)

        # Assert
        assert "a" in result
        assert result["a"] == pytest.approx(0.5)
        assert "b" not in result

    def test_fully_missing_column_included(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [None, None, None]})

        # Act
        result = validator._check_missing_data(df)

        # Assert
        assert result["a"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# DataValidator — _get_quality_color
# ---------------------------------------------------------------------------


class TestGetQualityColor:
    """Tests for _get_quality_color helper method."""

    def test_high_score_returns_green(self):
        # Arrange
        validator = DataValidator()

        # Act / Assert
        assert validator._get_quality_color(90.0) == "green"
        assert validator._get_quality_color(80.0) == "green"

    def test_medium_score_returns_yellow(self):
        # Arrange
        validator = DataValidator()

        # Act / Assert
        assert validator._get_quality_color(70.0) == "yellow"
        assert validator._get_quality_color(60.0) == "yellow"

    def test_low_score_returns_red(self):
        # Arrange
        validator = DataValidator()

        # Act / Assert
        assert validator._get_quality_color(50.0) == "red"
        assert validator._get_quality_color(0.0) == "red"


# ---------------------------------------------------------------------------
# DataValidator — generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Tests for generate_report — returns a human-readable string."""

    def test_report_is_string(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, 2]})
        results = validator.validate_dataframe(df)

        # Act
        report = validator.generate_report(results)

        # Assert
        assert isinstance(report, str)

    def test_report_contains_pass_for_valid(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, 2]})
        results = validator.validate_dataframe(df)

        # Act
        report = validator.generate_report(results)

        # Assert
        assert "PASS" in report

    def test_report_contains_fail_for_invalid(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame()
        results = validator.validate_dataframe(df)

        # Act
        report = validator.generate_report(results)

        # Assert
        assert "FAIL" in report

    def test_report_contains_quality_score(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"x": [1, 2, 3]})
        results = validator.validate_dataframe(df)

        # Act
        report = validator.generate_report(results)

        # Assert
        assert "Quality Score" in report

    def test_report_mentions_issues_when_present(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"name": ["a", "b"]})
        results = validator.validate_dataframe(df, required_fields=["id"])

        # Act
        report = validator.generate_report(results)

        # Assert
        assert "Issues" in report

    def test_report_includes_missing_data_section(self):
        # Arrange
        validator = DataValidator()
        df = pd.DataFrame({"a": [1, None, None, None]})
        results = validator.validate_dataframe(df)

        # Act
        report = validator.generate_report(results)

        # Assert
        assert "Missing Data" in report
