# ABOUTME: Unit tests for DNV OS-F101 submarine pipeline design checks.
# ABOUTME: Covers burst pressure, local buckling, von Mises stress, and buckle arrest.
"""Tests for pipeline_dnv module — DNV OS-F101 LRFD design checks.

Reference values are derived from DNV OS-F101 (2013) Section 5 worked examples
and standard hand-calculations using published partial safety factors.
"""
import math
import pytest

from assetutilities.calculations.pipeline_dnv import (
    MATERIAL_GRADES,
    burst_pressure_capacity,
    pressure_containment_check,
    local_buckling_combined_loading,
    von_mises_equivalent_stress,
    buckle_arrest_capacity,
)


# ---------------------------------------------------------------------------
# Fixtures — pipe geometry and loading used across multiple tests
# ---------------------------------------------------------------------------

@pytest.fixture
def x65_pipe():
    """12-inch X65 pipeline: OD=323.9 mm, WT=14.3 mm."""
    return {
        "D": 0.3239,   # outer diameter [m]
        "t": 0.0143,   # wall thickness [m]
        "f_y": 450e6,  # yield strength [Pa] — X65
        "f_u": 535e6,  # SMTS [Pa]
        "alpha_U": 0.96,  # material strength factor
    }


@pytest.fixture
def x52_pipe():
    """8-inch X52 pipeline: OD=219.1 mm, WT=12.7 mm."""
    return {
        "D": 0.2191,
        "t": 0.0127,
        "f_y": 358e6,
        "f_u": 455e6,
        "alpha_U": 0.96,
    }


# ---------------------------------------------------------------------------
# Material grades
# ---------------------------------------------------------------------------

class TestMaterialGrades:
    def test_x52_yield_strength(self):
        assert MATERIAL_GRADES["X52"]["f_y"] == pytest.approx(358e6, rel=1e-3)

    def test_x60_yield_strength(self):
        assert MATERIAL_GRADES["X60"]["f_y"] == pytest.approx(413e6, rel=1e-3)

    def test_x65_yield_strength(self):
        assert MATERIAL_GRADES["X65"]["f_y"] == pytest.approx(450e6, rel=1e-3)

    def test_x70_yield_strength(self):
        assert MATERIAL_GRADES["X70"]["f_y"] == pytest.approx(482e6, rel=1e-3)

    def test_x65_smts(self):
        assert MATERIAL_GRADES["X65"]["f_u"] == pytest.approx(535e6, rel=1e-3)

    def test_all_grades_present(self):
        for grade in ("X52", "X60", "X65", "X70"):
            assert grade in MATERIAL_GRADES
            assert "f_y" in MATERIAL_GRADES[grade]
            assert "f_u" in MATERIAL_GRADES[grade]


# ---------------------------------------------------------------------------
# Burst pressure capacity  (DNV OS-F101 Sec 5 D300)
# P_b = (2 * t / D) * f_cb * alpha_fab
# f_cb = min(f_y * alpha_U, f_u * alpha_U / 1.15)
# ---------------------------------------------------------------------------

class TestBurstPressureCapacity:
    def test_basic_result_positive(self, x65_pipe):
        P_b = burst_pressure_capacity(**x65_pipe)
        assert P_b > 0

    def test_x65_burst_pressure_approximate(self, x65_pipe):
        """Expected ~35 MPa for typical 12-inch X65 pipeline."""
        P_b = burst_pressure_capacity(**x65_pipe)
        assert 30e6 < P_b < 45e6

    def test_thicker_wall_higher_pressure(self, x65_pipe):
        thin = burst_pressure_capacity(**x65_pipe)
        thick_pipe = dict(x65_pipe)
        thick_pipe["t"] = 0.020
        thick = burst_pressure_capacity(**thick_pipe)
        assert thick > thin

    def test_larger_diameter_lower_pressure(self, x65_pipe):
        small = burst_pressure_capacity(**x65_pipe)
        large_pipe = dict(x65_pipe)
        large_pipe["D"] = 0.500
        large = burst_pressure_capacity(**large_pipe)
        assert large < small

    def test_fab_factor_reduces_capacity(self, x65_pipe):
        no_weld = burst_pressure_capacity(**x65_pipe, alpha_fab=1.00)
        welded = burst_pressure_capacity(**x65_pipe, alpha_fab=0.85)
        assert welded < no_weld

    def test_d_over_t_ratio_respected(self):
        """Very thin wall: capacity still positive and finite."""
        P_b = burst_pressure_capacity(D=0.500, t=0.005, f_y=450e6, f_u=535e6, alpha_U=0.96)
        assert math.isfinite(P_b) and P_b > 0


