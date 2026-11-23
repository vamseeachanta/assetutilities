# ABOUTME: Tests for Steel Catenary Riser (SCR) fatigue calculations.
# ABOUTME: Covers TDZ hotspot, KC number, Miner's rule, S-N, VIV amplitude, Brooks screening.

import math
import pytest

from assetutilities.calculations.scr_fatigue import (
    keulegan_carpenter_number,
    soil_interaction_fatigue_factor,
    fatigue_damage_tdz,
    scr_sn_fatigue_life,
    allen_viv_amplitude_ratio,
    brooks_viv_screening,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sn_params():
    """DNV D-curve S-N parameters (seawater, cathodic protection)."""
    return {
        "a_param": 1.592e12,  # cycles at unit stress range
        "m_param": 3.0,       # slope exponent
    }


# ---------------------------------------------------------------------------
# keulegan_carpenter_number
# KC = U_m * T / D
# ---------------------------------------------------------------------------

class TestKeulaganCarpenterNumber:
    def test_known_value(self):
        # KC = 1.5 * 10 / 0.5 = 30
        kc = keulegan_carpenter_number(u_m=1.5, period=10.0, diameter=0.5)
        assert kc == pytest.approx(30.0, rel=1e-9)

    def test_returns_positive_value(self):
        kc = keulegan_carpenter_number(u_m=0.8, period=12.0, diameter=0.4)
        assert kc > 0

    def test_scales_linearly_with_velocity(self):
        kc1 = keulegan_carpenter_number(u_m=1.0, period=10.0, diameter=0.5)
        kc2 = keulegan_carpenter_number(u_m=2.0, period=10.0, diameter=0.5)
        assert kc2 == pytest.approx(2.0 * kc1, rel=1e-9)

    def test_scales_linearly_with_period(self):
        kc1 = keulegan_carpenter_number(u_m=1.0, period=5.0, diameter=0.5)
        kc2 = keulegan_carpenter_number(u_m=1.0, period=10.0, diameter=0.5)
        assert kc2 == pytest.approx(2.0 * kc1, rel=1e-9)

    def test_inversely_proportional_to_diameter(self):
        kc1 = keulegan_carpenter_number(u_m=1.0, period=10.0, diameter=0.5)
        kc2 = keulegan_carpenter_number(u_m=1.0, period=10.0, diameter=1.0)
        assert kc1 == pytest.approx(2.0 * kc2, rel=1e-9)

    def test_raises_on_non_positive_diameter(self):
        with pytest.raises(ValueError, match="diameter must be positive"):
            keulegan_carpenter_number(u_m=1.0, period=10.0, diameter=0.0)

    def test_raises_on_non_positive_period(self):
        with pytest.raises(ValueError, match="period must be positive"):
            keulegan_carpenter_number(u_m=1.0, period=0.0, diameter=0.5)

    def test_raises_on_negative_velocity(self):
        with pytest.raises(ValueError, match="u_m must be non-negative"):
            keulegan_carpenter_number(u_m=-1.0, period=10.0, diameter=0.5)

    def test_zero_velocity_gives_zero_kc(self):
        kc = keulegan_carpenter_number(u_m=0.0, period=10.0, diameter=0.5)
        assert kc == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# soil_interaction_fatigue_factor
# Low KC correction for TDZ soil damping (OTC2001-13109)
# factor >= 1.0 for KC < 10 (conservative amplification); factor = 1.0 for KC >= 10
# ---------------------------------------------------------------------------

class TestSoilInteractionFatigueFactor:
    def test_high_kc_gives_factor_one(self):
        factor = soil_interaction_fatigue_factor(kc=15.0)
        assert factor == pytest.approx(1.0, rel=1e-9)

    def test_low_kc_gives_factor_greater_than_one(self):
        factor = soil_interaction_fatigue_factor(kc=2.0)
        assert factor > 1.0

    def test_factor_at_boundary_kc_10(self):
        factor = soil_interaction_fatigue_factor(kc=10.0)
        assert factor == pytest.approx(1.0, rel=1e-3)

    def test_factor_decreases_with_increasing_kc_below_10(self):
        f_low = soil_interaction_fatigue_factor(kc=3.0)
        f_high = soil_interaction_fatigue_factor(kc=7.0)
        assert f_low > f_high

    def test_factor_is_positive(self):
        for kc in [0.5, 1.0, 5.0, 10.0, 20.0]:
            assert soil_interaction_fatigue_factor(kc=kc) > 0

    def test_raises_on_negative_kc(self):
        with pytest.raises(ValueError, match="kc must be non-negative"):
            soil_interaction_fatigue_factor(kc=-1.0)

    def test_returns_float(self):
        result = soil_interaction_fatigue_factor(kc=5.0)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# fatigue_damage_tdz
# D = sum(n_i / N_fi) — Miner's rule
# N_fi = A / (Delta_sigma_i)^m * (1 / soil_factor_i)
# ---------------------------------------------------------------------------

class TestFatigueDamageTdz:
    def test_returns_positive_damage(self, sn_params):
        damage = fatigue_damage_tdz(
            stress_ranges=[15e6, 20e6, 30e6],
            cycle_counts=[1e5, 5e4, 1e4],
            kc_numbers=[2.0, 5.0, 8.0],
            **sn_params,
        )
        assert damage > 0

    def test_zero_cycles_zero_damage(self, sn_params):
        damage = fatigue_damage_tdz(
            stress_ranges=[20e6],
            cycle_counts=[0.0],
            kc_numbers=[5.0],
            **sn_params,
        )
        assert damage == pytest.approx(0.0, abs=1e-12)

    def test_miner_sum_manual_check(self, sn_params):
        sigma = 20e6
        n = 1e4
        kc = 15.0  # factor = 1.0
        a = sn_params["a_param"]
        m = sn_params["m_param"]
        n_f = a / (sigma ** m)
        expected = n / n_f
        result = fatigue_damage_tdz(
            stress_ranges=[sigma],
            cycle_counts=[n],
            kc_numbers=[kc],
            **sn_params,
        )
        assert result == pytest.approx(expected, rel=1e-9)

    def test_low_kc_increases_damage(self, sn_params):
        d_high_kc = fatigue_damage_tdz(
            stress_ranges=[20e6], cycle_counts=[1e4], kc_numbers=[15.0],
            **sn_params,
        )
        d_low_kc = fatigue_damage_tdz(
            stress_ranges=[20e6], cycle_counts=[1e4], kc_numbers=[2.0],
            **sn_params,
        )
        assert d_low_kc > d_high_kc

    def test_raises_on_mismatched_inputs(self, sn_params):
        with pytest.raises(ValueError, match="same length"):
            fatigue_damage_tdz(
                stress_ranges=[20e6, 30e6],
                cycle_counts=[1e4],
                kc_numbers=[5.0, 8.0],
                **sn_params,
            )

    def test_damage_increases_with_stress_range(self, sn_params):
        d_low = fatigue_damage_tdz(
            stress_ranges=[15e6], cycle_counts=[1e4], kc_numbers=[10.0],
            **sn_params,
        )
        d_high = fatigue_damage_tdz(
            stress_ranges=[30e6], cycle_counts=[1e4], kc_numbers=[10.0],
            **sn_params,
        )
        assert d_high > d_low


# ---------------------------------------------------------------------------
# scr_sn_fatigue_life
# Delta_sigma = 2 * sigma_a  (double amplitude → stress range)
# N_f = A / (Delta_sigma)^m
# ---------------------------------------------------------------------------

class TestScrSnFatigueLife:
    def test_returns_positive_life(self, sn_params):
        n_f = scr_sn_fatigue_life(sigma_a=20e6, **sn_params)
        assert n_f > 0

    def test_formula_correctness(self, sn_params):
        sigma_a = 25e6
        a = sn_params["a_param"]
        m = sn_params["m_param"]
        delta_sigma = 2 * sigma_a
        expected = a / (delta_sigma ** m)
        result = scr_sn_fatigue_life(sigma_a=sigma_a, **sn_params)
        assert result == pytest.approx(expected, rel=1e-9)

    def test_higher_stress_gives_shorter_life(self, sn_params):
        n_low = scr_sn_fatigue_life(sigma_a=15e6, **sn_params)
        n_high = scr_sn_fatigue_life(sigma_a=30e6, **sn_params)
        assert n_high < n_low

    def test_raises_on_non_positive_sigma_a(self, sn_params):
        with pytest.raises(ValueError, match="sigma_a must be positive"):
            scr_sn_fatigue_life(sigma_a=0.0, **sn_params)

    def test_raises_on_non_positive_a_param(self):
        with pytest.raises(ValueError, match="a_param must be positive"):
            scr_sn_fatigue_life(sigma_a=20e6, a_param=0.0, m_param=3.0)

    def test_returns_float(self, sn_params):
        result = scr_sn_fatigue_life(sigma_a=20e6, **sn_params)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# allen_viv_amplitude_ratio
# A/D vs Vr curve fit (Allen 1995)
# Vr < 4.0 → A/D ~ 0.0 (no lock-in)
# 4.0 <= Vr <= 8.0 → A/D = 0.2 * (Vr - 4.0)  (linear ramp)
# Vr > 8.0 → A/D = 0.8  (saturation)
# ---------------------------------------------------------------------------

class TestAllenVivAmplitudeRatio:
    def test_below_onset_zero_amplitude(self):
        ratio = allen_viv_amplitude_ratio(vr=3.0)
        assert ratio == pytest.approx(0.0, abs=1e-9)

    def test_at_onset_zero_amplitude(self):
        ratio = allen_viv_amplitude_ratio(vr=4.0)
        assert ratio == pytest.approx(0.0, abs=1e-9)

    def test_in_lock_in_range_positive(self):
        ratio = allen_viv_amplitude_ratio(vr=6.0)
        assert ratio > 0

    def test_at_saturation_boundary(self):
        ratio = allen_viv_amplitude_ratio(vr=8.0)
        assert ratio == pytest.approx(0.8, abs=1e-9)

    def test_above_saturation_capped(self):
        ratio = allen_viv_amplitude_ratio(vr=12.0)
        assert ratio == pytest.approx(0.8, abs=1e-9)

    def test_amplitude_increases_through_lock_in(self):
        r5 = allen_viv_amplitude_ratio(vr=5.0)
        r7 = allen_viv_amplitude_ratio(vr=7.0)
        assert r7 > r5

    def test_raises_on_negative_vr(self):
        with pytest.raises(ValueError, match="vr must be non-negative"):
            allen_viv_amplitude_ratio(vr=-1.0)

    def test_returns_float(self):
        result = allen_viv_amplitude_ratio(vr=6.0)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# brooks_viv_screening
# Brooks (1987) pragmatic criterion:
#   Vr > 4.0 → potential VIV (flag True)
#   lock-in → A/D ≈ 0.9
# Returns (viv_risk: bool, a_over_d: float)
# ---------------------------------------------------------------------------

class TestBrooksVivScreening:
    def test_below_threshold_no_risk(self):
        risk, a_d = brooks_viv_screening(vr=3.5)
        assert risk is False

    def test_at_threshold_no_risk(self):
        risk, a_d = brooks_viv_screening(vr=4.0)
        assert risk is False

    def test_above_threshold_risk(self):
        risk, a_d = brooks_viv_screening(vr=5.0)
        assert risk is True

    def test_lock_in_amplitude_approx_0_9(self):
        _, a_d = brooks_viv_screening(vr=5.0)
        assert a_d == pytest.approx(0.9, rel=1e-9)

    def test_no_risk_amplitude_zero(self):
        _, a_d = brooks_viv_screening(vr=2.0)
        assert a_d == pytest.approx(0.0, abs=1e-9)

    def test_returns_tuple_bool_float(self):
        result = brooks_viv_screening(vr=5.0)
        assert isinstance(result, tuple)
        assert isinstance(result[0], bool)
        assert isinstance(result[1], float)

    def test_raises_on_negative_vr(self):
        with pytest.raises(ValueError, match="vr must be non-negative"):
            brooks_viv_screening(vr=-1.0)
