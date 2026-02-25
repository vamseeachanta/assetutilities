# ABOUTME: Tests for casing/tubing pipe strength calculations per API 5C3 / ISO TR 10400.
# ABOUTME: Covers burst, collapse, tensile ratings using published API table values.

import math
import pytest

from assetutilities.calculations.casing_pipe import (
    PipeGrade,
    CasingPipeProperties,
    burst_pressure_rating,
    collapse_pressure_rating,
    axial_tensile_yield_strength,
    wall_thickness_for_design_pressure,
    temperature_derating_factor,
    CasingPipeRatings,
    rate_casing_pipe,
)


# ---------------------------------------------------------------------------
# Fixtures – 9-5/8" 47 ppf N-80 (published API 5C3 data)
# ---------------------------------------------------------------------------
@pytest.fixture
def n80_9_625_47ppf():
    """9-5/8 in, 47 ppf, N-80 casing — standard API published pipe."""
    return CasingPipeProperties(
        od_in=9.625,
        wall_thickness_in=0.472,
        grade=PipeGrade.N80,
    )


@pytest.fixture
def p110_7_0_29ppf():
    """7 in, 29 ppf, P-110 casing."""
    return CasingPipeProperties(
        od_in=7.0,
        wall_thickness_in=0.408,
        grade=PipeGrade.P110,
    )


# ---------------------------------------------------------------------------
# PipeGrade enum
# ---------------------------------------------------------------------------
class TestPipeGrade:
    def test_n80_yield_strength_psi(self):
        assert PipeGrade.N80.yield_strength_psi == 80_000

    def test_p110_yield_strength_psi(self):
        assert PipeGrade.P110.yield_strength_psi == 110_000

    def test_j55_yield_strength_psi(self):
        assert PipeGrade.J55.yield_strength_psi == 55_000

    def test_l80_yield_strength_psi(self):
        assert PipeGrade.L80.yield_strength_psi == 80_000

    def test_c95_yield_strength_psi(self):
        assert PipeGrade.C95.yield_strength_psi == 95_000

    def test_q125_yield_strength_psi(self):
        assert PipeGrade.Q125.yield_strength_psi == 125_000


# ---------------------------------------------------------------------------
# CasingPipeProperties geometry
# ---------------------------------------------------------------------------
class TestCasingPipeProperties:
    def test_id_computed_correctly(self, n80_9_625_47ppf):
        pipe = n80_9_625_47ppf
        expected_id = 9.625 - 2 * 0.472
        assert pipe.id_in == pytest.approx(expected_id, rel=1e-6)

    def test_cross_sectional_area(self, n80_9_625_47ppf):
        pipe = n80_9_625_47ppf
        expected_area = math.pi / 4 * (9.625**2 - pipe.id_in**2)
        assert pipe.cross_sectional_area_in2 == pytest.approx(expected_area, rel=1e-4)

    def test_dt_ratio(self, n80_9_625_47ppf):
        pipe = n80_9_625_47ppf
        expected = 9.625 / 0.472
        assert pipe.dt_ratio == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Burst pressure rating (Barlow / API 5C3)
