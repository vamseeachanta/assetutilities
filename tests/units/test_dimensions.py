# ABOUTME: Tests for dimension analysis API on TrackedQuantity.
# ABOUTME: Covers .dimensions, .is_compatible(), and .check_dimensions().

import pytest

from assetutilities.units import TrackedQuantity


class TestDimensionsProperty:
    """TrackedQuantity.dimensions returns human-readable dimensionality."""

    def test_length_dimensions(self):
        q = TrackedQuantity(10.0, "m", source="test")
        assert q.dimensions == "[length]"

    def test_pressure_dimensions(self):
        q = TrackedQuantity(100.0, "Pa", source="test")
        assert q.dimensions == "[mass] / [length] / [time] ** 2"

    def test_force_dimensions(self):
        q = TrackedQuantity(50.0, "N", source="test")
        assert q.dimensions == "[mass] * [length] / [time] ** 2"

    def test_dimensionless(self):
        q = TrackedQuantity(3.14, "dimensionless", source="test")
        assert q.dimensions == "dimensionless"

    def test_compound_dimensions(self):
        # kg/m^3 = mass / length^3
        q = TrackedQuantity(1025.0, "kg/m**3", source="test")
        assert "[mass]" in q.dimensions
        assert "[length]" in q.dimensions


class TestIsCompatible:
    """TrackedQuantity.is_compatible checks dimensional compatibility."""

    def test_same_unit_compatible(self):
        a = TrackedQuantity(10.0, "m", source="test")
        b = TrackedQuantity(5.0, "m", source="test")
        assert a.is_compatible(b) is True

    def test_same_dimension_different_unit_compatible(self):
        a = TrackedQuantity(10.0, "m", source="test")
        b = TrackedQuantity(33.0, "ft", source="test")
        assert a.is_compatible(b) is True

    def test_different_dimensions_incompatible(self):
        a = TrackedQuantity(10.0, "m", source="test")
        b = TrackedQuantity(5.0, "kg", source="test")
        assert a.is_compatible(b) is False

    def test_pressure_units_compatible(self):
        a = TrackedQuantity(100.0, "kPa", source="test")
        b = TrackedQuantity(14.7, "psi", source="test")
        assert a.is_compatible(b) is True

    def test_force_and_pressure_incompatible(self):
        a = TrackedQuantity(50.0, "kN", source="test")
        b = TrackedQuantity(100.0, "kPa", source="test")
        assert a.is_compatible(b) is False

    def test_compatible_with_string_unit(self):
        a = TrackedQuantity(10.0, "m", source="test")
        assert a.is_compatible("ft") is True
        assert a.is_compatible("kg") is False


class TestCheckDimensions:
    """TrackedQuantity.check_dimensions validates against expected dimension."""

    def test_check_length_passes(self):
        q = TrackedQuantity(10.0, "m", source="test")
        q.check_dimensions("[length]")  # should not raise

    def test_check_wrong_dimension_raises(self):
        q = TrackedQuantity(10.0, "m", source="test")
        with pytest.raises(ValueError, match="length.*mass"):
            q.check_dimensions("[mass]")

    def test_check_pressure_passes(self):
        q = TrackedQuantity(100.0, "kPa", source="test")
        q.check_dimensions("[mass] / [length] / [time] ** 2")

    def test_check_with_unit_string(self):
        # Accept a unit string — check if compatible with that unit's dimensions
        q = TrackedQuantity(10.0, "m", source="test")
        q.check_dimensions("ft")  # ft is length, should pass

    def test_check_with_incompatible_unit_string_raises(self):
        q = TrackedQuantity(10.0, "m", source="test")
        with pytest.raises(ValueError):
            q.check_dimensions("kg")
