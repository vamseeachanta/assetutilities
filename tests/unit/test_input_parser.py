# ABOUTME: Tests for input_parser module — config value parsing into TrackedQuantity.
# ABOUTME: Validates unit inference from field names, unit systems, and explicit overrides.

import pytest

from assetutilities.units.input_parser import (
    FIELD_QUANTITY_MAP,
    UNIT_SYSTEMS,
    parse_config_section,
    parse_config_value,
)
from assetutilities.units.quantity import TrackedQuantity


class TestParseConfigValue:
    def test_numeric_with_known_field_returns_tracked_quantity(self):
        result = parse_config_value(0.025, "thickness", unit_system="SI")
        assert isinstance(result, TrackedQuantity)
        assert float(result) == pytest.approx(0.025)
        assert str(result.units) == "meter"

    def test_explicit_unit_overrides_inference(self):
        result = parse_config_value(100.0, "thickness", explicit_unit="mm")
        assert isinstance(result, TrackedQuantity)
        assert str(result.units) == "millimeter"

    def test_inch_unit_system(self):
        result = parse_config_value(1.5, "thickness", unit_system="inch")
        assert isinstance(result, TrackedQuantity)
        assert str(result.units) == "inch"

    def test_metric_engineering_unit_system(self):
        result = parse_config_value(210000.0, "youngs_modulus", unit_system="metric_engineering")
        assert isinstance(result, TrackedQuantity)
        assert str(result.units) == "megapascal"

    def test_unknown_field_returns_raw_value(self):
        result = parse_config_value(42.0, "unknown_field")
        assert result == 42.0
        assert not isinstance(result, TrackedQuantity)

    def test_non_numeric_returns_raw_value(self):
        result = parse_config_value("steel", "material")
        assert result == "steel"
        assert not isinstance(result, TrackedQuantity)

    def test_unknown_unit_system_raises(self):
        with pytest.raises(ValueError, match="Unknown unit system"):
            parse_config_value(1.0, "thickness", unit_system="martian")

    def test_provenance_records_source(self):
        result = parse_config_value(
            10.0, "depth", unit_system="SI", source="config/pipe.yml"
        )
        assert isinstance(result, TrackedQuantity)
        assert any(
            p.source == "config/pipe.yml" for p in result.provenance
        )

    def test_stress_field_si(self):
        result = parse_config_value(210e9, "youngs_modulus", unit_system="SI")
        assert isinstance(result, TrackedQuantity)
        assert str(result.units) == "pascal"

    def test_stress_field_inch_system(self):
        result = parse_config_value(30e6, "youngs_modulus", unit_system="inch")
        assert isinstance(result, TrackedQuantity)
        # pint uses canonical name 'pound_force_per_square_inch' for psi
        unit_str = str(result.units)
        assert unit_str in ("psi", "pound_force_per_square_inch")

    def test_force_field(self):
        result = parse_config_value(1000.0, "force", unit_system="SI")
        assert isinstance(result, TrackedQuantity)
        assert str(result.units) == "newton"

    def test_temperature_field(self):
        result = parse_config_value(20.0, "temperature", unit_system="SI")
        assert isinstance(result, TrackedQuantity)


class TestParseConfigSection:
    def test_mixed_config_dict(self):
        config = {
            "thickness": 0.025,
            "breadth": 0.3,
            "material": "steel",
            "youngs_modulus": 210e9,
        }
        result = parse_config_section(config, unit_system="SI", source="test.yml")

        assert isinstance(result["thickness"], TrackedQuantity)
        assert isinstance(result["breadth"], TrackedQuantity)
        assert result["material"] == "steel"
        assert isinstance(result["youngs_modulus"], TrackedQuantity)

    def test_all_values_have_provenance(self):
        config = {"thickness": 0.025, "depth": 100.0}
        result = parse_config_section(config, source="myconfig.yml")

        for key in ["thickness", "depth"]:
            tq = result[key]
            assert isinstance(tq, TrackedQuantity)
            assert len(tq.provenance) >= 1

    def test_empty_config(self):
        result = parse_config_section({})
        assert result == {}
