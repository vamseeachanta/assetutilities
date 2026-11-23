# ABOUTME: Unit tests for riser VIV and hydrodynamics calculation module.
# ABOUTME: Covers drag, Strouhal, reduced velocity, lock-in, fatigue, and natural frequency.
"""Tests for riser_viv module — VIV, drag, fatigue, and effective tension.

Reference values from:
- Blevins (1990) Flow-Induced Vibrations — Strouhal, Griffin curve constants
- BP riser drag data correlations (smooth/rough cylinder)
- Shear7 manual — mode shape natural frequency formula
- TNE011-1, TNE012-1 internal paper reference values
"""
import math
import pytest

from assetutilities.calculations.riser_viv import (
    drag_coefficient_smooth_cylinder,
    drag_coefficient_bundle,
    strouhal_frequency,
    reduced_velocity,
    viv_amplitude_response,
    viv_lock_in,
    viv_fatigue_damage,
    effective_tension,
    riser_natural_frequency,
)


# ---------------------------------------------------------------------------
# Drag coefficient — smooth cylinder
# ---------------------------------------------------------------------------

class TestDragCoefficientSmooth:
    def test_subcritical_regime(self):
        """Re ~ 1e4: Cd should be close to 1.2."""
        Cd = drag_coefficient_smooth_cylinder(Re=1e4)
        assert 0.9 < Cd < 1.5

    def test_critical_regime(self):
        """Re ~ 5e5: Cd drops (drag crisis ~0.3-0.5)."""
        Cd = drag_coefficient_smooth_cylinder(Re=5e5)
        assert 0.1 < Cd < 0.7

    def test_supercritical_regime(self):
        """Re ~ 1e7: Cd recovers to ~0.5-0.7."""
        Cd = drag_coefficient_smooth_cylinder(Re=1e7)
        assert 0.3 < Cd < 1.0

    def test_returns_positive(self):
        for Re in (1e3, 1e5, 1e6, 1e8):
            assert drag_coefficient_smooth_cylinder(Re) > 0

    def test_invalid_re_raises(self):
        with pytest.raises(ValueError):
            drag_coefficient_smooth_cylinder(Re=0)


# ---------------------------------------------------------------------------
# Drag coefficient — riser bundle (BP correlations)
# ---------------------------------------------------------------------------

class TestDragCoefficientBundle:
    def test_single_riser_same_as_smooth(self):
        """Bundle of 1 should return the smooth cylinder drag."""
        Re = 1e4
        Cd_single = drag_coefficient_smooth_cylinder(Re=Re)
        Cd_bundle = drag_coefficient_bundle(Re=Re, n_risers=1, pitch_diameter_ratio=1.0)
        assert Cd_bundle == pytest.approx(Cd_single, rel=0.05)

    def test_bundle_higher_than_single(self):
        """Bundle interference increases effective drag."""
        Re = 1e4
        Cd_single = drag_coefficient_bundle(Re=Re, n_risers=1, pitch_diameter_ratio=2.5)
        Cd_bundle = drag_coefficient_bundle(Re=Re, n_risers=4, pitch_diameter_ratio=2.5)
        assert Cd_bundle > Cd_single

    def test_returns_positive(self):
        Cd = drag_coefficient_bundle(Re=5e4, n_risers=3, pitch_diameter_ratio=2.0)
        assert Cd > 0

    def test_invalid_n_risers_raises(self):
        with pytest.raises(ValueError):
            drag_coefficient_bundle(Re=1e4, n_risers=0, pitch_diameter_ratio=2.0)


# ---------------------------------------------------------------------------
# Strouhal vortex shedding frequency
# f_s = St * U / D
# ---------------------------------------------------------------------------

class TestStrouhalFrequency:
    def test_standard_strouhal_number(self):
        """St = 0.2, U = 1.0, D = 0.5 => f_s = 0.4 Hz."""
        f_s = strouhal_frequency(U=1.0, D=0.5, St=0.2)
        assert f_s == pytest.approx(0.4, rel=1e-6)

    def test_default_strouhal_is_02(self):
        """Default St = 0.2 for subcritical cylinders."""
        f_s = strouhal_frequency(U=2.0, D=0.25)
        assert f_s == pytest.approx(0.2 * 2.0 / 0.25, rel=1e-6)

    def test_proportional_to_velocity(self):
        f1 = strouhal_frequency(U=1.0, D=0.5)
        f2 = strouhal_frequency(U=2.0, D=0.5)
        assert f2 == pytest.approx(2.0 * f1, rel=1e-6)

    def test_inversely_proportional_to_diameter(self):
        f1 = strouhal_frequency(U=1.0, D=0.5)
        f2 = strouhal_frequency(U=1.0, D=1.0)
        assert f1 == pytest.approx(2.0 * f2, rel=1e-6)

    def test_zero_velocity_returns_zero(self):
        f_s = strouhal_frequency(U=0.0, D=0.5)
        assert f_s == pytest.approx(0.0, abs=1e-12)

    def test_invalid_diameter_raises(self):
        with pytest.raises(ValueError):
            strouhal_frequency(U=1.0, D=0.0)


