# ABOUTME: Tests for TLP well system and riser calculations.
# ABOUTME: Covers tendon tension, tensioner stroke, fatigue, interference, damping, set-down.

import math
import pytest

from assetutilities.calculations.tlp_well_system import (
    tendon_effective_tension,
    riser_tensioner_stroke,
    wellhead_fatigue_accumulation,
    riser_interference_check,
    critical_damping_ratio,
    platform_set_down,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def nominal_tlp():
    """Typical TLP configuration: deepwater, moderate offset."""
    return {
        "t_pretension": 5_000_000.0,   # N  (5 MN)
        "delta_t_hull": 200_000.0,      # N  (0.2 MN tension reduction from hull motion)
    }


@pytest.fixture
def nominal_riser():
    """Nominal tensioned riser: 2000 m water depth."""
    return {
        "length": 2000.0,      # m
        "delta_vert": 5.0,     # m  (vertical displacement)
        "delta_horiz": 20.0,   # m  (horizontal offset)
    }


@pytest.fixture
def sn_curve_params():
    """API X S-N curve parameters for fatigue accumulation."""
    return {
        "a_param": 2.0e12,   # S-N intercept constant (cycles at unit stress range)
        "m_param": 3.0,      # S-N slope exponent
    }


# ---------------------------------------------------------------------------
# tendon_effective_tension
# T_eff = T_pretension - delta_T_hull_motion
# ---------------------------------------------------------------------------

class TestTendonEffectiveTension:
    def test_nominal_result_positive(self, nominal_tlp):
        t_eff = tendon_effective_tension(**nominal_tlp)
        assert t_eff > 0

    def test_formula_correctness(self):
        t_pre = 6_000_000.0
        delta_t = 500_000.0
        result = tendon_effective_tension(
            t_pretension=t_pre, delta_t_hull=delta_t
        )
        assert result == pytest.approx(t_pre - delta_t, rel=1e-9)

    def test_zero_hull_motion_returns_pretension(self):
        t_pre = 4_500_000.0
        result = tendon_effective_tension(
            t_pretension=t_pre, delta_t_hull=0.0
        )
        assert result == pytest.approx(t_pre, rel=1e-9)

    def test_large_delta_gives_reduced_tension(self, nominal_tlp):
        small = tendon_effective_tension(**nominal_tlp)
        large = tendon_effective_tension(
            t_pretension=nominal_tlp["t_pretension"],
            delta_t_hull=nominal_tlp["delta_t_hull"] * 3,
        )
        assert large < small

    def test_raises_when_result_would_be_negative(self):
        with pytest.raises(ValueError, match="effective tension"):
            tendon_effective_tension(
                t_pretension=1_000_000.0, delta_t_hull=2_000_000.0
            )

    def test_returns_float(self, nominal_tlp):
        result = tendon_effective_tension(**nominal_tlp)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# riser_tensioner_stroke
# s = sqrt((L + delta_vert)^2 + delta_horiz^2) - L
# ---------------------------------------------------------------------------

class TestRiserTensionerStroke:
    def test_zero_displacements_gives_zero_stroke(self):
        s = riser_tensioner_stroke(length=1500.0, delta_vert=0.0, delta_horiz=0.0)
        assert s == pytest.approx(0.0, abs=1e-9)

    def test_nominal_result_positive(self, nominal_riser):
        s = riser_tensioner_stroke(**nominal_riser)
        assert s > 0

    def test_formula_correctness(self):
        L = 1000.0
        dv = 3.0
        dh = 10.0
        expected = math.sqrt((L + dv) ** 2 + dh ** 2) - L
        result = riser_tensioner_stroke(length=L, delta_vert=dv, delta_horiz=dh)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_larger_offset_gives_more_stroke(self, nominal_riser):
        s_low = riser_tensioner_stroke(**nominal_riser)
        s_high = riser_tensioner_stroke(
            length=nominal_riser["length"],
            delta_vert=nominal_riser["delta_vert"],
            delta_horiz=nominal_riser["delta_horiz"] * 2,
        )
        assert s_high > s_low

    def test_raises_on_non_positive_length(self):
        with pytest.raises(ValueError, match="length must be positive"):
            riser_tensioner_stroke(length=0.0, delta_vert=0.0, delta_horiz=5.0)

    def test_returns_float(self, nominal_riser):
        result = riser_tensioner_stroke(**nominal_riser)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# wellhead_fatigue_accumulation
# D = sum(n / N_f) — Miner's rule via S-N integration over service life
# N_f = A / (delta_sigma)^m
# ---------------------------------------------------------------------------

class TestWellheadFatigueAccumulation:
    def test_returns_positive_damage(self, sn_curve_params):
        # stress ranges [Pa] and annual cycle counts
        stress_ranges = [20e6, 30e6, 40e6]
        annual_cycles = [1e4, 5e3, 1e3]
        service_years = 20.0
        damage = wellhead_fatigue_accumulation(
            stress_ranges=stress_ranges,
            annual_cycles=annual_cycles,
            service_years=service_years,
            **sn_curve_params,
        )
        assert damage > 0

    def test_zero_cycles_gives_zero_damage(self, sn_curve_params):
        damage = wellhead_fatigue_accumulation(
            stress_ranges=[30e6],
            annual_cycles=[0.0],
            service_years=20.0,
            **sn_curve_params,
        )
        assert damage == pytest.approx(0.0, abs=1e-12)

    def test_damage_scales_with_service_years(self, sn_curve_params):
        kwargs = dict(
            stress_ranges=[25e6, 35e6],
            annual_cycles=[2e4, 8e3],
            a_param=sn_curve_params["a_param"],
            m_param=sn_curve_params["m_param"],
        )
        d10 = wellhead_fatigue_accumulation(service_years=10.0, **kwargs)
        d20 = wellhead_fatigue_accumulation(service_years=20.0, **kwargs)
        assert d20 == pytest.approx(2.0 * d10, rel=1e-9)

    def test_higher_stress_gives_more_damage(self, sn_curve_params):
        d_low = wellhead_fatigue_accumulation(
            stress_ranges=[20e6], annual_cycles=[1e4], service_years=20.0,
            **sn_curve_params,
        )
        d_high = wellhead_fatigue_accumulation(
            stress_ranges=[40e6], annual_cycles=[1e4], service_years=20.0,
            **sn_curve_params,
        )
        assert d_high > d_low

    def test_miner_sum_formula(self, sn_curve_params):
        sigma = 25e6
        n_annual = 1000.0
        years = 10.0
        a = sn_curve_params["a_param"]
        m = sn_curve_params["m_param"]
        n_total = n_annual * years
        n_f = a / (sigma ** m)
        expected = n_total / n_f
        result = wellhead_fatigue_accumulation(
            stress_ranges=[sigma],
            annual_cycles=[n_annual],
            service_years=years,
            **sn_curve_params,
        )
        assert result == pytest.approx(expected, rel=1e-9)

    def test_raises_on_mismatched_inputs(self, sn_curve_params):
        with pytest.raises(ValueError, match="same length"):
            wellhead_fatigue_accumulation(
                stress_ranges=[20e6, 30e6],
                annual_cycles=[1e4],
                service_years=20.0,
                **sn_curve_params,
            )


# ---------------------------------------------------------------------------
# riser_interference_check
# Check clear separation between tensioned risers and drilling riser.
# Returns (is_clear: bool, min_separation: float)
# ---------------------------------------------------------------------------

class TestRiserInterferenceCheck:
    def test_sufficient_separation_passes(self):
        is_clear, sep = riser_interference_check(
            tensioned_riser_od=0.50,
            drilling_riser_od=0.60,
            centre_to_centre=2.0,
        )
        assert is_clear is True

    def test_insufficient_separation_fails(self):
        is_clear, sep = riser_interference_check(
            tensioned_riser_od=0.50,
            drilling_riser_od=0.60,
            centre_to_centre=0.40,
        )
        assert is_clear is False

    def test_minimum_separation_is_gap(self):
        od_t = 0.4
        od_d = 0.5
        ctc = 1.5
        expected_gap = ctc - (od_t / 2) - (od_d / 2)
        _, sep = riser_interference_check(
            tensioned_riser_od=od_t,
            drilling_riser_od=od_d,
            centre_to_centre=ctc,
        )
        assert sep == pytest.approx(expected_gap, rel=1e-9)

    def test_touching_risers_are_not_clear(self):
        od_t = 0.5
        od_d = 0.5
        ctc = 0.5  # sum of radii = 0.5, exactly touching
        is_clear, _ = riser_interference_check(
            tensioned_riser_od=od_t,
            drilling_riser_od=od_d,
            centre_to_centre=ctc,
        )
        assert is_clear is False

    def test_returns_tuple_of_bool_and_float(self):
        result = riser_interference_check(
            tensioned_riser_od=0.4,
            drilling_riser_od=0.5,
            centre_to_centre=2.0,
        )
        assert isinstance(result, tuple)
        assert isinstance(result[0], bool)
        assert isinstance(result[1], float)

    def test_raises_on_non_positive_od(self):
        with pytest.raises(ValueError, match="outer diameter must be positive"):
            riser_interference_check(
                tensioned_riser_od=0.0,
                drilling_riser_od=0.5,
                centre_to_centre=2.0,
            )


# ---------------------------------------------------------------------------
# critical_damping_ratio
# zeta = C / (2 * sqrt(K * M))
# ---------------------------------------------------------------------------

class TestCriticalDampingRatio:
    def test_underdamped_less_than_one(self):
        zeta = critical_damping_ratio(C=1e6, K=5e8, M=2e6)
        assert zeta < 1.0

    def test_overdamped_greater_than_one(self):
        zeta = critical_damping_ratio(C=1e9, K=5e8, M=2e6)
        assert zeta > 1.0

    def test_formula_correctness(self):
        C = 5e5
        K = 4e8
        M = 1.5e6
        expected = C / (2 * math.sqrt(K * M))
        result = critical_damping_ratio(C=C, K=K, M=M)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_critical_damping_equals_one(self):
        # C = 2*sqrt(K*M) → zeta = 1
        K = 1e6
        M = 1e6
        C = 2 * math.sqrt(K * M)
        zeta = critical_damping_ratio(C=C, K=K, M=M)
        assert zeta == pytest.approx(1.0, rel=1e-9)

    def test_returns_positive_value(self):
        zeta = critical_damping_ratio(C=1e5, K=1e7, M=5e5)
        assert zeta > 0

    def test_raises_on_non_positive_stiffness(self):
        with pytest.raises(ValueError, match="K must be positive"):
            critical_damping_ratio(C=1e5, K=0.0, M=5e5)

    def test_raises_on_non_positive_mass(self):
        with pytest.raises(ValueError, match="M must be positive"):
            critical_damping_ratio(C=1e5, K=1e7, M=0.0)


# ---------------------------------------------------------------------------
# platform_set_down
# delta_z = L * (1 - cos(theta))
# theta = arcsin(delta_horiz / L)  when L >> delta_horiz
# Alternative direct form: delta_z = L - sqrt(L^2 - delta_horiz^2)
# ---------------------------------------------------------------------------

class TestPlatformSetDown:
    def test_zero_offset_gives_zero_setdown(self):
        dz = platform_set_down(length=1500.0, delta_horiz=0.0)
        assert dz == pytest.approx(0.0, abs=1e-9)

    def test_setdown_positive_for_positive_offset(self):
        dz = platform_set_down(length=1500.0, delta_horiz=30.0)
        assert dz > 0

    def test_formula_correctness(self):
        L = 1200.0
        dh = 25.0
        theta = math.asin(dh / L)
        expected = L * (1 - math.cos(theta))
        result = platform_set_down(length=L, delta_horiz=dh)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_larger_offset_gives_more_setdown(self):
        dz_small = platform_set_down(length=1500.0, delta_horiz=10.0)
        dz_large = platform_set_down(length=1500.0, delta_horiz=50.0)
        assert dz_large > dz_small

    def test_raises_on_non_positive_length(self):
        with pytest.raises(ValueError, match="length must be positive"):
            platform_set_down(length=0.0, delta_horiz=10.0)

    def test_raises_when_offset_exceeds_length(self):
        with pytest.raises(ValueError, match="delta_horiz must be less than length"):
            platform_set_down(length=100.0, delta_horiz=150.0)

    def test_returns_float(self):
        result = platform_set_down(length=1500.0, delta_horiz=20.0)
        assert isinstance(result, float)
