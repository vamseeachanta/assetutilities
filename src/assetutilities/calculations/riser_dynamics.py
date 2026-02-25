# ABOUTME: Riser dynamics calculations covering tow-out, VIV, damping, and residual strength.
# ABOUTME: Implements methods from Huse, Norton, Vandiver, Smith, and TNE guidelines.

import math


def tow_out_catenary_tension(
    submerged_weight: float,
    water_depth: float,
    angle_from_horizontal_deg: float,
) -> float:
    """Compute catenary horizontal tension during riser tow-out (TNE004-1).

    For a catenary riser hanging from a vessel, the horizontal component of
    tension at the vessel connection point is:
        T_H = w * d / tan(theta)
    where theta is the riser angle measured from the horizontal at the vessel,
    w is the submerged weight per unit length, and d is the water depth.

    Args:
        submerged_weight: Submerged weight per unit length of riser (N/m).
        water_depth: Water depth (m).
        angle_from_horizontal_deg: Riser angle from horizontal at vessel (degrees),
            must be in range (0, 90].

    Returns:
        Horizontal tension component T_H (N).

    Raises:
        ValueError: If any input is out of valid range.
    """
    if submerged_weight <= 0.0:
        raise ValueError("submerged_weight must be positive")
    if water_depth <= 0.0:
        raise ValueError("water_depth must be positive")
    if not (0.0 < angle_from_horizontal_deg <= 90.0):
        raise ValueError(
            "angle_from_horizontal_deg must be in range (0, 90]"
        )
    theta = math.radians(angle_from_horizontal_deg)
    tan_theta = math.tan(theta)
    if tan_theta == 0.0:
        return 0.0
    return submerged_weight * water_depth / tan_theta


def hydrodynamic_damping_ratio(
    drag_coefficient: float,
    fluid_density: float,
    diameter: float,
    current_velocity: float,
    mass_per_unit_length: float,
    natural_frequency: float,
) -> float:
    """Compute hydrodynamic damping ratio for a riser in current (Vandiver 1987).

    Formula:
        zeta_h = C_d * rho * D * U / (4 * pi * m * f_n)

    Args:
        drag_coefficient: Drag coefficient C_d (dimensionless).
        fluid_density: Fluid density rho (kg/m^3).
        diameter: Riser outer diameter D (m).
        current_velocity: Far-field current velocity U (m/s).
        mass_per_unit_length: Riser mass per unit length m (kg/m),
            including structural and internal fluid mass.
        natural_frequency: Natural frequency of the mode f_n (Hz).

    Returns:
        Hydrodynamic damping ratio zeta_h (dimensionless).

    Raises:
        ValueError: If mass_per_unit_length or natural_frequency are not positive.
    """
    if mass_per_unit_length <= 0.0:
        raise ValueError("mass_per_unit_length must be positive")
    if natural_frequency <= 0.0:
        raise ValueError("natural_frequency must be positive")
    return (
        drag_coefficient * fluid_density * diameter * current_velocity
        / (4.0 * math.pi * mass_per_unit_length * natural_frequency)
    )


def viv_fatigue_correction_factor(
    correlation_length: float,
    span_length: float,
) -> float:
    """Compute the Huse VIV fatigue correction for short correlation length.

    When the VIV correlation length L_c is shorter than the riser span L,
    the fatigue damage is overestimated by full-span analysis. The Huse
    correction factor eta reduces the effective fatigue damage:
        eta = min(L_c / L, 1.0)

    Args:
        correlation_length: VIV correlation length L_c (m).
        span_length: Riser span (or mode half-wavelength) L (m).

    Returns:
        Correction factor eta (0 < eta <= 1.0).

    Raises:
        ValueError: If either length is not positive.
    """
    if correlation_length <= 0.0:
        raise ValueError("correlation_length must be positive")
    if span_length <= 0.0:
        raise ValueError("span_length must be positive")
    return min(correlation_length / span_length, 1.0)


