# ABOUTME: Tests for UnitSystemPolicy project-wide unit enforcement.
# ABOUTME: Verifies validation, conversion, and strict mode behavior.

import pytest

from assetutilities.units.policy import UnitSystemPolicy
from assetutilities.units.quantity import TrackedQuantity


class TestPolicyCreation:
    def test_create_si_policy(self):
        policy = UnitSystemPolicy(system="SI")
        assert policy.system == "SI"

    def test_create_with_strict_mode(self):
        policy = UnitSystemPolicy(system="SI", strict=True)
        assert policy.strict is True

    def test_create_with_auto_convert(self):
        policy = UnitSystemPolicy(system="SI", auto_convert=True)
        assert policy.auto_convert is True

    def test_unknown_system_raises(self):
        with pytest.raises(ValueError, match="Unknown unit system"):
            UnitSystemPolicy(system="martian")


class TestPolicyValidate:
    """Verify validate() checks if a TrackedQuantity conforms to the policy."""

    def test_validate_correct_unit_passes(self):
        policy = UnitSystemPolicy(system="SI")
        tq = TrackedQuantity(100.0, "m", source="test")
        assert policy.validate(tq, "length") is True

    def test_validate_wrong_unit_fails(self):
        policy = UnitSystemPolicy(system="SI")
        tq = TrackedQuantity(100.0, "inch", source="test")
        assert policy.validate(tq, "length") is False

    def test_validate_compatible_dimension_wrong_unit_fails(self):
        policy = UnitSystemPolicy(system="SI")
        tq = TrackedQuantity(100.0, "mm", source="test")
        # mm is length but SI expects "m"
        assert policy.validate(tq, "length") is False

    def test_validate_unknown_quantity_type_passes(self):
        policy = UnitSystemPolicy(system="SI")
        tq = TrackedQuantity(100.0, "m", source="test")
        # Unknown quantity types pass validation (no rule to check against)
        assert policy.validate(tq, "some_custom_type") is True


class TestPolicyEnforce:
    """Verify enforce() converts or raises based on policy settings."""

    def test_enforce_auto_convert_converts(self):
        policy = UnitSystemPolicy(system="SI", auto_convert=True)
        tq = TrackedQuantity(1000.0, "mm", source="test")
        result = policy.enforce(tq, "length")
        assert result.magnitude == pytest.approx(1.0)
        assert str(result.units) == "meter"

    def test_enforce_auto_convert_preserves_provenance(self):
        policy = UnitSystemPolicy(system="SI", auto_convert=True)
        tq = TrackedQuantity(1000.0, "mm", source="test")
        result = policy.enforce(tq, "length")
        assert len(result.provenance) >= 2  # created + converted

    def test_enforce_strict_wrong_unit_raises(self):
        policy = UnitSystemPolicy(system="SI", strict=True, auto_convert=False)
        tq = TrackedQuantity(100.0, "inch", source="test")
        with pytest.raises(ValueError, match="(?i)expected.*m"):
            policy.enforce(tq, "length")

    def test_enforce_strict_correct_unit_passes(self):
        policy = UnitSystemPolicy(system="SI", strict=True, auto_convert=False)
        tq = TrackedQuantity(100.0, "m", source="test")
        result = policy.enforce(tq, "length")
        assert result.magnitude == pytest.approx(100.0)

    def test_enforce_unknown_quantity_returns_unchanged(self):
        policy = UnitSystemPolicy(system="SI", auto_convert=True)
        tq = TrackedQuantity(42.0, "furlong", source="test")
        result = policy.enforce(tq, "unknown_type")
        assert result.magnitude == pytest.approx(42.0)

    def test_enforce_imperial_system(self):
        policy = UnitSystemPolicy(system="inch", auto_convert=True)
        tq = TrackedQuantity(1.0, "m", source="test")
        result = policy.enforce(tq, "length")
        assert result.magnitude == pytest.approx(39.3701, rel=1e-3)
        assert "inch" in str(result.units)

    def test_enforce_metric_engineering_pressure(self):
        policy = UnitSystemPolicy(system="metric_engineering", auto_convert=True)
        tq = TrackedQuantity(1e6, "Pa", source="test")
        result = policy.enforce(tq, "pressure")
        assert result.magnitude == pytest.approx(1.0)
        assert "megapascal" in str(result.units)
