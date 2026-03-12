import pytest
from assetutilities.calculations.riser_viv import (
    drag_coefficient_smooth_cylinder,
    drag_coefficient_bundle,
    strouhal_frequency,
    reduced_velocity,
    viv_lock_in,
    viv_amplitude_response,
    viv_fatigue_damage,
    effective_tension,
    riser_natural_frequency,
)

class TestRiserViv:
    def test_drag_coefficient_smooth_cylinder_subcritical(self):
        assert drag_coefficient_smooth_cylinder(Re=1e5) == 1.2

    def test_drag_coefficient_smooth_cylinder_supercritical(self):
        assert drag_coefficient_smooth_cylinder(Re=1e7) == 0.6

    def test_drag_coefficient_smooth_cylinder_invalid_re_raises_error(self):
        with pytest.raises(ValueError, match="Reynolds number must be positive"):
            drag_coefficient_smooth_cylinder(Re=-1e5)

    def test_drag_coefficient_bundle_single_riser(self):
        assert drag_coefficient_bundle(Re=1e5, n_risers=1, pitch_diameter_ratio=2.0) == 1.2

    def test_drag_coefficient_bundle_multiple_risers(self):
        result = drag_coefficient_bundle(Re=1e5, n_risers=3, pitch_diameter_ratio=2.0)
        assert result == pytest.approx(1.8)

    def test_drag_coefficient_bundle_invalid_risers_raises_error(self):
        with pytest.raises(ValueError, match="n_risers must be >= 1"):
            drag_coefficient_bundle(Re=1e5, n_risers=0, pitch_diameter_ratio=2.0)

    def test_strouhal_frequency_happy_path(self):
        assert strouhal_frequency(U=2.0, D=0.5) == 0.8

    def test_strouhal_frequency_invalid_diameter_raises_error(self):
        with pytest.raises(ValueError, match="Diameter must be positive"):
            strouhal_frequency(U=2.0, D=0.0)

    def test_reduced_velocity_happy_path(self):
        assert reduced_velocity(U=2.0, f_n=0.5, D=0.5) == 8.0

    def test_reduced_velocity_invalid_frequency_raises_error(self):
        with pytest.raises(ValueError, match="Natural frequency must be positive"):
            reduced_velocity(U=2.0, f_n=0.0, D=0.5)

    def test_viv_lock_in_inside_range(self):
        assert viv_lock_in(Vr=5.0) is True

    def test_viv_lock_in_outside_range(self):
        assert viv_lock_in(Vr=3.0) is False

    def test_viv_amplitude_response_inside_lock_in(self):
        result = viv_amplitude_response(Vr=6.0, Ks=0.1)
        assert result > 0.0

    def test_viv_amplitude_response_outside_lock_in(self):
        result = viv_amplitude_response(Vr=3.0, Ks=0.1)
        assert result == 0.0

    def test_viv_fatigue_damage_happy_path(self):
        result = viv_fatigue_damage(stress_ranges=[1e6, 2e6], cycle_counts=[100, 50])
        assert result > 0.0

    def test_viv_fatigue_damage_mismatched_lengths_raises_error(self):
        with pytest.raises(ValueError, match="must equal cycle_counts length"):
            viv_fatigue_damage(stress_ranges=[1e6], cycle_counts=[100, 50, 10])

    def test_effective_tension_happy_path(self):
        result = effective_tension(T_wall=1e6, pi=1e7, pe=2e7, D=0.5, t=0.02)
        assert result > 0.0

    def test_riser_natural_frequency_happy_path(self):
        result = riser_natural_frequency(n=1, L=100.0, EI=1e8, m=200.0)
        assert result > 0.0

    def test_riser_natural_frequency_invalid_mode_raises_error(self):
        with pytest.raises(ValueError, match="Mode number n must be >= 1"):
            riser_natural_frequency(n=0, L=100.0, EI=1e8, m=200.0)
