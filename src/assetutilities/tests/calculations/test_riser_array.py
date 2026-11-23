# ABOUTME: Tests for riser array design calculations (BP Riser Array Guidelines v2).
# ABOUTME: Covers equivalent diameter, de-equivalencing, shadow factor, and spacing checks.

import math
import pytest

from assetutilities.calculations.riser_array import (
    equivalent_diameter,
    de_equivalencing_factor,
    hydrodynamic_shadow_factor,
    check_minimum_spacing,
)


class TestEquivalentDiameter:
    """Tests for D_eq = sqrt(n * D^2) = D * sqrt(n)."""

    def test_single_riser_returns_original_diameter(self):
        d_eq = equivalent_diameter(n=1, diameter=0.3)
        assert d_eq == pytest.approx(0.3)

    def test_four_risers_doubles_diameter(self):
        # sqrt(4) == 2, so D_eq = 2 * D
        d_eq = equivalent_diameter(n=4, diameter=0.3)
        assert d_eq == pytest.approx(0.6)

    def test_nine_risers_triples_diameter(self):
        d_eq = equivalent_diameter(n=9, diameter=0.25)
        assert d_eq == pytest.approx(0.75)

    def test_formula_is_d_times_sqrt_n(self):
        n, d = 7, 0.508
        d_eq = equivalent_diameter(n=n, diameter=d)
        assert d_eq == pytest.approx(d * math.sqrt(n))

    def test_raises_on_zero_risers(self):
        with pytest.raises(ValueError, match="n must be a positive integer"):
            equivalent_diameter(n=0, diameter=0.3)

    def test_raises_on_negative_diameter(self):
        with pytest.raises(ValueError, match="diameter must be positive"):
            equivalent_diameter(n=4, diameter=-0.3)

    def test_raises_on_zero_diameter(self):
        with pytest.raises(ValueError, match="diameter must be positive"):
            equivalent_diameter(n=4, diameter=0.0)


class TestDeEquivalencingFactor:
    """Tests for load de-equivalencing from array to individual riser."""

    def test_single_riser_factor_is_one(self):
        factor = de_equivalencing_factor(n=1)
        assert factor == pytest.approx(1.0)

    def test_four_risers_factor_is_half(self):
        # Factor = 1/sqrt(n): each riser carries 1/sqrt(n) of equivalent load
        factor = de_equivalencing_factor(n=4)
        assert factor == pytest.approx(0.5)

    def test_nine_risers_factor_is_one_third(self):
        factor = de_equivalencing_factor(n=9)
        assert factor == pytest.approx(1.0 / 3.0)

    def test_factor_equals_one_over_sqrt_n(self):
        for n in [2, 5, 10, 16]:
            factor = de_equivalencing_factor(n=n)
            assert factor == pytest.approx(1.0 / math.sqrt(n))

    def test_raises_on_non_positive_n(self):
        with pytest.raises(ValueError, match="n must be a positive integer"):
            de_equivalencing_factor(n=0)


class TestHydrodynamicShadowFactor:
    """Tests for the shadow factor between parallel risers in current."""

    def test_large_spacing_gives_no_shielding(self):
        # At spacing >= 10D the downstream riser is essentially unshielded
        shadow = hydrodynamic_shadow_factor(spacing_ratio=10.0)
        assert shadow == pytest.approx(1.0, abs=0.05)

    def test_minimum_spacing_three_diameters_has_shielding(self):
        # At 3D spacing there should be meaningful shielding (factor < 1)
        shadow = hydrodynamic_shadow_factor(spacing_ratio=3.0)
        assert shadow < 1.0

    def test_shadow_factor_bounded_zero_to_one(self):
        for sr in [1.5, 2.0, 3.0, 4.0, 6.0, 8.0]:
            shadow = hydrodynamic_shadow_factor(spacing_ratio=sr)
            assert 0.0 <= shadow <= 1.0

    def test_shadow_factor_increases_with_spacing(self):
        # More spacing → less shielding → larger factor
        s_close = hydrodynamic_shadow_factor(spacing_ratio=2.0)
        s_far = hydrodynamic_shadow_factor(spacing_ratio=6.0)
        assert s_far > s_close

    def test_raises_on_non_positive_spacing_ratio(self):
        with pytest.raises(ValueError, match="spacing_ratio must be positive"):
            hydrodynamic_shadow_factor(spacing_ratio=0.0)


class TestCheckMinimumSpacing:
    """Tests for the minimum centre-to-centre spacing requirement (>3D)."""

    def test_spacing_above_3d_passes(self):
        result = check_minimum_spacing(centre_to_centre=1.0, diameter=0.3)
        assert result is True

    def test_spacing_exactly_3d_fails(self):
        # 3D is the minimum: exactly 3D is not above threshold, so fails.
        # Use diameter=1.0 to avoid floating point ambiguity in 3*D.
        result = check_minimum_spacing(centre_to_centre=3.0, diameter=1.0)
        assert result is False

    def test_spacing_below_3d_fails(self):
        result = check_minimum_spacing(centre_to_centre=0.6, diameter=0.3)
        assert result is False

    def test_custom_multiplier_respected(self):
        # Using a 4D requirement
        result_fail = check_minimum_spacing(
            centre_to_centre=1.0, diameter=0.3, min_multiplier=4.0
        )
        result_pass = check_minimum_spacing(
            centre_to_centre=1.3, diameter=0.3, min_multiplier=4.0
        )
        assert result_fail is False
        assert result_pass is True

    def test_raises_on_non_positive_diameter(self):
        with pytest.raises(ValueError, match="diameter must be positive"):
            check_minimum_spacing(centre_to_centre=1.0, diameter=0.0)

    def test_raises_on_non_positive_spacing(self):
        with pytest.raises(ValueError, match="centre_to_centre must be positive"):
            check_minimum_spacing(centre_to_centre=0.0, diameter=0.3)
