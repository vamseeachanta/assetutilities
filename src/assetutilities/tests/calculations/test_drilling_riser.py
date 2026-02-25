# ABOUTME: Tests for deepwater drilling riser analysis calculations from OTC literature.
# ABOUTME: Covers Gardner 1982 tension, Kim 1975 natural frequency, Grant 1977 fairing, Vandiver 1985 lock-in, Miller 1985 mud pressure, Imas SCR.

import math
import pytest

from assetutilities.calculations.drilling_riser import (
    gardner_bottom_tension,
    gardner_top_tension,
    kim_natural_frequency_with_pressure,
    grant_faired_drag_coefficient,
    jacobsen_suppression_damage_ratio,
    dsouza_flex_riser_effective_weight,
    vandiver_lock_in_velocity,
    miller_mud_column_pressure,
    imas_scr_response_amplification,
    berner_riser_effective_tension,
)


# ---------------------------------------------------------------------------
# Gardner (1982) drilling riser bottom tension
# T_bottom = (w_air - w_buoyancy) * L - BOP_weight
# ---------------------------------------------------------------------------
class TestGardnerBottomTension:
    def test_returns_value(self):
        t = gardner_bottom_tension(
            w_air_lbf_per_ft=200.0,
            w_buoyancy_lbf_per_ft=80.0,
            length_ft=5000.0,
            bop_weight_lbf=300_000.0,
        )
        assert isinstance(t, float)

    def test_manual_formula_check(self):
        w_air = 200.0
        w_buoy = 80.0
        L = 5000.0
        bop = 300_000.0
        expected = (w_air - w_buoy) * L - bop
        result = gardner_bottom_tension(w_air, w_buoy, L, bop)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_heavier_riser_increases_tension(self):
        t_light = gardner_bottom_tension(150.0, 80.0, 5000.0, 200_000.0)
        t_heavy = gardner_bottom_tension(250.0, 80.0, 5000.0, 200_000.0)
        assert t_heavy > t_light

    def test_longer_riser_increases_bottom_tension(self):
        t_short = gardner_bottom_tension(200.0, 80.0, 3000.0, 200_000.0)
        t_long = gardner_bottom_tension(200.0, 80.0, 7000.0, 200_000.0)
        assert t_long > t_short

    def test_heavier_bop_reduces_bottom_tension(self):
        t_light_bop = gardner_bottom_tension(200.0, 80.0, 5000.0, 100_000.0)
        t_heavy_bop = gardner_bottom_tension(200.0, 80.0, 5000.0, 400_000.0)
        assert t_heavy_bop < t_light_bop

    def test_representative_deepwater_case(self):
        # 5000 ft riser, submerged weight 120 lb/ft, BOP 350 kips
        result = gardner_bottom_tension(200.0, 80.0, 5000.0, 350_000.0)
        expected = (200.0 - 80.0) * 5000.0 - 350_000.0
        assert result == pytest.approx(expected, rel=1e-9)


class TestGardnerTopTension:
    def test_top_greater_than_bottom(self):
        # T_top = T_bottom + sum(segment weights)
        t_bottom = 50_000.0
        segment_weights = [10_000.0, 20_000.0, 15_000.0]
        t_top = gardner_top_tension(t_bottom, segment_weights)
        assert t_top > t_bottom

    def test_formula_manual_check(self):
        t_bottom = 50_000.0
        segments = [10_000.0, 15_000.0, 25_000.0]
        expected = t_bottom + sum(segments)
        result = gardner_top_tension(t_bottom, segments)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_empty_segments_equals_bottom_tension(self):
        t_bottom = 100_000.0
        result = gardner_top_tension(t_bottom, [])
        assert result == pytest.approx(t_bottom, rel=1e-9)

    def test_more_segments_gives_higher_top_tension(self):
        t_few = gardner_top_tension(50_000.0, [10_000.0])
        t_many = gardner_top_tension(50_000.0, [10_000.0, 20_000.0, 30_000.0])
        assert t_many > t_few


