# ABOUTME: Tests for shared engineering constants library.
# ABOUTME: Covers physical constants, material properties, fluid props, and unit conversions.

import math
import pytest

from assetutilities.constants import (
    # Physical
    G,
    G_PRECISE,
    PI,
    E,
    STD_ATMOSPHERE_KPA,
    # Fluids
    RHO_SEAWATER,
    RHO_FRESHWATER,
    RHO_CRUDE_OIL_MIN,
    RHO_CRUDE_OIL_MAX,
    # Steel
    E_STEEL,
    NU_STEEL,
    RHO_STEEL,
    ALPHA_STEEL,
    G_STEEL,
    FY_A36,
    FY_X52,
    FY_X65,
    FY_X70,
    FY_X80,
    # Concrete
    RHO_CONCRETE_NORMAL,
    RHO_CONCRETE_MARINE,
    # Offshore
    SEAWATER_PRESSURE_GRADIENT,
)
from assetutilities.constants.conversions import (
    psi_to_mpa,
    mpa_to_psi,
    bar_to_mpa,
    mpa_to_bar,
    kpa_to_psi,
    psi_to_kpa,
    ft_to_m,
    m_to_ft,
    inch_to_mm,
    mm_to_inch,
    n_to_kn,
    kn_to_n,
    n_to_lbf,
    lbf_to_n,
    kn_to_kip,
    kip_to_kn,
    kg_to_lb,
    lb_to_kg,
    kg_to_tonne,
    tonne_to_kg,
    tonne_to_short_ton,
    short_ton_to_tonne,
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    celsius_to_kelvin,
    kelvin_to_celsius,
    depth_to_pressure_kpa,
)


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

class TestPhysicalConstants:
    def test_gravitational_acceleration(self):
        assert G == pytest.approx(9.81)

    def test_standard_gravity_precise(self):
        assert G_PRECISE == pytest.approx(9.80665)

    def test_pi_value(self):
        assert PI == pytest.approx(math.pi)

    def test_euler_number(self):
        assert E == pytest.approx(math.e)

    def test_standard_atmosphere_kpa(self):
        # ISO 2533 / ICAO: 101.325 kPa
        assert STD_ATMOSPHERE_KPA == pytest.approx(101.325)


# ---------------------------------------------------------------------------
# Fluid properties
# ---------------------------------------------------------------------------

class TestFluidProperties:
    def test_seawater_density_reference_value(self):
        # API RP 2A / DNV-RP-C205: 1025 kg/m³ at 15°C, 35 ppt salinity
        assert RHO_SEAWATER == 1025.0

    def test_freshwater_density_reference_value(self):
        assert RHO_FRESHWATER == 1000.0

    def test_crude_oil_density_min(self):
        assert RHO_CRUDE_OIL_MIN == pytest.approx(700.0)

    def test_crude_oil_density_max(self):
        assert RHO_CRUDE_OIL_MAX == pytest.approx(900.0)

    def test_crude_oil_range_order(self):
        assert RHO_CRUDE_OIL_MIN < RHO_CRUDE_OIL_MAX


# ---------------------------------------------------------------------------
# Steel material properties
# ---------------------------------------------------------------------------

class TestSteelProperties:
    def test_youngs_modulus_gpa_range(self):
        # EN 10025-2 / ASTM reference: 207 GPa
        assert E_STEEL == pytest.approx(207e9, rel=1e-6)

    def test_poissons_ratio(self):
        assert NU_STEEL == pytest.approx(0.30)

    def test_steel_density(self):
        assert RHO_STEEL == pytest.approx(7850.0)

    def test_thermal_expansion(self):
        # 11.7e-6 /°C per EN 1993
        assert ALPHA_STEEL == pytest.approx(11.7e-6, rel=1e-6)

    def test_shear_modulus_derived_from_E_and_nu(self):
        # G = E / (2*(1+nu))
        expected = 207e9 / (2.0 * (1.0 + 0.30))
        assert G_STEEL == pytest.approx(expected, rel=1e-6)

    def test_yield_strength_A36_mpa(self):
        # ASTM A36: 250 MPa min
        assert FY_A36 == pytest.approx(250e6, rel=1e-6)

    def test_yield_strength_X52_mpa(self):
        # API 5L X52: 358 MPa (52 ksi)
        assert FY_X52 == pytest.approx(358e6, rel=1e-6)

    def test_yield_strength_X65_mpa(self):
        # API 5L X65: 448 MPa (65 ksi)
        assert FY_X65 == pytest.approx(448e6, rel=1e-6)

    def test_yield_strength_X70_mpa(self):
        # API 5L X70: 483 MPa (70 ksi)
        assert FY_X70 == pytest.approx(483e6, rel=1e-6)

    def test_yield_strength_X80_mpa(self):
        # API 5L X80: 552 MPa (80 ksi)
        assert FY_X80 == pytest.approx(552e6, rel=1e-6)

    def test_grade_yield_strengths_ascending(self):
        assert FY_A36 < FY_X52 < FY_X65 < FY_X70 < FY_X80


