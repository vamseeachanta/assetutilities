import pytest
from assetutilities.calculations.scr_fatigue import (
    keulegan_carpenter_number,
    soil_interaction_fatigue_factor,
    fatigue_damage_tdz,
    scr_sn_fatigue_life,
    allen_viv_amplitude_ratio,
    brooks_viv_screening,
)

class TestScrFatigue:
    def test_keulegan_carpenter_number_valid_inputs_computes_correctly(self):
        result = keulegan_carpenter_number(u_m=2.0, period=10.0, diameter=0.5)
        assert result == pytest.approx(40.0)

    def test_keulegan_carpenter_number_zero_velocity_returns_zero(self):
        result = keulegan_carpenter_number(u_m=0.0, period=10.0, diameter=0.5)
        assert result == pytest.approx(0.0)

    def test_keulegan_carpenter_number_negative_diameter_raises_value_error(self):
        with pytest.raises(ValueError, match="diameter must be positive"):
            keulegan_carpenter_number(u_m=2.0, period=10.0, diameter=-0.5)

    def test_keulegan_carpenter_number_negative_period_raises_value_error(self):
        with pytest.raises(ValueError, match="period must be positive"):
            keulegan_carpenter_number(u_m=2.0, period=-10.0, diameter=0.5)

    def test_keulegan_carpenter_number_negative_velocity_raises_value_error(self):
        with pytest.raises(ValueError, match="u_m must be non-negative"):
            keulegan_carpenter_number(u_m=-2.0, period=10.0, diameter=0.5)


    def test_soil_interaction_fatigue_factor_high_kc_returns_one(self):
        result = soil_interaction_fatigue_factor(kc=15.0)
        assert result == pytest.approx(1.0)

    def test_soil_interaction_fatigue_factor_low_kc_returns_amplified_factor(self):
        result = soil_interaction_fatigue_factor(kc=5.0)
        assert result == pytest.approx(1.125)

    def test_soil_interaction_fatigue_factor_threshold_kc_returns_one(self):
        result = soil_interaction_fatigue_factor(kc=10.0)
        assert result == pytest.approx(1.0)

    def test_soil_interaction_fatigue_factor_negative_kc_raises_value_error(self):
        with pytest.raises(ValueError, match="kc must be non-negative"):
            soil_interaction_fatigue_factor(kc=-1.0)


    def test_fatigue_damage_tdz_valid_inputs_computes_correctly(self):
        stress_ranges = [100.0, 200.0]
        cycle_counts = [1e4, 1e3]
        kc_numbers = [15.0, 5.0]
        a_param = 1e12
        m_param = 3.0
        
        result = fatigue_damage_tdz(stress_ranges, cycle_counts, kc_numbers, a_param, m_param)
        assert result == pytest.approx(0.019)

    def test_fatigue_damage_tdz_empty_lists_returns_zero(self):
        result = fatigue_damage_tdz([], [], [], 1e12, 3.0)
        assert result == 0.0

    def test_fatigue_damage_tdz_mismatched_lists_raises_value_error(self):
        with pytest.raises(ValueError, match="must have the same length"):
            fatigue_damage_tdz([100.0], [1e4, 1e3], [15.0], 1e12, 3.0)


    def test_scr_sn_fatigue_life_valid_inputs_computes_correctly(self):
        result = scr_sn_fatigue_life(sigma_a=50.0, a_param=1e12, m_param=3.0)
        assert result == pytest.approx(1e6)

    def test_scr_sn_fatigue_life_small_stress_returns_large_life(self):
        result = scr_sn_fatigue_life(sigma_a=1e-3, a_param=1e12, m_param=3.0)
        assert result > 1e12

    def test_scr_sn_fatigue_life_non_positive_stress_raises_value_error(self):
        with pytest.raises(ValueError, match="sigma_a must be positive"):
            scr_sn_fatigue_life(sigma_a=0.0, a_param=1e12, m_param=3.0)

    def test_scr_sn_fatigue_life_non_positive_a_param_raises_value_error(self):
        with pytest.raises(ValueError, match="a_param must be positive"):
            scr_sn_fatigue_life(sigma_a=50.0, a_param=-1e12, m_param=3.0)


    def test_allen_viv_amplitude_ratio_low_vr_returns_zero(self):
        result = allen_viv_amplitude_ratio(vr=3.0)
        assert result == 0.0

    def test_allen_viv_amplitude_ratio_mid_vr_returns_linear_interpolation(self):
        result = allen_viv_amplitude_ratio(vr=6.0)
        assert result == pytest.approx(0.4)

    def test_allen_viv_amplitude_ratio_high_vr_returns_max(self):
        result = allen_viv_amplitude_ratio(vr=10.0)
        assert result == pytest.approx(0.8)

    def test_allen_viv_amplitude_ratio_negative_vr_raises_value_error(self):
        with pytest.raises(ValueError, match="vr must be non-negative"):
            allen_viv_amplitude_ratio(vr=-1.0)


    def test_brooks_viv_screening_low_vr_returns_false_and_zero(self):
        viv_risk, a_over_d = brooks_viv_screening(vr=3.0)
        assert viv_risk is False
        assert a_over_d == 0.0

    def test_brooks_viv_screening_high_vr_returns_true_and_lock_in_ratio(self):
        viv_risk, a_over_d = brooks_viv_screening(vr=5.0)
        assert viv_risk is True
        assert a_over_d == pytest.approx(0.9)

    def test_brooks_viv_screening_negative_vr_raises_value_error(self):
        with pytest.raises(ValueError, match="vr must be non-negative"):
            brooks_viv_screening(vr=-1.0)
