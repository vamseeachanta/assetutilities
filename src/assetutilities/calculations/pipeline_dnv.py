# ABOUTME: DNV OS-F101 submarine pipeline system design checks (LRFD format).
# ABOUTME: Covers burst pressure, local buckling, von Mises stress, and buckle arrest.
"""DNV OS-F101 (2013) submarine pipeline design checks.

Implements LRFD-format design equations from DNV OS-F101 Section 5:
  - Pressure containment (burst): Section 5 D300
  - Local buckling combined loading: Section 5 D500
  - Von Mises equivalent stress: Section 5 D600
  - Buckle arrest capacity: Section 5 D800

All stress values are in Pa, pressure in Pa, dimensions in metres.

Partial safety factors (gamma values) follow Table 5-4 and 5-6 of the standard.
Default fabrication factor alpha_fab = 0.85 for seam-welded pipe (Table 5-3).
"""
import math


# ---------------------------------------------------------------------------
# Material grade database  (API 5L / DNV OS-F101 Table 5-1)
# All stress values in Pa.
# ---------------------------------------------------------------------------

MATERIAL_GRADES: dict[str, dict[str, float]] = {
    "X52": {"f_y": 358e6, "f_u": 455e6},
    "X60": {"f_y": 413e6, "f_u": 517e6},
    "X65": {"f_y": 450e6, "f_u": 535e6},
    "X70": {"f_y": 482e6, "f_u": 565e6},
}

# Default partial safety factors used when not supplied by the caller.
_DEFAULT_GAMMA_M = 1.15       # material resistance factor (normal)
_DEFAULT_GAMMA_SCPC = 1.05    # safety-class factor for pressure containment (medium)
_DEFAULT_ALPHA_FAB = 0.85     # fabrication factor for seam-welded pipe
_DEFAULT_ALPHA_U = 0.96       # material strength factor (supplementary requirement U)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _characteristic_strength(f_y: float, f_u: float, alpha_U: float) -> float:
    """Return the characteristic flow stress for pressure containment.

    DNV OS-F101 Eq 5.8: f_cb = min(f_y * alpha_U, f_u * alpha_U / 1.15).
    """
    return min(f_y * alpha_U, f_u * alpha_U / 1.15)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def burst_pressure_capacity(
    D: float,
    t: float,
    f_y: float,
    f_u: float,
    alpha_U: float = _DEFAULT_ALPHA_U,
    alpha_fab: float = _DEFAULT_ALPHA_FAB,
) -> float:
    """Burst pressure capacity per DNV OS-F101 Section 5 D300.

    P_b = (2 * t / D) * f_cb * alpha_fab

    Args:
        D: Outer diameter [m].
        t: Nominal wall thickness [m].
        f_y: Specified minimum yield strength [Pa].
        f_u: Specified minimum tensile strength (SMTS) [Pa].
        alpha_U: Material strength factor (default 0.96, Table 5-2).
        alpha_fab: Fabrication factor (default 0.85 for seam-welded, Table 5-3).

    Returns:
        Burst pressure capacity P_b [Pa].
    """
    f_cb = _characteristic_strength(f_y, f_u, alpha_U)
    return (2.0 * t / D) * f_cb * alpha_fab


def pressure_containment_check(
    P_li: float,
    D: float,
    t: float,
    f_y: float,
    f_u: float,
    gamma_m: float = _DEFAULT_GAMMA_M,
    gamma_SCPC: float = _DEFAULT_GAMMA_SCPC,
    alpha_U: float = _DEFAULT_ALPHA_U,
    alpha_fab: float = _DEFAULT_ALPHA_FAB,
) -> float:
    """LRFD pressure containment (burst) utilization.

    The design requirement is:  P_li <= P_b / (gamma_m * gamma_SCPC)
    Returned utilization = P_li * gamma_m * gamma_SCPC / P_b

    A value <= 1.0 means the design is acceptable.

    Args:
        P_li: Local incidental pressure [Pa].
        D: Outer diameter [m].
        t: Wall thickness [m].
        f_y: Yield strength [Pa].
        f_u: SMTS [Pa].
        gamma_m: Material resistance factor.
        gamma_SCPC: Safety-class resistance factor for pressure containment.
        alpha_U: Material strength factor.
        alpha_fab: Fabrication factor.

    Returns:
        Utilization ratio (dimensionless). >1.0 indicates overstress.
    """
    P_b = burst_pressure_capacity(D=D, t=t, f_y=f_y, f_u=f_u,
                                  alpha_U=alpha_U, alpha_fab=alpha_fab)
    allowable = P_b / (gamma_m * gamma_SCPC)
    return float(P_li / allowable)


