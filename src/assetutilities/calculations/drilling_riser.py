# ABOUTME: Deepwater drilling riser analysis calculations from OTC literature.
# ABOUTME: Implements Gardner 1982 tension, Kim 1975 frequency, Grant 1977 fairing, Vandiver 1985 lock-in, Miller 1985 mud pressure, Imas SCR.

"""
Deepwater Drilling Riser Analysis
====================================
References:
  - Gardner, T.N., et al, 1982 - Deepwater Drilling in High Currents (OTC)
  - Kim, Y.Y., et al, 1975 - Analysis of Simultaneous Wave Forces (OTC)
  - Grant, R., 1977 - Riser Fairing for Reduced Drag and Vortex Suppression (OTC)
  - Jacobsen, V., et al, 1996 - Vibration Suppression Devices for Risers (OTC)
  - D'Souza, R., et al, 2002 - The Next Generation Production Drilling Riser (OTC)
  - Vandiver, J.K., 1985 - The Prediction of Lock-in Vibration on Flexible Cylinders (OTC)
  - Miller, J.E., et al, 1985 - Influence of Mud Column Dynamics (OTC)
  - Imas, L., et al - Sensitivity of SCR Response and Fatigue (OTC)
  - Berner, P., et al, 1997 - Neptune Project Production Riser (OTC)
  - Stahl, OTC 3902 - Design Methodology for Offshore Platform Conductors

All forces in lbf, pressures in psi, lengths in ft unless noted.
"""

import math

# Default Strouhal number for smooth cylinders in turbulent flow
_DEFAULT_STROUHAL: float = 0.2

# Field unit conversion factor: psi = 0.052 * mud_weight_ppg * depth_ft
_MUD_PRESSURE_FACTOR: float = 0.052


def gardner_bottom_tension(
    w_air_lbf_per_ft: float,
    w_buoyancy_lbf_per_ft: float,
    length_ft: float,
    bop_weight_lbf: float,
) -> float:
    """Compute drilling riser bottom tension per Gardner (1982).

    The bottom tension required to maintain positive effective tension
    throughout the riser is governed by the submerged weight minus the BOP:

      T_bottom = (w_air - w_buoyancy) * L - BOP_weight

    A negative result implies the BOP weight dominates and the effective
    tension is compressive at the bottom.

    Args:
        w_air_lbf_per_ft: Riser weight per unit length in air (lbf/ft).
        w_buoyancy_lbf_per_ft: Buoyancy force per unit length (lbf/ft).
        length_ft: Riser length in feet.
        bop_weight_lbf: Blowout preventer weight in lbf.

    Returns:
        Bottom tension in lbf.
    """
    return (w_air_lbf_per_ft - w_buoyancy_lbf_per_ft) * length_ft - bop_weight_lbf


def gardner_top_tension(
    bottom_tension_lbf: float,
    segment_weights_lbf: list[float],
) -> float:
    """Compute required top tension to maintain positive effective tension.

    Top tension must support the bottom tension plus all riser segment weights:
      T_top = T_bottom + sum(w_segment)

    Args:
        bottom_tension_lbf: Required bottom tension in lbf.
        segment_weights_lbf: List of riser segment submerged weights in lbf.

    Returns:
        Required top tension in lbf.
    """
    return bottom_tension_lbf + sum(segment_weights_lbf)


