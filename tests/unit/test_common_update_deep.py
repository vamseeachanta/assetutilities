# ABOUTME: Tests for common/update_deep.py — deep dictionary merge utilities.
# ABOUTME: Covers AttributeDict and update_deep_dictionary with nominal and edge cases.

import pytest

from assetutilities.common.update_deep import AttributeDict, update_deep_dictionary


class TestUpdateDeepDictionary:
    """Tests for update_deep_dictionary — recursive dict merge."""

    def test_update_shallow_key(self):
        # Arrange
        base = {"a": 1, "b": 2}
        updates = {"b": 99}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["b"] == 99
        assert result["a"] == 1

    def test_update_nested_key(self):
        # Arrange
        base = {"outer": {"inner": 1, "other": 2}}
        updates = {"outer": {"inner": 42}}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["outer"]["inner"] == 42
        assert result["outer"]["other"] == 2

    def test_add_new_top_level_key(self):
        # Arrange
        base = {"a": 1}
        updates = {"b": 2}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["b"] == 2
        assert result["a"] == 1

    def test_add_new_nested_key(self):
        # Arrange
        base = {"outer": {"existing": 1}}
        updates = {"outer": {"new_key": 99}}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["outer"]["new_key"] == 99
        assert result["outer"]["existing"] == 1

    def test_three_level_nesting(self):
        # Arrange
        base = {"a": {"b": {"c": 1, "d": 2}}}
        updates = {"a": {"b": {"c": 99}}}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["a"]["b"]["c"] == 99
        assert result["a"]["b"]["d"] == 2

    def test_empty_update_leaves_base_unchanged(self):
        # Arrange
        base = {"a": 1, "b": {"c": 2}}
        updates = {}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result == {"a": 1, "b": {"c": 2}}

    def test_update_with_list_value(self):
        # Arrange
        base = {"items": [1, 2, 3]}
        updates = {"items": [4, 5, 6]}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["items"] == [4, 5, 6]

    def test_update_with_none_value(self):
        # Arrange
        base = {"key": "original"}
        updates = {"key": None}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["key"] is None

    def test_non_mapping_base_gets_replaced(self):
        # Arrange: when d is not a mapping, it should be replaced by u
        d = "not_a_dict"
        u = {"a": 1}

        # Act
        result = update_deep_dictionary(d, u)

        # Assert — function sets d = u when d is not a Mapping
        assert result == {"a": 1}

    def test_update_preserves_unmentioned_siblings(self):
        # Arrange
        base = {"sibling1": {"x": 1, "y": 2}, "sibling2": {"z": 3}}
        updates = {"sibling1": {"x": 100}}

        # Act
        result = update_deep_dictionary(base, updates)

        # Assert
        assert result["sibling1"]["x"] == 100
        assert result["sibling1"]["y"] == 2
        assert result["sibling2"]["z"] == 3


class TestAttributeDict:
    """Tests for AttributeDict — dict subclass with attribute-style access."""

    def test_attribute_access_returns_value(self):
        # Arrange
        d = AttributeDict({"key": "value"})

        # Act / Assert
        assert d.key == "value"

    def test_item_access_returns_value(self):
        # Arrange
        d = AttributeDict({"key": "value"})

        # Act / Assert
        assert d["key"] == "value"

    def test_attribute_and_item_access_consistent(self):
        # Arrange
        d = AttributeDict({"alpha": 42})

        # Act / Assert
        assert d.alpha == d["alpha"]

    def test_set_via_attribute(self):
        # Arrange
        d = AttributeDict()

        # Act
        d.new_key = "hello"

        # Assert
        assert d["new_key"] == "hello"

    def test_set_via_item(self):
        # Arrange
        d = AttributeDict()

        # Act
        d["item_key"] = 123

        # Assert
        assert d.item_key == 123

    def test_initialise_with_kwargs(self):
        # Arrange / Act
        d = AttributeDict(x=10, y=20)

        # Assert
        assert d.x == 10
        assert d.y == 20

    def test_nested_dict_not_auto_converted(self):
        # Arrange: nested plain dict stays as dict
        d = AttributeDict({"outer": {"inner": 1}})

        # Act / Assert
        assert isinstance(d["outer"], dict)
        assert d["outer"]["inner"] == 1

    def test_empty_attribute_dict(self):
        # Arrange / Act
        d = AttributeDict()

        # Assert
        assert len(d) == 0

    def test_is_subclass_of_dict(self):
        # Act
        d = AttributeDict({"a": 1})

        # Assert
        assert isinstance(d, dict)
