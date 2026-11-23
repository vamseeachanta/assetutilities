# ABOUTME: Riser VIV and hydrodynamics calculations for offshore pipeline/riser design.
# ABOUTME: Covers drag, vortex shedding, lock-in, VIV amplitude, fatigue, and effective tension.
"""Riser VIV and hydrodynamics calculations.

Implements formulae from:
  - BP Riser Drag Data correlations (smooth/rough cylinder, bundle effects)
  - Strouhal (1878), Bearman (1984) — vortex shedding frequency
  - Griffin (1980), Vandiver (1993) — VIV amplitude response (Griffin curve)
  - DNV RP-C203 (2016) S-N D-curve — VIV fatigue damage (Palmgren-Miner)
  - TNE012-1 — effective tension accounting for internal/external pressure
  - Shear7 pinned-pinned beam natural frequency model (Vandiver, MIT)

Consistent SI units throughout: Pa, N, m, kg, s, Hz.
"""
import math
from typing import Sequence


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# DNV RP-C203 D-curve S-N parameters (in air/cathodic protection)
# log10(N) = log10(a) - m * log10(sigma_MPa)
_SN_LOG10_A = 12.164   # intercept for D-curve (N < 1e7 cycles)
_SN_M = 3.0            # slope (negative exponent on stress range)

# Conventional VIV lock-in reduced velocity bounds (Blevins, 1990)
_VR_LOCK_IN_LOW = 4.0
_VR_LOCK_IN_HIGH = 8.0

# Strouhal number default for subcritical smooth cylinder
_ST_DEFAULT = 0.2


# ---------------------------------------------------------------------------
# Drag coefficient — smooth cylinder (piecewise Reynolds approximation)
# Based on Achenbach (1968) measurements; matches BP drag data guidance.
# ---------------------------------------------------------------------------

def drag_coefficient_smooth_cylinder(Re: float) -> float:
    """Drag coefficient for a smooth circular cylinder.

    Piecewise model based on experimental data (Achenbach, 1968):
      - Subcritical  (Re < 2e5):  Cd ≈ 1.2
      - Critical     (2e5-5e5):   drag crisis — Cd falls to ≈ 0.3
      - Supercritical (Re > 5e5): Cd recovers to ≈ 0.5-0.7

    This is the baseline used in BP riser drag correlations before
    bundle interference factors are applied.

    Args:
        Re: Reynolds number (U * D / nu). Must be positive.

    Returns:
        Drag coefficient Cd (dimensionless).

    Raises:
        ValueError: If Re <= 0.
    """
    if Re <= 0:
        raise ValueError(f"Reynolds number must be positive, got {Re}")

    if Re < 2.0e5:
        # Subcritical — approximately constant
        return 1.2

    if Re < 5.0e5:
        # Drag crisis — linear drop from 1.2 to 0.3
        fraction = (Re - 2.0e5) / (5.0e5 - 2.0e5)
        return 1.2 - fraction * (1.2 - 0.3)

    if Re < 1.0e6:
        # Post-critical recovery — linear rise from 0.3 to 0.6
        fraction = (Re - 5.0e5) / (1.0e6 - 5.0e5)
        return 0.3 + fraction * (0.6 - 0.3)

    # Fully turbulent supercritical — approximately constant
    return 0.6


# ---------------------------------------------------------------------------
# Drag coefficient — riser bundle  (BP Riser Drag Data correlations)
# ---------------------------------------------------------------------------

def drag_coefficient_bundle(
    Re: float,
    n_risers: int,
    pitch_diameter_ratio: float,
) -> float:
    """Effective drag coefficient for a riser bundle.

    Based on BP Riser Drag Data (internal guidance document) correlation
    for multiple parallel cylinders:

        Cd_bundle = Cd_single * (1 + k_interference * (n - 1) / (p/D))

    where k_interference = 0.5 is the interference amplification factor
    from BP data fitting (valid for p/D in [1.5, 4.0]).

    Args:
        Re: Reynolds number for individual riser diameter.
        n_risers: Number of risers in the bundle (>= 1).
        pitch_diameter_ratio: Centre-to-centre spacing / riser diameter (p/D).

    Returns:
        Effective bundle drag coefficient (dimensionless).

    Raises:
        ValueError: If n_risers < 1 or Re <= 0.
    """
    if n_risers < 1:
        raise ValueError(f"n_risers must be >= 1, got {n_risers}")

    Cd_single = drag_coefficient_smooth_cylinder(Re)

    if n_risers == 1:
        return Cd_single

    k_interference = 0.5
    amplification = 1.0 + k_interference * (n_risers - 1) / max(pitch_diameter_ratio, 1.0)
    return Cd_single * amplification


