# ABOUTME: Tests for common/data.py — data reading, transformation, and string utilities.
# ABOUTME: Covers FromString, Transform, ReadData, DefineData, AttributeDict, and related classes.

import json
import os
import tempfile

import pandas as pd
import pytest

from assetutilities.common.data import (
    AttributeDict,
    DateTimeUtility,
    DefineData,
    FromString,
    NumberFormat,
    ReadData,
    SaveData,
    Transform,
    TransformData,
    objdict,
    transform_df_datetime_to_str,
)


# ---------------------------------------------------------------------------
# FromString
# ---------------------------------------------------------------------------


class TestFromStringUsingRegex:
    """Tests for FromString.using_regex."""

    def test_regex_finds_match(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.using_regex(r"\d+", "abc123def")

        # Assert
        assert result == "123"

    def test_regex_no_match_returns_none(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.using_regex(r"\d+", "no digits here")

        # Assert
        assert result is None

    def test_regex_case_insensitive(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.using_regex(r"hello", "HELLO WORLD")

        # Assert
        assert result == "HELLO"


class TestFromStringConvertFractionToFloat:
    """Tests for FromString.convert_fraction_to_float."""

    def test_plain_float_string(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.convert_fraction_to_float("3.14")

        # Assert
        assert result == pytest.approx(3.14)

    def test_simple_fraction(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.convert_fraction_to_float("1/2")

        # Assert
        assert result == pytest.approx(0.5)

    def test_mixed_number_fraction(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.convert_fraction_to_float("2 3/4")

        # Assert
        assert result == pytest.approx(2.75)

    def test_integer_as_string(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.convert_fraction_to_float("5")

        # Assert
        assert result == pytest.approx(5.0)


class TestFromStringRemoveStrings:
    """Tests for FromString.remove_strings and remove_string."""

    def test_remove_single_string(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.remove_string("hello world", "world")

        # Assert
        assert result == "hello "

    def test_remove_multiple_strings(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.remove_strings("hello foo bar", ["foo ", "bar"])

        # Assert
        assert result == "hello "

    def test_remove_string_not_present(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.remove_string("hello world", "xyz")

        # Assert
        assert result == "hello world"

    def test_remove_strings_with_none_text(self):
        # Arrange
        fs = FromString()

        # Act — None text should return None (checked inside)
        result = fs.remove_strings(None, ["foo"])

        # Assert
        assert result is None


class TestFromStringRemoveNextLineValues:
    """Tests for FromString.remove_next_line_values."""

    def test_removes_newline_characters(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.remove_next_line_values("line1\nline2\n")

        # Assert
        assert result == "line1line2"

    def test_no_newlines_unchanged(self):
        # Arrange
        fs = FromString()

        # Act
        result = fs.remove_next_line_values("no newlines here")

        # Assert
        assert result == "no newlines here"


class TestFromStringGetValueByDelimiter:
    """Tests for FromString.get_value_by_delimiter."""

    def test_space_delimiter_column_1(self):
        # Arrange
        fs = FromString()
        cfg = {"text": "10.5 20.3 30.1", "delimiter": " ", "column": 1, "data_type": "float"}

        # Act
        result = fs.get_value_by_delimiter(cfg)

        # Assert
        assert result == pytest.approx(10.5)

    def test_space_delimiter_column_2(self):
        # Arrange
        fs = FromString()
        cfg = {"text": "10.5 20.3 30.1", "delimiter": " ", "column": 2, "data_type": "float"}

        # Act
        result = fs.get_value_by_delimiter(cfg)

        # Assert
        assert result == pytest.approx(20.3)

    def test_comma_delimiter_returns_string_type(self):
        # Arrange
        fs = FromString()
        cfg = {"text": "alpha,beta,gamma", "delimiter": ",", "column": 2, "data_type": "str"}

        # Act
        result = fs.get_value_by_delimiter(cfg)

        # Assert
        assert result == "beta"

    def test_comma_delimiter_float_conversion(self):
        # Arrange
        fs = FromString()
        cfg = {"text": "1.1,2.2,3.3", "delimiter": ",", "column": 3, "data_type": "float"}

        # Act
        result = fs.get_value_by_delimiter(cfg)

        # Assert
        assert result == pytest.approx(3.3)


# ---------------------------------------------------------------------------
# ReadData
# ---------------------------------------------------------------------------


class TestReadDataExtractFromDictionary:
    """Tests for ReadData.extract_from_dictionary."""

    def test_extract_top_level_key(self):
        # Arrange
        rd = ReadData()
        data = {"a": 1, "b": 2}

        # Act
        result = rd.extract_from_dictionary(data, ["a"])

        # Assert
        assert result == 1

    def test_extract_nested_key(self):
        # Arrange
        rd = ReadData()
        data = {"outer": {"inner": 42}}

        # Act
        result = rd.extract_from_dictionary(data, ["outer", "inner"])

        # Assert
        assert result == 42

    def test_extract_three_levels(self):
        # Arrange
        rd = ReadData()
        data = {"a": {"b": {"c": "deep_value"}}}

        # Act
        result = rd.extract_from_dictionary(data, ["a", "b", "c"])

        # Assert
        assert result == "deep_value"


class TestReadDataKeyChain:
    """Tests for ReadData.key_chain — safe nested access."""

    def test_single_key_exists(self):
        # Arrange
        rd = ReadData()
        data = {"key": "value"}

        # Act
        result = rd.key_chain(data, "key")

        # Assert
        assert result == "value"

    def test_nested_keys_exist(self):
        # Arrange
        rd = ReadData()
        data = {"a": {"b": {"c": 99}}}

        # Act
        result = rd.key_chain(data, "a", "b", "c")

        # Assert
        assert result == 99

    def test_missing_key_returns_default_none(self):
        # Arrange
        rd = ReadData()
        data = {"a": 1}

        # Act
        result = rd.key_chain(data, "missing_key")

        # Assert
        assert result is None

    def test_missing_nested_key_returns_default(self):
        # Arrange
        rd = ReadData()
        data = {"a": {"b": 1}}

        # Act
        result = rd.key_chain(data, "a", "missing", default="fallback")

        # Assert
        assert result == "fallback"

    def test_list_access_by_index(self):
        # Arrange
        rd = ReadData()
        data = [10, 20, 30]

        # Act
        result = rd.key_chain(data, 1)

        # Assert
        assert result == 20

    def test_list_out_of_bounds_returns_default(self):
        # Arrange
        rd = ReadData()
        data = [1, 2, 3]

        # Act
        result = rd.key_chain(data, 99, default="out_of_bounds")

        # Assert
        assert result == "out_of_bounds"

    def test_non_dict_non_list_with_key_returns_default(self):
        # Arrange
        rd = ReadData()
        data = "not_a_dict"

        # Act
        result = rd.key_chain(data, "key", default="fallback")

        # Assert
        assert result == "fallback"


class TestReadDataGetArrayRowsContainingKeywords:
    """Tests for ReadData.get_array_rows_containing_keywords."""

    def test_finds_rows_with_keyword(self):
        # Arrange
        rd = ReadData()
        array = ["apple banana", "cherry", "banana cherry", "date"]

        # Act
        result = rd.get_array_rows_containing_keywords(array, ["banana"])

        # Assert
        # Row numbers are 1-indexed
        assert 1 in result
        assert 3 in result

    def test_no_match_returns_empty(self):
        # Arrange
        rd = ReadData()
        array = ["alpha", "beta", "gamma"]

        # Act
        result = rd.get_array_rows_containing_keywords(array, ["xyz"])

        # Assert
        assert result == []

    def test_with_transform(self):
        # Arrange
        rd = ReadData()
        array = ["match", "no", "match"]
        cfg = {"transform": {"scale": 2, "shift": 0}}

        # Act
        result = rd.get_array_rows_containing_keywords(array, ["match"], cfg)

        # Assert: row numbers 1 and 3 get scaled by 2
        assert 2 in result
        assert 6 in result

    def test_multiple_keywords(self):
        # Arrange
        rd = ReadData()
        array = ["alpha", "beta", "gamma alpha", "delta"]

        # Act
        result = rd.get_array_rows_containing_keywords(array, ["alpha", "gamma"])

        # Assert: rows 1 and 3 match
        assert 1 in result
        assert 3 in result


class TestReadDataFilterByColumnValues:
    """Tests for ReadData.df_filter_by_column_values."""

    def test_filter_single_value(self):
        # Arrange
        rd = ReadData()
        df = pd.DataFrame({"category": ["A", "B", "A", "C"], "value": [1, 2, 3, 4]})
        cfg = {"filter": [{"column": "category", "value": "A"}]}

        # Act
        result = rd.df_filter_by_column_values(cfg, df)

        # Assert
        assert list(result["category"]) == ["A", "A"]
        assert list(result["value"]) == [1, 3]

    def test_filter_none_returns_full_df(self):
        # Arrange
        rd = ReadData()
        df = pd.DataFrame({"x": [1, 2, 3]})
        cfg = {"filter": None}

        # Act
        result = rd.df_filter_by_column_values(cfg, df)

        # Assert
        assert len(result) == 3

    def test_filter_resets_index(self):
        # Arrange
        rd = ReadData()
        df = pd.DataFrame({"cat": ["X", "Y", "X"], "val": [10, 20, 30]})
        cfg = {"filter": [{"column": "cat", "value": "X"}]}

        # Act
        result = rd.df_filter_by_column_values(cfg, df)

        # Assert: index should be reset
        assert list(result.index) == [0, 1]


class TestReadDataGetFileListFromFolder:
    """Tests for ReadData.get_file_list_from_folder."""

    def test_returns_files_in_folder(self):
        # Arrange
        rd = ReadData()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a couple of temp files
            path1 = os.path.join(tmpdir, "file1.txt")
            path2 = os.path.join(tmpdir, "file2.txt")
            open(path1, "w").close()
            open(path2, "w").close()

            # Act
            result = rd.get_file_list_from_folder(
                os.path.join(tmpdir, "*.txt"), with_path=True, with_extension=True
            )

            # Assert
            assert len(result) == 2
            assert all(f.endswith(".txt") for f in result)

    def test_without_path_returns_basename_only(self):
        # Arrange
        rd = ReadData()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "my_file.csv")
            open(path, "w").close()

            # Act
            result = rd.get_file_list_from_folder(
                os.path.join(tmpdir, "*.csv"), with_path=False, with_extension=True
            )

            # Assert
            assert result == ["my_file.csv"]

    def test_without_extension_strips_ext(self):
        # Arrange
        rd = ReadData()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "my_file.csv")
            open(path, "w").close()

            # Act
            result = rd.get_file_list_from_folder(
                os.path.join(tmpdir, "*.csv"), with_path=False, with_extension=False
            )

            # Assert
            assert result == ["my_file"]


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------


class TestTransformDataframeToDict:
    """Tests for Transform.dataframe_to_dict."""

    def test_simple_dataframe_to_records(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        # Act
        result = t.dataframe_to_dict(df)

        # Assert
        assert result == [{"a": 1, "b": 3}, {"a": 2, "b": 4}]

    def test_none_df_returns_empty_dict(self):
        # Arrange
        t = Transform()

        # Act
        result = t.dataframe_to_dict(None)

        # Assert
        assert result == {}

    def test_custom_orient_index(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        # Act
        result = t.dataframe_to_dict(df, cfg={"orient": "index"})

        # Assert
        assert isinstance(result, dict)
        assert 0 in result


class TestTransformGetTransformedDf:
    """Tests for Transform.get_transformed_df."""

    def test_scale_and_shift_applied(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
        cfg_transform = [{"column": "x", "scale": 2, "shift": 1}]

        # Act
        result = t.get_transformed_df(cfg_transform, df)

        # Assert: x = x*2 + 1
        assert list(result["x"]) == [3, 5, 7]
        assert list(result["y"]) == [10, 20, 30]  # unchanged

    def test_column_not_in_df_skipped(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"a": [1, 2]})
        cfg_transform = [{"column": "nonexistent", "scale": 10, "shift": 0}]

        # Act
        result = t.get_transformed_df(cfg_transform, df)

        # Assert: original unchanged
        assert list(result["a"]) == [1, 2]

    def test_original_df_not_mutated(self):
        # Arrange
        t = Transform()
        df = pd.DataFrame({"z": [5, 10]})
        cfg_transform = [{"column": "z", "scale": 3, "shift": 0}]

        # Act
        t.get_transformed_df(cfg_transform, df)

        # Assert: original df unchanged
        assert list(df["z"]) == [5, 10]


class TestTransformListToUniqueList:
    """Tests for Transform.transform_list_to_unique_list."""

    def test_no_duplicates_unchanged(self):
        # Arrange
        t = Transform()
        cfg = {"list": ["a", "b", "c"], "transform_character": "trailing_alphabet"}

        # Act
        result = t.transform_list_to_unique_list(cfg)

        # Assert
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_duplicate_gets_trailing_alphabet(self):
        # Arrange
        t = Transform()
        cfg = {"list": ["col", "col", "other"], "transform_character": "trailing_alphabet"}

        # Act
        result = t.transform_list_to_unique_list(cfg)

        # Assert: one "col" stays, one gets modified
        assert len(result) == 3
        assert len(set(result)) == 3  # all unique now


# ---------------------------------------------------------------------------
# TransformData
# ---------------------------------------------------------------------------


class TestTransformDataLinear:
    """Tests for TransformData.linear — linear transform with scale/shift."""

    def test_list_input_scaled_and_shifted(self):
        # Arrange
        from assetutilities.common.data import TransformData
        td = TransformData()
        cfg = {"type": "linear", "scale": 2.0, "shift": 1.0, "data": [1.0, 2.0, 3.0]}

        # Act
        result = td.linear(cfg)

        # Assert
        assert result["data"] == pytest.approx([3.0, 5.0, 7.0])

    def test_scalar_input_scaled_and_shifted(self):
        # Arrange
        from assetutilities.common.data import TransformData
        td = TransformData()
        cfg = {"type": "linear", "scale": 3.0, "shift": 10.0, "data": 5.0}

        # Act
        result = td.linear(cfg)

        # Assert
        assert result["data"] == pytest.approx(25.0)


# ---------------------------------------------------------------------------
# DefineData
# ---------------------------------------------------------------------------


class TestDefineDataEmptyDataFrame:
    """Tests for DefineData.empty_data_frame."""

    def test_creates_empty_dataframe_with_columns(self):
        # Arrange
        dd = DefineData()

        # Act
        result = dd.empty_data_frame(columns=["a", "b", "c"])

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["a", "b", "c"]
        assert len(result) == 0

    def test_creates_empty_dataframe_without_columns(self):
        # Arrange
        dd = DefineData()

        # Act
        result = dd.empty_data_frame()

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# AttributeDict / objdict
# ---------------------------------------------------------------------------


class TestAttributeDictInData:
    """Tests for AttributeDict and objdict in data.py."""

    def test_attribute_dict_access(self):
        # Arrange
        d = AttributeDict({"key": "val"})

        # Act / Assert
        assert d.key == "val"

    def test_objdict_get_attr(self):
        # Arrange
        d = objdict({"x": 10})

        # Act / Assert
        assert d.x == 10

    def test_objdict_set_attr(self):
        # Arrange
        d = objdict()

        # Act
        d.new_key = 42

        # Assert
        assert d["new_key"] == 42

    def test_objdict_del_attr(self):
        # Arrange
        d = objdict({"remove_me": "yes"})

        # Act
        del d.remove_me

        # Assert
        assert "remove_me" not in d

    def test_objdict_missing_attr_raises(self):
        # Arrange
        d = objdict()

        # Act / Assert
        with pytest.raises(AttributeError):
            _ = d.nonexistent

    def test_objdict_missing_del_raises(self):
        # Arrange
        d = objdict()

        # Act / Assert
        with pytest.raises(AttributeError):
            del d.nonexistent


# ---------------------------------------------------------------------------
# DateTimeUtility
# ---------------------------------------------------------------------------


class TestDateTimeUtility:
    """Tests for DateTimeUtility.last_day_of_month."""

    def test_last_day_of_january(self):
        # Arrange
        import datetime
        dtu = DateTimeUtility()
        jan_15 = datetime.date(2024, 1, 15)

        # Act
        result = dtu.last_day_of_month(jan_15)

        # Assert
        assert result.day == 31
        assert result.month == 1

    def test_last_day_of_february_leap_year(self):
        # Arrange
        import datetime
        dtu = DateTimeUtility()
        feb_10 = datetime.date(2024, 2, 10)  # 2024 is a leap year

        # Act
        result = dtu.last_day_of_month(feb_10)

        # Assert
        assert result.day == 29
        assert result.month == 2

    def test_last_day_of_february_non_leap_year(self):
        # Arrange
        import datetime
        dtu = DateTimeUtility()
        feb_01 = datetime.date(2023, 2, 1)

        # Act
        result = dtu.last_day_of_month(feb_01)

        # Assert
        assert result.day == 28
        assert result.month == 2

    def test_last_day_of_april(self):
        # Arrange
        import datetime
        dtu = DateTimeUtility()
        apr_05 = datetime.date(2024, 4, 5)

        # Act
        result = dtu.last_day_of_month(apr_05)

        # Assert
        assert result.day == 30
        assert result.month == 4


# ---------------------------------------------------------------------------
# NumberFormat
# ---------------------------------------------------------------------------


class TestNumberFormat:
    """Tests for NumberFormat.format_number."""

    def test_format_float_two_decimals(self):
        # Arrange
        nf = NumberFormat()

        # Act
        result = nf.format_number(3.14159, "{:.2f}")

        # Assert
        assert result == "3.14"

    def test_format_integer(self):
        # Arrange
        nf = NumberFormat()

        # Act
        result = nf.format_number(42, "{:d}")

        # Assert
        assert result == "42"

    def test_format_with_padding(self):
        # Arrange
        nf = NumberFormat()

        # Act
        result = nf.format_number(7, "{:05d}")

        # Assert
        assert result == "00007"


# ---------------------------------------------------------------------------
# SaveData — file I/O tests using temp files
# ---------------------------------------------------------------------------


class TestSaveDataJson:
    """Tests for SaveData.saveDataJson — save dict as JSON."""

    def test_saves_json_file(self):
        # Arrange
        sd = SaveData()
        data = {"key": "value", "number": 42}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_output")

            # Act
            sd.saveDataJson(data, filename)

            # Assert
            json_path = filename + ".json"
            assert os.path.exists(json_path)
            with open(json_path) as f:
                loaded = json.load(f)
            assert loaded == data

    def test_saves_nested_data(self):
        # Arrange
        sd = SaveData()
        data = {"nested": {"a": 1, "b": [1, 2, 3]}}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "nested_output")

            # Act
            sd.saveDataJson(data, filename)

            # Assert
            with open(filename + ".json") as f:
                loaded = json.load(f)
            assert loaded["nested"]["b"] == [1, 2, 3]


class TestSaveDataYaml:
    """Tests for SaveData.saveDataYaml — save dict as YAML."""

    def test_saves_yaml_file(self):
        # Arrange
        import yaml
        sd = SaveData()
        data = {"key": "value", "items": [1, 2, 3]}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_output")

            # Act
            sd.saveDataYaml(data, filename)

            # Assert
            yml_path = filename + ".yml"
            assert os.path.exists(yml_path)
            with open(yml_path) as f:
                loaded = yaml.safe_load(f)
            assert loaded["key"] == "value"

    def test_saves_with_none_flow_style(self):
        # Arrange
        import yaml
        sd = SaveData()
        data = {"a": 1}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "none_flow")

            # Act
            sd.saveDataYaml(data, filename, default_flow_style=None)

            # Assert
            assert os.path.exists(filename + ".yml")


class TestSaveDataFrame:
    """Tests for SaveData.saveDataFrame — save DataFrame as CSV."""

    def test_saves_csv_file(self):
        # Arrange
        sd = SaveData()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_df")

            # Act
            sd.saveDataFrame(df, filename)

            # Assert
            csv_path = filename + ".csv"
            assert os.path.exists(csv_path)
            loaded = pd.read_csv(csv_path, index_col=0)
            assert list(loaded.columns) == ["a", "b"]
