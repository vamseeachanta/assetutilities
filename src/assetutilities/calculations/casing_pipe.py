# ABOUTME: Casing and tubing pipe strength calculations per API 5C3 / ISO TR 10400.
# ABOUTME: Implements burst, collapse, tensile ratings for oil-country tubular goods (OCTG).

"""
Casing/Tubing Pipe Strength Calculations
=========================================
Standards covered:
  - API BULL 5C3: Formulas and Calculations for Casing, Tubing, Drill & Line Pipe
  - API TR 5C3 (2008): Technical Report on Equations and Calculations for Casing,
    Tubing, and Line Pipe Used as Casing or Tubing
  - ISO TR 10400, 1st Ed (2007): Equations and calculations for the properties of
    casing, tubing, drill pipe and line pipe used as casing or tubing

All pressures are in psi, forces in lbf, dimensions in inches unless noted.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Pipe grade definitions (yield strength in psi)
# ---------------------------------------------------------------------------

class PipeGrade(Enum):
    """API/ISO pipe grades with minimum yield strength in psi."""

    J55 = 55_000
    K55 = 55_000
    N80 = 80_000
    L80 = 80_000
    C90 = 90_000
    C95 = 95_000
    T95 = 95_000
    P110 = 110_000
    Q125 = 125_000

    @property
    def yield_strength_psi(self) -> float:
        """Minimum yield strength in psi."""
        return float(self.value)


# ---------------------------------------------------------------------------
# Pipe geometry dataclass
# ---------------------------------------------------------------------------

@dataclass
class CasingPipeProperties:
    """Geometric and material properties of a casing or tubing string."""

    od_in: float
    """Nominal outside diameter, inches."""

    wall_thickness_in: float
    """Nominal wall thickness, inches."""

    grade: PipeGrade
    """API/ISO pipe grade (sets yield strength)."""

    @property
    def id_in(self) -> float:
        """Inside diameter, inches: ID = OD - 2*t."""
        return self.od_in - 2.0 * self.wall_thickness_in

    @property
    def cross_sectional_area_in2(self) -> float:
        """Steel cross-sectional area, in²: A = π/4 * (OD² - ID²)."""
        return math.pi / 4.0 * (self.od_in**2 - self.id_in**2)

    @property
    def dt_ratio(self) -> float:
        """Diameter-to-thickness ratio: OD / t."""
        return self.od_in / self.wall_thickness_in


# ---------------------------------------------------------------------------
# Ratings output dataclass
# ---------------------------------------------------------------------------

@dataclass
class CasingPipeRatings:
    """Consolidated strength ratings for a casing/tubing pipe."""

    burst_psi: float
    """Internal pressure at burst (Barlow formula), psi."""

    collapse_psi: float
    """External pressure at collapse (API 5C3 regime), psi."""

    tensile_yield_lbf: float
    """Axial tensile yield strength of pipe body, lbf."""

    temperature_f: float
    """Service temperature used for derating, °F."""

    derating_factor: float
    """Temperature derating factor applied to burst and tensile ratings."""


# ---------------------------------------------------------------------------
# Burst pressure rating (API 5C3 / ISO TR 10400)
# ---------------------------------------------------------------------------

def burst_pressure_rating(pipe: CasingPipeProperties) -> float:
    """
    API 5C3 / ISO TR 10400 burst pressure rating using the Barlow formula.

    P_burst = 0.875 * (2 * Yp * t) / OD

    The factor 0.875 accounts for the permissible wall-thickness under-tolerance
    (87.5 % of nominal wall per API Spec 5CT).

    Args:
        pipe: Casing/tubing geometric and material properties.

    Returns:
        Burst pressure rating in psi.
    """
    yp = pipe.grade.yield_strength_psi
    t = pipe.wall_thickness_in
    od = pipe.od_in
    return 0.875 * (2.0 * yp * t) / od


# ---------------------------------------------------------------------------
# Collapse pressure rating (API 5C3 / ISO TR 10400)
# ---------------------------------------------------------------------------

# API 5C3 Table 1 coefficients for collapse regimes (N-80 representative)
# Full implementation uses D/t-based regime switching per the standard.
_COLLAPSE_COEFFICIENTS = {
    # regime: (F, G) — used in transitional formula Pc = Yp*(F/D_t - G)
    "yield":        None,          # handled separately
    "plastic":      (2.066, 0.0532),
    "transitional": (None, None),  # computed from plastic/elastic boundary
    "elastic":      None,          # handled separately
}

# API 5C3 elastic collapse constants
_ELASTIC_COLLAPSE_CONST = 46.95e6   # psi — empirical constant for steel

# Regime boundary D/t values for N-80 (representative; exact values vary by grade)
# Boundaries are computed from API 5C3 equations; these are nominal defaults.
_YIELD_PLASTIC_DT = {
    55_000: 15.24,
    80_000: 13.38,
    95_000: 12.44,
    110_000: 11.84,
    125_000: 11.09,
}
_TRANSITIONAL_ELASTIC_DT = {
    55_000: 37.21,
    80_000: 32.05,
    95_000: 29.18,
    110_000: 27.01,
    125_000: 25.01,
}


def _nearest_dt_boundary(yp: float, table: dict) -> float:
    """Return the D/t boundary for the closest yield strength in a table."""
    keys = sorted(table.keys())
    closest = min(keys, key=lambda k: abs(k - yp))
    return table[closest]


def _yield_collapse_pressure(yp: float, dt_ratio: float) -> float:
    """API 5C3 yield-strength collapse: Pyc = 2*Yp*(D/t-1)/(D/t)²."""
    return 2.0 * yp * (dt_ratio - 1.0) / dt_ratio**2


def _elastic_collapse_pressure(dt_ratio: float) -> float:
    """API 5C3 elastic collapse (Lame): Pe = 46.95e6 / (D/t*(D/t-1)²)."""
    return _ELASTIC_COLLAPSE_CONST / (dt_ratio * (dt_ratio - 1.0) ** 2)


def _plastic_collapse_pressure(yp: float, dt_ratio: float) -> float:
    """
    API 5C3 plastic collapse:
      Pp = Yp * (A / (D/t) - B) - C
    where A, B, C are grade-dependent coefficients from API 5C3 Table C1.

    Coefficients here are the standard published values for selected grades.
    For unlisted grades, the nearest published grade is used.
    """
    _plastic_abc = {
        55_000:  (2.991, 0.0541, 1206),
        80_000:  (3.071, 0.0667, 1955),
        95_000:  (3.124, 0.0743, 2426),
        110_000: (3.181, 0.0819, 2955),
        125_000: (3.239, 0.0895, 3501),
    }
    keys = sorted(_plastic_abc.keys())
    closest_yp = min(keys, key=lambda k: abs(k - yp))
    a, b, c = _plastic_abc[closest_yp]
    return yp * (a / dt_ratio - b) - c


def _transitional_collapse_pressure(yp: float, dt_ratio: float) -> float:
    """
    API 5C3 transitional collapse:
      Pt = Yp * (F / (D/t) - G)
    where F and G are grade-dependent coefficients interpolated between
    plastic and elastic regimes.
    """
    _trans_fg = {
        55_000:  (2.066, 0.0532),
        80_000:  (1.998, 0.0434),
        95_000:  (1.989, 0.0426),
        110_000: (1.994, 0.0430),
        125_000: (2.009, 0.0445),
    }
    keys = sorted(_trans_fg.keys())
    closest_yp = min(keys, key=lambda k: abs(k - yp))
    f, g = _trans_fg[closest_yp]
    return yp * (f / dt_ratio - g)


def collapse_pressure_rating(pipe: CasingPipeProperties) -> float:
    """
    API 5C3 / ISO TR 10400 collapse pressure rating.

    Selects the appropriate collapse regime (yield-strength, plastic,
    transitional, elastic) based on the pipe D/t ratio and grade.

    Args:
        pipe: Casing/tubing geometric and material properties.

    Returns:
        Collapse pressure rating in psi.
    """
    yp = pipe.grade.yield_strength_psi
    dt = pipe.dt_ratio

    dt_yp = _nearest_dt_boundary(yp, _YIELD_PLASTIC_DT)
    dt_te = _nearest_dt_boundary(yp, _TRANSITIONAL_ELASTIC_DT)

    # Transitional/plastic boundary: computed from plastic = transitional equality
    # For simplicity, use API 5C3 representative split at midpoint.
    dt_pt = dt_yp + (dt_te - dt_yp) * 0.45  # approximate plastic-to-transitional

    if dt <= dt_yp:
        return _yield_collapse_pressure(yp, dt)
    elif dt <= dt_pt:
        return _plastic_collapse_pressure(yp, dt)
    elif dt <= dt_te:
        return _transitional_collapse_pressure(yp, dt)
    else:
        return _elastic_collapse_pressure(dt)


# ---------------------------------------------------------------------------
# Axial tensile yield strength
# ---------------------------------------------------------------------------

def axial_tensile_yield_strength(pipe: CasingPipeProperties) -> float:
    """
    Axial tensile yield strength of the pipe body.

    F_yield = Yp * A_s

    where A_s is the steel cross-sectional area.

    Args:
        pipe: Casing/tubing geometric and material properties.

    Returns:
        Axial tensile yield force in lbf.
    """
    return pipe.grade.yield_strength_psi * pipe.cross_sectional_area_in2


# ---------------------------------------------------------------------------
# Wall thickness for a given design pressure
# ---------------------------------------------------------------------------

def wall_thickness_for_design_pressure(
    od_in: float,
    design_pressure_psi: float,
    grade: PipeGrade,
) -> float:
    """
    Required wall thickness to meet a burst design pressure.

    Rearranges the Barlow formula:
      t = P * OD / (0.875 * 2 * Yp)

    Args:
        od_in: Pipe outside diameter, inches.
        design_pressure_psi: Target burst design pressure, psi.
        grade: Pipe grade (sets yield strength).

    Returns:
        Required wall thickness in inches.
    """
    yp = grade.yield_strength_psi
    return (design_pressure_psi * od_in) / (0.875 * 2.0 * yp)


# ---------------------------------------------------------------------------
# Temperature derating factor
# ---------------------------------------------------------------------------

def temperature_derating_factor(temperature_f: float) -> float:
    """
    Yield strength derating factor as a function of temperature.

    Based on API TR 5C3 / ISO TR 10400 guidance for carbon and low-alloy steel.
    At ambient (≤ 200 °F) the factor is 1.0.  Above 200 °F a linear reduction
    is applied per common industry practice for L-80/N-80 grade steel:
      - 200 °F → 1.000
      - 300 °F → 0.970
      - 400 °F → 0.940
    Values are linearly interpolated / extrapolated.

    Args:
        temperature_f: Service temperature in degrees Fahrenheit.

    Returns:
        Dimensionless derating factor in the range (0, 1].
    """
    if temperature_f <= 200.0:
        return 1.0
    # Linear reduction: 1% per 33.3 °F above 200 °F (approximately)
    reduction_rate = 0.03 / 100.0  # 3 % per 100 °F
    excess = temperature_f - 200.0
    factor = 1.0 - reduction_rate * excess
    return max(factor, 0.01)  # prevent nonsensical zero/negative values


# ---------------------------------------------------------------------------
# Convenience wrapper: rate_casing_pipe
# ---------------------------------------------------------------------------

def rate_casing_pipe(
    pipe: CasingPipeProperties,
    temperature_f: float = 70.0,
) -> CasingPipeRatings:
    """
    Compute all strength ratings for a casing/tubing pipe at a given temperature.

    Applies the API 5C3 / ISO TR 10400 temperature derating factor to both
    the burst and tensile ratings.  Collapse pressure is returned at ambient
    conditions (temperature effects on collapse are minor and not standardised
    in API 5C3).

    Args:
        pipe: Casing/tubing geometric and material properties.
        temperature_f: Service temperature in degrees Fahrenheit (default 70 °F).

    Returns:
        CasingPipeRatings with burst, collapse, and tensile values.
    """
    derating = temperature_derating_factor(temperature_f)

    raw_burst = burst_pressure_rating(pipe)
    raw_tensile = axial_tensile_yield_strength(pipe)
    collapse = collapse_pressure_rating(pipe)

    return CasingPipeRatings(
        burst_psi=raw_burst * derating,
        collapse_psi=collapse,
        tensile_yield_lbf=raw_tensile * derating,
        temperature_f=temperature_f,
        derating_factor=derating,
    )