# ---------------------------------------------------------------------------
# Strouhal vortex shedding frequency
# ---------------------------------------------------------------------------

def strouhal_frequency(U: float, D: float, St: float = _ST_DEFAULT) -> float:
    """Vortex shedding frequency using the Strouhal relationship.

    f_s = St * U / D

    Args:
        U: Flow velocity [m/s].
        D: Riser outer diameter [m]. Must be positive.
        St: Strouhal number (default 0.2 for subcritical smooth cylinder).

    Returns:
        Vortex shedding frequency f_s [Hz].

    Raises:
        ValueError: If D <= 0.
    """
    if D <= 0.0:
        raise ValueError(f"Diameter must be positive, got {D}")
    return St * U / D


# ---------------------------------------------------------------------------
# Reduced velocity
# ---------------------------------------------------------------------------

def reduced_velocity(U: float, f_n: float, D: float) -> float:
    """Reduced velocity for VIV assessment.

    Vr = U / (f_n * D)

    VIV lock-in typically occurs for Vr in [4, 8] (smooth cylinder,
    Blevins 1990).

    Args:
        U: Flow velocity [m/s].
        f_n: Natural frequency of the riser mode [Hz]. Must be positive.
        D: Riser outer diameter [m]. Must be positive.

    Returns:
        Reduced velocity Vr (dimensionless).

    Raises:
        ValueError: If f_n <= 0 or D <= 0.
    """
    if f_n <= 0.0:
        raise ValueError(f"Natural frequency must be positive, got {f_n}")
    if D <= 0.0:
        raise ValueError(f"Diameter must be positive, got {D}")
    return U / (f_n * D)


# ---------------------------------------------------------------------------
# VIV lock-in condition
# ---------------------------------------------------------------------------

def viv_lock_in(Vr: float) -> bool:
    """Determine whether VIV lock-in conditions are met.

    Lock-in occurs when the vortex shedding frequency synchronises with the
    structural natural frequency.  Conventional bounds: Vr in [4, 8].

    Args:
        Vr: Reduced velocity (dimensionless).

    Returns:
        True if Vr is within the lock-in range [4, 8], else False.
    """
    return _VR_LOCK_IN_LOW <= Vr <= _VR_LOCK_IN_HIGH


# ---------------------------------------------------------------------------
# VIV amplitude response  (Griffin curve / Vandiver correlation)
# ---------------------------------------------------------------------------

def viv_amplitude_response(Vr: float, Ks: float) -> float:
    """Cross-flow VIV amplitude response using the Griffin-Vandiver model.

    The Griffin curve (Griffin, 1980; Vandiver, 1993) gives the normalised
    steady-state cross-flow amplitude A/D as a function of reduced velocity
    and the mass-damping parameter (Skop-Griffin parameter) Ks.

    Outside lock-in: A/D = 0.
    Inside lock-in:  A/D = A_max / (1 + 0.21 * Ks^1.29)
    where A_max is the peak amplitude at the resonant reduced velocity,
    modelled here as a Gaussian centred at Vr = 6.0 with sigma = 1.5.

    Args:
        Vr: Reduced velocity (dimensionless).
        Ks: Mass-damping parameter (Skop-Griffin): Ks = 2 * pi^3 * St^2 * m* * zeta
            where m* = m / (rho * D^2) and zeta is the structural damping ratio.

    Returns:
        Non-dimensional cross-flow amplitude A/D (>= 0).
    """
    if not viv_lock_in(Vr):
        return 0.0

    # Peak A/D at resonance (Vandiver 1993, Eq 9)
    A_max_peak = 1.29 / (1.0 + 0.21 * Ks**1.29)

    # Gaussian envelope within lock-in band
    Vr_res = 6.0    # resonant reduced velocity
    sigma = 1.5
    envelope = math.exp(-0.5 * ((Vr - Vr_res) / sigma) ** 2)

    return float(A_max_peak * envelope)


