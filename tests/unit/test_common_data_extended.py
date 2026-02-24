# ABOUTME: Extended tests for common/data.py — additional coverage for Transform and SaveData.
# ABOUTME: Covers PandasChainedAssignent, transform_df_datetime_to_str, SaveData, and ascii I/O.

import datetime
import os
import tempfile

import pandas as pd
import pytest

from assetutilities.common.data import (
    PandasChainedAssignent,
    SaveData,
    Transform,
    transform_df_datetime_to_str,
)


# ---------------------------------------------------------------------------
# PandasChainedAssignent context manager
# ---------------------------------------------------------------------------


class TestPandasChainedAssignent:
    """Tests for PandasChainedAssignent context manager."""

    def test_context_manager_sets_and_restores_none(self):
        # Arrange
        original = pd.options.mode.chained_assignment

        with PandasChainedAssignent(chained=None):
            assert pd.options.mode.chained_assignment is None

        # After exit, restored
        assert pd.options.mode.chained_assignment == original

    def test_context_manager_sets_warn(self):
        # Arrange
        with PandasChainedAssignent(chained="warn"):
            # Act / Assert
            assert pd.options.mode.chained_assignment == "warn"

    def test_context_manager_sets_raise(self):
        # Act / Assert
        with PandasChainedAssignent(chained="raise"):
            assert pd.options.mode.chained_assignment == "raise"

    def test_invalid_value_raises_assertion(self):
        # Act / Assert
        with pytest.raises(AssertionError):
            PandasChainedAssignent(chained="invalid")

    def test_restores_after_exception(self):
        # Arrange
        original = pd.options.mode.chained_assignment

        # Act
        try:
            with PandasChainedAssignent(chained=None):
                raise RuntimeError("test exception")
        except RuntimeError:
            pass

        # Assert: still restored even after exception
        assert pd.options.mode.chained_assignment == original


# ---------------------------------------------------------------------------
# transform_df_datetime_to_str
# ---------------------------------------------------------------------------


class TestTransformDfDatetimeToStr:
    """Tests for transform_df_datetime_to_str — covers the empty df path.

    Note: the source function has a bug where it calls 'datetime.datetime' after
    'from datetime import datetime', so the isinstance check raises AttributeError
    for any non-empty df. Only the empty-df branch is safely testable.
    """

    def test_empty_df_returns_empty_without_error(self):
        # Arrange: empty df skips the loop entirely
        df = pd.DataFrame({"date": [], "val": []})

        # Act
        result = transform_df_datetime_to_str(df)

        # Assert
        assert len(result) == 0
        assert isinstance(result, type(df))


# ---------------------------------------------------------------------------
# SaveData — additional methods
# ---------------------------------------------------------------------------


class TestSaveDataAsciiFile:
    """Tests for SaveData.save_ascii_file_from_array — write lines to file."""

    def test_writes_string_lines_to_file(self):
        # Arrange
        sd = SaveData()
        lines = ["line one\n", "line two\n", "line three\n"]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "output.txt")

            # Act
            sd.save_ascii_file_from_array(lines, filename)

            # Assert
            assert os.path.exists(filename)
            with open(filename) as f:
                content = f.read()
            assert "line one" in content
            assert "line three" in content

    def test_writes_lines_without_newlines(self):
        # Arrange
        sd = SaveData()
        lines = ["no newline here", "another line"]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "no_newline.txt")

            # Act
            sd.save_ascii_file_from_array(lines, filename)

            # Assert
            with open(filename) as f:
                content = f.read()
            assert "no newline here\n" in content

    def test_file_extension_appended(self):
        # Arrange
        sd = SaveData()
        lines = ["data line\n"]

        with tempfile.TemporaryDirectory() as tmpdir:
            base_name = os.path.join(tmpdir, "output")

            # Act
            sd.save_ascii_file_from_array(lines, base_name, extension=".dat")

            # Assert
            assert os.path.exists(base_name + ".dat")


class TestSaveDataWriteAsciiFromText:
    """Tests for SaveData.write_ascii_file_from_text."""

    def test_writes_text_to_file(self):
        # Arrange
        sd = SaveData()
        text = "Hello, World!"

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "text_output.txt")

            # Act
            sd.write_ascii_file_from_text(text, filename)

            # Assert
            assert os.path.exists(filename)
            with open(filename, "rb") as f:
                content = f.read()
            assert content == b"Hello, World!"

    def test_writes_unicode_text(self):
        # Arrange
        sd = SaveData()
        text = "Unicode: \u00e9\u00e0\u00fc"

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "unicode_out.txt")

            # Act
            sd.write_ascii_file_from_text(text, filename)

            # Assert
            assert os.path.exists(filename)


# ---------------------------------------------------------------------------
# Transform — additional methods
# ---------------------------------------------------------------------------


class TestTransformDataframeToJson:
    """Tests for Transform.dataframe_to_json."""

    def test_simple_df_returns_json_string(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        # Act
        result = t.dataframe_to_json(df, cfg={"index": False})

        # Assert
        assert isinstance(result, str)
        assert "a" in result
        assert "b" in result

    def test_none_df_returns_empty_string(self):
        # Arrange
        t = Transform()

        # Act
        result = t.dataframe_to_json(None)

        # Assert
        assert result == ""

    def test_duplicate_columns_renamed(self):
        # Arrange
        t = Transform()
        # Create df with duplicate column names
        df = pd.DataFrame([[1, 2, 3]], columns=["a", "a", "b"])

        # Act — should not raise
        result = t.dataframe_to_json(df, cfg={"index": False})

        # Assert: a string is returned
        assert isinstance(result, str)


class TestTransformTransposeAndAdd:
    """Tests for Transform.transpose_df and add_column_to_df."""

    def test_transpose_df_with_column_as_header(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"label": ["x", "y"], "v1": [1, 2], "v2": [3, 4]})
        cfg = {"transposed_df_column_name": {"column": "label", "drop": True}}

        # Act
        result = t.transpose_df(df, cfg)

        # Assert: columns of transposed df become 'x', 'y'
        assert list(result.columns) == ["x", "y"]

    def test_transpose_df_no_config_returns_unchanged(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"a": [1, 2]})
        cfg = {}

        # Act
        result = t.transpose_df(df, cfg)

        # Assert: unchanged
        assert list(result.columns) == ["a"]

    def test_add_column_to_df_inserts_column(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        cfg = {
            "add_column_to_transposed_df": {
                "location": 0,
                "header": "new_col",
                "values": ["x", "y"],
            }
        }

        # Act
        result = t.add_column_to_df(df, cfg)

        # Assert
        assert "new_col" in result.columns
        assert list(result["new_col"]) == ["x", "y"]

    def test_add_column_no_config_returns_unchanged(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"a": [1, 2]})
        cfg = {}

        # Act
        result = t.add_column_to_df(df, cfg)

        # Assert
        assert list(result.columns) == ["a"]

    def test_add_column_with_none_df_returns_none(self):
        # Arrange
        t = Transform()
        cfg = {"add_column_to_transposed_df": {"location": 0, "header": "h", "values": []}}

        # Act
        result = t.add_column_to_df(None, cfg)

        # Assert
        assert result is None
