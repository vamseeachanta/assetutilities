# ABOUTME: Tests for YAML variable-definition support in common/yml_utilities.py.
# ABOUTME: Covers single variables, directive blocks (anchors) and {{ }} placeholders (issue #59).

import os

import pytest
import yaml

from assetutilities.common.yml_utilities import (
    WorkingWithYAML,
    resolve_placeholders,
)

# Example yml referenced by issue #59 (anchor-based single + block variables).
EXAMPLE_1 = os.path.join(
    os.path.dirname(__file__),
    "..",
    "modules",
    "yml_utilities",
    "yml",
    "variables",
    "variable_example_1.yml",
)


# ---------------------------------------------------------------------------
# Single variable + directive block (native YAML anchors / aliases)
# ---------------------------------------------------------------------------


class TestAnchorVariables:
    """A YAML anchor (``&name``) defines a variable; aliases (``*name``) reuse it."""

    def test_single_variable_alias_resolves_to_anchor_value(self):
        # Arrange / Act
        cfg = yaml.safe_load(open(EXAMPLE_1, encoding="utf-8"))

        # Assert: the aliased label equals the anchored define value.
        assert cfg["define"] == cfg["data"]["groups"][0]["label"]
        assert cfg["data"]["groups"][0]["label"] == "fsts_l015_hwl_125km3_l100_sb"

    def test_directive_block_anchor_reused_as_mapping(self):
        # Arrange: a block anchor shares a whole nested mapping across the doc.
        text = (
            "define: &cfg\n"
            "  template: collated/template.xlsx\n"
            "  filename: collated/out.xlsx\n"
            "data:\n"
            "  groups:\n"
            "    - target: *cfg\n"
        )

        # Act
        cfg = yaml.safe_load(text)
        target = cfg["data"]["groups"][0]["target"]

        # Assert: the whole block (not just a scalar) is reused.
        assert target == cfg["define"]
        assert target["template"] == "collated/template.xlsx"


class TestWorkingWithYAMLVariableHelpers:
    """The WorkingWithYAML test_* helpers report reusability of variables/blocks."""

    def test_single_variable_helper_returns_true(self):
        wwyaml = WorkingWithYAML()
        cfg = yaml.safe_load(open(EXAMPLE_1, encoding="utf-8"))

        ok, label = wwyaml.test_single_variable(cfg)

        assert ok is True
        assert label == "fsts_l015_hwl_125km3_l100_sb"

    def test_directive_block_helper_returns_block(self):
        wwyaml = WorkingWithYAML()
        cfg = yaml.safe_load(open(EXAMPLE_1, encoding="utf-8"))

        ok, block = wwyaml.test_directive_block(cfg)

        assert ok is True
        assert block["template"].endswith("template_WLNG_FSTs_LNGC.xlsx")


# ---------------------------------------------------------------------------
# Placeholders ({{ key }} resolved after parsing)
# ---------------------------------------------------------------------------


class TestResolvePlaceholders:
    """resolve_placeholders substitutes ``{{ key }}`` against the document context."""

    def test_self_referential_document(self):
        # Arrange: placeholders reference other keys in the same document.
        cfg = {
            "meta": {"library": "assetutilities"},
            "test_variables": {"method": "placeholder"},
            "placeholder_tests": {
                "method": "{{ test_variables.method }}",
                "library": "{{ meta.library }}",
            },
        }

        # Act
        resolved = resolve_placeholders(cfg)

        # Assert
        assert resolved["placeholder_tests"]["method"] == "placeholder"
        assert resolved["placeholder_tests"]["library"] == "assetutilities"

    def test_placeholder_embedded_in_larger_string(self):
        cfg = {"meta": {"library": "assetutilities"}, "path": "lib_{{ meta.library }}_v1"}

        resolved = resolve_placeholders(cfg)

        assert resolved["path"] == "lib_assetutilities_v1"

    def test_explicit_context_overrides_self(self):
        data = {"label": "{{ name }}"}

        resolved = resolve_placeholders(data, context={"name": "fsts_l015"})

        assert resolved["label"] == "fsts_l015"

    def test_placeholder_inside_list(self):
        cfg = {"label": "fsts", "groups": [{"label": "{{ label }}"}]}

        resolved = resolve_placeholders(cfg)

        assert resolved["groups"][0]["label"] == "fsts"

    def test_undefined_placeholder_left_untouched(self):
        # Arrange: braces that reference nothing should not be destroyed.
        data = {"value": "{{ does_not_exist }}"}

        resolved = resolve_placeholders(data)

        assert resolved["value"] == "{{ does_not_exist }}"

    def test_non_placeholder_strings_unchanged(self):
        data = {"a": "plain text", "n": 5, "flag": True}

        resolved = resolve_placeholders(data)

        assert resolved == data

    def test_process_placeholders_alias_matches_function(self):
        wwyaml = WorkingWithYAML()
        cfg = {"meta": {"library": "assetutilities"}, "x": "{{ meta.library }}"}

        assert wwyaml.process_placeholders(cfg)["x"] == "assetutilities"


class TestPlaceholderHelper:
    """test_variable_placeholder resolves placeholders then reports reusability."""

    def test_helper_resolves_and_reports(self):
        wwyaml = WorkingWithYAML()
        cfg = {
            "meta": {"library": "assetutilities"},
            "test_variables": {"flag": True, "method": "placeholder"},
            "placeholder_tests": {
                "method": "{{ test_variables.method }}",
                "library": "{{ meta.library }}",
            },
        }

        ok, method = wwyaml.test_variable_placeholder(cfg)

        assert ok is True
        assert method == "placeholder"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