# Published: 9-5/8" 47 ppf N-80 → ~6350 psi
# ---------------------------------------------------------------------------
class TestBurstPressureRating:
    def test_n80_9_625_47ppf_burst_approx_6870_psi(self, n80_9_625_47ppf):
        result = burst_pressure_rating(n80_9_625_47ppf)
        # API 5C3 Barlow formula for 9-5/8 in 47 ppf N-80 (t=0.472 in):
        #   P = 0.875 * 2 * 80000 * 0.472 / 9.625 ≈ 6865 psi
        # Allow ±50 psi tolerance around the formula value.
        assert 6800 <= result <= 6920, f"Burst = {result:.0f} psi, expected ~6865 psi"

    def test_p110_7_0_29ppf_burst_positive(self, p110_7_0_29ppf):
        result = burst_pressure_rating(p110_7_0_29ppf)
        assert result > 0

    def test_burst_increases_with_wall_thickness(self, n80_9_625_47ppf):
        thinner = CasingPipeProperties(od_in=9.625, wall_thickness_in=0.35, grade=PipeGrade.N80)
        thicker = CasingPipeProperties(od_in=9.625, wall_thickness_in=0.53, grade=PipeGrade.N80)
        assert burst_pressure_rating(thinner) < burst_pressure_rating(thicker)

    def test_burst_increases_with_yield_grade(self):
        j55 = CasingPipeProperties(od_in=7.0, wall_thickness_in=0.3, grade=PipeGrade.J55)
        p110 = CasingPipeProperties(od_in=7.0, wall_thickness_in=0.3, grade=PipeGrade.P110)
        assert burst_pressure_rating(j55) < burst_pressure_rating(p110)

    def test_burst_formula_manual_check(self):
        # P = 0.875 * 2 * Yp * t / OD
        od = 5.5
        t = 0.304
        yp = 80_000
        expected = 0.875 * 2 * yp * t / od
        pipe = CasingPipeProperties(od_in=od, wall_thickness_in=t, grade=PipeGrade.N80)
        assert burst_pressure_rating(pipe) == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Collapse pressure rating (API 5C3 regime selection)
# Published: 9-5/8" 47 ppf N-80 → ~5190 psi
# ---------------------------------------------------------------------------
class TestCollapsePressureRating:
    def test_n80_9_625_47ppf_collapse_approx_4760_psi(self, n80_9_625_47ppf):
        result = collapse_pressure_rating(n80_9_625_47ppf)
        # API 5C3 plastic collapse formula for 9-5/8 in 47 ppf N-80 (D/t≈20.39):
        #   Pp = Yp*(A/dt - B) - C = 80000*(3.071/20.39 - 0.0667) - 1955 ≈ 4757 psi
        # Allow ±100 psi tolerance around the formula value.
        assert 4650 <= result <= 4870, f"Collapse = {result:.0f} psi, expected ~4757 psi"

    def test_collapse_positive(self, p110_7_0_29ppf):
        assert collapse_pressure_rating(p110_7_0_29ppf) > 0

    def test_thick_wall_higher_collapse(self):
        thin = CasingPipeProperties(od_in=7.0, wall_thickness_in=0.2, grade=PipeGrade.N80)
        thick = CasingPipeProperties(od_in=7.0, wall_thickness_in=0.5, grade=PipeGrade.N80)
        assert collapse_pressure_rating(thin) < collapse_pressure_rating(thick)

    def test_high_dt_ratio_gives_positive_result(self):
        # Very thin-walled pipe → elastic or transitional collapse
        pipe = CasingPipeProperties(od_in=9.625, wall_thickness_in=0.25, grade=PipeGrade.N80)
        result = collapse_pressure_rating(pipe)
        assert result > 0


# ---------------------------------------------------------------------------
# Axial tensile yield strength
# ---------------------------------------------------------------------------
class TestAxialTensileYieldStrength:
    def test_n80_9_625_47ppf_tensile_positive(self, n80_9_625_47ppf):
        result = axial_tensile_yield_strength(n80_9_625_47ppf)
        assert result > 0

    def test_tensile_equals_yield_times_area(self, n80_9_625_47ppf):
        pipe = n80_9_625_47ppf
        expected = pipe.grade.yield_strength_psi * pipe.cross_sectional_area_in2
        assert axial_tensile_yield_strength(pipe) == pytest.approx(expected, rel=1e-6)

    def test_tensile_increases_with_grade(self):
        j55 = CasingPipeProperties(od_in=7.0, wall_thickness_in=0.3, grade=PipeGrade.J55)
        p110 = CasingPipeProperties(od_in=7.0, wall_thickness_in=0.3, grade=PipeGrade.P110)
        assert axial_tensile_yield_strength(j55) < axial_tensile_yield_strength(p110)


