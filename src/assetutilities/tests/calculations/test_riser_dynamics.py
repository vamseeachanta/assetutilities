# ABOUTME: Tests for riser dynamics calculations (WRK-439 through WRK-445).
# ABOUTME: Covers tow-out tension, hydrodynamic damping, VIV correction,
# ABOUTME: Norton wind drag, Vandiver added mass, Smith residual strength,
# ABOUTME: and cross-flow PSD amplitude.

import math
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


class TestTowOutCatenaryTension:
    """Tests for catenary horizontal tension during riser tow-out.

    Formula: T_H = w * L_h where L_h is derived from catenary geometry.
    Equivalently for a catenary: T_H = w / (1 - cos(theta)) * sin(theta)
    or in the standard form: T_H = w * s / tan(theta) ... but the canonical
    catenary horizontal tension for a given submerged weight per unit length
    w (N/m) and lay angle theta (rad) at the touchdown is:
        T_H = w * R  where R is the radius of curvature at TDP
    The simplest direct formulation used here:
        T_H = w * L_suspended * cos(theta)
    The task specification gives: T_H = catenary horizontal force for given
    submerged weight (w N/m) and angle (theta degrees from vertical).
    Standard catenary: T_H = T * sin(theta) and T_V = T * cos(theta),
    with T_V = w * L (arc length component).
    For a free-hanging catenary hanging from a vessel:
        Angle from horizontal at top = alpha  (degrees)
        T_H = T * cos(alpha)
        T_V = T * sin(alpha) = w * L_vert / sin(alpha)  [for simple case]
    The simplest engineering approximation used in tow-out:
        T_H = submerged_weight_per_unit_length * water_depth / tan(angle_from_horizontal)
    where angle_from_horizontal (degrees) is the riser angle at the vessel connection.
    """

    def test_vertical_hang_gives_zero_horizontal_tension(self):
        # At 90 degrees from horizontal (vertical hang), no horizontal component
        T_H = tow_out_catenary_tension(
            submerged_weight=500.0,
            water_depth=100.0,
            angle_from_horizontal_deg=90.0,
        )
        assert T_H == pytest.approx(0.0, abs=1.0)

    def test_shallow_angle_gives_large_horizontal_tension(self):
        # At 10 degrees from horizontal the catenary is nearly horizontal
        T_H_shallow = tow_out_catenary_tension(
            submerged_weight=500.0,
            water_depth=100.0,
            angle_from_horizontal_deg=10.0,
        )
        T_H_steep = tow_out_catenary_tension(
            submerged_weight=500.0,
            water_depth=100.0,
            angle_from_horizontal_deg=45.0,
        )
        assert T_H_shallow > T_H_steep

    def test_known_value_at_45_degrees(self):
        # T_H = w * d / tan(45) = w * d
        w, d = 300.0, 200.0
        T_H = tow_out_catenary_tension(
            submerged_weight=w,
            water_depth=d,
            angle_from_horizontal_deg=45.0,
        )
        assert T_H == pytest.approx(w * d, rel=1e-6)

    def test_known_value_at_30_degrees(self):
        # T_H = w * d / tan(30) = w * d * sqrt(3)
        w, d = 400.0, 150.0
        T_H = tow_out_catenary_tension(
            submerged_weight=w,
            water_depth=d,
            angle_from_horizontal_deg=30.0,
        )
        expected = w * d / math.tan(math.radians(30.0))
        assert T_H == pytest.approx(expected, rel=1e-6)

    def test_raises_on_non_positive_weight(self):
        with pytest.raises(ValueError, match="submerged_weight must be positive"):
            tow_out_catenary_tension(
                submerged_weight=0.0,
                water_depth=100.0,
                angle_from_horizontal_deg=45.0,
            )

    def test_raises_on_non_positive_depth(self):
        with pytest.raises(ValueError, match="water_depth must be positive"):
            tow_out_catenary_tension(
                submerged_weight=500.0,
                water_depth=0.0,
                angle_from_horizontal_deg=45.0,
            )

    def test_raises_on_angle_out_of_range(self):
        with pytest.raises(ValueError, match="angle_from_horizontal_deg must be"):
            tow_out_catenary_tension(
                submerged_weight=500.0,
                water_depth=100.0,
                angle_from_horizontal_deg=0.0,
            )


