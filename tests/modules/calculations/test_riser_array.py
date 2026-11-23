import pytest
from assetutilities.calculations.riser_array import (
    equivalent_diameter,
    de_equivalencing_factor,
    hydrodynamic_shadow_factor,
    check_minimum_spacing,
)

class TestRiserArray:
    def test_equivalent_diameter_happy_path(self):
        result = equivalent_diameter(n=4, diameter=0.5)
        assert result == 1.0

    def test_equivalent_diameter_invalid_n_raises_error(self):
        with pytest.raises(ValueError, match="n must be a positive integer"):
            equivalent_diameter(n=0, diameter=0.5)

    def test_equivalent_diameter_invalid_diameter_raises_error(self):
        with pytest.raises(ValueError, match="diameter must be positive"):
            equivalent_diameter(n=4, diameter=-0.5)

    def test_de_equivalencing_factor_happy_path(self):
        result = de_equivalencing_factor(n=4)
        assert result == 0.5

    def test_de_equivalencing_factor_invalid_n_raises_error(self):
        with pytest.raises(ValueError, match="n must be a positive integer"):
            de_equivalencing_factor(n=0)

    def test_hydrodynamic_shadow_factor_happy_path(self):
        result = hydrodynamic_shadow_factor(spacing_ratio=2.0)
        assert result == pytest.approx(0.4230, rel=1e-3)

    def test_hydrodynamic_shadow_factor_large_spacing(self):
        result = hydrodynamic_shadow_factor(spacing_ratio=100.0)
        assert result == 1.0

    def test_hydrodynamic_shadow_factor_invalid_spacing_raises_error(self):
        with pytest.raises(ValueError, match="spacing_ratio must be positive"):
            hydrodynamic_shadow_factor(spacing_ratio=-1.0)

    def test_check_minimum_spacing_happy_path_is_true(self):
        result = check_minimum_spacing(centre_to_centre=2.0, diameter=0.5)
        assert result is True

    def test_check_minimum_spacing_fails_is_false(self):
        result = check_minimum_spacing(centre_to_centre=1.0, diameter=0.5)
        assert result is False

    def test_check_minimum_spacing_invalid_diameter_raises_error(self):
        with pytest.raises(ValueError, match="diameter must be positive"):
            check_minimum_spacing(centre_to_centre=2.0, diameter=-0.5)
