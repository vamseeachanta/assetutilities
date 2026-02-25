# ABOUTME: Steel Catenary Riser (SCR) fatigue calculations for deepwater applications.
# ABOUTME: Implements Allen 1995 VIV, Brooks 1987 screening, KC number, and TDZ fatigue.

"""Steel Catenary Riser (SCR) fatigue calculation module.

References:
- Allen, D.W. (1995) — Vortex-Induced Vibration Analysis of the Auger TLP, OTC.
- Brooks, I.H. (1987) — A Pragmatic Approach to Vortex-Induced Vibrations, OTC.
- OTC1997-8494 — Code Conflicts: pipeline codes for SCR design.
- OTC2001-13109 — SCR Fatigue at Low Keulegan-Carpenter Number.
"""

import math
from typing import List, Tuple

# Threshold reduced velocity for VIV onset (Brooks 1987)
_VR_ONSET = 4.0

# Brooks (1987) lock-in amplitude ratio A/D
_BROOKS_LOCK_IN_A_OVER_D = 0.9

# KC threshold below which soil interaction increases fatigue damage
_KC_SOIL_THRESHOLD = 10.0


def keulegan_carpenter_number(
    u_m: float,
    period: float,
    diameter: float,
) -> float:
    """Compute the Keulegan-Carpenter (KC) number for oscillatory flow.

    KC = U_m * T / D

    KC characterises the ratio of fluid particle displacement to pipe diameter
    in oscillatory flow. Low KC (< ~10) indicates drag-dominated flow where
    soil interaction effects on TDZ fatigue are significant (OTC2001-13109).

    Args:
        u_m: Maximum oscillatory flow velocity amplitude [m/s].
        period: Wave or oscillation period [s].
        diameter: Pipe outer diameter [m].

    Returns:
        Keulegan-Carpenter number (dimensionless).

    Raises:
        ValueError: If diameter or period are non-positive, or u_m is negative.
    """
    if diameter <= 0.0:
        raise ValueError(f"diameter must be positive; got {diameter}")
    if period <= 0.0:
        raise ValueError(f"period must be positive; got {period}")
    if u_m < 0.0:
        raise ValueError(f"u_m must be non-negative; got {u_m}")
    return float(u_m * period / diameter)


def soil_interaction_fatigue_factor(kc: float) -> float:
    """Compute the soil interaction fatigue correction factor for the TDZ.

    At low KC numbers (< 10) the soil-pipe interaction at the touch-down zone
    damps relative motion differently than at higher KC, leading to elevated
    effective stress ranges. This factor amplifies fatigue damage to account
    for that effect (OTC2001-13109).

    Factor model:
        kc >= 10  → factor = 1.0   (no correction)
        kc < 10   → factor = 1.0 + 0.5 * (1 - kc / 10)^2  (parabolic ramp)

    Args:
        kc: Keulegan-Carpenter number (dimensionless).

    Returns:
        Soil interaction correction factor (>= 1.0).

    Raises:
        ValueError: If kc is negative.
    """
    if kc < 0.0:
        raise ValueError(f"kc must be non-negative; got {kc}")
    if kc >= _KC_SOIL_THRESHOLD:
        return 1.0
    fraction = 1.0 - kc / _KC_SOIL_THRESHOLD
    return float(1.0 + 0.5 * fraction ** 2)


