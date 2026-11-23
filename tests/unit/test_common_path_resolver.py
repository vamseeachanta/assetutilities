# ABOUTME: Tests for common/path_resolver.py — path resolution utilities.
# ABOUTME: Covers PathResolver static methods for absolute/relative path handling.

import os
import tempfile

import pytest

from assetutilities.common.path_resolver import PathResolver


class TestResolvePathAbsolute:
    """resolve_path with absolute paths — must be returned unchanged."""

    def test_absolute_path_returned_unchanged(self):
        # Arrange
        abs_path = "/absolute/path/to/file.txt"

        # Act
        result = PathResolver.resolve_path(abs_path)

        # Assert
        assert result == abs_path

    def test_absolute_path_with_cfg_still_returned_unchanged(self):
        # Arrange
        abs_path = "/some/absolute/file.yml"
        cfg = {"_config_dir_path": "/should/be/ignored"}

        # Act
        result = PathResolver.resolve_path(abs_path, cfg=cfg)

        # Assert
        assert result == abs_path

    def test_pathlib_path_object_converted_to_str(self):
        # Arrange
        from pathlib import Path
        abs_path = Path("/absolute/path")

        # Act
        result = PathResolver.resolve_path(abs_path)

        # Assert
        assert isinstance(result, str)
        assert result == "/absolute/path"


class TestResolvePathRelative:
    """resolve_path with relative paths — should use cfg or fallback dirs."""

    def test_relative_path_uses_config_dir(self):
        # Arrange
        cfg = {"_config_dir_path": "/config/dir"}
        relative = "sub/file.txt"

        # Act
        result = PathResolver.resolve_path(relative, cfg=cfg)

        # Assert
        assert result == "/config/dir/sub/file.txt"

    def test_relative_path_uses_analysis_root_folder_fallback(self):
        # Arrange: _config_dir_path not set, use Analysis.analysis_root_folder
        cfg = {"Analysis": {"analysis_root_folder": "/analysis/root"}}
        relative = "data/input.csv"

        # Act
        result = PathResolver.resolve_path(relative, cfg=cfg)

        # Assert
        assert result == "/analysis/root/data/input.csv"

    def test_relative_path_uses_fallback_dir(self):
        # Arrange
        relative = "output/results.csv"

        # Act
        result = PathResolver.resolve_path(relative, fallback_dir="/my/fallback")

        # Assert
        assert result == "/my/fallback/output/results.csv"

    def test_relative_path_falls_back_to_cwd_when_no_config(self):
        # Arrange
        relative = "my_file.txt"
        expected = os.path.join(os.getcwd(), relative)

        # Act
        result = PathResolver.resolve_path(relative)

        # Assert
        assert result == expected

    def test_config_dir_path_takes_priority_over_analysis_root(self):
        # Arrange
        cfg = {
            "_config_dir_path": "/config/dir",
            "Analysis": {"analysis_root_folder": "/analysis/root"},
        }
        relative = "data.yml"

        # Act
        result = PathResolver.resolve_path(relative, cfg=cfg)

        # Assert — _config_dir_path has priority
        assert result == "/config/dir/data.yml"

    def test_empty_cfg_dict_falls_back_to_cwd(self):
        # Arrange
        relative = "file.txt"
        expected = os.path.join(os.getcwd(), relative)

        # Act
        result = PathResolver.resolve_path(relative, cfg={})

        # Assert
        assert result == expected

    def test_none_cfg_falls_back_to_cwd(self):
        # Arrange
        relative = "relative_file.yml"
        expected = os.path.join(os.getcwd(), relative)

        # Act
        result = PathResolver.resolve_path(relative, cfg=None)

        # Assert
        assert result == expected


class TestResolveOutputDirectory:
    """resolve_output_directory — picks output path from config sections."""

    def test_uses_visualization_output_directory(self):
        # Arrange
        cfg = {
            "_config_dir_path": "/cfg",
            "visualization": {"output_directory": "plots"},
        }

        # Act
        result = PathResolver.resolve_output_directory(cfg)

        # Assert
        assert result == "/cfg/plots"

    def test_falls_back_to_visualization_plot_directory(self):
        # Arrange
        cfg = {
            "_config_dir_path": "/cfg",
            "visualization": {"plot_directory": "figs"},
        }

        # Act
        result = PathResolver.resolve_output_directory(cfg)

        # Assert
        assert result == "/cfg/figs"

    def test_falls_back_to_file_management(self):
        # Arrange
        cfg = {
            "_config_dir_path": "/cfg",
            "visualization": {},
            "file_management": {"output_directory": "fm_output"},
        }

        # Act
        result = PathResolver.resolve_output_directory(cfg)

        # Assert
        assert result == "/cfg/fm_output"

    def test_falls_back_to_analysis_result_folder(self):
        # Arrange
        cfg = {
            "_config_dir_path": "/cfg",
            "visualization": {},
            "file_management": {},
            "Analysis": {"result_folder": "results"},
        }

        # Act
        result = PathResolver.resolve_output_directory(cfg)

        # Assert
        assert result == "/cfg/results"

    def test_uses_default_fallback_when_no_keys(self):
        # Arrange
        cfg = {"_config_dir_path": "/cfg", "visualization": {}, "Analysis": {}}

        # Act
        result = PathResolver.resolve_output_directory(cfg)

        # Assert — default fallback is "output"
        assert result == "/cfg/output"

    def test_custom_fallback_string(self):
        # Arrange
        cfg = {"_config_dir_path": "/cfg", "visualization": {}, "Analysis": {}}

        # Act
        result = PathResolver.resolve_output_directory(cfg, fallback="custom_out")

        # Assert
        assert result == "/cfg/custom_out"


class TestEnsureConfigTracking:
    """ensure_config_tracking — attaches path metadata to cfg dict."""

    def test_adds_config_file_and_dir_paths(self):
        # Arrange: create a real temp file so os.path.exists() returns True
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
            config_file_path = f.name

        try:
            cfg = {}

            # Act
            result = PathResolver.ensure_config_tracking(cfg, config_file_path)

            # Assert
            assert result["_config_file_path"] == os.path.abspath(config_file_path)
            assert result["_config_dir_path"] == os.path.dirname(
                os.path.abspath(config_file_path)
            )
        finally:
            os.unlink(config_file_path)

    def test_nonexistent_file_does_not_add_keys(self):
        # Arrange
        cfg = {}

        # Act
        result = PathResolver.ensure_config_tracking(cfg, "/nonexistent/file.yml")

        # Assert
        assert "_config_file_path" not in result
        assert "_config_dir_path" not in result

    def test_no_path_leaves_cfg_unchanged(self):
        # Arrange
        cfg = {"existing": "value"}

        # Act
        result = PathResolver.ensure_config_tracking(cfg, config_file_path=None)

        # Assert
        assert result == {"existing": "value"}

    def test_returns_the_same_cfg_object(self):
        # Arrange
        cfg = {}
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
            config_file_path = f.name

        try:
            # Act
            result = PathResolver.ensure_config_tracking(cfg, config_file_path)

            # Assert — mutates and returns same dict
            assert result is cfg
        finally:
            os.unlink(config_file_path)