# ---------------------------------------------------------------------------
# Reduced velocity
# Vr = U / (f_n * D)
# ---------------------------------------------------------------------------

class TestReducedVelocity:
    def test_basic_calculation(self):
        """U=1.0, f_n=1.0, D=0.25 => Vr=4.0."""
        Vr = reduced_velocity(U=1.0, f_n=1.0, D=0.25)
        assert Vr == pytest.approx(4.0, rel=1e-6)

    def test_lock_in_range(self):
        """VIV lock-in typically occurs at Vr in [4, 8]; check a mid-range value."""
        Vr = reduced_velocity(U=1.0, f_n=0.25, D=0.5)
        assert 4.0 < Vr < 10.0

    def test_invalid_fn_raises(self):
        with pytest.raises(ValueError):
            reduced_velocity(U=1.0, f_n=0.0, D=0.5)

    def test_invalid_diameter_raises(self):
        with pytest.raises(ValueError):
            reduced_velocity(U=1.0, f_n=1.0, D=0.0)


# ---------------------------------------------------------------------------
# VIV lock-in condition
# ---------------------------------------------------------------------------

class TestVIVLockIn:
    def test_in_lock_in_range(self):
        assert viv_lock_in(Vr=5.0) is True

    def test_below_lock_in_range(self):
        assert viv_lock_in(Vr=1.0) is False

    def test_above_lock_in_range(self):
        assert viv_lock_in(Vr=12.0) is False

    def test_boundary_low(self):
        """Vr=4 is the conventional lower boundary — in lock-in."""
        assert viv_lock_in(Vr=4.0) is True

    def test_boundary_high(self):
        """Vr=8 is the conventional upper boundary — in lock-in."""
        assert viv_lock_in(Vr=8.0) is True


# ---------------------------------------------------------------------------
# VIV amplitude response (Griffin curve / Vandiver correlation)
# A/D = f(Vr, Ks)
# ---------------------------------------------------------------------------

class TestVIVAmplitudeResponse:
    def test_no_lock_in_gives_low_amplitude(self):
        """Outside lock-in: amplitude should be negligible."""
        A_D = viv_amplitude_response(Vr=2.0, Ks=0.1)
        assert A_D < 0.05

    def test_lock_in_gives_significant_amplitude(self):
        """At Vr~5, low damping => A/D should be ~0.5-1.5 range."""
        A_D = viv_amplitude_response(Vr=5.5, Ks=0.05)
        assert 0.1 < A_D < 2.0

    def test_higher_damping_reduces_amplitude(self):
        """Higher mass-damping (Ks) suppresses VIV."""
        A_low = viv_amplitude_response(Vr=5.5, Ks=0.05)
        A_high = viv_amplitude_response(Vr=5.5, Ks=1.0)
        assert A_low > A_high

    def test_returns_non_negative(self):
        for Vr in (1.0, 5.0, 9.0):
            assert viv_amplitude_response(Vr=Vr, Ks=0.1) >= 0.0


# ---------------------------------------------------------------------------
# VIV fatigue damage  (S-N Palmgren-Miner)
# D = sum(n_i / N_i)
# N_i = a * sigma_i^(-m)   (DNV RP-C203 D-curve defaults)
# ---------------------------------------------------------------------------

class TestVIVFatigueDamage:
    def test_zero_cycles_zero_damage(self):
        D = viv_fatigue_damage(stress_ranges=[], cycle_counts=[])
        assert D == pytest.approx(0.0, abs=1e-12)

    def test_single_block_result(self):
        """Simple check: one stress range, known N => D = n/N."""
        sigma = 50e6   # 50 MPa
        n_cycles = 1000
        # DNV D-curve: log10(N) = 12.164 - 3*log10(sigma_MPa)
        log_N = 12.164 - 3.0 * math.log10(50.0)
        N_expected = 10**log_N
        D_expected = n_cycles / N_expected
        D = viv_fatigue_damage(
            stress_ranges=[sigma],
            cycle_counts=[n_cycles],
        )
        assert D == pytest.approx(D_expected, rel=1e-3)

    def test_more_cycles_more_damage(self):
        D1 = viv_fatigue_damage(stress_ranges=[50e6], cycle_counts=[1000])
        D2 = viv_fatigue_damage(stress_ranges=[50e6], cycle_counts=[2000])
        assert D2 == pytest.approx(2.0 * D1, rel=1e-6)

    def test_miner_sum_is_additive(self):
        D_combined = viv_fatigue_damage(
            stress_ranges=[50e6, 100e6],
            cycle_counts=[1000, 500],
        )
        D1 = viv_fatigue_damage(stress_ranges=[50e6], cycle_counts=[1000])
        D2 = viv_fatigue_damage(stress_ranges=[100e6], cycle_counts=[500])
        assert D_combined == pytest.approx(D1 + D2, rel=1e-6)

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            viv_fatigue_damage(stress_ranges=[50e6, 100e6], cycle_counts=[1000])


