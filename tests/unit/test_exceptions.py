# ABOUTME: Tests for UnitMismatchError engineering-friendly exception.
# ABOUTME: Verifies clear error messages for unit dimension mismatches.

import pytest

from assetutilities.units.exceptions import UnitMismatchError
from assetutilities.units.quantity import TrackedQuantity


class TestUnitMismatchErrorCreation:
    def test_create_with_message(self):
        err = UnitMismatchError("Cannot add pressure to length")
        assert "pressure" in str(err)
        assert "length" in str(err)

    def test_create_from_dimensions(self):
        err = UnitMismatchError.from_dimensions(
            operation="add",
            left_unit="Pa",
            right_unit="m",
        )
        assert "add" in str(err).lower()
        assert "Pa" in str(err) or "pascal" in str(err).lower()
        assert "m" in str(err) or "meter" in str(err).lower()

    def test_is_exception(self):
        err = UnitMismatchError("test")
        assert isinstance(err, Exception)

    def test_preserves_original_error(self):
        original = ValueError("pint error")
        err = UnitMismatchError("wrapped", original_error=original)
        assert err.original_error is original


class TestTrackedQuantityMismatchError:
    """Verify TrackedQuantity raises UnitMismatchError for incompatible operations."""

    def test_add_incompatible_raises_unit_mismatch(self):
        a = TrackedQuantity(100.0, "Pa", source="test")
        b = TrackedQuantity(1.0, "m", source="test")
        with pytest.raises(UnitMismatchError):
            a + b

    def test_subtract_incompatible_raises_unit_mismatch(self):
        a = TrackedQuantity(10.0, "m", source="test")
        b = TrackedQuantity(5.0, "kg", source="test")
        with pytest.raises(UnitMismatchError):
            a - b

    def test_mismatch_error_has_helpful_message(self):
        a = TrackedQuantity(100.0, "Pa", source="sensor_1")
        b = TrackedQuantity(1.0, "m", source="input_file")
        with pytest.raises(UnitMismatchError, match="(?i)add"):
            a + b

    def test_compatible_add_still_works(self):
        a = TrackedQuantity(100.0, "Pa", source="test")
        b = TrackedQuantity(200.0, "Pa", source="test")
        result = a + b
        assert result.magnitude == pytest.approx(300.0)

    def test_compatible_add_different_units_works(self):
        a = TrackedQuantity(1.0, "kPa", source="test")
        b = TrackedQuantity(500.0, "Pa", source="test")
        result = a + b
        # pint returns result in left operand's unit (kPa)
        assert result.magnitude == pytest.approx(1.5)