# ---------------------------------------------------------------------------
# Kim (1975) natural frequency shift with internal/external pressure
# ---------------------------------------------------------------------------
class TestKimNaturalFrequencyWithPressure:
    def test_returns_positive_frequency(self):
        fn = kim_natural_frequency_with_pressure(
            fn_vacuum_hz=0.5,
            internal_pressure_psi=5_000.0,
            external_pressure_psi=2_000.0,
            pipe_cross_section_in2=10.0,
            riser_length_ft=5000.0,
            riser_weight_lbf=500_000.0,
        )
        assert fn > 0

    def test_internal_pressure_reduces_frequency(self):
        # Higher internal pressure reduces effective tension → lower natural frequency
        fn_low_p = kim_natural_frequency_with_pressure(0.5, 1_000.0, 2_000.0, 10.0, 5000.0, 500_000.0)
        fn_high_p = kim_natural_frequency_with_pressure(0.5, 10_000.0, 2_000.0, 10.0, 5000.0, 500_000.0)
        assert fn_high_p < fn_low_p

    def test_external_pressure_increases_frequency(self):
        # Higher external pressure increases effective tension → higher natural frequency
        fn_low_ext = kim_natural_frequency_with_pressure(0.5, 2_000.0, 1_000.0, 10.0, 5000.0, 500_000.0)
        fn_high_ext = kim_natural_frequency_with_pressure(0.5, 2_000.0, 8_000.0, 10.0, 5000.0, 500_000.0)
        assert fn_high_ext > fn_low_ext

    def test_zero_pressure_gives_vacuum_frequency(self):
        fn_vac = 0.4
        fn = kim_natural_frequency_with_pressure(fn_vac, 0.0, 0.0, 10.0, 5000.0, 500_000.0)
        assert fn == pytest.approx(fn_vac, rel=1e-6)


# ---------------------------------------------------------------------------
# Grant (1977) riser fairing drag reduction
# Cd_faired = 0.7 * Cd_bare (or configurable factor)
# ---------------------------------------------------------------------------
class TestGrantFairedDragCoefficient:
    def test_faired_lower_than_bare(self):
        cd_bare = 1.0
        cd_faired = grant_faired_drag_coefficient(cd_bare)
        assert cd_faired < cd_bare

    def test_default_reduction_factor(self):
        cd_bare = 1.2
        cd_faired = grant_faired_drag_coefficient(cd_bare)
        assert cd_faired == pytest.approx(0.7 * 1.2, rel=1e-9)

    def test_custom_reduction_factor(self):
        cd_bare = 1.0
        cd_faired = grant_faired_drag_coefficient(cd_bare, reduction_factor=0.5)
        assert cd_faired == pytest.approx(0.5, rel=1e-9)

    def test_result_is_positive(self):
        assert grant_faired_drag_coefficient(1.0) > 0

    def test_raises_on_negative_cd(self):
        with pytest.raises(ValueError):
            grant_faired_drag_coefficient(-0.5)

    def test_raises_on_reduction_factor_out_of_range(self):
        with pytest.raises(ValueError):
            grant_faired_drag_coefficient(1.0, reduction_factor=1.5)


# ---------------------------------------------------------------------------
# Jacobsen (1996) suppression device effectiveness
# fatigue_damage_ratio = suppressed / unsuppressed
# ---------------------------------------------------------------------------
class TestJacobsenSuppressionDamageRatio:
    def test_returns_value_between_zero_and_one(self):
        ratio = jacobsen_suppression_damage_ratio(
            unsuppressed_damage=1.0,
            suppression_effectiveness=0.7,
        )
        assert 0.0 <= ratio <= 1.0

    def test_formula_manual_check(self):
        # damage_ratio = 1.0 - suppression_effectiveness
        unsuppressed = 1.0
        effectiveness = 0.85
        expected = 1.0 - effectiveness
        result = jacobsen_suppression_damage_ratio(unsuppressed, effectiveness)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_full_suppression_gives_zero_damage_ratio(self):
        ratio = jacobsen_suppression_damage_ratio(1.0, 1.0)
        assert ratio == pytest.approx(0.0, abs=1e-12)

    def test_no_suppression_gives_ratio_one(self):
        ratio = jacobsen_suppression_damage_ratio(1.0, 0.0)
        assert ratio == pytest.approx(1.0, rel=1e-9)

    def test_higher_effectiveness_gives_lower_ratio(self):
        r1 = jacobsen_suppression_damage_ratio(1.0, 0.5)
        r2 = jacobsen_suppression_damage_ratio(1.0, 0.9)
        assert r2 < r1

    def test_actual_suppressed_damage(self):
        unsuppressed = 2.5
        effectiveness = 0.80
        expected = unsuppressed * (1.0 - effectiveness)
        result = jacobsen_suppression_damage_ratio(unsuppressed, effectiveness)
        assert result == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# D'Souza (2002) unbonded flex riser weight and tension loss model