# ---------------------------------------------------------------------------
# Pressure containment check  (LRFD format)
# Utilization = P_li / (P_b / (gamma_m * gamma_SCPC))
# ---------------------------------------------------------------------------

class TestPressureContainmentCheck:
    def test_safe_returns_utilization_below_one(self, x65_pipe):
        util = pressure_containment_check(
            P_li=15e6,
            gamma_m=1.15,
            gamma_SCPC=1.05,
            **x65_pipe,
        )
        assert util < 1.0

    def test_overpressure_returns_utilization_above_one(self, x65_pipe):
        util = pressure_containment_check(
            P_li=60e6,
            gamma_m=1.15,
            gamma_SCPC=1.05,
            **x65_pipe,
        )
        assert util > 1.0

    def test_utilization_scales_linearly_with_pressure(self, x65_pipe):
        u1 = pressure_containment_check(P_li=10e6, gamma_m=1.15, gamma_SCPC=1.05, **x65_pipe)
        u2 = pressure_containment_check(P_li=20e6, gamma_m=1.15, gamma_SCPC=1.05, **x65_pipe)
        assert u2 == pytest.approx(2.0 * u1, rel=1e-6)

    def test_returns_float(self, x65_pipe):
        result = pressure_containment_check(
            P_li=10e6, gamma_m=1.15, gamma_SCPC=1.05, **x65_pipe
        )
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# Local buckling — combined loading  (DNV OS-F101 Sec 5 D500)
# Utilization check for bending + pressure + tension
# ---------------------------------------------------------------------------

class TestLocalBucklingCombinedLoading:
    def test_zero_loads_is_safe(self, x65_pipe):
        util = local_buckling_combined_loading(
            D=x65_pipe["D"],
            t=x65_pipe["t"],
            f_y=x65_pipe["f_y"],
            M=0.0,
            S=0.0,
            delta_p=0.0,
            gamma_m=1.15,
            gamma_SC=1.138,
        )
        assert util == pytest.approx(0.0, abs=1e-9)

    def test_pure_bending_utilization(self, x65_pipe):
        """Apply a moderate bending moment; utilisation should be between 0 and 1."""
        D, t, f_y = x65_pipe["D"], x65_pipe["t"], x65_pipe["f_y"]
        # Plastic moment capacity ~ f_y * D^2 * t
        M_ref = f_y * D**2 * t * 0.3
        util = local_buckling_combined_loading(
            D=D, t=t, f_y=f_y,
            M=M_ref, S=0.0, delta_p=0.0,
            gamma_m=1.15, gamma_SC=1.138,
        )
        assert 0.0 < util < 1.0

    def test_utilization_increases_with_moment(self, x65_pipe):
        D, t, f_y = x65_pipe["D"], x65_pipe["t"], x65_pipe["f_y"]
        M_ref = f_y * D**2 * t * 0.3
        u_low = local_buckling_combined_loading(
            D=D, t=t, f_y=f_y, M=M_ref * 0.5, S=0.0,
            delta_p=0.0, gamma_m=1.15, gamma_SC=1.138,
        )
        u_high = local_buckling_combined_loading(
            D=D, t=t, f_y=f_y, M=M_ref, S=0.0,
            delta_p=0.0, gamma_m=1.15, gamma_SC=1.138,
        )
        assert u_high > u_low

    def test_returns_float(self, x65_pipe):
        result = local_buckling_combined_loading(
            D=x65_pipe["D"], t=x65_pipe["t"], f_y=x65_pipe["f_y"],
            M=0.0, S=0.0, delta_p=0.0,
            gamma_m=1.15, gamma_SC=1.138,
        )
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# Von Mises equivalent stress
# sigma_eq = sqrt(sigma_l^2 - sigma_l*sigma_h + sigma_h^2 + 3*tau^2)
# ---------------------------------------------------------------------------

