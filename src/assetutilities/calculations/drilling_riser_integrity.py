# ABOUTME: Deep water drilling riser integrity calculations per AMJIG Rev 1/2
# ABOUTME: (1998-2000) and rpt001-3 Part 1 Inspection (Nov 1997) guidelines.

from typing import Sequence, Dict


def riser_effective_tension(t_top: float, w_sub: float, z: float) -> float:
    """Return the riser effective tension at depth z below the top.

    T_eff(z) = T_top - w_sub * z

    The effective tension accounts for the submerged weight of riser pipe,
    mud, and contents above the cross-section of interest.

    Args:
        t_top: Effective tension at the top of the riser (N or lbf).
        w_sub: Submerged weight per unit length of the riser (N/m or lbf/ft).
        z: Depth below the riser top at which tension is evaluated (m or ft).

    Returns:
        Effective tension at depth z.
    """
    return t_top - w_sub * z


def riser_collapse_pressure(E: float, t: float, D: float, nu: float) -> float:
    """Return the critical riser collapse pressure (Timoshenko thin-shell formula).

    P_c = 2 * E * (t / D)^3 / (1 - nu^2)

    This is the elastic (Timoshenko) critical external pressure for a thin
    cylindrical shell and is applicable for deep-water risers where the
    D/t ratio is large.

    Args:
        E: Young's modulus of the pipe material (Pa or psi).
        t: Wall thickness of the riser pipe (m or in).
        D: Outer diameter of the riser pipe (m or in).
        nu: Poisson's ratio of the pipe material (dimensionless).

    Returns:
        Critical collapse pressure in the same pressure units as E.
    """
    return 2.0 * E * (t / D) ** 3 / (1.0 - nu ** 2)


def minimum_top_tension(
    w_sub: float,
    L: float,
    bop_weight: float,
    safety_factor: float,
) -> float:
    """Return the required minimum top tension for the riser system.

    T_min = (w_sub * L + BOP_weight) * safety_factor

    The minimum top tension must support the full submerged weight of the
    riser string plus the BOP stack, with an additional safety margin.

    Args:
        w_sub: Submerged weight per unit length of the riser (N/m or lbf/ft).
        L: Total riser length from surface to mudline (m or ft).
        bop_weight: Submerged weight of the BOP stack (N or lbf).
        safety_factor: Dimensionless safety factor applied to the total load
            (typically 1.10 to 1.25 per AMJIG guidelines).

    Returns:
        Required minimum top tension.
    """
    return (w_sub * L + bop_weight) * safety_factor


def tensile_utilization(t_eff: float, a_steel: float, f_y: float) -> float:
    """Return the riser joint tensile utilization ratio.

    U_t = T_eff / (A_steel * F_y)

    A utilization of 1.0 indicates the pipe is at its axial yield capacity.
    Values less than 1.0 are required for structural acceptability.

    Args:
        t_eff: Effective tension in the riser at the cross-section of interest
            (N or lbf).
        a_steel: Cross-sectional area of the steel pipe wall (m^2 or in^2).
        f_y: Specified minimum yield strength of the pipe material (Pa or psi).

    Returns:
        Dimensionless tensile utilization ratio.
    """
    return t_eff / (a_steel * f_y)


def bending_moment_from_offset(t_eff: float, delta: float) -> float:
    """Return the bending moment at a critical riser section due to lateral offset.

    M = T_eff * delta  (small-angle approximation)

    This simplification is valid when the lateral offset delta is small
    relative to the riser length (i.e., the angle of inclination is small).

    Args:
        t_eff: Effective tension in the riser at the critical section (N or lbf).
        delta: Lateral offset of the riser at the critical section (m or ft).

    Returns:
        Bending moment at the critical section (N·m or lbf·ft).
    """
    return t_eff * delta


def combined_loading_utilization(
    t_eff: float,
    t_allow: float,
    M: float,
    M_allow: float,
) -> float:
    """Return the combined tension-bending utilization per AMJIG interaction formula.

    U_combined = T_eff / T_allow + M / M_allow

    The riser joint is structurally acceptable when U_combined < 1.0.

    Args:
        t_eff: Applied effective tension (N or lbf).
        t_allow: Allowable tension capacity (N or lbf).
        M: Applied bending moment at the critical section (N·m or lbf·ft).
        M_allow: Allowable bending moment capacity (N·m or lbf·ft).

    Returns:
        Dimensionless combined utilization ratio. Values < 1.0 are acceptable.
    """
    return t_eff / t_allow + M / M_allow


def annual_fatigue_damage(
    sea_states: Sequence[Dict[str, float]],
) -> float:
    """Return the Palmgren-Miner annual fatigue damage accumulated across all sea states.

    D_annual = sum(n_cycles_i / N_f_i)  for each sea state i

    Per AMJIG guidelines, the annual fatigue life is acceptable when
    D_annual < 1 / design_fatigue_factor (typically DFF = 3 to 10).

    Args:
        sea_states: Sequence of dicts, each containing:
            - ``n_cycles``: Number of stress cycles in the sea state per year.
            - ``N_f``: Fatigue life (number of cycles to failure) at the
              governing stress range for that sea state, from an S-N curve.

    Returns:
        Dimensionless annual fatigue damage fraction (Palmgren-Miner sum).
        A value of 1.0 represents exhaustion of the full fatigue life.
    """
    return sum(ss["n_cycles"] / ss["N_f"] for ss in sea_states)
