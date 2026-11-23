# ABOUTME: Unit conversion functions for engineering quantities.
# ABOUTME: All conversions are exact or traceable to NIST / SI definitions.

from assetutilities.constants import RHO_SEAWATER, G

# ---------------------------------------------------------------------------
# Pressure conversions
# Reference: NIST SP 811; 1 psi = 6894.757293... Pa (exact)
# ---------------------------------------------------------------------------

_PSI_PER_MPA = 145.0377438  # psi per MPa (1 MPa / 6894.757293e-6 MPa)
_MPA_PER_PSI = 1.0 / _PSI_PER_MPA


def psi_to_mpa(psi: float) -> float:
    """Convert pounds per square inch to megapascals."""
    return psi * _MPA_PER_PSI


def mpa_to_psi(mpa: float) -> float:
    """Convert megapascals to pounds per square inch."""
    return mpa * _PSI_PER_MPA


def bar_to_mpa(bar: float) -> float:
    """Convert bar to megapascals. 1 bar = 0.1 MPa (exact)."""
    return bar * 0.1


def mpa_to_bar(mpa: float) -> float:
    """Convert megapascals to bar. 1 MPa = 10 bar (exact)."""
    return mpa * 10.0


def kpa_to_psi(kpa: float) -> float:
    """Convert kilopascals to pounds per square inch."""
    return mpa_to_psi(kpa / 1000.0)


def psi_to_kpa(psi: float) -> float:
    """Convert pounds per square inch to kilopascals."""
    return psi_to_mpa(psi) * 1000.0


# ---------------------------------------------------------------------------
# Length conversions
# Reference: 1 international foot = 0.3048 m (exact, ISO 31-1)
# ---------------------------------------------------------------------------

_M_PER_FT = 0.3048    # exact
_FT_PER_M = 1.0 / _M_PER_FT

_MM_PER_INCH = 25.4   # exact
_INCH_PER_MM = 1.0 / _MM_PER_INCH


def ft_to_m(ft: float) -> float:
    """Convert feet to metres."""
    return ft * _M_PER_FT


def m_to_ft(m: float) -> float:
    """Convert metres to feet."""
    return m * _FT_PER_M


def inch_to_mm(inch: float) -> float:
    """Convert inches to millimetres."""
    return inch * _MM_PER_INCH


def mm_to_inch(mm: float) -> float:
    """Convert millimetres to inches."""
    return mm * _INCH_PER_MM


# ---------------------------------------------------------------------------
# Force conversions
# Reference: 1 lbf = 4.4482216152605 N (exact, NIST)
#            1 kip = 1000 lbf
# ---------------------------------------------------------------------------

_N_PER_LBF = 4.4482216152605
_LBF_PER_N = 1.0 / _N_PER_LBF
_KN_PER_KIP = _N_PER_LBF   # 1 kip = 1000 lbf; 1 kip/kN = 4.4482... kN/kip


def n_to_kn(n: float) -> float:
    """Convert newtons to kilonewtons."""
    return n / 1000.0


def kn_to_n(kn: float) -> float:
    """Convert kilonewtons to newtons."""
    return kn * 1000.0


def n_to_lbf(n: float) -> float:
    """Convert newtons to pound-force."""
    return n * _LBF_PER_N


def lbf_to_n(lbf: float) -> float:
    """Convert pound-force to newtons."""
    return lbf * _N_PER_LBF


def kn_to_kip(kn: float) -> float:
    """Convert kilonewtons to kips (1 kip = 1000 lbf = 4.44822 kN)."""
    return kn / _KN_PER_KIP


def kip_to_kn(kip: float) -> float:
    """Convert kips to kilonewtons."""
    return kip * _KN_PER_KIP


# ---------------------------------------------------------------------------
# Mass conversions
# Reference: 1 lb = 0.45359237 kg (exact, NIST)
#            1 metric tonne = 1000 kg (exact)
#            1 short ton = 2000 lb
# ---------------------------------------------------------------------------

_KG_PER_LB = 0.45359237
_LB_PER_KG = 1.0 / _KG_PER_LB
_KG_PER_SHORT_TON = 2000.0 * _KG_PER_LB  # 907.18474 kg


def kg_to_lb(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * _LB_PER_KG


def lb_to_kg(lb: float) -> float:
    """Convert pounds to kilograms."""
    return lb * _KG_PER_LB


def kg_to_tonne(kg: float) -> float:
    """Convert kilograms to metric tonnes."""
    return kg / 1000.0


def tonne_to_kg(tonne: float) -> float:
    """Convert metric tonnes to kilograms."""
    return tonne * 1000.0


def tonne_to_short_ton(tonne: float) -> float:
    """Convert metric tonnes to short tons (US tons)."""
    return tonne_to_kg(tonne) / _KG_PER_SHORT_TON


def short_ton_to_tonne(short_ton: float) -> float:
    """Convert short tons (US tons) to metric tonnes."""
    return short_ton * _KG_PER_SHORT_TON / 1000.0


# ---------------------------------------------------------------------------
# Temperature conversions
# Reference: T(°F) = T(°C) * 9/5 + 32; T(K) = T(°C) + 273.15
# ---------------------------------------------------------------------------

def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert degrees Celsius to Fahrenheit."""
    return celsius * 9.0 / 5.0 + 32.0


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert degrees Fahrenheit to Celsius."""
    return (fahrenheit - 32.0) * 5.0 / 9.0


def celsius_to_kelvin(celsius: float) -> float:
    """Convert degrees Celsius to Kelvin."""
    return celsius + 273.15


def kelvin_to_celsius(kelvin: float) -> float:
    """Convert Kelvin to degrees Celsius."""
    return kelvin - 273.15


# ---------------------------------------------------------------------------
# Offshore utility
# ---------------------------------------------------------------------------

def depth_to_pressure_kpa(depth_m: float) -> float:
    """Return gauge hydrostatic pressure (kPa) at given seawater depth.

    Uses standard seawater density (1025 kg/m³) and g = 9.81 m/s².
    Result is gauge pressure (zero at surface).
    Reference: DNV-RP-C205 Section 3.
    """
    return RHO_SEAWATER * G * depth_m / 1000.0