# ---------------------------------------------------------------------------
# Concrete properties
# ---------------------------------------------------------------------------

class TestConcreteProperties:
    def test_normal_weight_concrete_density(self):
        assert RHO_CONCRETE_NORMAL == pytest.approx(2400.0)

    def test_marine_weight_coating_density(self):
        assert RHO_CONCRETE_MARINE == pytest.approx(2250.0)

    def test_marine_coating_lighter_than_normal(self):
        assert RHO_CONCRETE_MARINE < RHO_CONCRETE_NORMAL


# ---------------------------------------------------------------------------
# Offshore-specific constants
# ---------------------------------------------------------------------------

class TestOffshoreConstants:
    def test_seawater_pressure_gradient_kpa_per_m(self):
        # rho * g = 1025 * 9.81 / 1000 kPa/m
        expected = 1025.0 * 9.81 / 1000.0
        assert SEAWATER_PRESSURE_GRADIENT == pytest.approx(expected, rel=1e-4)


# ---------------------------------------------------------------------------
# Pressure conversions
# ---------------------------------------------------------------------------

class TestPressureConversions:
    def test_psi_to_mpa_one_mpa(self):
        # 145.038 psi = 1 MPa (exact definition)
        assert psi_to_mpa(145.038) == pytest.approx(1.0, abs=0.001)

    def test_mpa_to_psi_roundtrip(self):
        original = 10.0
        assert mpa_to_psi(psi_to_mpa(original)) == pytest.approx(original, rel=1e-6)

    def test_psi_to_mpa_zero(self):
        assert psi_to_mpa(0.0) == 0.0

    def test_bar_to_mpa(self):
        # 1 bar = 0.1 MPa
        assert bar_to_mpa(1.0) == pytest.approx(0.1, rel=1e-9)

    def test_mpa_to_bar(self):
        assert mpa_to_bar(0.1) == pytest.approx(1.0, rel=1e-9)

    def test_bar_mpa_roundtrip(self):
        assert mpa_to_bar(bar_to_mpa(5.0)) == pytest.approx(5.0, rel=1e-9)

    def test_kpa_to_psi(self):
        # 6.89476 kPa = 1 psi
        assert kpa_to_psi(6.89476) == pytest.approx(1.0, abs=0.001)

    def test_psi_to_kpa(self):
        assert psi_to_kpa(1.0) == pytest.approx(6.89476, rel=1e-4)


# ---------------------------------------------------------------------------
# Length conversions
# ---------------------------------------------------------------------------

class TestLengthConversions:
    def test_ft_to_m(self):
        # 1 ft = 0.3048 m (exact)
        assert ft_to_m(1.0) == pytest.approx(0.3048, rel=1e-9)

    def test_m_to_ft(self):
        assert m_to_ft(0.3048) == pytest.approx(1.0, rel=1e-9)

    def test_ft_m_roundtrip(self):
        assert m_to_ft(ft_to_m(100.0)) == pytest.approx(100.0, rel=1e-9)

    def test_inch_to_mm(self):
        # 1 inch = 25.4 mm (exact)
        assert inch_to_mm(1.0) == pytest.approx(25.4, rel=1e-9)

    def test_mm_to_inch(self):
        assert mm_to_inch(25.4) == pytest.approx(1.0, rel=1e-9)

    def test_inch_mm_roundtrip(self):
        assert mm_to_inch(inch_to_mm(12.0)) == pytest.approx(12.0, rel=1e-9)


# ---------------------------------------------------------------------------
# Force conversions
# ---------------------------------------------------------------------------

