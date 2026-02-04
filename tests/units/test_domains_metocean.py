# ABOUTME: Compatibility tests for the metocean domain adapter vs worldenergydata UnitConverter.
# ABOUTME: Validates pint-backed conversions match hardcoded conversion factors.

import pytest

from assetutilities.units.domains.metocean import (
    convert_length,
    convert_pressure,
    convert_speed,
    convert_temperature,
)


class TestSpeedConversions:
    """Match worldenergydata UnitConverter speed conversion factors."""

    KTS_TO_MS = 0.514444
    KMH_TO_MS = 0.277778
    MPH_TO_MS = 0.44704
    FPS_TO_MS = 0.3048

    def test_knots_to_ms(self):
        result = convert_speed(25.0, "knots", "m/s")
        expected = 25.0 * self.KTS_TO_MS
        assert result == pytest.approx(expected, rel=1e-4)

    def test_kmh_to_ms(self):
        result = convert_speed(100.0, "km/h", "m/s")
        expected = 100.0 * self.KMH_TO_MS
        assert result == pytest.approx(expected, rel=1e-4)

    def test_mph_to_ms(self):
        result = convert_speed(60.0, "mph", "m/s")
        expected = 60.0 * self.MPH_TO_MS
        assert result == pytest.approx(expected, rel=1e-4)

    def test_fps_to_ms(self):
        result = convert_speed(10.0, "ft/s", "m/s")
        expected = 10.0 * self.FPS_TO_MS
        assert result == pytest.approx(expected, rel=1e-4)

    def test_ms_to_knots(self):
        result = convert_speed(12.86, "m/s", "knots")
        expected = 12.86 / self.KTS_TO_MS
        assert result == pytest.approx(expected, rel=1e-4)

    def test_ms_identity(self):
        result = convert_speed(5.0, "m/s", "m/s")
        assert result == pytest.approx(5.0)

    def test_none_returns_none(self):
        assert convert_speed(None, "knots") is None


class TestLengthConversions:
    """Match worldenergydata UnitConverter length conversion factors."""

    FT_TO_M = 0.3048
    IN_TO_M = 0.0254
    CM_TO_M = 0.01
    MM_TO_M = 0.001
    NM_TO_M = 1852.0
    KM_TO_M = 1000.0

    def test_feet_to_m(self):
        result = convert_length(6.5, "feet", "m")
        expected = 6.5 * self.FT_TO_M
        assert result == pytest.approx(expected, rel=1e-4)

    def test_inches_to_m(self):
        result = convert_length(12.0, "inches", "m")
        expected = 12.0 * self.IN_TO_M
        assert result == pytest.approx(expected, rel=1e-4)

    def test_cm_to_m(self):
        result = convert_length(250.0, "cm", "m")
        expected = 250.0 * self.CM_TO_M
        assert result == pytest.approx(expected, rel=1e-4)

    def test_mm_to_m(self):
        result = convert_length(1500.0, "mm", "m")
        expected = 1500.0 * self.MM_TO_M
        assert result == pytest.approx(expected, rel=1e-4)

    def test_nm_to_m(self):
        result = convert_length(1.0, "nm", "m")
        expected = 1.0 * self.NM_TO_M
        assert result == pytest.approx(expected, rel=1e-4)

    def test_km_to_m(self):
        result = convert_length(5.0, "km", "m")
        expected = 5.0 * self.KM_TO_M
        assert result == pytest.approx(expected, rel=1e-4)

    def test_m_to_feet(self):
        result = convert_length(1.0, "m", "feet")
        expected = 1.0 / self.FT_TO_M
        assert result == pytest.approx(expected, rel=1e-4)

    def test_none_returns_none(self):
        assert convert_length(None, "feet") is None


class TestTemperatureConversions:
    """Match worldenergydata UnitConverter temperature conversions."""

    def test_fahrenheit_to_celsius(self):
        result = convert_temperature(75.0, "fahrenheit", "celsius")
        expected = (75.0 - 32) * 5 / 9
        assert result == pytest.approx(expected, rel=1e-4)

    def test_kelvin_to_celsius(self):
        result = convert_temperature(300.0, "kelvin", "celsius")
        expected = 300.0 - 273.15
        assert result == pytest.approx(expected, rel=1e-4)

    def test_celsius_to_fahrenheit(self):
        result = convert_temperature(20.0, "celsius", "fahrenheit")
        expected = 20.0 * 9 / 5 + 32
        assert result == pytest.approx(expected, rel=1e-4)

    def test_celsius_identity(self):
        result = convert_temperature(25.0, "celsius", "celsius")
        assert result == pytest.approx(25.0)

    def test_none_returns_none(self):
        assert convert_temperature(None, "fahrenheit") is None


class TestPressureConversions:
    """Match worldenergydata UnitConverter pressure conversion factors."""

    PA_TO_HPA = 0.01
    KPA_TO_HPA = 10.0
    INHG_TO_HPA = 33.8639
    MMHG_TO_HPA = 1.33322
    ATM_TO_HPA = 1013.25
    PSI_TO_HPA = 68.9476

    def test_pa_to_hpa(self):
        result = convert_pressure(101325.0, "Pa", "hPa")
        expected = 101325.0 * self.PA_TO_HPA
        assert result == pytest.approx(expected, rel=1e-3)

    def test_kpa_to_hpa(self):
        result = convert_pressure(101.325, "kPa", "hPa")
        expected = 101.325 * self.KPA_TO_HPA
        assert result == pytest.approx(expected, rel=1e-3)

    def test_inhg_to_hpa(self):
        result = convert_pressure(29.92, "inHg", "hPa")
        expected = 29.92 * self.INHG_TO_HPA
        assert result == pytest.approx(expected, rel=1e-3)

    def test_mmhg_to_hpa(self):
        result = convert_pressure(760.0, "mmHg", "hPa")
        expected = 760.0 * self.MMHG_TO_HPA
        assert result == pytest.approx(expected, rel=1e-3)

    def test_atm_to_hpa(self):
        result = convert_pressure(1.0, "atm", "hPa")
        expected = 1.0 * self.ATM_TO_HPA
        assert result == pytest.approx(expected, rel=1e-3)

    def test_psi_to_hpa(self):
        result = convert_pressure(14.696, "psi", "hPa")
        expected = 14.696 * self.PSI_TO_HPA
        assert result == pytest.approx(expected, rel=1e-3)

    def test_mbar_to_hpa(self):
        result = convert_pressure(1013.25, "mbar", "hPa")
        assert result == pytest.approx(1013.25, rel=1e-3)

    def test_hpa_to_psi(self):
        result = convert_pressure(1013.25, "hPa", "psi")
        expected = 1013.25 / self.PSI_TO_HPA
        assert result == pytest.approx(expected, rel=1e-3)

    def test_none_returns_none(self):
        assert convert_pressure(None, "psi") is None


class TestMetoceanEdgeCases:
    def test_unknown_speed_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown speed unit"):
            convert_speed(10.0, "furlongs_per_fortnight")

    def test_unknown_length_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown length unit"):
            convert_length(10.0, "leagues")

    def test_unknown_temp_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown temperature unit"):
            convert_temperature(10.0, "rankine")

    def test_unknown_pressure_unit_raises(self):
        with pytest.raises(ValueError, match="Unknown pressure unit"):
            convert_pressure(10.0, "bar")
