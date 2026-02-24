# ABOUTME: Tests for common/saveData.py — standalone save functions (dump_ordered, saveDataYaml).
# ABOUTME: Covers saveDataJson, saveDataYaml, dump_ordered, and dump_ordered_yaml.

import json
import os
import tempfile
from collections import OrderedDict

import pytest
import yaml

from assetutilities.common.saveData import (
    dump_ordered,
    dump_ordered_yaml,
    saveDataJson,
    saveDataYaml,
)


class TestSaveDataJson:
    """Tests for saveDataJson — write dict as JSON file."""

    def test_saves_dict_to_json_file(self):
        # Arrange
        data = {"key": "value", "num": 42}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "output")

            # Act
            saveDataJson(data, filename)

            # Assert
            assert os.path.exists(filename + ".json")
            with open(filename + ".json") as f:
                loaded = json.load(f)
            assert loaded == data

    def test_saves_nested_dict(self):
        # Arrange
        data = {"outer": {"inner": [1, 2, 3]}}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "nested")

            # Act
            saveDataJson(data, filename)

            # Assert
            with open(filename + ".json") as f:
                loaded = json.load(f)
            assert loaded["outer"]["inner"] == [1, 2, 3]

    def test_saves_empty_dict(self):
        # Arrange
        data = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "empty")

            # Act
            saveDataJson(data, filename)

            # Assert
            with open(filename + ".json") as f:
                loaded = json.load(f)
            assert loaded == {}


class TestSaveDataYaml:
    """Tests for saveDataYaml — write dict as YAML file."""

    def test_saves_dict_to_yaml_file(self):
        # Arrange
        data = {"key": "value", "items": [1, 2]}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "output")

            # Act
            saveDataYaml(data, filename)

            # Assert
            assert os.path.exists(filename + ".yml")
            with open(filename + ".yml") as f:
                loaded = yaml.safe_load(f)
            assert loaded["key"] == "value"

    def test_saves_with_none_flow_style(self):
        # Arrange
        data = {"a": 1}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "none_style")

            # Act
            saveDataYaml(data, filename, default_flow_style=None)

            # Assert
            assert os.path.exists(filename + ".yml")

    def test_saves_with_non_alias_dumper(self):
        # Arrange
        data = {"a": 1, "b": 2}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "non_alias")

            # Act
            saveDataYaml(data, filename, default_flow_style="NonAlias")

            # Assert
            assert os.path.exists(filename + ".yml")

    def test_saves_with_ordered_dumper(self):
        # Arrange
        data = OrderedDict([("z", 1), ("a", 2)])

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "ordered")

            # Act
            saveDataYaml(data, filename, default_flow_style="OrderedDumper")

            # Assert
            assert os.path.exists(filename + ".yml")

    def test_default_flow_style_false_produces_block(self):
        # Arrange
        data = {"key": "value"}

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "block_style")

            # Act
            saveDataYaml(data, filename, default_flow_style=False)

            # Assert: block style produces multi-line YAML
            with open(filename + ".yml") as f:
                content = f.read()
            assert "key: value" in content


class TestDumpOrdered:
    """Tests for dump_ordered — returns YAML string from OrderedDict."""

    def test_returns_yaml_string(self):
        # Arrange
        data = OrderedDict([("b", 2), ("a", 1)])

        # Act
        result = dump_ordered(data)

        # Assert
        assert isinstance(result, str)
        assert "b:" in result
        assert "a:" in result

    def test_empty_ordered_dict(self):
        # Arrange
        data = OrderedDict()

        # Act
        result = dump_ordered(data)

        # Assert
        assert isinstance(result, str)

    def test_plain_dict_also_works(self):
        # Arrange
        data = {"x": 10}

        # Act
        result = dump_ordered(data)

        # Assert
        assert "x:" in result
        assert "10" in result


class TestDumpOrderedYaml:
    """Tests for dump_ordered_yaml — write OrderedDict to YAML file."""

    def test_writes_yaml_file(self):
        # Arrange
        data = OrderedDict([("first", 1), ("second", 2)])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "ordered_output.yml")

            # Act
            dump_ordered_yaml(data, output_path)

            # Assert
            assert os.path.exists(output_path)
            with open(output_path) as f:
                content = f.read()
            assert "first" in content
            assert "second" in content

    def test_plain_dict_writes_yaml_file(self):
        # Arrange
        data = {"alpha": "a", "beta": "b"}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "plain_dict.yml")

            # Act
            dump_ordered_yaml(data, output_path)

            # Assert
            assert os.path.exists(output_path)