def norton_drag_coefficient(reynolds_number: float) -> float:
    """Return drag coefficient for a marine riser per Norton (1981) wind tunnel data.

    Norton et al. (1981) wind tunnel tests on inclined cylinders established
    the following empirical drag coefficient values as a function of Reynolds
    number, with a smooth transition through the critical regime:
        Re < 2e5  : C_d = 1.2  (subcritical)
        Re > 5e5  : C_d = 0.5  (supercritical)
        Transition: linear interpolation between the two regimes.

    Args:
        reynolds_number: Reynolds number Re = rho * U * D / mu (dimensionless).

    Returns:
        Drag coefficient C_d (dimensionless).

    Raises:
        ValueError: If reynolds_number is not positive.
    """
    if reynolds_number <= 0.0:
        raise ValueError("reynolds_number must be positive")
    RE_SUBCRITICAL = 2.0e5
    RE_SUPERCRITICAL = 5.0e5
    CD_SUBCRITICAL = 1.2
    CD_SUPERCRITICAL = 0.5
    if reynolds_number < RE_SUBCRITICAL:
        return CD_SUBCRITICAL
    if reynolds_number > RE_SUPERCRITICAL:
        return CD_SUPERCRITICAL
    fraction = (reynolds_number - RE_SUBCRITICAL) / (
        RE_SUPERCRITICAL - RE_SUBCRITICAL
    )
    return CD_SUBCRITICAL + fraction * (CD_SUPERCRITICAL - CD_SUBCRITICAL)


def vandiver_added_mass_coefficient(
    shape: str = "circular",
    kc_number: float = None,
) -> float:
    """Return added mass coefficient for a riser in oscillatory flow (Vandiver 1987).

    Vandiver (1987) established that for circular cylinders in oscillatory
    flow the added mass coefficient is Ca = 1.0, consistent with potential
    flow theory. The KC number and shape arguments are provided for
    extensibility but do not change the result for circular sections.

    Args:
        shape: Cross-section shape; currently only "circular" is supported.
        kc_number: Keulegan-Carpenter number (optional, included for future use).

    Returns:
        Added mass coefficient Ca = 1.0 for circular cylinders.
    """
    return 1.0


def smith_residual_collapse_factor(ovality: float, k: float = 2.0) -> float:
    """Compute residual collapse pressure reduction factor per Smith (1981).

    Smith et al. (1981) provide an empirical relationship between pipe ovality
    (due to local buckling) and the reduction in collapse pressure capacity:
        eta_r = max(0.0, 1 - k * ovality)
    where ovality = (D_max - D_min) / D_nominal and k ≈ 2.0 from experiments.

    Args:
        ovality: Normalised pipe ovality (D_max - D_min) / D_nominal (dimensionless,
            must be >= 0).
        k: Empirical reduction coefficient (default 2.0 per Smith 1981).

    Returns:
        Residual collapse pressure factor eta_r in [0, 1].

    Raises:
        ValueError: If ovality is negative.
    """
    if ovality < 0.0:
        raise ValueError("ovality must be non-negative")
    return max(0.0, 1.0 - k * ovality)


def crossflow_psd_amplitude(
    lift_coefficient: float,
    fluid_density: float,
    diameter: float,
    current_velocity: float,
    total_mass_per_unit_length: float,
    natural_frequency: float,
) -> float:
    """Compute cross-flow RMS response amplitude via power spectral density.

    Uses the PSD-based formulation for the cross-flow response amplitude:
        A_rms = (C_L * rho_f * D * U^2) / (2 * m_total * omega_n)
    where omega_n = 2 * pi * f_n.

    Args:
        lift_coefficient: Lift (cross-flow excitation) coefficient C_L.
        fluid_density: Fluid density rho_f (kg/m^3).
        diameter: Riser outer diameter D (m).
        current_velocity: Current velocity U (m/s).
        total_mass_per_unit_length: Total mass per unit length m_total (kg/m),
            including structural mass, internal fluid, and hydrodynamic added mass.
        natural_frequency: Natural frequency f_n (Hz).

    Returns:
        Cross-flow RMS displacement amplitude A_rms (m).

    Raises:
        ValueError: If total_mass_per_unit_length or natural_frequency are not positive.
    """
    if total_mass_per_unit_length <= 0.0:
        raise ValueError("total_mass_per_unit_length must be positive")
    if natural_frequency <= 0.0:
        raise ValueError("natural_frequency must be positive")
    omega_n = 2.0 * math.pi * natural_frequency
    return (
        lift_coefficient
        * fluid_density
        * diameter
        * current_velocity**2
        / (2.0 * total_mass_per_unit_length * omega_n)
    )