class TestHydrodynamicDampingRatio:
    """Tests for Vandiver hydrodynamic damping ratio.

    Formula: zeta_h = C_d * rho * D * U / (4 * pi * m * f_n)
    """

    def test_formula_returns_correct_value(self):
        C_d = 1.2
        rho = 1025.0
        D = 0.5
        U = 1.0
        m = 200.0
        f_n = 0.5
        expected = C_d * rho * D * U / (4.0 * math.pi * m * f_n)
        result = hydrodynamic_damping_ratio(
            drag_coefficient=C_d,
            fluid_density=rho,
            diameter=D,
            current_velocity=U,
            mass_per_unit_length=m,
            natural_frequency=f_n,
        )
        assert result == pytest.approx(expected, rel=1e-9)

    def test_higher_velocity_gives_higher_damping(self):
        kwargs = dict(
            drag_coefficient=1.2,
            fluid_density=1025.0,
            diameter=0.5,
            mass_per_unit_length=200.0,
            natural_frequency=0.5,
        )
        zeta_low = hydrodynamic_damping_ratio(current_velocity=0.5, **kwargs)
        zeta_high = hydrodynamic_damping_ratio(current_velocity=2.0, **kwargs)
        assert zeta_high > zeta_low

    def test_higher_frequency_gives_lower_damping(self):
        kwargs = dict(
            drag_coefficient=1.2,
            fluid_density=1025.0,
            diameter=0.5,
            mass_per_unit_length=200.0,
            current_velocity=1.0,
        )
        zeta_low_fn = hydrodynamic_damping_ratio(natural_frequency=0.2, **kwargs)
        zeta_high_fn = hydrodynamic_damping_ratio(natural_frequency=2.0, **kwargs)
        assert zeta_low_fn > zeta_high_fn

    def test_result_is_positive(self):
        result = hydrodynamic_damping_ratio(
            drag_coefficient=1.0,
            fluid_density=1025.0,
            diameter=0.4,
            current_velocity=0.8,
            mass_per_unit_length=150.0,
            natural_frequency=0.3,
        )
        assert result > 0.0

    def test_raises_on_non_positive_mass(self):
        with pytest.raises(ValueError, match="mass_per_unit_length must be positive"):
            hydrodynamic_damping_ratio(
                drag_coefficient=1.0,
                fluid_density=1025.0,
                diameter=0.4,
                current_velocity=0.8,
                mass_per_unit_length=0.0,
                natural_frequency=0.3,
            )

    def test_raises_on_non_positive_frequency(self):
        with pytest.raises(ValueError, match="natural_frequency must be positive"):
            hydrodynamic_damping_ratio(
                drag_coefficient=1.0,
                fluid_density=1025.0,
                diameter=0.4,
                current_velocity=0.8,
                mass_per_unit_length=150.0,
                natural_frequency=0.0,
            )


class TestVivFatigueCorrectionFactor:
    """Tests for Huse VIV fatigue correction for short correlation length.

    The Huse correction reduces VIV fatigue damage for short correlation
    lengths. The correction factor eta is:
        eta = L_c / L  when L_c < L  (partial correlation)
        eta = 1.0      when L_c >= L (full correlation)
    where L_c is the correlation length and L is the riser span.
    """

    def test_full_correlation_gives_factor_one(self):
        eta = viv_fatigue_correction_factor(
            correlation_length=200.0, span_length=100.0
        )
        assert eta == pytest.approx(1.0)

    def test_half_correlation_gives_factor_half(self):
        eta = viv_fatigue_correction_factor(
            correlation_length=50.0, span_length=100.0
        )
        assert eta == pytest.approx(0.5)

    def test_factor_bounded_zero_to_one(self):
        for lc in [10.0, 50.0, 100.0, 200.0]:
            eta = viv_fatigue_correction_factor(
                correlation_length=lc, span_length=100.0
            )
            assert 0.0 < eta <= 1.0

    def test_longer_span_gives_smaller_factor(self):
        eta_short = viv_fatigue_correction_factor(
            correlation_length=30.0, span_length=50.0
        )
        eta_long = viv_fatigue_correction_factor(
            correlation_length=30.0, span_length=200.0
        )
        assert eta_long < eta_short

    def test_raises_on_non_positive_lengths(self):
        with pytest.raises(ValueError, match="correlation_length must be positive"):
            viv_fatigue_correction_factor(
                correlation_length=0.0, span_length=100.0
            )
        with pytest.raises(ValueError, match="span_length must be positive"):
            viv_fatigue_correction_factor(
                correlation_length=30.0, span_length=0.0
            )


