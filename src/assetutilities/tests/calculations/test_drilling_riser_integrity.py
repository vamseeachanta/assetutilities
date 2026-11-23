# ABOUTME: Tests for deep water drilling riser integrity calculations per AMJIG
# ABOUTME: Rev 1/2 (1998-2000) and rpt001-3 (1997) guidelines.

import math
import pytest

from assetutilities.calculations.drilling_riser_integrity import (
    riser_effective_tension,
    riser_collapse_pressure,
    minimum_top_tension,
    tensile_utilization,
    bending_moment_from_offset,
    combined_loading_utilization,
    annual_fatigue_damage,
)


# ---------------------------------------------------------------------------
# riser_effective_tension
# ---------------------------------------------------------------------------
class TestRiserEffectiveTension:
    def test_tension_at_top_is_t_top(self):
        result = riser_effective_tension(t_top=500_000.0, w_sub=1_000.0, z=0.0)
        assert result == pytest.approx(500_000.0, rel=1e-9)

    def test_tension_decreases_with_depth(self):
        t_top = 800_000.0
        w_sub = 2_000.0
        z = 100.0
        result = riser_effective_tension(t_top, w_sub, z)
        assert result == pytest.approx(t_top - w_sub * z, rel=1e-9)

    def test_tension_monotonically_decreasing_with_depth(self):
        t_top, w_sub = 1_000_000.0, 1_500.0
        tensions = [riser_effective_tension(t_top, w_sub, z) for z in [0, 100, 300, 600]]
        assert all(tensions[i] > tensions[i + 1] for i in range(len(tensions) - 1))

    def test_tension_at_mudline_manual_check(self):
        # At depth = L (mudline), all submerged weight acts on top
        t_top = 600_000.0
        w_sub = 1_200.0
        L = 300.0
        result = riser_effective_tension(t_top, w_sub, L)
        assert result == pytest.approx(t_top - w_sub * L, rel=1e-9)

    def test_zero_submerged_weight_constant_tension(self):
        t_top = 400_000.0
        for z in [0.0, 50.0, 200.0, 500.0]:
            result = riser_effective_tension(t_top, w_sub=0.0, z=z)
            assert result == pytest.approx(t_top, rel=1e-9)


# ---------------------------------------------------------------------------
# riser_collapse_pressure
# ---------------------------------------------------------------------------
class TestRiserCollapsePressure:
    def test_result_is_positive(self):
        result = riser_collapse_pressure(
            E=200e9, t=0.025, D=0.5, nu=0.30
        )
        assert result > 0.0

    def test_thicker_wall_higher_collapse(self):
        base_kwargs = dict(E=200e9, D=0.5, nu=0.30)
        p_thin = riser_collapse_pressure(t=0.015, **base_kwargs)
        p_thick = riser_collapse_pressure(t=0.035, **base_kwargs)
        assert p_thick > p_thin

    def test_higher_modulus_higher_collapse(self):
        base_kwargs = dict(t=0.020, D=0.4, nu=0.30)
        p_low_E = riser_collapse_pressure(E=150e9, **base_kwargs)
        p_high_E = riser_collapse_pressure(E=210e9, **base_kwargs)
        assert p_high_E > p_low_E

    def test_manual_formula_check(self):
        # P_c = 2E(t/D)^3 / (1 - nu^2)
        E, t, D, nu = 200e9, 0.020, 0.400, 0.30
        expected = 2.0 * E * (t / D) ** 3 / (1.0 - nu ** 2)
        result = riser_collapse_pressure(E=E, t=t, D=D, nu=nu)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_smaller_diameter_higher_collapse_same_t(self):
        base_kwargs = dict(E=200e9, t=0.020, nu=0.30)
        p_large = riser_collapse_pressure(D=0.60, **base_kwargs)
        p_small = riser_collapse_pressure(D=0.30, **base_kwargs)
        assert p_small > p_large


