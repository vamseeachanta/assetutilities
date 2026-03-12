import pytest
from assetutilities.calculations.riser_dynamics import (
    tow_out_catenary_tension,
    hydrodynamic_damping_ratio,
    viv_fatigue_correction_factor,
    norton_drag_coefficient,
    vandiver_added_mass_coefficient,
    smith_residual_collapse_factor,
    crossflow_psd_amplitude,
)

class TestRiserDynamics:
    def test_tow_out_catenary_tension_happy_path(self):
        result = tow_out_catenary_tension(submerged_weight=1000.0, water_depth=100.0, angle_from_horizontal_deg=45.0)
        assert result == pytest.approx(100000.0)

    def test_tow_out_catenary_tension_vertical_angle_returns_zero(self):
        result = tow_out_catenary_tension(submerged_weight=1000.0, water_depth=100.0, angle_from_horizontal_deg=90.0)
        # Check that it returns approximately zero 
        assert result == pytest.approx(0.0, abs=1e-5)

    def test_tow_out_catenary_tension_invalid_angle_raises_error(self):
        with pytest.raises(ValueError, match="angle_from_horizontal_deg must be in range"):
            tow_out_catenary_tension(submerged_weight=1000.0, water_depth=100.0, angle_from_horizontal_deg=0.0)

    def test_hydrodynamic_damping_ratio_happy_path(self):
        result = hydrodynamic_damping_ratio(drag_coefficient=1.2, fluid_density=1025.0, diameter=0.5, current_velocity=1.0, mass_per_unit_length=200.0, natural_frequency=0.5)
        assert result > 0.0

    def test_hydrodynamic_damping_ratio_invalid_mass_raises_error(self):
        with pytest.raises(ValueError, match="mass_per_unit_length must be positive"):
            hydrodynamic_damping_ratio(drag_coefficient=1.2, fluid_density=1025.0, diameter=0.5, current_velocity=1.0, mass_per_unit_length=0.0, natural_frequency=0.5)

    def test_viv_fatigue_correction_factor_happy_path(self):
        result = viv_fatigue_correction_factor(correlation_length=10.0, span_length=20.0)
        assert result == 0.5

    def test_viv_fatigue_correction_factor_long_correlation_capped(self):
        result = viv_fatigue_correction_factor(correlation_length=30.0, span_length=20.0)
        assert result == 1.0

    def test_viv_fatigue_correction_factor_invalid_length_raises_error(self):
        with pytest.raises(ValueError, match="correlation_length must be positive"):
            viv_fatigue_correction_factor(correlation_length=-10.0, span_length=20.0)

    def test_norton_drag_coefficient_happy_path(self):
        assert norton_drag_coefficient(reynolds_number=1e5) == 1.2
        assert norton_drag_coefficient(reynolds_number=6e5) == 0.5

    def test_norton_drag_coefficient_invalid_re_raises_error(self):
        with pytest.raises(ValueError, match="reynolds_number must be positive"):
            norton_drag_coefficient(reynolds_number=-1e5)

    def test_vandiver_added_mass_coefficient_happy_path(self):
        assert vandiver_added_mass_coefficient() == 1.0

    def test_smith_residual_collapse_factor_happy_path(self):
        assert smith_residual_collapse_factor(ovality=0.1) == 0.8
        assert smith_residual_collapse_factor(ovality=0.6) == 0.0

    def test_smith_residual_collapse_factor_invalid_ovality_raises_error(self):
        with pytest.raises(ValueError, match="ovality must be non-negative"):
            smith_residual_collapse_factor(ovality=-0.1)

    def test_crossflow_psd_amplitude_happy_path(self):
        result = crossflow_psd_amplitude(lift_coefficient=0.5, fluid_density=1025.0, diameter=0.5, current_velocity=1.0, total_mass_per_unit_length=500.0, natural_frequency=0.5)
        assert result > 0.0

    def test_crossflow_psd_amplitude_invalid_frequency_raises_error(self):
        with pytest.raises(ValueError, match="natural_frequency must be positive"):
            crossflow_psd_amplitude(lift_coefficient=0.5, fluid_density=1025.0, diameter=0.5, current_velocity=1.0, total_mass_per_unit_length=500.0, natural_frequency=0.0)
