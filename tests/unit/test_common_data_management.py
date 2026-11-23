# ABOUTME: Tests for common/data_management.py — DataManagement class.
# ABOUTME: Covers get_filtered_df and get_transformed_df with real DataFrames.

import os
import tempfile

import pandas as pd
import pytest

from assetutilities.common.data_management import DataManagement


# ---------------------------------------------------------------------------
# DataManagement.get_filtered_df
# ---------------------------------------------------------------------------


class TestGetFilteredDf:
    """DataManagement.get_filtered_df — applies column-value filter to DataFrame."""

    def test_no_filter_key_returns_df_unchanged(self):
        # Arrange
        dm = DataManagement()
        df = pd.DataFrame({"col": [1, 2, 3]})
        cfg = {}  # no 'filter' key

        # Act
        result = dm.get_filtered_df(cfg, df)

        # Assert
        assert list(result["col"]) == [1, 2, 3]

    def test_filter_key_with_none_value_returns_unchanged(self):
        # Arrange
        dm = DataManagement()
        df = pd.DataFrame({"col": [1, 2, 3], "status": ["a", "b", "a"]})
        cfg = {"filter": None}

        # Act
        result = dm.get_filtered_df(cfg, df)

        # Assert — filter is None so no rows removed
        assert len(result) == 3

    def test_filter_single_column_value(self):
        # Arrange
        dm = DataManagement()
        df = pd.DataFrame(
            {"name": ["Alice", "Bob", "Alice"], "value": [10, 20, 30]}
        )
        cfg = {"filter": [{"column": "name", "value": "Alice"}]}

        # Act
        result = dm.get_filtered_df(cfg, df)

        # Assert
        assert len(result) == 2
        assert list(result["name"]) == ["Alice", "Alice"]

    def test_filter_returns_copy_not_same_object(self):
        # Arrange
        dm = DataManagement()
        df = pd.DataFrame({"x": [1, 2, 3]})
        cfg = {}

        # Act
        result = dm.get_filtered_df(cfg, df)

        # Assert — result is a fresh copy
        assert result is not df

    def test_filter_reduces_to_empty_if_no_match(self):
        # Arrange
        dm = DataManagement()
        df = pd.DataFrame({"col": ["a", "b", "c"]})
        cfg = {"filter": [{"column": "col", "value": "z"}]}

        # Act
        result = dm.get_filtered_df(cfg, df)

        # Assert
        assert len(result) == 0


# ---------------------------------------------------------------------------
# DataManagement.get_transformed_df
# ---------------------------------------------------------------------------


class TestGetTransformedDf:
    """DataManagement.get_transformed_df — applies transform config when present."""

    def test_no_transform_key_returns_df_unchanged(self):
        # Arrange
        dm = DataManagement()
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
        cfg = {}

        # Act
        result = dm.get_transformed_df(cfg, df)

        # Assert
        assert list(result["x"]) == [1.0, 2.0, 3.0]

    def test_no_transform_key_returns_copy(self):
        # Arrange
        dm = DataManagement()
        df = pd.DataFrame({"a": [10, 20]})
        cfg = {}

        # Act
        result = dm.get_transformed_df(cfg, df)

        # Assert — result is a fresh copy
        assert result is not df


# ---------------------------------------------------------------------------
# DataManagement.__init__ and router
# ---------------------------------------------------------------------------


class TestDataManagementInit:
    """DataManagement.router is a no-op stub; __init__ should succeed."""

    def test_init_returns_instance(self):
        # Act
        dm = DataManagement()

        # Assert
        assert isinstance(dm, DataManagement)

    def test_router_returns_none(self):
        # Arrange
        dm = DataManagement()
        cfg = {}

        # Act
        result = dm.router(cfg)

        # Assert — stub returns None
        assert result is None


# ---------------------------------------------------------------------------
# DataManagement.get_df_array_from_cfg
# ---------------------------------------------------------------------------


class TestGetDfArrayFromCfg:
    """DataManagement.get_df_array_from_cfg reads CSV files from the filesystem."""

    def test_single_group_reads_csv(self):
        # Arrange
        dm = DataManagement()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "data.csv")
            df_original = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
            df_original.to_csv(csv_path, index=False)

            cfg = {
                "Analysis": {"analysis_root_folder": tmpdir},
                "data": {
                    "groups": [{"file_name": csv_path}]
                },
            }

            # Act
            result = dm.get_df_array_from_cfg(cfg)

            # Assert
            assert len(result) == 1
            key = list(result[0].keys())[0]
            loaded_df = result[0][key]
            assert list(loaded_df.columns) == ["a", "b"]
            assert list(loaded_df["a"]) == [1, 2]

    def test_invalid_file_raises_value_error(self):
        # Arrange
        dm = DataManagement()
        cfg = {
            "Analysis": {"analysis_root_folder": "/tmp"},
            "data": {
                "groups": [{"file_name": "/nonexistent_file_xyz.csv"}]
            },
        }

        # Act / Assert
        with pytest.raises(ValueError):
            dm.get_df_array_from_cfg(cfg)

    def test_label_defaults_to_basename(self):
        # Arrange
        dm = DataManagement()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "my_data.csv")
            pd.DataFrame({"x": [1]}).to_csv(csv_path, index=False)

            cfg = {
                "Analysis": {"analysis_root_folder": tmpdir},
                "data": {
                    "groups": [{"file_name": csv_path}]
                },
            }

            # Act
            result = dm.get_df_array_from_cfg(cfg)

            # Assert — label is the basename of the file
            key = list(result[0].keys())[0]
            assert key == "my_data.csv"

    def test_explicit_label_used_when_present(self):
        # Arrange
        dm = DataManagement()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "my_data.csv")
            pd.DataFrame({"x": [1]}).to_csv(csv_path, index=False)

            cfg = {
                "Analysis": {"analysis_root_folder": tmpdir},
                "data": {
                    "groups": [{"file_name": csv_path, "label": "custom_label"}]
                },
            }

            # Act
            result = dm.get_df_array_from_cfg(cfg)

            # Assert
            assert "custom_label" in result[0]
