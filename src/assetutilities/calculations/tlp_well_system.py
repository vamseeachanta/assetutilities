# ABOUTME: TLP well system and riser engineering calculations.
# ABOUTME: Implements Javanmardi 1995, Fox 1995, Larimore 1998, Carminati 1999, Barton 1999.

"""TLP (Tension Leg Platform) well system and riser calculations.

References:
- Javanmardi, K. et al. (1995) — Auger TLP Well System Challenges, OTC.
- Fox, S.A. et al. (1995) — Design Analysis and Full Scale Pro, OTC.
- Larimore, D. et al. (1998) — Case History: First Diverless, OTC.
- Carminati, J.R. et al. (1999) — Ursa TLP Well System, OTC.
- Barton, D.R. et al. (1999) — Genesis Project Development Wells, OTC.
"""

import math
from typing import List, Tuple


def tendon_effective_tension(
    t_pretension: float,
    delta_t_hull: float,
) -> float:
    """Compute effective TLP tendon tension after hull motion load change.

    T_eff = T_pretension - delta_T_hull_motion

    Args:
        t_pretension: Tendon pre-tension [N].
        delta_t_hull: Tension reduction due to hull motion [N].

    Returns:
        Effective tendon tension [N].

    Raises:
        ValueError: If the resulting effective tension would be non-positive.
    """
    t_eff = t_pretension - delta_t_hull
    if t_eff <= 0.0:
        raise ValueError(
            f"effective tension must be positive; got {t_eff:.3e} N. "
            "Check pretension and hull motion parameters."
        )
    return float(t_eff)


def riser_tensioner_stroke(
    length: float,
    delta_vert: float,
    delta_horiz: float,
) -> float:
    """Compute tensioner stroke required to accommodate riser displacement.

    s = sqrt((L + delta_vert)^2 + delta_horiz^2) - L

    The stroke accounts for both vertical (heave) and horizontal (offset)
    platform displacement components.

    Args:
        length: Nominal riser length from tensioner to wellhead [m].
        delta_vert: Vertical displacement (positive downward) [m].
        delta_horiz: Horizontal offset [m].

    Returns:
        Required tensioner stroke [m].

    Raises:
        ValueError: If length is non-positive.
    """
    if length <= 0.0:
        raise ValueError(f"length must be positive; got {length}")
    stroke = math.sqrt((length + delta_vert) ** 2 + delta_horiz ** 2) - length
    return float(stroke)


def wellhead_fatigue_accumulation(
    stress_ranges: List[float],
    annual_cycles: List[float],
    service_years: float,
    a_param: float,
    m_param: float,
) -> float:
    """Accumulate wellhead fatigue damage over a service life using Miner's rule.

    D = sum(n_i / N_fi)  where  N_fi = A / (Delta_sigma_i)^m

    Each stress range bin contributes n_total = annual_cycles * service_years
    applied cycles against the S-N endurance N_fi.

    Args:
        stress_ranges: List of stress ranges for each bin [Pa or consistent units].
        annual_cycles: Annual cycle count for each stress range bin.
        service_years: Total service life [years].
        a_param: S-N curve intercept constant A (cycles at unit stress range).
        m_param: S-N curve slope exponent m.

    Returns:
        Total accumulated fatigue damage (dimensionless Miner's sum).

    Raises:
        ValueError: If stress_ranges and annual_cycles have different lengths.
    """
    if len(stress_ranges) != len(annual_cycles):
        raise ValueError(
            "stress_ranges and annual_cycles must have the same length; "
            f"got {len(stress_ranges)} and {len(annual_cycles)}"
        )
    damage = 0.0
    for sigma, n_annual in zip(stress_ranges, annual_cycles):
        n_total = n_annual * service_years
        n_f = a_param / (sigma ** m_param)
        damage += n_total / n_f
    return float(damage)


def riser_interference_check(
    tensioned_riser_od: float,
    drilling_riser_od: float,
    centre_to_centre: float,
    min_gap: float = 0.0,
) -> Tuple[bool, float]:
    """Check whether tensioned and drilling risers maintain adequate separation.

    Computes the clear gap between riser outer surfaces:
        gap = centre_to_centre - (tensioned_riser_od / 2) - (drilling_riser_od / 2)

    Args:
        tensioned_riser_od: Outer diameter of the tensioned production riser [m].
        drilling_riser_od: Outer diameter of the drilling riser [m].
        centre_to_centre: Centre-to-centre distance between risers [m].
        min_gap: Minimum acceptable clear gap [m]. Defaults to 0.0 (no contact).

    Returns:
        Tuple of (is_clear: bool, minimum_separation: float [m]).
        is_clear is True when gap > min_gap.

    Raises:
        ValueError: If any outer diameter is non-positive.
    """
    if tensioned_riser_od <= 0.0 or drilling_riser_od <= 0.0:
        raise ValueError(
            "outer diameter must be positive; "
            f"got tensioned_riser_od={tensioned_riser_od}, "
            f"drilling_riser_od={drilling_riser_od}"
        )
    separation = centre_to_centre - (tensioned_riser_od / 2.0) - (drilling_riser_od / 2.0)
    is_clear = separation > min_gap
    return bool(is_clear), float(separation)


def critical_damping_ratio(
    C: float,
    K: float,
    M: float,
) -> float:
    """Compute the critical damping ratio for a TLP hull or riser system.

    zeta = C / (2 * sqrt(K * M))

    Args:
        C: Damping coefficient [N·s/m].
        K: Stiffness [N/m].
        M: Mass (including added mass) [kg].

    Returns:
        Critical damping ratio zeta (dimensionless).

    Raises:
        ValueError: If K or M are non-positive.
    """
    if K <= 0.0:
        raise ValueError(f"K must be positive; got {K}")
    if M <= 0.0:
        raise ValueError(f"M must be positive; got {M}")
    zeta = C / (2.0 * math.sqrt(K * M))
    return float(zeta)


def platform_set_down(
    length: float,
    delta_horiz: float,
) -> float:
    """Compute TLP platform vertical set-down due to horizontal offset.

    For a TLP tendon of length L displaced horizontally by delta_horiz,
    the platform descends by:
        theta = arcsin(delta_horiz / L)
        delta_z = L * (1 - cos(theta))

    This is geometrically equivalent to delta_z = L - sqrt(L^2 - delta_horiz^2).

    Args:
        length: Tendon length (water depth) [m].
        delta_horiz: Horizontal offset of the platform [m].

    Returns:
        Vertical set-down delta_z [m] (positive downward).

    Raises:
        ValueError: If length is non-positive or delta_horiz >= length.
    """
    if length <= 0.0:
        raise ValueError(f"length must be positive; got {length}")
    if delta_horiz >= length:
        raise ValueError(
            f"delta_horiz must be less than length; "
            f"got delta_horiz={delta_horiz}, length={length}"
        )
    theta = math.asin(delta_horiz / length)
    delta_z = length * (1.0 - math.cos(theta))
    return float(delta_z)
