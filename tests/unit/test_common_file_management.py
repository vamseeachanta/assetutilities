# ABOUTME: Tests for common/file_management.py — FileManagement class.
# ABOUTME: Covers get_basenames, get_filename_without_extension, get_filtered_files.

import os
import pathlib
import tempfile

import pytest

from assetutilities.common.file_management import FileManagement


# ---------------------------------------------------------------------------
# FileManagement.get_basenames
# ---------------------------------------------------------------------------


class TestGetBasenames:
    """FileManagement.get_basenames extracts file names from full paths."""

    def test_single_file_path_returns_basename(self):
        # Arrange
        fm = FileManagement()
        files = ["/some/path/to/file.txt"]

        # Act
        result = fm.get_basenames(files)

        # Assert
        assert result == ["file.txt"]

    def test_multiple_files_returns_all_basenames(self):
        # Arrange
        fm = FileManagement()
        files = ["/a/b/c/one.csv", "/x/y/z/two.xlsx", "/report.pdf"]

        # Act
        result = fm.get_basenames(files)

        # Assert
        assert result == ["one.csv", "two.xlsx", "report.pdf"]

    def test_empty_list_returns_empty_list(self):
        # Arrange
        fm = FileManagement()

        # Act
        result = fm.get_basenames([])

        # Assert
        assert result == []

    def test_path_with_no_directory_returns_filename(self):
        # Arrange
        fm = FileManagement()

        # Act
        result = fm.get_basenames(["just_filename.dat"])

        # Assert
        assert result == ["just_filename.dat"]


# ---------------------------------------------------------------------------
# FileManagement.get_filename_without_extension
# ---------------------------------------------------------------------------


class TestGetFilenameWithoutExtension:
    """FileManagement.get_filename_without_extension strips extension from filename."""

    def test_removes_extension_from_simple_filename(self):
        # Arrange
        fm = FileManagement()

        # Act
        result = fm.get_filename_without_extension("/path/to/report.xlsx")

        # Assert
        assert result["without_path"] == "report"

    def test_with_path_includes_directory(self):
        # Arrange
        fm = FileManagement()

        # Act
        result = fm.get_filename_without_extension("/path/to/report.xlsx")

        # Assert
        assert result["with_path"] == "/path/to/report"

    def test_multiple_dots_strips_only_last_extension(self):
        # Arrange
        fm = FileManagement()

        # Act
        result = fm.get_filename_without_extension("/path/file.tar.gz")

        # Assert — os.path.splitext splits on last dot
        assert result["without_path"] == "file.tar"

    def test_returns_dict_with_both_keys(self):
        # Arrange
        fm = FileManagement()

        # Act
        result = fm.get_filename_without_extension("/some/path/data.csv")

        # Assert
        assert "without_path" in result
        assert "with_path" in result


# ---------------------------------------------------------------------------
# FileManagement.get_filtered_files
# ---------------------------------------------------------------------------


class TestGetFilteredFiles:
    """FileManagement.get_filtered_files applies stem-based filtering to a file list."""

    def _make_files(self, tmpdir, names):
        """Create empty files in tmpdir and return their pathlib.Path objects."""
        paths = []
        for name in names:
            p = pathlib.Path(tmpdir) / name
            p.touch()
            paths.append(p)
        return paths

    def test_contains_filter_keeps_matching_files(self):
        # Arrange
        fm = FileManagement()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._make_files(tmpdir, ["report_2023.csv", "data_2023.csv", "other.csv"])
            cfg_filter = {"contains": ["2023"]}

            # Act
            result = fm.get_filtered_files(files, cfg_filter)

            # Assert
            stems = [pathlib.Path(f).stem for f in result]
            assert "report_2023" in stems
            assert "data_2023" in stems
            assert "other" not in stems

    def test_not_contains_filter_removes_matching_files(self):
        # Arrange
        fm = FileManagement()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._make_files(tmpdir, ["final_result.txt", "draft_result.txt", "archive.txt"])
            cfg_filter = {"not_contains": ["draft"]}

            # Act
            result = fm.get_filtered_files(files, cfg_filter)

            # Assert
            stems = [pathlib.Path(f).stem for f in result]
            assert "final_result" in stems
            assert "archive" in stems
            assert "draft_result" not in stems

    def test_empty_filter_returns_all_files(self):
        # Arrange
        fm = FileManagement()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._make_files(tmpdir, ["a.txt", "b.txt"])
            cfg_filter = {}

            # Act
            result = fm.get_filtered_files(files, cfg_filter)

            # Assert — no filters applied, all files returned
            assert len(result) == 2

    def test_max_size_kb_removes_large_files(self):
        # Arrange
        fm = FileManagement()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a small file (< 1KB) and a larger file (> 1KB)
            small = pathlib.Path(tmpdir) / "small.dat"
            small.write_bytes(b"x" * 100)

            large = pathlib.Path(tmpdir) / "large.dat"
            large.write_bytes(b"x" * 5000)  # ~4.9 KB

            files = [small, large]
            cfg_filter = {"max_size_kb": 1.0}

            # Act
            result = fm.get_filtered_files(files, cfg_filter)

            # Assert — only small file passes
            assert small in result
            assert large not in result

    def test_min_size_kb_removes_small_files(self):
        # Arrange
        fm = FileManagement()
        with tempfile.TemporaryDirectory() as tmpdir:
            small = pathlib.Path(tmpdir) / "tiny.dat"
            small.write_bytes(b"x" * 10)

            large = pathlib.Path(tmpdir) / "big.dat"
            large.write_bytes(b"x" * 5000)

            files = [small, large]
            cfg_filter = {"min_size_kb": 1.0}

            # Act
            result = fm.get_filtered_files(files, cfg_filter)

            # Assert — only large file passes
            assert large in result
            assert small not in result

    def test_regex_filter_keeps_matching_stems(self):
        # Arrange
        fm = FileManagement()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._make_files(tmpdir, ["run_001_result.csv", "run_002_result.csv", "summary.csv"])
            cfg_filter = {"regex": r"run_\d+"}

            # Act
            result = fm.get_filtered_files(files, cfg_filter)

            # Assert
            stems = [pathlib.Path(f).stem for f in result]
            assert "run_001_result" in stems
            assert "run_002_result" in stems
            assert "summary" not in stems

    def test_null_string_filter_value_treated_as_empty(self):
        # Arrange
        fm = FileManagement()
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._make_files(tmpdir, ["file_a.txt", "file_b.txt"])
            cfg_filter = {"contains": "NULL"}  # sentinel value means ignore

            # Act
            result = fm.get_filtered_files(files, cfg_filter)

            # Assert — NULL is treated as disabled filter, all files returned
            assert len(result) == 2


# ---------------------------------------------------------------------------
# FileManagement.router
# ---------------------------------------------------------------------------


class TestRouter:
    """FileManagement.router short-circuits when file_management flag is False."""

    def test_router_returns_cfg_unchanged_when_no_file_management(self):
        # Arrange
        fm = FileManagement()
        cfg = {"other_key": "value"}

        # Act
        result = fm.router(cfg)

        # Assert — no file_management key means process_flag=False; cfg returned
        assert result == cfg

    def test_router_returns_cfg_unchanged_when_flag_false(self):
        # Arrange
        fm = FileManagement()

        class FakeCfg(dict):
            """Simulates AttributeDict-like access."""
            @property
            def file_management(self):
                return {"flag": False}

        cfg = FakeCfg({"file_management": {"flag": False}})

        # Act
        result = fm.router(cfg)

        # Assert
        assert result is cfg
