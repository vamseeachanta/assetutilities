import pytest
from assetutilities.calculations.tlp_well_system import (
    tendon_effective_tension,
    riser_tensioner_stroke,
    wellhead_fatigue_accumulation,
    riser_interference_check,
    critical_damping_ratio,
    platform_set_down,
)

class TestTlpWellSystem:
    def test_tendon_effective_tension_happy_path(self):
        result = tendon_effective_tension(t_pretension=1e6, delta_t_hull=1e5)
        assert result == 9e5

    def test_tendon_effective_tension_non_positive_raises_error(self):
        with pytest.raises(ValueError, match="effective tension must be positive"):
            tendon_effective_tension(t_pretension=1e5, delta_t_hull=1e6)

    def test_riser_tensioner_stroke_happy_path(self):
        result = riser_tensioner_stroke(length=100.0, delta_vert=2.0, delta_horiz=10.0)
        assert result > 0.0

    def test_riser_tensioner_stroke_invalid_length_raises_error(self):
        with pytest.raises(ValueError, match="length must be positive"):
            riser_tensioner_stroke(length=0.0, delta_vert=2.0, delta_horiz=10.0)

    def test_wellhead_fatigue_accumulation_happy_path(self):
        result = wellhead_fatigue_accumulation(stress_ranges=[1e6], annual_cycles=[100], service_years=20, a_param=1e12, m_param=3.0)
        assert result > 0.0

    def test_wellhead_fatigue_accumulation_mismatched_lists_raises_error(self):
        with pytest.raises(ValueError, match="must have the same length"):
            wellhead_fatigue_accumulation(stress_ranges=[1e6], annual_cycles=[100, 200], service_years=20, a_param=1e12, m_param=3.0)

    def test_riser_interference_check_clear(self):
        is_clear, gap = riser_interference_check(tensioned_riser_od=0.5, drilling_riser_od=0.6, centre_to_centre=2.0)
        assert is_clear is True
        assert gap == 1.45

    def test_riser_interference_check_invalid_od_raises_error(self):
        with pytest.raises(ValueError, match="outer diameter must be positive"):
            riser_interference_check(tensioned_riser_od=-0.5, drilling_riser_od=0.6, centre_to_centre=2.0)

    def test_critical_damping_ratio_happy_path(self):
        result = critical_damping_ratio(C=100.0, K=1000.0, M=10.0)
        assert result == 0.5

    def test_critical_damping_ratio_invalid_mass_raises_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            critical_damping_ratio(C=100.0, K=1000.0, M=0.0)

    def test_platform_set_down_happy_path(self):
        result = platform_set_down(length=1000.0, delta_horiz=100.0)
        assert result > 0.0

    def test_platform_set_down_invalid_offset_raises_error(self):
        with pytest.raises(ValueError, match="must be less than length"):
            platform_set_down(length=100.0, delta_horiz=100.0)
