# ABOUTME: Tests for TrackedQuantity provenance-tracking wrapper.
# ABOUTME: Verifies creation, conversion, arithmetic, and serialization.

import pytest
import pint

from assetutilities.units.quantity import ProvenanceEntry, TrackedQuantity


class TestTrackedQuantityCreation:
    def test_create_tracked_quantity(self):
        tq = TrackedQuantity(100.0, "Pa", source="test")
        assert tq is not None

    def test_magnitude_property(self):
        tq = TrackedQuantity(42.5, "Pa", source="test")
        assert tq.magnitude == pytest.approx(42.5)

    def test_units_property(self):
        tq = TrackedQuantity(1.0, "meter", source="test")
        assert str(tq.units) == "meter"

    def test_float_conversion(self):
        tq = TrackedQuantity(3.14, "Pa", source="test")
        assert float(tq) == pytest.approx(3.14)


class TestTrackedQuantityConversion:
    def test_to_conversion(self):
        tq = TrackedQuantity(1000.0, "Pa", source="test")
        converted = tq.to("kPa")
        assert converted.magnitude == pytest.approx(1.0)

    def test_provenance_recorded_on_creation(self):
        tq = TrackedQuantity(1.0, "Pa", source="sensor_a")
        assert len(tq.provenance) >= 1
        assert tq.provenance[0].operation == "created"

    def test_provenance_grows_on_conversion(self):
        tq = TrackedQuantity(1000.0, "Pa", source="sensor_a")
        initial_count = len(tq.provenance)
        converted = tq.to("kPa")
        assert len(converted.provenance) > initial_count


class TestTrackedQuantityArithmetic:
    def test_add_compatible_units(self):
        a = TrackedQuantity(100.0, "Pa", source="a")
        b = TrackedQuantity(200.0, "Pa", source="b")
        result = a + b
        assert result.magnitude == pytest.approx(300.0)

    def test_add_incompatible_raises(self):
        a = TrackedQuantity(1.0, "Pa", source="a")
        b = TrackedQuantity(1.0, "meter", source="b")
        with pytest.raises(pint.errors.DimensionalityError):
            a + b

    def test_subtract_compatible(self):
        a = TrackedQuantity(300.0, "Pa", source="a")
        b = TrackedQuantity(100.0, "Pa", source="b")
        result = a - b
        assert result.magnitude == pytest.approx(200.0)

    def test_multiply(self):
        a = TrackedQuantity(10.0, "meter", source="a")
        b = TrackedQuantity(5.0, "meter", source="b")
        result = a * b
        assert result.magnitude == pytest.approx(50.0)

    def test_divide(self):
        a = TrackedQuantity(100.0, "meter", source="a")
        b = TrackedQuantity(5.0, "second", source="b")
        result = a / b
        assert result.magnitude == pytest.approx(20.0)

    def test_arithmetic_propagates_provenance(self):
        a = TrackedQuantity(10.0, "Pa", source="sensor_1")
        b = TrackedQuantity(20.0, "Pa", source="sensor_2")
        result = a + b
        # Should have provenance from both a and b, plus the add operation
        assert len(result.provenance) >= len(a.provenance) + len(b.provenance)


class TestTrackedQuantitySerialization:
    def test_to_dict_roundtrip(self):
        tq = TrackedQuantity(42.0, "Pa", source="test")
        data = tq.to_dict()
        restored = TrackedQuantity.from_dict(data)
        assert restored.magnitude == pytest.approx(tq.magnitude)
        assert str(restored.units) == str(tq.units)

    def test_repr(self):
        tq = TrackedQuantity(1.0, "Pa", source="test")
        text = repr(tq)
        assert "1.0" in text
        assert "pascal" in text or "Pa" in text