# ---------------------------------------------------------------------------
# Effective tension  (internal pressure effects — TNE012-1)
# T_eff = T_wall - pi * A_i + pe * A_e
# ---------------------------------------------------------------------------

class TestEffectiveTension:
    def test_zero_pressure_equals_wall_tension(self):
        """No internal/external pressure => T_eff = T_wall."""
        D = 0.3239
        t = 0.0143
        T_eff = effective_tension(T_wall=1e6, pi=0.0, pe=0.0, D=D, t=t)
        assert T_eff == pytest.approx(1e6, rel=1e-6)

    def test_internal_pressure_reduces_tension(self):
        """High internal pressure produces end-cap force that reduces effective tension."""
        D, t = 0.3239, 0.0143
        T_no_p = effective_tension(T_wall=2e6, pi=0.0, pe=0.0, D=D, t=t)
        T_with_p = effective_tension(T_wall=2e6, pi=20e6, pe=0.0, D=D, t=t)
        assert T_with_p < T_no_p

    def test_external_pressure_increases_tension(self):
        """External pressure on cap increases effective tension."""
        D, t = 0.3239, 0.0143
        T_no_p = effective_tension(T_wall=2e6, pi=0.0, pe=0.0, D=D, t=t)
        T_with_ext = effective_tension(T_wall=2e6, pi=0.0, pe=5e6, D=D, t=t)
        assert T_with_ext > T_no_p

    def test_known_value(self):
        """
        T_wall=5 MN, pi=10 MPa, pe=1 MPa, D=0.5 m, t=0.02 m
        r_i = D/2 - t = 0.23 m  => A_i = pi * 0.23^2 = 0.16619 m^2
        A_e = pi * (D/2)^2     = pi * 0.0625 = 0.19635 m^2
        T_eff = 5e6 - 10e6*0.16619 + 1e6*0.19635
        """
        D, t = 0.5, 0.02
        r_i = D / 2 - t
        A_i = math.pi * r_i**2
        A_e = math.pi * (D / 2)**2
        T_wall = 5e6
        pi_p = 10e6
        pe = 1e6
        expected = T_wall - pi_p * A_i + pe * A_e
        T_eff = effective_tension(T_wall=T_wall, pi=pi_p, pe=pe, D=D, t=t)
        assert T_eff == pytest.approx(expected, rel=1e-5)


# ---------------------------------------------------------------------------
# Riser natural frequency — pinned-pinned beam
# f_n = (n / (2 * L)) * sqrt(EI / m)
# ---------------------------------------------------------------------------

class TestRiserNaturalFrequency:
    def test_mode_1_positive(self):
        f = riser_natural_frequency(n=1, L=500.0, EI=1e8, m=200.0)
        assert f > 0

    def test_mode_2_double_mode_1(self):
        """For pinned-pinned: f_n scales linearly with mode number."""
        f1 = riser_natural_frequency(n=1, L=500.0, EI=1e8, m=200.0)
        f2 = riser_natural_frequency(n=2, L=500.0, EI=1e8, m=200.0)
        assert f2 == pytest.approx(2.0 * f1, rel=1e-6)

    def test_longer_riser_lower_frequency(self):
        f_short = riser_natural_frequency(n=1, L=200.0, EI=1e8, m=200.0)
        f_long = riser_natural_frequency(n=1, L=500.0, EI=1e8, m=200.0)
        assert f_long < f_short

    def test_stiffer_riser_higher_frequency(self):
        f_soft = riser_natural_frequency(n=1, L=500.0, EI=1e7, m=200.0)
        f_stiff = riser_natural_frequency(n=1, L=500.0, EI=1e9, m=200.0)
        assert f_stiff > f_soft

    def test_known_value(self):
        """
        n=1, L=500 m, EI=1e8 N.m^2, m=200 kg/m
        f_1 = (1/(2*500)) * sqrt(1e8/200) = 0.001 * 707.107 = 0.707107 Hz
        """
        f = riser_natural_frequency(n=1, L=500.0, EI=1e8, m=200.0)
        expected = (1 / (2 * 500.0)) * math.sqrt(1e8 / 200.0)
        assert f == pytest.approx(expected, rel=1e-6)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            riser_natural_frequency(n=0, L=500.0, EI=1e8, m=200.0)

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError):
            riser_natural_frequency(n=1, L=0.0, EI=1e8, m=200.0)
