# ABOUTME: Tests for the @unit_checked decorator.
# ABOUTME: Validates unit conversion, backward compatibility, and provenance tracking.

import pytest

from assetutilities.units.computation import unit_checked
from assetutilities.units.quantity import TrackedQuantity


@unit_checked(youngs_modulus="Pa", thickness="m", breadth="m", _return="Pa")
def calc_buckling_stress(youngs_modulus, thickness, breadth):
    """Simplified elastic buckling stress for testing."""
    return youngs_modulus * (thickness / breadth) ** 2


@unit_checked(length="m", force="N", _return="Pa")
def calc_pressure(length, force, area):
    """Test function where 'area' has no unit spec."""
    return force / area


class TestUnitCheckedWithRawFloats:
    def test_raw_floats_pass_through(self):
        result = calc_buckling_stress(210e9, 0.025, 0.3)
        assert isinstance(result, (int, float))
        expected = 210e9 * (0.025 / 0.3) ** 2
        assert result == pytest.approx(expected)

    def test_raw_floats_no_tracked_return(self):
        result = calc_buckling_stress(210e9, 0.025, 0.3)
        assert not isinstance(result, TrackedQuantity)


class TestUnitCheckedWithTrackedQuantity:
    def test_tracked_quantities_converted_and_result_tracked(self):
        E = TrackedQuantity(210e9, "Pa", source="config")
        t = TrackedQuantity(0.025, "m", source="config")
        b = TrackedQuantity(0.3, "m", source="config")
        result = calc_buckling_stress(E, t, b)

        assert isinstance(result, TrackedQuantity)
        expected = 210e9 * (0.025 / 0.3) ** 2
        assert float(result) == pytest.approx(expected)
        assert str(result.units) == "pascal"

    def test_auto_converts_units(self):
        E = TrackedQuantity(30e6, "psi", source="config")
        t = TrackedQuantity(25.0, "mm", source="config")
        b = TrackedQuantity(300.0, "mm", source="config")
        result = calc_buckling_stress(E, t, b)

        assert isinstance(result, TrackedQuantity)
        assert str(result.units) == "pascal"
        # E in Pa: 30e6 * 6894.757... ≈ 2.068e11
        # (t/b)^2 = (0.025/0.3)^2
        E_pa = 30e6 * 6894.757293168
        expected = E_pa * (0.025 / 0.3) ** 2
        assert float(result) == pytest.approx(expected, rel=1e-3)

    def test_provenance_propagated(self):
        E = TrackedQuantity(210e9, "Pa", source="input_file")
        t = TrackedQuantity(0.025, "m", source="input_file")
        b = TrackedQuantity(0.3, "m", source="input_file")
        result = calc_buckling_stress(E, t, b)

        assert len(result.provenance) >= 3
        sources = [p.source for p in result.provenance]
        assert any("input_file" in s for s in sources)


class TestUnitCheckedMixedArgs:
    def test_mixed_tracked_and_float(self):
        E = TrackedQuantity(210e9, "Pa", source="config")
        result = calc_buckling_stress(E, 0.025, 0.3)
        assert isinstance(result, TrackedQuantity)
        expected = 210e9 * (0.025 / 0.3) ** 2
        assert float(result) == pytest.approx(expected)

    def test_unspecified_param_passes_through(self):
        length = TrackedQuantity(2.0, "m", source="config")
        force = TrackedQuantity(1000.0, "N", source="config")
        result = calc_pressure(length, force, 0.5)

        assert isinstance(result, TrackedQuantity)
        assert float(result) == pytest.approx(1000.0 / 0.5)


class TestUnitCheckedPreservesMetadata:
    def test_function_name_preserved(self):
        assert calc_buckling_stress.__name__ == "calc_buckling_stress"

    def test_docstring_preserved(self):
        assert "Simplified elastic buckling" in calc_buckling_stress.__doc__