def local_buckling_combined_loading(
    D: float,
    t: float,
    f_y: float,
    M: float,
    S: float,
    delta_p: float,
    gamma_m: float = _DEFAULT_GAMMA_M,
    gamma_SC: float = 1.138,
) -> float:
    """Local buckling utilization under combined bending, pressure, and tension.

    DNV OS-F101 Section 5 D500 — LRFD combined loading check.

    The utilization is defined as:
        U = (M / M_c)^2 + (delta_p / p_c) + (S / S_c)

    where:
        M_c  = gamma_m * gamma_SC * f_y * (pi/4) * D^2 * t  (plastic moment capacity)
        p_c  = gamma_m * gamma_SC * 2 * f_y * t / D          (collapse pressure)
        S_c  = gamma_m * gamma_SC * pi * D * t * f_y          (axial capacity)

    Args:
        D: Outer diameter [m].
        t: Wall thickness [m].
        f_y: Yield strength [Pa].
        M: Applied bending moment [N.m].
        S: Applied effective axial force [N]. Positive = tension.
        delta_p: Net internal overpressure (pi - pe) [Pa].
        gamma_m: Material resistance factor.
        gamma_SC: Safety-class resistance factor for local buckling.

    Returns:
        Combined utilization ratio (dimensionless). >1.0 = failure.
    """
    # Characteristic resistances divided by safety factors
    M_c = (math.pi / 4.0) * D**2 * t * f_y / (gamma_m * gamma_SC)
    p_c = 2.0 * f_y * t / (D * gamma_m * gamma_SC)
    S_c = math.pi * D * t * f_y / (gamma_m * gamma_SC)

    term_M = (M / M_c) ** 2 if M_c > 0 else 0.0
    term_p = delta_p / p_c if p_c > 0 else 0.0
    term_S = abs(S) / S_c if S_c > 0 else 0.0

    return float(term_M + term_p + term_S)


def von_mises_equivalent_stress(
    sigma_l: float,
    sigma_h: float,
    tau: float,
) -> float:
    """Von Mises equivalent stress per DNV OS-F101 Section 5 D600.

    sigma_eq = sqrt(sigma_l^2 - sigma_l * sigma_h + sigma_h^2 + 3 * tau^2)

    Args:
        sigma_l: Longitudinal (axial) stress component [Pa].
        sigma_h: Hoop (circumferential) stress component [Pa].
        tau: Shear stress component [Pa].

    Returns:
        Von Mises equivalent stress [Pa]. Always non-negative.
    """
    return math.sqrt(sigma_l**2 - sigma_l * sigma_h + sigma_h**2 + 3.0 * tau**2)


def buckle_arrest_capacity(
    D: float,
    t: float,
    f_y: float,
    gamma_m: float = _DEFAULT_GAMMA_M,
) -> float:
    """Buckle arrest capacity per DNV OS-F101 Section 5 D800 (LRFD).

    F_ba = 10.7 * f_y * t^2 * (t / D)^0.4 / gamma_m

    This is the characteristic buckle-arrest pressure reduced by the material
    resistance factor to give the design buckle-arrest capacity.

    Args:
        D: Outer diameter [m].
        t: Wall thickness [m].
        f_y: Yield strength [Pa].
        gamma_m: Material resistance factor.

    Returns:
        Design buckle-arrest capacity [Pa].
    """
    return 10.7 * f_y * t**2 * (t / D) ** 0.4 / gamma_m
