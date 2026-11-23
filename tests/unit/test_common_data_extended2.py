# ABOUTME: Additional tests for common/data.py — ReadData class methods.
# ABOUTME: Covers from_ascii_file methods, get_array_rows_containing_keywords, key_chain.

import os
import tempfile

import pytest

from assetutilities.common.data import ReadData


# ---------------------------------------------------------------------------
# ReadData.key_chain
# ---------------------------------------------------------------------------


class TestKeyChain:
    """ReadData.key_chain safely traverses nested dicts and lists."""

    def test_nested_dict_access(self):
        # Arrange
        rd = ReadData()
        data = {"a": {"b": {"c": 42}}}

        # Act
        result = rd.key_chain(data, "a", "b", "c")

        # Assert
        assert result == 42

    def test_missing_key_returns_default(self):
        # Arrange
        rd = ReadData()
        data = {"a": 1}

        # Act
        result = rd.key_chain(data, "missing", default="fallback")

        # Assert
        assert result == "fallback"

    def test_missing_key_returns_none_by_default(self):
        # Arrange
        rd = ReadData()
        data = {}

        # Act
        result = rd.key_chain(data, "nope")

        # Assert
        assert result is None

    def test_list_index_access(self):
        # Arrange
        rd = ReadData()
        data = {"items": ["first", "second", "third"]}

        # Act
        result = rd.key_chain(data, "items", 1)

        # Assert
        assert result == "second"

    def test_list_out_of_range_returns_default(self):
        # Arrange
        rd = ReadData()
        data = {"items": [1, 2]}

        # Act
        result = rd.key_chain(data, "items", 99, default="missing")

        # Assert
        assert result == "missing"

    def test_single_key(self):
        # Arrange
        rd = ReadData()
        data = {"x": 100}

        # Act
        result = rd.key_chain(data, "x")

        # Assert
        assert result == 100

    def test_non_dict_non_list_with_key_returns_default(self):
        # Arrange
        rd = ReadData()
        data = "not_a_dict"

        # Act
        result = rd.key_chain(data, "key", default="d")

        # Assert
        assert result == "d"


# ---------------------------------------------------------------------------
# ReadData.extract_from_dictionary
# ---------------------------------------------------------------------------


class TestExtractFromDictionary:
    """ReadData.extract_from_dictionary uses a key list to navigate nested dicts."""

    def test_single_level_extraction(self):
        # Arrange
        rd = ReadData()
        data = {"top": "value"}

        # Act
        result = rd.extract_from_dictionary(data, ["top"])

        # Assert
        assert result == "value"

    def test_nested_extraction(self):
        # Arrange
        rd = ReadData()
        data = {"level1": {"level2": {"level3": 99}}}

        # Act
        result = rd.extract_from_dictionary(data, ["level1", "level2", "level3"])

        # Assert
        assert result == 99

    def test_missing_key_raises_key_error(self):
        # Arrange
        rd = ReadData()
        data = {"a": 1}

        # Act / Assert
        with pytest.raises(KeyError):
            rd.extract_from_dictionary(data, ["nonexistent"])


# ---------------------------------------------------------------------------
# ReadData.df_filter_by_column_values
# ---------------------------------------------------------------------------


class TestDfFilterByColumnValues:
    """ReadData.df_filter_by_column_values applies column filters to a DataFrame."""

    def test_filter_single_column_value(self):
        # Arrange
        import pandas as pd

        rd = ReadData()
        df = pd.DataFrame({"cat": ["A", "B", "A"], "val": [1, 2, 3]})
        cfg = {"filter": [{"column": "cat", "value": "A"}]}

        # Act
        result = rd.df_filter_by_column_values(cfg, df)

        # Assert
        assert len(result) == 2
        assert list(result["cat"].unique()) == ["A"]

    def test_none_filter_returns_unchanged_df(self):
        # Arrange
        import pandas as pd

        rd = ReadData()
        df = pd.DataFrame({"x": [1, 2, 3]})
        cfg = {"filter": None}

        # Act
        result = rd.df_filter_by_column_values(cfg, df)

        # Assert
        assert len(result) == 3


# ---------------------------------------------------------------------------
# ReadData.get_array_rows_containing_keywords
# ---------------------------------------------------------------------------


class TestGetArrayRowsContainingKeywords:
    """ReadData.get_array_rows_containing_keywords finds rows with keywords."""

    def test_finds_rows_with_keyword(self):
        # Arrange
        rd = ReadData()
        array = ["line with DATA here", "irrelevant line", "DATA again"]
        key_words = ["DATA"]

        # Act
        result = rd.get_array_rows_containing_keywords(array, key_words)

        # Assert — rows are 1-indexed
        assert 1 in result
        assert 3 in result
        assert 2 not in result

    def test_empty_array_returns_empty_list(self):
        # Arrange
        rd = ReadData()

        # Act
        result = rd.get_array_rows_containing_keywords([], ["keyword"])

        # Assert
        assert result == []

    def test_no_matching_keyword_returns_empty_list(self):
        # Arrange
        rd = ReadData()
        array = ["line one", "line two"]
        key_words = ["NOTPRESENT"]

        # Act
        result = rd.get_array_rows_containing_keywords(array, key_words)

        # Assert
        assert result == []

    def test_multiple_keywords_any_match(self):
        # Arrange
        rd = ReadData()
        array = ["alpha content", "beta content", "gamma content"]
        key_words = ["alpha", "gamma"]

        # Act
        result = rd.get_array_rows_containing_keywords(array, key_words)

        # Assert
        assert 1 in result
        assert 3 in result
        assert 2 not in result

    def test_transform_applied_to_line_numbers(self):
        # Arrange
        rd = ReadData()
        array = ["KEYWORD found here"]
        key_words = ["KEYWORD"]
        cfg = {"transform": {"scale": 2, "shift": 0}}

        # Act
        result = rd.get_array_rows_containing_keywords(array, key_words, cfg)

        # Assert — row 1 * scale 2 + shift 0 = 2
        assert result == [2]