# ---------------------------------------------------------------------------
# Wall thickness for a given design pressure
# ---------------------------------------------------------------------------
class TestWallThicknessForDesignPressure:
    def test_round_trips_with_burst_formula(self):
        od = 9.625
        grade = PipeGrade.N80
        target_pressure = 6000.0
        t = wall_thickness_for_design_pressure(od_in=od, design_pressure_psi=target_pressure, grade=grade)
        pipe = CasingPipeProperties(od_in=od, wall_thickness_in=t, grade=grade)
        # Burst rating of resulting pipe should equal or exceed target
        assert burst_pressure_rating(pipe) >= target_pressure * 0.99

    def test_higher_pressure_needs_thicker_wall(self):
        od = 7.0
        grade = PipeGrade.N80
        t_low = wall_thickness_for_design_pressure(od_in=od, design_pressure_psi=3000, grade=grade)
        t_high = wall_thickness_for_design_pressure(od_in=od, design_pressure_psi=8000, grade=grade)
        assert t_high > t_low

    def test_result_is_positive(self):
        t = wall_thickness_for_design_pressure(od_in=5.5, design_pressure_psi=5000, grade=PipeGrade.J55)
        assert t > 0


# ---------------------------------------------------------------------------
# Temperature derating factor
# ---------------------------------------------------------------------------
class TestTemperatureDeratingFactor:
    def test_ambient_temperature_factor_is_one(self):
        factor = temperature_derating_factor(temperature_f=70.0)
        assert factor == pytest.approx(1.0, rel=1e-6)

    def test_elevated_temperature_factor_less_than_one(self):
        factor = temperature_derating_factor(temperature_f=400.0)
        assert factor < 1.0

    def test_factor_between_zero_and_one(self):
        for temp_f in [70, 200, 300, 400]:
            factor = temperature_derating_factor(temperature_f=float(temp_f))
            assert 0 < factor <= 1.0, f"Factor out of range at {temp_f}°F: {factor}"

    def test_higher_temp_lower_factor(self):
        f300 = temperature_derating_factor(temperature_f=300.0)
        f400 = temperature_derating_factor(temperature_f=400.0)
        assert f400 < f300


# ---------------------------------------------------------------------------
# rate_casing_pipe convenience wrapper
# ---------------------------------------------------------------------------
class TestRateCasingPipe:
    def test_returns_casing_pipe_ratings_object(self, n80_9_625_47ppf):
        ratings = rate_casing_pipe(n80_9_625_47ppf)
        assert isinstance(ratings, CasingPipeRatings)

    def test_ratings_burst_matches_standalone_function(self, n80_9_625_47ppf):
        ratings = rate_casing_pipe(n80_9_625_47ppf)
        assert ratings.burst_psi == pytest.approx(
            burst_pressure_rating(n80_9_625_47ppf), rel=1e-6
        )

    def test_ratings_collapse_matches_standalone_function(self, n80_9_625_47ppf):
        ratings = rate_casing_pipe(n80_9_625_47ppf)
        assert ratings.collapse_psi == pytest.approx(
            collapse_pressure_rating(n80_9_625_47ppf), rel=1e-6
        )

    def test_ratings_tensile_matches_standalone_function(self, n80_9_625_47ppf):
        ratings = rate_casing_pipe(n80_9_625_47ppf)
        assert ratings.tensile_yield_lbf == pytest.approx(
            axial_tensile_yield_strength(n80_9_625_47ppf), rel=1e-6
        )

    def test_temperature_derating_reduces_burst(self, n80_9_625_47ppf):
        cold = rate_casing_pipe(n80_9_625_47ppf, temperature_f=70.0)
        hot = rate_casing_pipe(n80_9_625_47ppf, temperature_f=400.0)
        assert hot.burst_psi < cold.burst_psi

    def test_all_ratings_positive(self, n80_9_625_47ppf):
        ratings = rate_casing_pipe(n80_9_625_47ppf)
        assert ratings.burst_psi > 0
        assert ratings.collapse_psi > 0
        assert ratings.tensile_yield_lbf > 0

    def test_n80_9_625_published_burst_with_derating_at_ambient(self, n80_9_625_47ppf):
        """At ambient temperature derating=1.0, derated burst equals raw burst."""
        ratings = rate_casing_pipe(n80_9_625_47ppf, temperature_f=70.0)
        assert ratings.burst_psi == pytest.approx(
            burst_pressure_rating(n80_9_625_47ppf), rel=1e-6
        )
