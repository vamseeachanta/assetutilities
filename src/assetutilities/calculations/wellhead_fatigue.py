# ABOUTME: Wellhead and conductor fatigue calculations from OTC deepwater drilling literature.
# ABOUTME: Implements Chen 1989 S-N fatigue, Sweeney 1991 HPHT effective stress, Allen 1998 VIV, Denison 1997 Mars TLP, Britton 1987.

"""
Wellhead and Conductor Fatigue Calculations
============================================
References:
  - Chen, W.C. 1989 - Fatigue Life Predictions for Threaded TLP (OTC)
  - Sweeney, T., et al, 1991 - Behaviour of 15ksi Subsea Wellhead (OTC)
  - Allen, D.W., 1998 - Vortex-Induced Vibration of Deepwater Risers (OTC)
  - Denison, E.B., et al, 1997 - Mars TLP Drilling and Production (OTC)
  - Britton, J.S., et al, 1987 - Improving Wellhead Performance (OTC)

All stress values in psi, forces in lbf, stiffness in consistent units.
"""

import math

# Seconds in a year (365.25 days)
_SECONDS_PER_YEAR: float = 365.25 * 24.0 * 3600.0


def sn_cycles_to_failure(
    delta_sigma: float,
    A: float,
    m: float,
) -> float:
    """Compute cycles to failure using the S-N (Wohler) relationship.

    Per Chen (1989): N_f = A / (Delta_sigma)^m

    Args:
        delta_sigma: Stress range in psi. Must be positive.
        A: S-N curve intercept parameter.
        m: S-N curve slope exponent.

    Returns:
        N_f: Number of cycles to failure.

    Raises:
        ValueError: If delta_sigma is not positive.
    """
    if delta_sigma <= 0.0:
        raise ValueError(
            f"delta_sigma must be positive, got {delta_sigma}"
        )
    return A / (delta_sigma ** m)


def fatigue_life_years(
    n_f: float,
    cycles_per_year: float,
) -> float:
    """Convert cycles-to-failure to fatigue life in years.

    life = N_f / cycles_per_year

    Args:
        n_f: Cycles to failure from S-N curve.
        cycles_per_year: Annual cycle count from loading spectrum.

    Returns:
        Fatigue life in years.

    Raises:
        ValueError: If cycles_per_year is not positive.
    """
    if cycles_per_year <= 0.0:
        raise ValueError(
            f"cycles_per_year must be positive, got {cycles_per_year}"
        )
    return n_f / cycles_per_year


def annual_fatigue_damage(
    n_applied: float,
    n_f: float,
) -> float:
    """Compute single-block Palmgren-Miner fatigue damage fraction.

    D = n_applied / N_f

    Args:
        n_applied: Number of cycles applied in the period.
        n_f: Cycles to failure at the corresponding stress range.

    Returns:
        Damage fraction (D = 1.0 at failure).

    Raises:
        ValueError: If n_f is not positive.
    """
    if n_f <= 0.0:
        raise ValueError(f"n_f must be positive, got {n_f}")
    return n_applied / n_f


def accumulate_fatigue_damage(
    blocks: list[tuple[float, float]],
) -> float:
    """Accumulate Palmgren-Miner fatigue damage over multiple stress blocks.

    D_total = sum(n_i / N_fi) for all blocks.

    Args:
        blocks: List of (n_applied, n_f) tuples per stress block.

    Returns:
        Total accumulated damage fraction.
    """
    total = 0.0
    for n_applied, n_f in blocks:
        total += annual_fatigue_damage(n_applied, n_f)
    return total


def sweeney_effective_stress(
    sigma_hoop: float,
    sigma_axial: float,
) -> float:
    """Compute von Mises effective stress for HPHT wellhead per Sweeney (1991).

    For 15ksi subsea wellheads under biaxial loading:
      sigma_eff = sqrt(sigma_hoop^2 - sigma_hoop*sigma_axial + sigma_axial^2)

    Args:
        sigma_hoop: Hoop (circumferential) stress in psi.
        sigma_axial: Axial stress in psi.

    Returns:
        Effective (von Mises equivalent) stress in psi.
    """
    val = sigma_hoop**2 - sigma_hoop * sigma_axial + sigma_axial**2
    return math.sqrt(val)


def viv_wellhead_fatigue_damage(
    viv_stress_range_psi: float,
    viv_frequency_hz: float,
    exposure_years: float,
    A: float,
    m: float,
) -> float:
    """Compute VIV-induced wellhead fatigue damage over an exposure period.

    Per Allen (1998), VIV causes sustained sinusoidal stress cycling:
      n_applied = viv_frequency_hz * exposure_years * seconds_per_year
      N_f = A / (delta_sigma)^m
      D = n_applied / N_f

    Args:
        viv_stress_range_psi: VIV-induced stress range at wellhead in psi.
        viv_frequency_hz: VIV frequency in Hz.
        exposure_years: Duration of VIV exposure in years.
        A: S-N curve intercept parameter.
        m: S-N curve slope exponent.

    Returns:
        Accumulated fatigue damage fraction from VIV loading.
    """
    n_applied = viv_frequency_hz * exposure_years * _SECONDS_PER_YEAR
    if n_applied == 0.0:
        return 0.0
    n_f = sn_cycles_to_failure(viv_stress_range_psi, A, m)
    return n_applied / n_f


def denison_conductor_tensioner_load(
    pretension_kips: float,
    viv_amplification: float,
    hydrodynamic_load_kips: float,
) -> float:
    """Compute conductor tensioner design load per Denison (1997) Mars TLP method.

    The tensioner must sustain pretension plus VIV-amplified hydrodynamic loading:
      T_design = pretension + viv_amplification * hydrodynamic_load

    Args:
        pretension_kips: Conductor tensioner pretension in kips.
        viv_amplification: Amplification factor on hydrodynamic load due to VIV.
        hydrodynamic_load_kips: Baseline hydrodynamic load per conductor in kips.

    Returns:
        Tensioner design load in kips.
    """
    return pretension_kips + viv_amplification * hydrodynamic_load_kips


def britton_fatigue_life_multiplier(
    baseline_stiffness: float,
    reduced_stiffness: float,
    m: float,
) -> float:
    """Compute fatigue life improvement multiplier from flex joint stiffness reduction.

    Per Britton (1987), reducing flex joint rotational stiffness decreases bending
    stress at the wellhead. Since bending moment and stress are proportional to
    stiffness, the life multiplier follows from the S-N relationship:

      sigma_new / sigma_base = reduced_stiffness / baseline_stiffness
      multiplier = N_new / N_base = (sigma_base / sigma_new)^m
                 = (baseline_stiffness / reduced_stiffness)^m

    Args:
        baseline_stiffness: Original flex joint rotational stiffness.
        reduced_stiffness: Improved (lower) flex joint stiffness. Must be positive.
        m: S-N curve slope exponent.

    Returns:
        Fatigue life multiplier (> 1 when reduced_stiffness < baseline_stiffness).

    Raises:
        ValueError: If reduced_stiffness is not positive.
    """
    if reduced_stiffness <= 0.0:
        raise ValueError(
            f"reduced_stiffness must be positive, got {reduced_stiffness}"
        )
    return (baseline_stiffness / reduced_stiffness) ** m