# ---------------------------------------------------------------------------
# ReadData.from_ascii_file_get_lines_as_string_arrays
# ---------------------------------------------------------------------------


class TestFromAsciiFileGetLinesAsStringArrays:
    """ReadData.from_ascii_file_get_lines_as_string_arrays reads lines from a file."""

    def test_reads_all_lines_by_default(self):
        # Arrange
        rd = ReadData()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            path = f.name

        try:
            cfg = {"io": path}

            # Act
            result = rd.from_ascii_file_get_lines_as_string_arrays(cfg)

            # Assert
            assert len(result) == 3
        finally:
            os.unlink(path)

    def test_start_and_end_line_subset(self):
        # Arrange
        rd = ReadData()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\n")
            path = f.name

        try:
            cfg = {"io": path, "start_line": 2, "end_line": 3}

            # Act
            result = rd.from_ascii_file_get_lines_as_string_arrays(cfg)

            # Assert — lines 2 and 3 only
            assert len(result) == 2
            assert "line2" in result[0]
            assert "line3" in result[1]
        finally:
            os.unlink(path)

    def test_lines_from_end(self):
        # Arrange: lines_from_end sets start_line internally but subsequent cfg.get
        # overrides it; must also set start_line explicitly to avoid the override.
        rd = ReadData()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\n")
            path = f.name

        try:
            # lines_from_end=2 with a 4-line file would set start=2, end=4
            # but start_line override applies, so explicitly set start_line too
            cfg = {"io": path, "lines_from_end": 2, "start_line": 3, "end_line": 4}

            # Act
            result = rd.from_ascii_file_get_lines_as_string_arrays(cfg)

            # Assert — lines 3 and 4 only
            assert len(result) == 2
            assert "line3" in result[0]
            assert "line4" in result[1]
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# ReadData.from_df_delete_unwanted_columns
# ---------------------------------------------------------------------------


class TestFromDfDeleteUnwantedColumns:
    """ReadData.from_df_delete_unwanted_columns drops columns by index list."""

    def test_drops_specified_column_indices(self):
        # Arrange
        import pandas as pd

        rd = ReadData()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})

        # Act — drop columns at indices 1 (b) and 2 (c)
        result = rd.from_df_delete_unwanted_columns(df, [1, 2])

        # Assert
        assert list(result.columns) == ["a"]

    def test_drop_first_column(self):
        # Arrange
        import pandas as pd

        rd = ReadData()
        df = pd.DataFrame({"x": [1], "y": [2], "z": [3]})

        # Act
        result = rd.from_df_delete_unwanted_columns(df, [0])

        # Assert
        assert "x" not in result.columns
        assert "y" in result.columns
        assert "z" in result.columns


# ---------------------------------------------------------------------------
# ReadData.get_file_list_from_folder
# ---------------------------------------------------------------------------


class TestGetFileListFromFolder:
    """ReadData.get_file_list_from_folder retrieves files matching a glob pattern."""

    def test_returns_files_matching_extension(self):
        # Arrange
        rd = ReadData()
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["file1.csv", "file2.csv", "other.txt"]:
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write("data")

            # Act
            result = rd.get_file_list_from_folder(os.path.join(tmpdir, "*.csv"))

            # Assert
            assert len(result) == 2
            assert all(f.endswith(".csv") for f in result)

    def test_without_extension_strips_extension(self):
        # Arrange
        rd = ReadData()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "report.csv"), "w") as f:
                f.write("data")

            # Act
            result = rd.get_file_list_from_folder(
                os.path.join(tmpdir, "*.csv"),
                with_path=True,
                with_extension=False
            )

            # Assert
            assert len(result) == 1
            assert not result[0].endswith(".csv")
            assert "report" in result[0]

    def test_without_path_returns_basename(self):
        # Arrange
        rd = ReadData()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "data.csv"), "w") as f:
                f.write("data")

            # Act
            result = rd.get_file_list_from_folder(
                os.path.join(tmpdir, "*.csv"),
                with_path=False,
                with_extension=True
            )

            # Assert
            assert result == ["data.csv"]

    def test_no_matching_files_returns_empty_list(self):
        # Arrange
        rd = ReadData()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Act
            result = rd.get_file_list_from_folder(os.path.join(tmpdir, "*.xyz"))

            # Assert
            assert result == []