def kim_natural_frequency_with_pressure(
    fn_vacuum_hz: float,
    internal_pressure_psi: float,
    external_pressure_psi: float,
    pipe_cross_section_in2: float,
    riser_length_ft: float,
    riser_weight_lbf: float,
) -> float:
    """Compute riser natural frequency accounting for internal/external pressure effects.

    Per Kim (1975), pressure loads modify the effective axial tension in a riser,
    which in turn shifts the natural frequency. The pressure-modified effective
    tension is:

      delta_T = (P_ext - P_int) * A_pipe

    This tension change scales the natural frequency as:

      fn_p = fn_vac * sqrt(1 + delta_T / (riser_weight * g_factor))

    where g_factor = riser_length_ft / pi^2 (beam column approximation).

    For zero pressure the formula returns fn_vacuum_hz exactly.

    Args:
        fn_vacuum_hz: Natural frequency in vacuum (no pressure) in Hz.
        internal_pressure_psi: Internal bore pressure in psi.
        external_pressure_psi: External hydrostatic pressure in psi.
        pipe_cross_section_in2: Pipe cross-sectional bore area in in^2.
        riser_length_ft: Riser suspended length in feet.
        riser_weight_lbf: Total riser weight in lbf (used as modal mass proxy).

    Returns:
        Natural frequency in Hz after pressure correction.
    """
    # Net pressure change on pipe cross-section (lbf/in^2 * in^2 = lbf)
    # External pressure increases effective tension; internal reduces it.
    delta_pressure_psi = external_pressure_psi - internal_pressure_psi
    # Convert pressure × area to lbf; 1 ft^2 = 144 in^2 (no conversion needed,
    # pipe_cross_section already in in^2)
    delta_tension_lbf = delta_pressure_psi * pipe_cross_section_in2

    # Beam-column approximation: reference axial load = weight over pi^2 * length
    if riser_weight_lbf == 0.0 or riser_length_ft == 0.0:
        return fn_vacuum_hz

    # Normalised stiffness change parameter
    reference_axial = riser_weight_lbf / (math.pi ** 2)
    ratio = delta_tension_lbf / reference_axial

    # Guard against negative radicand (should not occur for physical inputs)
    radicand = 1.0 + ratio
    if radicand <= 0.0:
        radicand = 0.0

    return fn_vacuum_hz * math.sqrt(radicand)


def grant_faired_drag_coefficient(
    cd_bare: float,
    reduction_factor: float = 0.7,
) -> float:
    """Compute faired riser drag coefficient per Grant (1977).

    Fairings reduce drag by streamlining the cylinder:
      Cd_faired = reduction_factor * Cd_bare

    Grant (1977) reports approximately 30% drag reduction for straked
    or faired risers (reduction_factor = 0.7).

    Args:
        cd_bare: Drag coefficient for a bare (unfaired) cylinder.
        reduction_factor: Fraction of bare Cd retained after fairing.
            Must be in (0, 1]. Defaults to 0.7.

    Returns:
        Drag coefficient for the faired riser.

    Raises:
        ValueError: If cd_bare <= 0 or reduction_factor is outside (0, 1].
    """
    if cd_bare < 0.0:
        raise ValueError(f"cd_bare must be non-negative, got {cd_bare}")
    if not 0.0 < reduction_factor <= 1.0:
        raise ValueError(
            f"reduction_factor must be in (0, 1], got {reduction_factor}"
        )
    return reduction_factor * cd_bare


def jacobsen_suppression_damage_ratio(
    unsuppressed_damage: float,
    suppression_effectiveness: float,
) -> float:
    """Compute fatigue damage ratio after VIV suppression per Jacobsen (1996).

    The residual damage fraction after applying a suppression device is:
      damage_ratio = unsuppressed_damage * (1.0 - suppression_effectiveness)

    where suppression_effectiveness is in [0, 1]:
      0.0 → no suppression (ratio = unsuppressed_damage)
      1.0 → full suppression (ratio = 0)

    Args:
        unsuppressed_damage: Baseline accumulated fatigue damage without suppression.
        suppression_effectiveness: Fractional reduction in damage (0 to 1).

    Returns:
        Residual fatigue damage after suppression.
    """
    return unsuppressed_damage * (1.0 - suppression_effectiveness)


def dsouza_flex_riser_effective_weight(
    weight_in_air_lbf_per_ft: float,
    displaced_fluid_weight_lbf_per_ft: float,
) -> float:
    """Compute unbonded flexible riser effective (submerged) weight per D'Souza (2002).

    The effective weight governs tension distribution and catenary shape:
      w_eff = w_air - w_displaced_fluid

    Args:
        weight_in_air_lbf_per_ft: Riser weight per foot in air (lbf/ft).
        displaced_fluid_weight_lbf_per_ft: Buoyancy per foot from displaced fluid (lbf/ft).

    Returns:
        Effective submerged weight per foot (lbf/ft).
    """
    return weight_in_air_lbf_per_ft - displaced_fluid_weight_lbf_per_ft


