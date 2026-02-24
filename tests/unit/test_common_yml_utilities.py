# ABOUTME: Tests for common/yml_utilities.py — WorkingWithYAML class.
# ABOUTME: Covers ymlInput, yml_read_stream, update_deep, load_yml_with_utf_8_sig.

import os
import tempfile

import pytest
import yaml

from assetutilities.common.yml_utilities import WorkingWithYAML, update_deep, ymlInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(content: dict, directory: str, filename: str = "test.yml") -> str:
    """Write a dict as YAML to a temp file and return the path."""
    path = os.path.join(directory, filename)
    with open(path, "w") as f:
        yaml.dump(content, f)
    return path


# ---------------------------------------------------------------------------
# WorkingWithYAML.ymlInput
# ---------------------------------------------------------------------------


class TestYmlInput:
    """WorkingWithYAML.ymlInput loads a YAML file and optionally merges an update."""

    def test_loads_basic_yaml_file(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_yaml({"key": "value", "num": 42}, tmpdir)

            wwy = WorkingWithYAML()

            # Act
            result = wwy.ymlInput(path)

            # Assert
            assert result["key"] == "value"
            assert result["num"] == 42

    def test_raises_on_nonexistent_default_file(self):
        # Arrange
        wwy = WorkingWithYAML()

        # Act / Assert
        with pytest.raises(Exception):
            wwy.ymlInput("/nonexistent/path/file.yml")

    def test_merge_update_yml_overrides_values(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            default_path = _write_yaml({"a": 1, "b": 2}, tmpdir, "default.yml")
            update_path = _write_yaml({"b": 99}, tmpdir, "update.yml")

            wwy = WorkingWithYAML()

            # Act
            result = wwy.ymlInput(default_path, updateYml=update_path)

            # Assert — b is overridden; a is preserved
            assert result["b"] == 99
            assert result["a"] == 1

    def test_merge_update_yml_adds_new_keys(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            default_path = _write_yaml({"existing": 1}, tmpdir, "default.yml")
            update_path = _write_yaml({"new_key": 42}, tmpdir, "update.yml")

            wwy = WorkingWithYAML()

            # Act
            result = wwy.ymlInput(default_path, updateYml=update_path)

            # Assert
            assert result["new_key"] == 42
            assert result["existing"] == 1

    def test_no_update_file_returns_defaults(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            default_path = _write_yaml({"only": "default"}, tmpdir)

            wwy = WorkingWithYAML()

            # Act
            result = wwy.ymlInput(default_path)

            # Assert
            assert result["only"] == "default"

    def test_module_level_ymlinput_delegates(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_yaml({"module_level": True}, tmpdir)

            # Act
            result = ymlInput(path)

            # Assert
            assert result["module_level"] is True


# ---------------------------------------------------------------------------
# WorkingWithYAML.yml_read_stream
# ---------------------------------------------------------------------------


class TestYmlReadStream:
    """WorkingWithYAML.yml_read_stream reads a YAML file into a dict."""

    def test_single_document_yaml_loaded(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_yaml({"x": 1, "y": 2}, tmpdir)

            wwy = WorkingWithYAML()

            # Act
            result = wwy.yml_read_stream(path)

            # Assert
            assert result["x"] == 1
            assert result["y"] == 2

    def test_empty_yaml_file_returns_empty_dict(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "empty.yml")
            with open(path, "w") as f:
                f.write("")

            wwy = WorkingWithYAML()

            # Act
            result = wwy.yml_read_stream(path)

            # Assert
            assert isinstance(result, dict)
            assert len(result) == 0


# ---------------------------------------------------------------------------
# WorkingWithYAML.update_deep
# ---------------------------------------------------------------------------


class TestWorkingWithYAMLUpdateDeep:
    """WorkingWithYAML.update_deep performs recursive dict merge."""

    def test_shallow_merge(self):
        # Arrange
        wwy = WorkingWithYAML()
        base = {"a": 1, "b": 2}
        updates = {"b": 99}

        # Act
        result = wwy.update_deep(base, updates)

        # Assert
        assert result["b"] == 99
        assert result["a"] == 1

    def test_deep_merge_preserves_untouched_keys(self):
        # Arrange
        wwy = WorkingWithYAML()
        base = {"outer": {"inner": 1, "keep": 2}}
        updates = {"outer": {"inner": 42}}

        # Act
        result = wwy.update_deep(base, updates)

        # Assert
        assert result["outer"]["inner"] == 42
        assert result["outer"]["keep"] == 2

    def test_module_level_update_deep_works(self):
        # Arrange
        base = {"x": 10}
        updates = {"y": 20}

        # Act
        result = update_deep(base, updates)

        # Assert
        assert result["y"] == 20
        assert result["x"] == 10


# ---------------------------------------------------------------------------
# WorkingWithYAML.load_yml_with_utf_8_sig
# ---------------------------------------------------------------------------


class TestLoadYmlWithUtf8Sig:
    """WorkingWithYAML.load_yml_with_utf_8_sig reads YAML with utf-8-sig encoding."""

    def test_loads_standard_yaml_file(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_yaml({"encoding_test": "ok"}, tmpdir)

            wwy = WorkingWithYAML()

            # Act
            result = wwy.load_yml_with_utf_8_sig(path)

            # Assert
            assert result["encoding_test"] == "ok"

    def test_loads_nested_yaml(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {"outer": {"inner": [1, 2, 3]}}
            path = _write_yaml(data, tmpdir)

            wwy = WorkingWithYAML()

            # Act
            result = wwy.load_yml_with_utf_8_sig(path)

            # Assert
            assert result["outer"]["inner"] == [1, 2, 3]