def fatigue_damage_tdz(
    stress_ranges: List[float],
    cycle_counts: List[float],
    kc_numbers: List[float],
    a_param: float,
    m_param: float,
) -> float:
    """Compute accumulated fatigue damage at the SCR touch-down zone (TDZ).

    Applies Miner's rule with a soil interaction correction for low KC regimes:
        N_fi = A / (Delta_sigma_i)^m / soil_factor_i
        D = sum(n_i / N_fi)

    The soil interaction factor amplifies damage for KC < 10 following
    the approach in OTC2001-13109.

    Args:
        stress_ranges: Hot-spot stress ranges per bin [Pa or consistent units].
        cycle_counts: Applied cycle count per bin.
        kc_numbers: Keulegan-Carpenter number for each bin.
        a_param: S-N curve intercept constant A.
        m_param: S-N curve slope exponent m.

    Returns:
        Total Miner's damage sum (dimensionless).

    Raises:
        ValueError: If input lists have different lengths.
    """
    if not (len(stress_ranges) == len(cycle_counts) == len(kc_numbers)):
        raise ValueError(
            "stress_ranges, cycle_counts, and kc_numbers must have the same length; "
            f"got {len(stress_ranges)}, {len(cycle_counts)}, {len(kc_numbers)}"
        )
    damage = 0.0
    for sigma, n_i, kc in zip(stress_ranges, cycle_counts, kc_numbers):
        soil_factor = soil_interaction_fatigue_factor(kc)
        n_f = a_param / (sigma ** m_param)
        damage += n_i / n_f * soil_factor
    return float(damage)


def scr_sn_fatigue_life(
    sigma_a: float,
    a_param: float,
    m_param: float,
) -> float:
    """Compute the S-N fatigue life for an SCR stress amplitude.

    The stress range is double the amplitude:
        Delta_sigma = 2 * sigma_a
        N_f = A / (Delta_sigma)^m

    Args:
        sigma_a: Stress amplitude (half range) [Pa or consistent units].
        a_param: S-N curve intercept constant A.
        m_param: S-N curve slope exponent m.

    Returns:
        Number of cycles to failure N_f.

    Raises:
        ValueError: If sigma_a or a_param are non-positive.
    """
    if sigma_a <= 0.0:
        raise ValueError(f"sigma_a must be positive; got {sigma_a}")
    if a_param <= 0.0:
        raise ValueError(f"a_param must be positive; got {a_param}")
    delta_sigma = 2.0 * sigma_a
    n_f = a_param / (delta_sigma ** m_param)
    return float(n_f)


def allen_viv_amplitude_ratio(vr: float) -> float:
    """Predict VIV amplitude ratio A/D for an SCR using Allen's (1995) curve fit.

    Piecewise linear model fitted to Allen's Auger TLP riser VIV data:
        Vr < 4.0               → A/D = 0.0  (no lock-in)
        4.0 <= Vr <= 8.0       → A/D = 0.2 * (Vr - 4.0)  (linear onset)
        Vr > 8.0               → A/D = 0.8  (saturation)

    The reduced velocity Vr = U / (f_n * D) where U is the current speed,
    f_n is the riser natural frequency, and D is the diameter.

    Args:
        vr: Reduced velocity (dimensionless).

    Returns:
        VIV amplitude-to-diameter ratio A/D (dimensionless).

    Raises:
        ValueError: If vr is negative.
    """
    if vr < 0.0:
        raise ValueError(f"vr must be non-negative; got {vr}")
    if vr < 4.0:
        return 0.0
    if vr <= 8.0:
        return float(0.2 * (vr - 4.0))
    return 0.8


def brooks_viv_screening(vr: float) -> Tuple[bool, float]:
    """Apply Brooks' (1987) pragmatic VIV screening criterion for SCRs.

    Screening rule:
        Vr <= 4.0  → no VIV risk; A/D = 0.0
        Vr > 4.0   → potential VIV; A/D ≈ 0.9 (lock-in estimate)

    Brooks' lock-in amplitude of A/D ≈ 0.9 is a conservative upper-bound
    estimate used for initial screening of deepwater riser designs.

    Args:
        vr: Reduced velocity Vr = U / (f_n * D) (dimensionless).

    Returns:
        Tuple of (viv_risk: bool, a_over_d: float).
        viv_risk is True when Vr > 4.0.
        a_over_d is the predicted amplitude ratio.

    Raises:
        ValueError: If vr is negative.
    """
    if vr < 0.0:
        raise ValueError(f"vr must be non-negative; got {vr}")
    if vr > _VR_ONSET:
        return True, float(_BROOKS_LOCK_IN_A_OVER_D)
    return False, 0.0
