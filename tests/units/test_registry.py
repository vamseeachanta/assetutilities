# ABOUTME: Tests for the singleton pint UnitRegistry with custom units.
# ABOUTME: Verifies custom energy/offshore unit definitions and conversions.

import pytest
import pint

from assetutilities.units.registry import get_registry


class TestGetRegistry:
    def test_get_registry_returns_unit_registry(self):
        ureg = get_registry()
        assert isinstance(ureg, pint.UnitRegistry)

    def test_get_registry_singleton(self):
        ureg1 = get_registry()
        ureg2 = get_registry()
        assert ureg1 is ureg2


class TestCustomEnergyUnits:
    def test_custom_unit_boe_defined(self):
        ureg = get_registry()
        q = ureg.Quantity(1, "BOE")
        assert q.magnitude == 1

    def test_custom_unit_mcf_defined(self):
        ureg = get_registry()
        q = ureg.Quantity(1, "MCF")
        assert q.magnitude == 1

    def test_custom_unit_mmbtu_defined(self):
        ureg = get_registry()
        q = ureg.Quantity(1, "MMBTU")
        assert q.magnitude == 1

    def test_custom_unit_toe_defined(self):
        ureg = get_registry()
        q = ureg.Quantity(1, "TOE")
        assert q.magnitude == 1


class TestUnitConversions:
    def test_boe_to_mmbtu_conversion(self):
        ureg = get_registry()
        q = ureg.Quantity(1, "BOE")
        converted = q.to("MMBTU")
        # 1 BOE = 5.8e6 BTU, 1 MMBTU = 1e6 BTU => 5.8 MMBTU
        assert converted.magnitude == pytest.approx(5.8, rel=1e-3)

    def test_mcf_to_boe_conversion(self):
        ureg = get_registry()
        q = ureg.Quantity(1, "MCF")
        converted = q.to("BOE")
        # 1 MCF = 1.028e6 BTU, 1 BOE = 5.8e6 BTU => ~0.17724 BOE
        assert converted.magnitude == pytest.approx(0.17724, rel=1e-2)

    def test_ksi_to_psi_conversion(self):
        ureg = get_registry()
        q = ureg.Quantity(1, "ksi")
        converted = q.to("psi")
        assert converted.magnitude == pytest.approx(1000.0, rel=1e-6)


class TestStandardUnits:
    def test_standard_si_units_work(self):
        ureg = get_registry()
        length = ureg.Quantity(1, "meter")
        pressure = ureg.Quantity(1, "Pa")
        force = ureg.Quantity(1, "N")
        assert length.magnitude == 1
        assert pressure.magnitude == 1
        assert force.magnitude == 1

    def test_incompatible_units_raises(self):
        ureg = get_registry()
        m = ureg.Quantity(1, "meter")
        s = ureg.Quantity(1, "second")
        with pytest.raises(pint.errors.DimensionalityError):
            m + s
