import pytest
import math
from assetutilities.calculations.casing_pipe import (
    CasingPipeProperties,
    PipeGrade,
    CasingPipeRatings,
    burst_pressure_rating,
    collapse_pressure_rating,
    axial_tensile_yield_strength,
    wall_thickness_for_design_pressure,
    temperature_derating_factor,
    rate_casing_pipe,
)

class TestCasingPipeCalculations:
    @pytest.fixture
    def sample_pipe(self):
        return CasingPipeProperties(od_in=9.625, wall_thickness_in=0.472, grade=PipeGrade.N80)

    def test_burst_pressure_rating_happy_path(self, sample_pipe):
        # Barlow: 0.875 * 2 * 80000 * 0.472 / 9.625 = 6865.4545
        result = burst_pressure_rating(sample_pipe)
        assert result == pytest.approx(6865.4545, rel=1e-4)

    def test_burst_pressure_rating_zero_thickness_returns_zero(self):
        pipe = CasingPipeProperties(od_in=9.625, wall_thickness_in=0.0, grade=PipeGrade.N80)
        result = burst_pressure_rating(pipe)
        assert result == 0.0

    def test_burst_pressure_rating_zero_od_raises_zero_division(self):
        pipe = CasingPipeProperties(od_in=0.0, wall_thickness_in=0.472, grade=PipeGrade.N80)
        with pytest.raises(ZeroDivisionError):
            burst_pressure_rating(pipe)

    def test_axial_tensile_yield_strength_happy_path(self, sample_pipe):
        # Area = pi/4 * (OD^2 - ID^2) = pi/4 * (9.625^2 - 8.681^2) = 13.57 in2
        # Yield force = 80000 * 13.57 = 1085600 lbf
        result = axial_tensile_yield_strength(sample_pipe)
        assert result == pytest.approx(1085788.71, rel=1e-3)

    def test_collapse_pressure_rating_happy_path(self, sample_pipe):
        # N80, D/t = 20.39 falls into Transitional or Plastic regime
        result = collapse_pressure_rating(sample_pipe)
        assert result > 0.0

    def test_wall_thickness_for_design_pressure_happy_path(self):
        result = wall_thickness_for_design_pressure(od_in=9.625, design_pressure_psi=6865.0, grade=PipeGrade.N80)
        assert result == pytest.approx(0.472, rel=1e-3)

    def test_temperature_derating_factor_ambient_returns_one(self):
        assert temperature_derating_factor(70.0) == 1.0
        assert temperature_derating_factor(200.0) == 1.0

    def test_temperature_derating_factor_elevated_linearly_interpolates(self):
        assert temperature_derating_factor(300.0) == pytest.approx(0.97)

    def test_temperature_derating_factor_extreme_capped_at_minimum(self):
        assert temperature_derating_factor(5000.0) == 0.01

    def test_rate_casing_pipe_happy_path_applies_derating(self, sample_pipe):
        ratings = rate_casing_pipe(sample_pipe, temperature_f=300.0)
        assert isinstance(ratings, CasingPipeRatings)
        assert ratings.temperature_f == 300.0
        assert ratings.derating_factor == pytest.approx(0.97)
        assert ratings.burst_psi == pytest.approx(6865.4545 * 0.97, rel=1e-4)