# ---------------------------------------------------------------------------
# VIV fatigue damage  (S-N Palmgren-Miner rule, DNV RP-C203 D-curve)
# ---------------------------------------------------------------------------

def viv_fatigue_damage(
    stress_ranges: Sequence[float],
    cycle_counts: Sequence[int | float],
) -> float:
    """Cumulative VIV fatigue damage using the Palmgren-Miner rule.

    D = sum(n_i / N_i)

    N_i is taken from the DNV RP-C203 D-curve:
        log10(N_i) = log10(a) - m * log10(sigma_i_MPa)
    with log10(a) = 12.164 and m = 3.0.

    Args:
        stress_ranges: Sequence of stress range amplitudes [Pa].
        cycle_counts:  Corresponding number of cycles (n_i).

    Returns:
        Total Palmgren-Miner fatigue damage sum D (dimensionless).
        D >= 1.0 implies fatigue failure.

    Raises:
        ValueError: If lengths of stress_ranges and cycle_counts differ.
    """
    if len(stress_ranges) != len(cycle_counts):
        raise ValueError(
            f"stress_ranges length ({len(stress_ranges)}) must equal "
            f"cycle_counts length ({len(cycle_counts)})"
        )

    total_damage = 0.0
    for sigma_Pa, n_i in zip(stress_ranges, cycle_counts):
        if sigma_Pa <= 0.0 or n_i <= 0.0:
            continue
        sigma_MPa = sigma_Pa / 1e6
        log10_N = _SN_LOG10_A - _SN_M * math.log10(sigma_MPa)
        N_i = 10.0 ** log10_N
        total_damage += n_i / N_i

    return float(total_damage)


# ---------------------------------------------------------------------------
# Effective tension  (TNE012-1 — internal pressure effects on riser tension)
# ---------------------------------------------------------------------------

def effective_tension(
    T_wall: float,
    pi: float,
    pe: float,
    D: float,
    t: float,
) -> float:
    """Effective (Lagrangian) tension accounting for internal and external pressure.

    Per Sparks (1984) / TNE012-1:
        T_eff = T_wall - pi * A_i + pe * A_e

    where:
        A_i = pi * r_i^2  (internal cross-section area)
        A_e = pi * (D/2)^2 (external cross-section area)
        r_i = D/2 - t      (internal radius)

    The effective tension governs riser dynamics (natural frequency, buckling)
    whereas T_wall is the physical stress resultant in the pipe wall.

    Args:
        T_wall: Wall tension (true wall tension) [N].
        pi: Internal fluid pressure [Pa].
        pe: External hydrostatic pressure [Pa].
        D: Outer diameter [m].
        t: Wall thickness [m].

    Returns:
        Effective tension T_eff [N].
    """
    r_i = D / 2.0 - t
    A_i = math.pi * r_i**2
    A_e = math.pi * (D / 2.0) ** 2
    return float(T_wall - pi * A_i + pe * A_e)


# ---------------------------------------------------------------------------
# Riser natural frequency — pinned-pinned beam (Shear7 model)
# ---------------------------------------------------------------------------

def riser_natural_frequency(
    n: int,
    L: float,
    EI: float,
    m: float,
) -> float:
    """Natural frequency of mode n for a pinned-pinned uniform beam (riser).

    Shear7 / Euler-Bernoulli beam equation for pinned-pinned boundary conditions:
        f_n = (n / (2 * L)) * sqrt(EI / m)

    This is the pure bending natural frequency; for real risers the effective
    tension modifies this (see also Vandiver 1993). The formula is consistent
    with the Shear7 model input for mode shapes.

    Args:
        n: Mode number (positive integer, 1 = fundamental).
        L: Riser length [m]. Must be positive.
        EI: Bending stiffness [N.m^2].
        m: Mass per unit length [kg/m]. Must be positive.

    Returns:
        Natural frequency f_n [Hz].

    Raises:
        ValueError: If n < 1 or L <= 0 or m <= 0.
    """
    if n < 1:
        raise ValueError(f"Mode number n must be >= 1, got {n}")
    if L <= 0.0:
        raise ValueError(f"Riser length L must be positive, got {L}")
    if m <= 0.0:
        raise ValueError(f"Mass per unit length m must be positive, got {m}")

    return float((n / (2.0 * L)) * math.sqrt(EI / m))