def vandiver_lock_in_velocity(
    natural_frequency_hz: float,
    diameter_ft: float,
    strouhal_number: float = _DEFAULT_STROUHAL,
) -> float:
    """Compute critical current velocity for VIV lock-in per Vandiver (1985).

    Lock-in occurs when the vortex shedding frequency equals the structural
    natural frequency:
      Vc = f_n * D / St

    Args:
        natural_frequency_hz: Structural natural frequency in Hz.
        diameter_ft: Riser outer diameter in feet.
        strouhal_number: Strouhal number (dimensionless). Defaults to 0.2.

    Returns:
        Critical current velocity for lock-in onset in ft/s.

    Raises:
        ValueError: If strouhal_number is not positive.
    """
    if strouhal_number <= 0.0:
        raise ValueError(
            f"strouhal_number must be positive, got {strouhal_number}"
        )
    return natural_frequency_hz * diameter_ft / strouhal_number


def miller_mud_column_pressure(
    mud_weight_ppg: float,
    depth_ft: float,
) -> float:
    """Compute mud column hydrostatic pressure per Miller (1985) field unit formula.

    The standard oilfield pressure gradient formula:
      P_psi = 0.052 * mud_weight_ppg * depth_ft

    Miller (1985) investigates this pressure's dynamic effect on riser tension
    during storm hang-off, noting that treating mud as rigid underestimates
    dynamic loads for risers exceeding 2000 ft.

    Args:
        mud_weight_ppg: Drilling mud weight in pounds per gallon.
        depth_ft: Depth below surface in feet. Must be non-negative.

    Returns:
        Hydrostatic pressure in psi.

    Raises:
        ValueError: If mud_weight_ppg < 0 or depth_ft < 0.
    """
    if mud_weight_ppg < 0.0:
        raise ValueError(f"mud_weight_ppg must be non-negative, got {mud_weight_ppg}")
    if depth_ft < 0.0:
        raise ValueError(f"depth_ft must be non-negative, got {depth_ft}")
    return _MUD_PRESSURE_FACTOR * mud_weight_ppg * depth_ft


def imas_scr_response_amplification(
    current_velocity: float,
    A: float,
    B: float,
) -> float:
    """Compute SCR (Steel Catenary Riser) VIV response amplification per Imas et al.

    The empirical power-law model for SCR response in current:
      response_amplification = A * U^B

    where U is the current velocity, A is a scale coefficient, and B is
    the velocity sensitivity exponent.

    Args:
        current_velocity: Ambient current velocity (ft/s or m/s, consistent with A).
            Must be non-negative.
        A: Empirical amplitude coefficient.
        B: Velocity exponent (sensitivity).

    Returns:
        Response amplification factor.

    Raises:
        ValueError: If current_velocity is negative.
    """
    if current_velocity < 0.0:
        raise ValueError(
            f"current_velocity must be non-negative, got {current_velocity}"
        )
    return A * current_velocity ** B


def berner_riser_effective_tension(
    top_tension_lbf: float,
    submerged_weight_lbf_per_ft: float,
    riser_length_ft: float,
    vessel_offset_tension_delta_lbf: float = 0.0,
) -> float:
    """Compute drilling riser effective tension per Berner (1997) Neptune Project method.

    Combines the Stahl (OTC 3902) offshore platform conductor design methodology
    with vessel offset correction for deepwater production risers:

      T_eff = T_top - (w_submerged * L) + delta_tension_from_vessel_offset

    Args:
        top_tension_lbf: Applied top tension at the tensioner in lbf.
        submerged_weight_lbf_per_ft: Riser submerged weight per foot (lbf/ft).
        riser_length_ft: Riser suspended length in feet.
        vessel_offset_tension_delta_lbf: Tension change from vessel offset (lbf).
            Positive = increases effective tension. Defaults to 0.

    Returns:
        Effective tension in lbf at the base of the riser.
    """
    return (
        top_tension_lbf
        - submerged_weight_lbf_per_ft * riser_length_ft
        + vessel_offset_tension_delta_lbf
    )