class TestNortonDragCoefficient:
    """Tests for Norton wind tunnel drag coefficient correlation.

    Norton (1981) provides C_d as a function of Reynolds number for
    inclined cylinders in wind tunnel tests.
    Typical values: C_d ~= 1.2 for Re < 2e5, C_d ~= 0.6 for Re > 5e5.
    """

    def test_low_reynolds_gives_high_cd(self):
        cd = norton_drag_coefficient(reynolds_number=1e4)
        assert cd >= 0.8

    def test_high_reynolds_gives_lower_cd(self):
        cd_low_re = norton_drag_coefficient(reynolds_number=1e4)
        cd_high_re = norton_drag_coefficient(reynolds_number=1e6)
        assert cd_high_re < cd_low_re

    def test_subcritical_cd_in_expected_range(self):
        cd = norton_drag_coefficient(reynolds_number=1e5)
        assert 0.8 <= cd <= 1.4

    def test_supercritical_cd_in_expected_range(self):
        cd = norton_drag_coefficient(reynolds_number=1e6)
        assert 0.3 <= cd <= 0.8

    def test_result_is_positive(self):
        for re in [1e3, 1e4, 1e5, 5e5, 1e6, 1e7]:
            assert norton_drag_coefficient(reynolds_number=re) > 0.0

    def test_raises_on_non_positive_re(self):
        with pytest.raises(ValueError, match="reynolds_number must be positive"):
            norton_drag_coefficient(reynolds_number=0.0)


class TestVandiverAddedMassCoefficient:
    """Tests for Vandiver added mass coefficient.

    For circular cylinders in oscillatory flow, Ca = 1.0 (Vandiver 1987).
    The function may accept shape or KC number arguments.
    """

    def test_circular_cylinder_returns_one(self):
        ca = vandiver_added_mass_coefficient()
        assert ca == pytest.approx(1.0)

    def test_returns_float(self):
        ca = vandiver_added_mass_coefficient()
        assert isinstance(ca, float)

    def test_explicit_circular_shape_returns_one(self):
        ca = vandiver_added_mass_coefficient(shape="circular")
        assert ca == pytest.approx(1.0)

    def test_kc_number_does_not_change_value_for_circular(self):
        ca_low = vandiver_added_mass_coefficient(kc_number=2.0)
        ca_high = vandiver_added_mass_coefficient(kc_number=20.0)
        assert ca_low == pytest.approx(1.0)
        assert ca_high == pytest.approx(1.0)