class TestVonMisesEquivalentStress:
    def test_uniaxial_equals_input(self):
        sigma = von_mises_equivalent_stress(sigma_l=100e6, sigma_h=0.0, tau=0.0)
        assert sigma == pytest.approx(100e6, rel=1e-6)

    def test_equal_biaxial(self):
        """sigma_l = sigma_h => sigma_eq = sigma_l."""
        sigma = von_mises_equivalent_stress(sigma_l=200e6, sigma_h=200e6, tau=0.0)
        assert sigma == pytest.approx(200e6, rel=1e-6)

    def test_pure_shear(self):
        """tau only => sigma_eq = sqrt(3) * tau."""
        tau = 100e6
        sigma = von_mises_equivalent_stress(sigma_l=0.0, sigma_h=0.0, tau=tau)
        assert sigma == pytest.approx(math.sqrt(3) * tau, rel=1e-6)

    def test_combined_loading(self):
        """Known result: sigma_l=300, sigma_h=150, tau=0 => sqrt(300^2-300*150+150^2)."""
        sl, sh = 300e6, 150e6
        expected = math.sqrt(sl**2 - sl * sh + sh**2)
        sigma = von_mises_equivalent_stress(sigma_l=sl, sigma_h=sh, tau=0.0)
        assert sigma == pytest.approx(expected, rel=1e-6)

    def test_non_negative(self):
        sigma = von_mises_equivalent_stress(sigma_l=-100e6, sigma_h=50e6, tau=30e6)
        assert sigma >= 0.0


# ---------------------------------------------------------------------------
# Buckle arrest capacity  (DNV OS-F101 Sec 5 D800 LRFD)
# F_ba = 10.7 * f_y * t^2 * (t / D)^0.4 / gamma_m
# ---------------------------------------------------------------------------

class TestBuckleArrestCapacity:
    def test_basic_result_positive(self, x65_pipe):
        F_ba = buckle_arrest_capacity(
            D=x65_pipe["D"],
            t=x65_pipe["t"],
            f_y=x65_pipe["f_y"],
            gamma_m=1.15,
        )
        assert F_ba > 0

    def test_thicker_wall_higher_arrest(self, x65_pipe):
        thin = buckle_arrest_capacity(
            D=x65_pipe["D"], t=x65_pipe["t"],
            f_y=x65_pipe["f_y"], gamma_m=1.15,
        )
        thick = buckle_arrest_capacity(
            D=x65_pipe["D"], t=x65_pipe["t"] * 1.5,
            f_y=x65_pipe["f_y"], gamma_m=1.15,
        )
        assert thick > thin

    def test_higher_gamma_reduces_capacity(self, x65_pipe):
        low_gm = buckle_arrest_capacity(
            D=x65_pipe["D"], t=x65_pipe["t"],
            f_y=x65_pipe["f_y"], gamma_m=1.05,
        )
        high_gm = buckle_arrest_capacity(
            D=x65_pipe["D"], t=x65_pipe["t"],
            f_y=x65_pipe["f_y"], gamma_m=1.45,
        )
        assert high_gm < low_gm

    def test_returns_finite(self, x65_pipe):
        F_ba = buckle_arrest_capacity(
            D=x65_pipe["D"], t=x65_pipe["t"],
            f_y=x65_pipe["f_y"], gamma_m=1.15,
        )
        assert math.isfinite(F_ba)
