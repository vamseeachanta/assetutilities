# ABOUTME: Tests for common/utilities.py — file/directory validation helpers.
# ABOUTME: Covers is_file_valid_func, is_dir_valid_func, add_cwd_to_filename, get_common_name.

import os
import tempfile

import pytest

from assetutilities.common.utilities import (
    add_cwd_to_filename,
    get_common_name_from_2_filenames,
    is_dir_valid_func,
    is_file_valid_func,
)


# ---------------------------------------------------------------------------
# is_file_valid_func
# ---------------------------------------------------------------------------


class TestIsFileValidFunc:
    """Tests for is_file_valid_func — determines if a file exists."""

    def test_existing_absolute_file_is_valid(self):
        # Arrange: use a real temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            abs_path = f.name

        try:
            # Act
            valid, resolved = is_file_valid_func(abs_path)

            # Assert
            assert valid is True
            assert os.path.isabs(resolved)
        finally:
            os.unlink(abs_path)

    def test_nonexistent_absolute_file_is_invalid(self):
        # Arrange
        nonexistent = "/this/path/does/not/exist_abc123.txt"

        # Act
        valid, resolved = is_file_valid_func(nonexistent)

        # Assert
        assert valid is False

    def test_relative_file_resolved_from_analysis_root(self):
        # Arrange: create a temp file and use its directory as analysis_root_folder
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".yml", dir=tempfile.gettempdir()
        ) as f:
            abs_path = f.name
            filename_only = os.path.basename(abs_path)
            parent_dir = os.path.dirname(abs_path)

        try:
            # Act
            valid, resolved = is_file_valid_func(
                filename_only, analysis_root_folder=parent_dir
            )

            # Assert
            assert valid is True
            assert resolved == abs_path
        finally:
            os.unlink(abs_path)

    def test_nonexistent_relative_file_is_invalid(self):
        # Arrange
        relative = "absolutely_nonexistent_file_xyz987.txt"

        # Act
        valid, resolved = is_file_valid_func(relative)

        # Assert
        assert valid is False

    def test_absolute_nonexistent_with_analysis_root_is_invalid(self):
        # Arrange: absolute path that doesn't exist — no fallback even with root
        nonexistent_abs = "/no/such/file_abc.txt"

        # Act
        valid, resolved = is_file_valid_func(
            nonexistent_abs, analysis_root_folder="/tmp"
        )

        # Assert
        assert valid is False


# ---------------------------------------------------------------------------
# is_dir_valid_func
# ---------------------------------------------------------------------------


class TestIsDirValidFunc:
    """Tests for is_dir_valid_func — determines if a directory exists."""

    def test_existing_absolute_dir_is_valid(self):
        # Arrange
        existing_dir = tempfile.gettempdir()

        # Act
        valid, resolved = is_dir_valid_func(existing_dir)

        # Assert
        assert valid is True
        assert os.path.isabs(resolved)

    def test_nonexistent_absolute_dir_is_invalid(self):
        # Arrange
        nonexistent = "/no/such/directory/xyz987"

        # Act
        valid, resolved = is_dir_valid_func(nonexistent)

        # Assert
        assert valid is False

    def test_relative_dir_resolved_from_analysis_root(self):
        # Arrange: create a temp subdirectory
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir_name = "test_subdir"
            subdir_path = os.path.join(tmpdir, subdir_name)
            os.makedirs(subdir_path)

            # Act
            valid, resolved = is_dir_valid_func(
                subdir_name, analysis_root_folder=tmpdir
            )

            # Assert
            assert valid is True
            assert resolved == subdir_path

    def test_existing_absolute_dir_returns_absolute_path(self):
        # Arrange
        existing_dir = tempfile.gettempdir()

        # Act
        valid, resolved = is_dir_valid_func(existing_dir)

        # Assert
        assert os.path.isabs(resolved)

    def test_nonexistent_relative_dir_is_invalid(self):
        # Arrange
        relative = "this_dir_does_not_exist_abc987"

        # Act
        valid, resolved = is_dir_valid_func(relative)

        # Assert
        assert valid is False


# ---------------------------------------------------------------------------
# add_cwd_to_filename
# ---------------------------------------------------------------------------


class TestAddCwdToFilename:
    """Tests for add_cwd_to_filename — prepends cwd to relative paths."""

    def test_relative_path_gets_cwd_prepended(self):
        # Arrange
        relative = "my_file.txt"
        cwd = "/my/working/dir"

        # Act
        result = add_cwd_to_filename(relative, cwd=cwd)

        # Assert
        assert result == "/my/working/dir/my_file.txt"

    def test_absolute_path_returned_unchanged(self):
        # Arrange
        absolute = "/absolute/path/file.txt"

        # Act
        result = add_cwd_to_filename(absolute, cwd="/ignored")

        # Assert
        assert result == absolute

    def test_relative_subpath_prepended_correctly(self):
        # Arrange
        relative = "sub/dir/file.yml"
        cwd = "/root"

        # Act
        result = add_cwd_to_filename(relative, cwd=cwd)

        # Assert
        assert result == "/root/sub/dir/file.yml"


# ---------------------------------------------------------------------------
# get_common_name_from_2_filenames
# ---------------------------------------------------------------------------


class TestGetCommonNameFrom2Filenames:
    """Tests for get_common_name_from_2_filenames — derives unique name from two filenames."""

    def test_common_prefix_stripped_from_second(self):
        # Arrange: both share 'report_' prefix
        f1 = "/data/report_2023.xlsx"
        f2 = "/data/report_2024.xlsx"

        # Act
        result = get_common_name_from_2_filenames(f1, f2)

        # Assert
        assert result == "report_2023_2024"

    def test_no_common_prefix_uses_full_stems(self):
        # Arrange
        f1 = "/path/alpha.csv"
        f2 = "/path/beta.csv"

        # Act
        result = get_common_name_from_2_filenames(f1, f2)

        # Assert: unique basename = 'alpha' + '_' + remaining of 'beta' after common ''
        assert "alpha" in result
        assert "beta" in result

    def test_identical_stems_produces_stem_plus_empty_suffix(self):
        # Arrange
        f1 = "/path/same_name.txt"
        f2 = "/other/same_name.txt"

        # Act
        result = get_common_name_from_2_filenames(f1, f2)

        # Assert: common prefix is full stem; second's remainder after removing it is ''
        assert result == "same_name_"

    def test_result_is_string(self):
        # Arrange
        f1 = "file_a.txt"
        f2 = "file_b.txt"

        # Act
        result = get_common_name_from_2_filenames(f1, f2)

        # Assert
        assert isinstance(result, str)
