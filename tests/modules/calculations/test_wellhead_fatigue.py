import pytest
from assetutilities.calculations.wellhead_fatigue import (
    sn_cycles_to_failure,
    fatigue_life_years,
    annual_fatigue_damage,
    accumulate_fatigue_damage,
    sweeney_effective_stress,
    viv_wellhead_fatigue_damage,
    denison_conductor_tensioner_load,
    britton_fatigue_life_multiplier,
)

class TestWellheadFatigue:
    def test_sn_cycles_to_failure_happy_path(self):
        result = sn_cycles_to_failure(delta_sigma=100.0, A=1e12, m=3.0)
        assert result == 1e6

    def test_sn_cycles_to_failure_invalid_stress_raises_error(self):
        with pytest.raises(ValueError, match="delta_sigma must be positive"):
            sn_cycles_to_failure(delta_sigma=0.0, A=1e12, m=3.0)

    def test_fatigue_life_years_happy_path(self):
        result = fatigue_life_years(n_f=1e6, cycles_per_year=1e5)
        assert result == 10.0

    def test_fatigue_life_years_invalid_cycles_raises_error(self):
        with pytest.raises(ValueError, match="cycles_per_year must be positive"):
            fatigue_life_years(n_f=1e6, cycles_per_year=0.0)

    def test_annual_fatigue_damage_happy_path(self):
        result = annual_fatigue_damage(n_applied=1e5, n_f=1e6)
        assert result == 0.1

    def test_annual_fatigue_damage_invalid_nf_raises_error(self):
        with pytest.raises(ValueError, match="n_f must be positive"):
            annual_fatigue_damage(n_applied=1e5, n_f=-1e6)

    def test_accumulate_fatigue_damage_happy_path(self):
        result = accumulate_fatigue_damage(blocks=[(1e5, 1e6), (2e5, 2e6)])
        assert result == 0.2

    def test_sweeney_effective_stress_happy_path(self):
        result = sweeney_effective_stress(sigma_hoop=100.0, sigma_axial=50.0)
        assert result > 0.0

    def test_viv_wellhead_fatigue_damage_happy_path(self):
        result = viv_wellhead_fatigue_damage(viv_stress_range_psi=100.0, viv_frequency_hz=0.5, exposure_years=1.0, A=1e12, m=3.0)
        assert result > 0.0

    def test_viv_wellhead_fatigue_damage_zero_exposure(self):
        result = viv_wellhead_fatigue_damage(viv_stress_range_psi=100.0, viv_frequency_hz=0.5, exposure_years=0.0, A=1e12, m=3.0)
        assert result == 0.0

    def test_denison_conductor_tensioner_load_happy_path(self):
        result = denison_conductor_tensioner_load(pretension_kips=100.0, viv_amplification=1.5, hydrodynamic_load_kips=50.0)
        assert result == 175.0

    def test_britton_fatigue_life_multiplier_happy_path(self):
        result = britton_fatigue_life_multiplier(baseline_stiffness=2.0, reduced_stiffness=1.0, m=3.0)
        assert result == 8.0

    def test_britton_fatigue_life_multiplier_invalid_stiffness_raises_error(self):
        with pytest.raises(ValueError, match="reduced_stiffness must be positive"):
            britton_fatigue_life_multiplier(baseline_stiffness=2.0, reduced_stiffness=-1.0, m=3.0)