# ---------------------------------------------------------------------------
# minimum_top_tension
# ---------------------------------------------------------------------------
class TestMinimumTopTension:
    def test_result_greater_than_submerged_weight_alone(self):
        result = minimum_top_tension(
            w_sub=1_500.0, L=300.0, bop_weight=50_000.0, safety_factor=1.10
        )
        assert result > 1_500.0 * 300.0

    def test_longer_riser_requires_more_tension(self):
        t_short = minimum_top_tension(w_sub=1_500.0, L=200.0, bop_weight=50_000.0, safety_factor=1.10)
        t_long = minimum_top_tension(w_sub=1_500.0, L=500.0, bop_weight=50_000.0, safety_factor=1.10)
        assert t_long > t_short

    def test_higher_safety_factor_increases_tension(self):
        kwargs = dict(w_sub=1_200.0, L=250.0, bop_weight=40_000.0)
        t_low_sf = minimum_top_tension(**kwargs, safety_factor=1.0)
        t_high_sf = minimum_top_tension(**kwargs, safety_factor=1.5)
        assert t_high_sf > t_low_sf

    def test_manual_check(self):
        # T_min = (w_sub * L + BOP) * safety_factor
        w_sub, L, bop, sf = 1_000.0, 200.0, 30_000.0, 1.25
        expected = (w_sub * L + bop) * sf
        result = minimum_top_tension(w_sub=w_sub, L=L, bop_weight=bop, safety_factor=sf)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_safety_factor_one_no_overhead(self):
        w_sub, L, bop = 800.0, 300.0, 20_000.0
        result = minimum_top_tension(w_sub, L, bop, safety_factor=1.0)
        assert result == pytest.approx(w_sub * L + bop, rel=1e-9)


# ---------------------------------------------------------------------------
# tensile_utilization
# ---------------------------------------------------------------------------
class TestTensileUtilization:
    def test_utilization_at_yield_equals_one(self):
        A = 0.05   # m^2
        F_y = 250e6  # Pa
        T_eff = A * F_y
        result = tensile_utilization(t_eff=T_eff, a_steel=A, f_y=F_y)
        assert result == pytest.approx(1.0, rel=1e-9)

    def test_utilization_below_one_for_sub_yield(self):
        A = 0.04
        F_y = 300e6
        T_eff = 0.5 * A * F_y
        result = tensile_utilization(T_eff, A, F_y)
        assert result == pytest.approx(0.5, rel=1e-9)

    def test_higher_tension_higher_utilization(self):
        A, F_y = 0.03, 250e6
        u_low = tensile_utilization(t_eff=2e6, a_steel=A, f_y=F_y)
        u_high = tensile_utilization(t_eff=5e6, a_steel=A, f_y=F_y)
        assert u_high > u_low

    def test_formula_is_t_over_af(self):
        T, A, F = 3e6, 0.02, 250e6
        result = tensile_utilization(T, A, F)
        assert result == pytest.approx(T / (A * F), rel=1e-9)

    def test_result_positive_for_positive_inputs(self):
        result = tensile_utilization(t_eff=1e6, a_steel=0.01, f_y=200e6)
        assert result > 0.0


# ---------------------------------------------------------------------------
# bending_moment_from_offset
# ---------------------------------------------------------------------------
class TestBendingMomentFromOffset:
    def test_zero_offset_zero_moment(self):
        result = bending_moment_from_offset(t_eff=500_000.0, delta=0.0)
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_proportional_to_offset(self):
        t_eff = 400_000.0
        m1 = bending_moment_from_offset(t_eff, delta=1.0)
        m2 = bending_moment_from_offset(t_eff, delta=3.0)
        assert m2 == pytest.approx(3.0 * m1, rel=1e-9)

    def test_proportional_to_tension(self):
        delta = 2.0
        m1 = bending_moment_from_offset(t_eff=100_000.0, delta=delta)
        m2 = bending_moment_from_offset(t_eff=300_000.0, delta=delta)
        assert m2 == pytest.approx(3.0 * m1, rel=1e-9)

    def test_manual_check(self):
        T, d = 250_000.0, 5.0
        result = bending_moment_from_offset(t_eff=T, delta=d)
        assert result == pytest.approx(T * d, rel=1e-9)

    def test_result_positive_for_positive_inputs(self):
        result = bending_moment_from_offset(t_eff=300_000.0, delta=2.5)
        assert result > 0.0


