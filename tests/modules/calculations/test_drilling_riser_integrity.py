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

class TestDrillingRiserIntegrity:
    def test_riser_effective_tension_happy_path(self):
        result = riser_effective_tension(t_top=1000.0, w_sub=10.0, z=50.0)
        assert result == 500.0

    def test_riser_effective_tension_zero_depth(self):
        result = riser_effective_tension(t_top=1000.0, w_sub=10.0, z=0.0)
        assert result == 1000.0

    def test_riser_collapse_pressure_happy_path(self):
        result = riser_collapse_pressure(E=2e11, t=0.02, D=0.5, nu=0.3)
        assert result == pytest.approx(28131868.13, rel=1e-4)

    def test_riser_collapse_pressure_zero_diameter_raises_error(self):
        with pytest.raises(ZeroDivisionError):
            riser_collapse_pressure(E=2e11, t=0.02, D=0.0, nu=0.3)

    def test_minimum_top_tension_happy_path(self):
        result = minimum_top_tension(w_sub=10.0, L=100.0, bop_weight=500.0, safety_factor=1.2)
        assert result == 1800.0

    def test_tensile_utilization_happy_path(self):
        result = tensile_utilization(t_eff=500.0, a_steel=0.1, f_y=2e8)
        assert result == 2.5e-5

    def test_tensile_utilization_zero_area_raises_error(self):
        with pytest.raises(ZeroDivisionError):
            tensile_utilization(t_eff=500.0, a_steel=0.0, f_y=2e8)

    def test_bending_moment_from_offset_happy_path(self):
        result = bending_moment_from_offset(t_eff=1000.0, delta=2.0)
        assert result == 2000.0

    def test_combined_loading_utilization_happy_path(self):
        result = combined_loading_utilization(t_eff=500.0, t_allow=1000.0, M=200.0, M_allow=1000.0)
        assert result == 0.7

    def test_annual_fatigue_damage_happy_path(self):
        sea_states = [{"n_cycles": 1000, "N_f": 10000}, {"n_cycles": 500, "N_f": 5000}]
        result = annual_fatigue_damage(sea_states)
        assert result == 0.2
        
    def test_annual_fatigue_damage_empty_list_returns_zero(self):
        result = annual_fatigue_damage([])
        assert result == 0.0
