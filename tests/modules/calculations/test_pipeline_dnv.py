import pytest
from assetutilities.calculations.pipeline_dnv import (
    burst_pressure_capacity,
    pressure_containment_check,
    local_buckling_combined_loading,
    von_mises_equivalent_stress,
    buckle_arrest_capacity,
)

class TestPipelineDnv:
    def test_burst_pressure_capacity_happy_path(self):
        result = burst_pressure_capacity(D=0.5, t=0.02, f_y=450e6, f_u=535e6)
        assert result > 0.0

    def test_burst_pressure_capacity_zero_diameter_raises_error(self):
        with pytest.raises(ZeroDivisionError):
            burst_pressure_capacity(D=0.0, t=0.02, f_y=450e6, f_u=535e6)

    def test_pressure_containment_check_happy_path(self):
        result = pressure_containment_check(P_li=1e7, D=0.5, t=0.02, f_y=450e6, f_u=535e6)
        assert result > 0.0

    def test_pressure_containment_check_zero_capacity_raises_error(self):
        with pytest.raises(ZeroDivisionError):
            pressure_containment_check(P_li=1e7, D=0.5, t=0.0, f_y=450e6, f_u=535e6)

    def test_local_buckling_combined_loading_happy_path(self):
        result = local_buckling_combined_loading(D=0.5, t=0.02, f_y=450e6, M=1e5, S=1e6, delta_p=1e6)
        assert result > 0.0

    def test_von_mises_equivalent_stress_happy_path(self):
        result = von_mises_equivalent_stress(sigma_l=100.0, sigma_h=50.0, tau=25.0)
        assert result == pytest.approx(96.82, rel=1e-3)

    def test_buckle_arrest_capacity_happy_path(self):
        result = buckle_arrest_capacity(D=0.5, t=0.02, f_y=450e6)
        assert result > 0.0

    def test_buckle_arrest_capacity_zero_diameter_raises_error(self):
        with pytest.raises(ZeroDivisionError):
            buckle_arrest_capacity(D=0.0, t=0.02, f_y=450e6)
