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

class TestDrillingRiser:
    def test_gardner_bottom_tension_happy_path(self):
        result = gardner_bottom_tension(w_air_lbf_per_ft=100.0, w_buoyancy_lbf_per_ft=40.0, length_ft=1000.0, bop_weight_lbf=10000.0)
        assert result == 50000.0

    def test_gardner_top_tension_happy_path(self):
        result = gardner_top_tension(bottom_tension_lbf=50000.0, segment_weights_lbf=[10000.0, 20000.0])
        assert result == 80000.0

    def test_kim_natural_frequency_with_pressure_happy_path(self):
        result = kim_natural_frequency_with_pressure(
            fn_vacuum_hz=0.5, internal_pressure_psi=1000.0, external_pressure_psi=2000.0,
            pipe_cross_section_in2=10.0, riser_length_ft=1000.0, riser_weight_lbf=100000.0
        )
        assert result > 0.5

    def test_kim_natural_frequency_zero_weight_returns_vacuum_freq(self):
        result = kim_natural_frequency_with_pressure(
            fn_vacuum_hz=0.5, internal_pressure_psi=1000.0, external_pressure_psi=2000.0,
            pipe_cross_section_in2=10.0, riser_length_ft=1000.0, riser_weight_lbf=0.0
        )
        assert result == 0.5

    def test_grant_faired_drag_coefficient_happy_path(self):
        result = grant_faired_drag_coefficient(cd_bare=1.2, reduction_factor=0.7)
        assert result == pytest.approx(0.84)

    def test_grant_faired_drag_coefficient_invalid_cd_raises_error(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            grant_faired_drag_coefficient(cd_bare=-1.0)

    def test_jacobsen_suppression_damage_ratio_happy_path(self):
        result = jacobsen_suppression_damage_ratio(unsuppressed_damage=0.5, suppression_effectiveness=0.8)
        assert result == pytest.approx(0.1)

    def test_dsouza_flex_riser_effective_weight_happy_path(self):
        result = dsouza_flex_riser_effective_weight(weight_in_air_lbf_per_ft=100.0, displaced_fluid_weight_lbf_per_ft=40.0)
        assert result == 60.0

    def test_vandiver_lock_in_velocity_happy_path(self):
        result = vandiver_lock_in_velocity(natural_frequency_hz=0.2, diameter_ft=2.0, strouhal_number=0.2)
        assert result == 2.0

    def test_vandiver_lock_in_velocity_invalid_strouhal_raises_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            vandiver_lock_in_velocity(natural_frequency_hz=0.2, diameter_ft=2.0, strouhal_number=0.0)

    def test_miller_mud_column_pressure_happy_path(self):
        result = miller_mud_column_pressure(mud_weight_ppg=10.0, depth_ft=1000.0)
        assert result == pytest.approx(520.0)

    def test_miller_mud_column_pressure_negative_depth_raises_error(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            miller_mud_column_pressure(mud_weight_ppg=10.0, depth_ft=-1000.0)

    def test_imas_scr_response_amplification_happy_path(self):
        result = imas_scr_response_amplification(current_velocity=2.0, A=1.5, B=2.0)
        assert result == 6.0

    def test_berner_riser_effective_tension_happy_path(self):
        result = berner_riser_effective_tension(
            top_tension_lbf=100000.0, submerged_weight_lbf_per_ft=50.0,
            riser_length_ft=1000.0, vessel_offset_tension_delta_lbf=5000.0
        )
        assert result == 55000.0