class TestForceConversions:
    def test_n_to_kn(self):
        assert n_to_kn(1000.0) == pytest.approx(1.0, rel=1e-9)

    def test_kn_to_n(self):
        assert kn_to_n(1.0) == pytest.approx(1000.0, rel=1e-9)

    def test_n_to_lbf(self):
        # 1 N = 0.224809 lbf
        assert n_to_lbf(1.0) == pytest.approx(0.224809, rel=1e-4)

    def test_lbf_to_n(self):
        assert lbf_to_n(1.0) == pytest.approx(4.44822, rel=1e-4)

    def test_n_lbf_roundtrip(self):
        assert lbf_to_n(n_to_lbf(500.0)) == pytest.approx(500.0, rel=1e-6)

    def test_kn_to_kip(self):
        # 1 kip = 4.44822 kN
        assert kn_to_kip(4.44822) == pytest.approx(1.0, rel=1e-4)

    def test_kip_to_kn(self):
        assert kip_to_kn(1.0) == pytest.approx(4.44822, rel=1e-4)


# ---------------------------------------------------------------------------
# Mass conversions
# ---------------------------------------------------------------------------

class TestMassConversions:
    def test_kg_to_lb(self):
        # 1 kg = 2.20462 lb
        assert kg_to_lb(1.0) == pytest.approx(2.20462, rel=1e-4)

    def test_lb_to_kg(self):
        assert lb_to_kg(2.20462) == pytest.approx(1.0, rel=1e-4)

    def test_kg_lb_roundtrip(self):
        assert lb_to_kg(kg_to_lb(75.0)) == pytest.approx(75.0, rel=1e-6)

    def test_kg_to_tonne(self):
        assert kg_to_tonne(1000.0) == pytest.approx(1.0, rel=1e-9)

    def test_tonne_to_kg(self):
        assert tonne_to_kg(1.0) == pytest.approx(1000.0, rel=1e-9)

    def test_tonne_to_short_ton(self):
        # 1 metric tonne = 1.10231 short tons
        assert tonne_to_short_ton(1.0) == pytest.approx(1.10231, rel=1e-4)

    def test_short_ton_to_tonne(self):
        assert short_ton_to_tonne(1.10231) == pytest.approx(1.0, rel=1e-4)


# ---------------------------------------------------------------------------
# Temperature conversions
# ---------------------------------------------------------------------------

class TestTemperatureConversions:
    def test_celsius_to_fahrenheit_freezing(self):
        assert celsius_to_fahrenheit(0.0) == pytest.approx(32.0, rel=1e-9)

    def test_celsius_to_fahrenheit_boiling(self):
        assert celsius_to_fahrenheit(100.0) == pytest.approx(212.0, rel=1e-9)

    def test_fahrenheit_to_celsius_freezing(self):
        assert fahrenheit_to_celsius(32.0) == pytest.approx(0.0, abs=1e-9)

    def test_fahrenheit_to_celsius_boiling(self):
        assert fahrenheit_to_celsius(212.0) == pytest.approx(100.0, rel=1e-9)

    def test_celsius_fahrenheit_roundtrip(self):
        assert fahrenheit_to_celsius(celsius_to_fahrenheit(25.0)) == pytest.approx(25.0, rel=1e-9)

    def test_celsius_to_kelvin_absolute_zero(self):
        assert celsius_to_kelvin(-273.15) == pytest.approx(0.0, abs=1e-9)

    def test_celsius_to_kelvin_standard(self):
        assert celsius_to_kelvin(0.0) == pytest.approx(273.15, rel=1e-9)

    def test_kelvin_to_celsius(self):
        assert kelvin_to_celsius(273.15) == pytest.approx(0.0, abs=1e-9)

    def test_kelvin_celsius_roundtrip(self):
        assert kelvin_to_celsius(celsius_to_kelvin(20.0)) == pytest.approx(20.0, rel=1e-9)


# ---------------------------------------------------------------------------
# Offshore depth-pressure utility
# ---------------------------------------------------------------------------

class TestDepthToPressure:
    def test_zero_depth_returns_zero_gauge(self):
        assert depth_to_pressure_kpa(0.0) == pytest.approx(0.0)

    def test_100m_depth(self):
        # P = rho * g * h / 1000 kPa
        expected = 1025.0 * 9.81 * 100.0 / 1000.0
        assert depth_to_pressure_kpa(100.0) == pytest.approx(expected, rel=1e-4)

    def test_1000m_depth(self):
        expected = 1025.0 * 9.81 * 1000.0 / 1000.0
        assert depth_to_pressure_kpa(1000.0) == pytest.approx(expected, rel=1e-4)

    def test_depth_pressure_linear(self):
        # Doubling depth doubles pressure
        p_100 = depth_to_pressure_kpa(100.0)
        p_200 = depth_to_pressure_kpa(200.0)
        assert p_200 == pytest.approx(2.0 * p_100, rel=1e-9)