# ---------------------------------------------------------------------------
# combined_loading_utilization
# ---------------------------------------------------------------------------
class TestCombinedLoadingUtilization:
    def test_fully_loaded_gives_one(self):
        # U = t_eff/t_allow + M/M_allow = 0.5 + 0.5 = 1.0
        result = combined_loading_utilization(
            t_eff=500_000.0, t_allow=1_000_000.0,
            M=250_000.0, M_allow=500_000.0
        )
        assert result == pytest.approx(1.0, rel=1e-9)

    def test_under_loaded_gives_less_than_one(self):
        result = combined_loading_utilization(
            t_eff=300_000.0, t_allow=1_000_000.0,
            M=100_000.0, M_allow=500_000.0
        )
        assert result < 1.0

    def test_tension_only_no_bending(self):
        result = combined_loading_utilization(
            t_eff=600_000.0, t_allow=1_200_000.0,
            M=0.0, M_allow=500_000.0
        )
        assert result == pytest.approx(0.5, rel=1e-9)

    def test_bending_only_no_tension(self):
        result = combined_loading_utilization(
            t_eff=0.0, t_allow=1_000_000.0,
            M=250_000.0, M_allow=1_000_000.0
        )
        assert result == pytest.approx(0.25, rel=1e-9)

    def test_increasing_loads_raises_utilization(self):
        u_low = combined_loading_utilization(100_000.0, 1_000_000.0, 50_000.0, 500_000.0)
        u_high = combined_loading_utilization(500_000.0, 1_000_000.0, 250_000.0, 500_000.0)
        assert u_high > u_low

    def test_manual_formula_check(self):
        T_eff, T_allow = 400_000.0, 800_000.0
        M, M_allow = 150_000.0, 600_000.0
        expected = T_eff / T_allow + M / M_allow
        result = combined_loading_utilization(T_eff, T_allow, M, M_allow)
        assert result == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# annual_fatigue_damage
# ---------------------------------------------------------------------------
class TestAnnualFatigueDamage:
    def test_single_sea_state_damage_calculation(self):
        # D = n_cycles / N_f for one sea state
        sea_states = [{"n_cycles": 1_000.0, "N_f": 10_000.0}]
        result = annual_fatigue_damage(sea_states)
        assert result == pytest.approx(0.1, rel=1e-9)

    def test_two_sea_states_sum_correctly(self):
        sea_states = [
            {"n_cycles": 500.0, "N_f": 5_000.0},
            {"n_cycles": 200.0, "N_f": 4_000.0},
        ]
        result = annual_fatigue_damage(sea_states)
        expected = 500.0 / 5_000.0 + 200.0 / 4_000.0
        assert result == pytest.approx(expected, rel=1e-9)

    def test_empty_sea_states_returns_zero(self):
        result = annual_fatigue_damage([])
        assert result == pytest.approx(0.0)

    def test_larger_n_f_reduces_damage(self):
        ss_low_life = [{"n_cycles": 1000.0, "N_f": 5_000.0}]
        ss_high_life = [{"n_cycles": 1000.0, "N_f": 50_000.0}]
        d_low = annual_fatigue_damage(ss_low_life)
        d_high = annual_fatigue_damage(ss_high_life)
        assert d_high < d_low

    def test_scaling_n_cycles_scales_damage(self):
        ss1 = [{"n_cycles": 100.0, "N_f": 1_000.0}]
        ss2 = [{"n_cycles": 500.0, "N_f": 1_000.0}]
        d1 = annual_fatigue_damage(ss1)
        d2 = annual_fatigue_damage(ss2)
        assert d2 == pytest.approx(5.0 * d1, rel=1e-9)

    def test_damage_below_one_is_acceptable(self):
        # Fatigue life > 1 year => D_annual < 1.0
        sea_states = [
            {"n_cycles": 1_000.0, "N_f": 100_000.0},
            {"n_cycles": 500.0, "N_f": 50_000.0},
        ]
        result = annual_fatigue_damage(sea_states)
        assert result < 1.0

    def test_three_sea_states_manual_check(self):
        sea_states = [
            {"n_cycles": 2_000.0, "N_f": 20_000.0},
            {"n_cycles": 800.0, "N_f": 8_000.0},
            {"n_cycles": 400.0, "N_f": 2_000.0},
        ]
        expected = 2000 / 20000 + 800 / 8000 + 400 / 2000
        result = annual_fatigue_damage(sea_states)
        assert result == pytest.approx(expected, rel=1e-9)