class TestSmithResidualCollapseFactor:
    """Tests for Smith (1981) residual strength after local buckling.

    Smith provides a reduction factor eta_r on the collapse pressure:
        P_residual = eta_r * P_collapse_intact
    The factor depends on the normalised buckle amplitude d/D (ovality).
        eta_r = 1 - k * (d/D)
    where k is an empirical constant (~2.0 from Smith's experiments).
    """

    def test_zero_ovality_gives_factor_one(self):
        eta = smith_residual_collapse_factor(ovality=0.0)
        assert eta == pytest.approx(1.0)

    def test_ovality_reduces_factor(self):
        eta = smith_residual_collapse_factor(ovality=0.1)
        assert eta < 1.0

    def test_factor_is_bounded_zero_to_one(self):
        for ov in [0.0, 0.05, 0.1, 0.2, 0.3]:
            eta = smith_residual_collapse_factor(ovality=ov)
            assert 0.0 <= eta <= 1.0

    def test_higher_ovality_gives_lower_factor(self):
        eta_small = smith_residual_collapse_factor(ovality=0.05)
        eta_large = smith_residual_collapse_factor(ovality=0.25)
        assert eta_large < eta_small

    def test_known_value_with_default_k(self):
        # With k=2.0: eta = 1 - 2*0.1 = 0.8
        eta = smith_residual_collapse_factor(ovality=0.1, k=2.0)
        assert eta == pytest.approx(0.8)

    def test_raises_on_negative_ovality(self):
        with pytest.raises(ValueError, match="ovality must be non-negative"):
            smith_residual_collapse_factor(ovality=-0.1)


class TestCrossflowPsdAmplitude:
    """Tests for cross-flow response amplitude via power spectral density.

    The PSD-based cross-flow amplitude A_rms is:
        A_rms = C_L * rho * D * U^2 / (2 * m_total * omega_n)
    where m_total = m + Ca * rho_f * pi * D^2 / 4  (total mass including added)
    and omega_n = 2 * pi * f_n.

    Simplified form:
        A_rms = (C_L * rho_f * D * U^2) / (2 * m_total * 2 * pi * f_n)
    """

    def test_result_is_positive(self):
        amp = crossflow_psd_amplitude(
            lift_coefficient=0.3,
            fluid_density=1025.0,
            diameter=0.5,
            current_velocity=1.5,
            total_mass_per_unit_length=250.0,
            natural_frequency=0.4,
        )
        assert amp > 0.0

    def test_higher_velocity_gives_larger_amplitude(self):
        kwargs = dict(
            lift_coefficient=0.3,
            fluid_density=1025.0,
            diameter=0.5,
            total_mass_per_unit_length=250.0,
            natural_frequency=0.4,
        )
        amp_low = crossflow_psd_amplitude(current_velocity=0.5, **kwargs)
        amp_high = crossflow_psd_amplitude(current_velocity=2.0, **kwargs)
        assert amp_high > amp_low

    def test_higher_frequency_gives_smaller_amplitude(self):
        kwargs = dict(
            lift_coefficient=0.3,
            fluid_density=1025.0,
            diameter=0.5,
            current_velocity=1.5,
            total_mass_per_unit_length=250.0,
        )
        amp_low_fn = crossflow_psd_amplitude(natural_frequency=0.2, **kwargs)
        amp_high_fn = crossflow_psd_amplitude(natural_frequency=2.0, **kwargs)
        assert amp_low_fn > amp_high_fn

    def test_formula_value(self):
        C_L = 0.4
        rho = 1025.0
        D = 0.5
        U = 1.0
        m = 300.0
        f_n = 0.5
        omega_n = 2.0 * math.pi * f_n
        expected = (C_L * rho * D * U**2) / (2.0 * m * omega_n)
        result = crossflow_psd_amplitude(
            lift_coefficient=C_L,
            fluid_density=rho,
            diameter=D,
            current_velocity=U,
            total_mass_per_unit_length=m,
            natural_frequency=f_n,
        )
        assert result == pytest.approx(expected, rel=1e-9)

    def test_raises_on_non_positive_mass(self):
        with pytest.raises(ValueError, match="total_mass_per_unit_length must be positive"):
            crossflow_psd_amplitude(
                lift_coefficient=0.3,
                fluid_density=1025.0,
                diameter=0.5,
                current_velocity=1.5,
                total_mass_per_unit_length=0.0,
                natural_frequency=0.4,
            )

    def test_raises_on_non_positive_frequency(self):
        with pytest.raises(ValueError, match="natural_frequency must be positive"):
            crossflow_psd_amplitude(
                lift_coefficient=0.3,
                fluid_density=1025.0,
                diameter=0.5,
                current_velocity=1.5,
                total_mass_per_unit_length=250.0,
                natural_frequency=0.0,
            )