# ---------------------------------------------------------------------------
class TestDsouzaFlexRiserEffectiveWeight:
    def test_returns_positive_weight(self):
        w = dsouza_flex_riser_effective_weight(
            weight_in_air_lbf_per_ft=80.0,
            displaced_fluid_weight_lbf_per_ft=55.0,
        )
        assert w > 0

    def test_formula_manual_check(self):
        w_air = 80.0
        w_fluid = 55.0
        expected = w_air - w_fluid
        result = dsouza_flex_riser_effective_weight(w_air, w_fluid)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_neutral_buoyancy_gives_zero_weight(self):
        result = dsouza_flex_riser_effective_weight(60.0, 60.0)
        assert result == pytest.approx(0.0, abs=1e-12)

    def test_tension_loss_along_length(self):
        # Tension loss = effective_weight * length
        w_eff = dsouza_flex_riser_effective_weight(80.0, 55.0)
        length = 1000.0
        tension_loss = w_eff * length
        assert tension_loss == pytest.approx(25_000.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Vandiver (1985) lock-in prediction: critical velocity
# Vc = f_n * D / St
# ---------------------------------------------------------------------------
class TestVandiversLockInVelocity:
    def test_returns_positive_velocity(self):
        vc = vandiver_lock_in_velocity(
            natural_frequency_hz=0.5,
            diameter_ft=1.5,
            strouhal_number=0.2,
        )
        assert vc > 0

    def test_formula_manual_check(self):
        f_n = 0.4
        D = 1.5
        St = 0.2
        expected = f_n * D / St
        result = vandiver_lock_in_velocity(f_n, D, St)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_higher_frequency_gives_higher_critical_velocity(self):
        vc_low = vandiver_lock_in_velocity(0.3, 1.5, 0.2)
        vc_high = vandiver_lock_in_velocity(0.8, 1.5, 0.2)
        assert vc_high > vc_low

    def test_larger_diameter_gives_higher_critical_velocity(self):
        vc_small = vandiver_lock_in_velocity(0.5, 1.0, 0.2)
        vc_large = vandiver_lock_in_velocity(0.5, 2.0, 0.2)
        assert vc_large > vc_small

    def test_higher_strouhal_gives_lower_critical_velocity(self):
        vc_low_st = vandiver_lock_in_velocity(0.5, 1.5, 0.15)
        vc_high_st = vandiver_lock_in_velocity(0.5, 1.5, 0.25)
        assert vc_high_st < vc_low_st

    def test_default_strouhal_number(self):
        # Default St = 0.2 for smooth cylinders in turbulent flow
        vc = vandiver_lock_in_velocity(0.5, 1.5)
        expected = 0.5 * 1.5 / 0.2
        assert vc == pytest.approx(expected, rel=1e-9)

    def test_raises_on_zero_strouhal(self):
        with pytest.raises((ValueError, ZeroDivisionError)):
            vandiver_lock_in_velocity(0.5, 1.5, 0.0)


# ---------------------------------------------------------------------------
# Miller (1985) mud column internal pressure
# P_mud = rho_mud * g * depth  (in SI) or 0.052 * mud_weight_ppg * depth_ft (field units)
# ---------------------------------------------------------------------------
class TestMillerMudColumnPressure:
    def test_returns_positive_pressure(self):
        p = miller_mud_column_pressure(
            mud_weight_ppg=12.0,
            depth_ft=10_000.0,
        )
        assert p > 0

    def test_formula_field_units(self):
        # P_psi = 0.052 * mud_weight_ppg * depth_ft
        mud_weight = 12.0
        depth = 10_000.0
        expected = 0.052 * mud_weight * depth
        result = miller_mud_column_pressure(mud_weight, depth)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_heavier_mud_gives_higher_pressure(self):
        p_light = miller_mud_column_pressure(9.0, 10_000.0)
        p_heavy = miller_mud_column_pressure(16.0, 10_000.0)
        assert p_heavy > p_light

    def test_deeper_gives_higher_pressure(self):
        p_shallow = miller_mud_column_pressure(12.0, 5_000.0)
        p_deep = miller_mud_column_pressure(12.0, 15_000.0)
        assert p_deep > p_shallow

    def test_sea_water_equivalent_check(self):
        # Seawater ≈ 8.6 ppg → ~4472 psi at 10000 ft
        p = miller_mud_column_pressure(8.6, 10_000.0)
        assert p == pytest.approx(0.052 * 8.6 * 10_000.0, rel=1e-6)

    def test_zero_depth_gives_zero_pressure(self):
        p = miller_mud_column_pressure(12.0, 0.0)
        assert p == pytest.approx(0.0, abs=1e-12)

    def test_raises_on_negative_mud_weight(self):
        with pytest.raises(ValueError):
            miller_mud_column_pressure(-1.0, 10_000.0)

    def test_raises_on_negative_depth(self):
        with pytest.raises(ValueError):
            miller_mud_column_pressure(12.0, -100.0)


# ---------------------------------------------------------------------------
# Imas SCR response sensitivity
# response_amplification = A * U^B
# ---------------------------------------------------------------------------
class TestImasScRResponseAmplification:
    def test_returns_positive_value(self):
        amp = imas_scr_response_amplification(
            current_velocity=1.0,
            A=1.0,
            B=2.0,
        )
        assert amp > 0

    def test_formula_manual_check(self):
        U = 1.5
        A = 0.8
        B = 2.5
        expected = A * U ** B
        result = imas_scr_response_amplification(U, A, B)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_higher_velocity_gives_higher_amplification(self):
        amp_low = imas_scr_response_amplification(0.5, 1.0, 2.0)
        amp_high = imas_scr_response_amplification(2.0, 1.0, 2.0)
        assert amp_high > amp_low

    def test_higher_B_gives_greater_velocity_sensitivity(self):
        # At U > 1: higher B gives higher amplification
        amp_low_b = imas_scr_response_amplification(2.0, 1.0, 1.5)
        amp_high_b = imas_scr_response_amplification(2.0, 1.0, 3.0)
        assert amp_high_b > amp_low_b

    def test_zero_velocity_gives_zero_amplification(self):
        amp = imas_scr_response_amplification(0.0, 1.0, 2.0)
        assert amp == pytest.approx(0.0, abs=1e-12)

    def test_unit_velocity_equals_coefficient_A(self):
        A = 1.5
        amp = imas_scr_response_amplification(1.0, A, 3.0)
        assert amp == pytest.approx(A, rel=1e-9)

    def test_raises_on_negative_velocity(self):
        with pytest.raises(ValueError):
            imas_scr_response_amplification(-1.0, 1.0, 2.0)


# ---------------------------------------------------------------------------
# Berner (1997) Neptune Project riser effective tension
# Stahl OTC 3902 offshore platform conductor method used for top tension check
# T_eff = T_top - (w_submerged * L) + delta_tension_from_vessel_offset
# ---------------------------------------------------------------------------
class TestBernerRiserEffectiveTension:
    def test_returns_value(self):
        t_eff = berner_riser_effective_tension(
            top_tension_lbf=500_000.0,
            submerged_weight_lbf_per_ft=120.0,
            riser_length_ft=3000.0,
            vessel_offset_tension_delta_lbf=20_000.0,
        )
        assert isinstance(t_eff, float)

    def test_formula_manual_check(self):
        T_top = 500_000.0
        w_sub = 120.0
        L = 3000.0
        delta = 20_000.0
        expected = T_top - w_sub * L + delta
        result = berner_riser_effective_tension(T_top, w_sub, L, delta)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_higher_top_tension_increases_effective_tension(self):
        t1 = berner_riser_effective_tension(400_000.0, 120.0, 3000.0, 0.0)
        t2 = berner_riser_effective_tension(600_000.0, 120.0, 3000.0, 0.0)
        assert t2 > t1

    def test_longer_riser_reduces_effective_tension(self):
        t_short = berner_riser_effective_tension(500_000.0, 120.0, 2000.0, 0.0)
        t_long = berner_riser_effective_tension(500_000.0, 120.0, 5000.0, 0.0)
        assert t_long < t_short

    def test_positive_offset_delta_increases_tension(self):
        t_no_offset = berner_riser_effective_tension(500_000.0, 120.0, 3000.0, 0.0)
        t_with_offset = berner_riser_effective_tension(500_000.0, 120.0, 3000.0, 50_000.0)
        assert t_with_offset > t_no_offset
