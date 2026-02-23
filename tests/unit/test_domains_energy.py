# ABOUTME: Compatibility tests for the energy domain adapter vs worldenergydata constants.
# ABOUTME: Validates that pint-backed conversions match hardcoded conversion factors.

import pytest

from assetutilities.units.domains.energy import (
    EnergyUnitMapping,
    convert_energy_units,
)


class TestEnergyUnitMappingCoverage:
    def test_all_worldenergydata_enums_mapped(self):
        expected_keys = {
            "BTU", "MMBTU", "THERM", "GJ", "MWH", "KWH", "TOE", "BOE",
            "BBL", "BBL_OIL", "GAL", "L", "M3",
            "MCF", "MMCF", "BCF", "TCF", "SCF",
            "TONNE", "SHORT_TON", "LONG_TON", "KG", "LB",
        }
        assert set(EnergyUnitMapping.keys()) == expected_keys


class TestEnergyConversionsMatchWorldEnergyData:
    """Verify pint conversions match the hardcoded UNIT_CONVERSIONS from worldenergydata.

    Tolerances are set to match the precision of the hardcoded values (typically
    3-4 significant figures).
    """

    def test_boe_to_mmbtu(self):
        result = convert_energy_units(1.0, "BOE", "MMBTU")
        assert result == pytest.approx(5.8, rel=1e-3)

    def test_boe_to_btu(self):
        result = convert_energy_units(1.0, "BOE", "BTU")
        assert result == pytest.approx(5.8e6, rel=1e-3)

    def test_mcf_to_btu(self):
        result = convert_energy_units(1.0, "MCF", "BTU")
        assert result == pytest.approx(1.028e6, rel=1e-3)

    def test_mcf_to_boe(self):
        result = convert_energy_units(1.0, "MCF", "BOE")
        assert result == pytest.approx(0.17724, rel=1e-2)

    def test_mcf_to_mmbtu(self):
        result = convert_energy_units(1.0, "MCF", "MMBTU")
        assert result == pytest.approx(1.028, rel=1e-3)

    def test_toe_to_boe(self):
        result = convert_energy_units(1.0, "TOE", "BOE")
        assert result == pytest.approx(6.841, rel=1e-2)

    def test_toe_to_gj(self):
        result = convert_energy_units(1.0, "TOE", "MMBTU")
        assert result == pytest.approx(39.68, rel=1e-2)

    def test_mmbtu_to_gj(self):
        result = convert_energy_units(1.0, "MMBTU", "GJ")
        assert result == pytest.approx(1.0545, rel=1e-3)

    def test_mwh_to_btu(self):
        result = convert_energy_units(1.0, "MWH", "BTU")
        assert result == pytest.approx(3412141.63, rel=1e-3)

    def test_kwh_to_btu(self):
        result = convert_energy_units(1.0, "KWH", "BTU")
        assert result == pytest.approx(3412.14, rel=1e-3)


class TestEnergyMassConversions:
    def test_tonne_to_kg(self):
        result = convert_energy_units(1.0, "TONNE", "KG")
        assert result == pytest.approx(1000.0, rel=1e-6)

    def test_tonne_to_lb(self):
        result = convert_energy_units(1.0, "TONNE", "LB")
        assert result == pytest.approx(2204.62, rel=1e-3)

    def test_kg_to_lb(self):
        result = convert_energy_units(1.0, "KG", "LB")
        assert result == pytest.approx(2.20462, rel=1e-4)

    def test_short_ton_to_tonne(self):
        result = convert_energy_units(1.0, "SHORT_TON", "TONNE")
        assert result == pytest.approx(0.9072, rel=1e-3)


class TestEnergyVolumeConversions:
    def test_barrel_to_gallon(self):
        result = convert_energy_units(1.0, "BBL", "GAL")
        assert result == pytest.approx(42.0, rel=1e-3)

    def test_barrel_to_liter(self):
        result = convert_energy_units(1.0, "BBL", "L")
        assert result == pytest.approx(158.987, rel=1e-3)

    def test_mcf_to_mmcf(self):
        result = convert_energy_units(1000.0, "MCF", "MMCF")
        assert result == pytest.approx(1.0, rel=1e-6)

    def test_bcf_to_mcf(self):
        result = convert_energy_units(1.0, "BCF", "MCF")
        assert result == pytest.approx(1e6, rel=1e-6)


class TestEnergyEdgeCases:
    def test_same_unit_returns_same_value(self):
        result = convert_energy_units(42.0, "BTU", "BTU")
        assert result == pytest.approx(42.0)

    def test_unknown_from_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown energy unit"):
            convert_energy_units(1.0, "UNKNOWN", "BTU")

    def test_unknown_to_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown energy unit"):
            convert_energy_units(1.0, "BTU", "UNKNOWN")

    def test_zero_converts_to_zero(self):
        result = convert_energy_units(0.0, "BOE", "BTU")
        assert result == 0.0
