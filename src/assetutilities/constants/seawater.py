# ABOUTME: Seawater density and viscosity as functions of temperature and salinity.
# ABOUTME: Density: simplified UNESCO 1980 / IES 80. Viscosity: ITTC 2011 formula.

"""Seawater property functions for offshore engineering calculations.

Density uses a simplified form of the UNESCO 1980 international equation of
state for seawater (IES 80), valid for:
  - Temperature: 0°C to 40°C
  - Salinity:    0 to 42 ppt (g/kg)
  - Pressure:    surface (0 dbar)

Viscosity uses the ITTC 2011 recommended procedure (7.5-02-01-03) which is
referenced by API RP 2A and many offshore hydrodynamic codes.

References:
    Fofonoff & Millard (1983). "Algorithms for the Computation of Fundamental
    Properties of Seawater." UNESCO Technical Papers in Marine Science No. 44.

    ITTC (2011). "ITTC Recommended Procedures and Guidelines: Fresh Water
    and Seawater Properties." ITTC 7.5-02-01-03 Rev 02.
"""


def seawater_density(temperature_c: float, salinity_ppt: float) -> float:
    """Return seawater density in kg/m³ at the given temperature and salinity.

    Uses the simplified UNESCO 1980 surface-pressure equation of state for
    seawater (IES 80), valid at 0 dbar (sea surface).

    Args:
        temperature_c:  Water temperature in degrees Celsius (0 to 40 °C).
        salinity_ppt:   Practical salinity in parts per thousand (0 to 42 ppt).

    Returns:
        Density in kg/m³.

    References:
        Fofonoff & Millard (1983), UNESCO Technical Papers No. 44.
    """
    t = temperature_c
    s = salinity_ppt

    # Pure water density (IES 80, Eq. 13)
    rho_w = (
        999.842594
        + 6.793952e-2 * t
        - 9.095290e-3 * t ** 2
        + 1.001685e-4 * t ** 3
        - 1.120083e-6 * t ** 4
        + 6.536332e-9 * t ** 5
    )

    # Salinity correction terms (IES 80, Eq. 13 continued)
    a = (
        8.24493e-1
        - 4.0899e-3 * t
        + 7.6438e-5 * t ** 2
        - 8.2467e-7 * t ** 3
        + 5.3875e-9 * t ** 4
    )
    b = -5.72466e-3 + 1.0227e-4 * t - 1.6546e-6 * t ** 2
    c = 4.8314e-4

    return float(rho_w + a * s + b * s ** 1.5 + c * s ** 2)


def seawater_dynamic_viscosity(
    temperature_c: float, salinity_ppt: float
) -> float:
    """Return seawater dynamic viscosity in Pa·s at the given temperature and salinity.

    Uses the ISO/ITTC 2011 recommended formula:

    Pure water viscosity (ISO-recommended polynomial, from ITTC 7.5-02-01-03):
        μ_w = 4.2844e-5 + 1 / (0.157 * (T + 64.993)² - 91.296)   [Pa·s]
    where T is in degrees Celsius.  Accurate to within ±0.3 % for 0–40°C.

    Salinity correction (Millero 1974 linear fit, calibrated at S=35 ppt):
        μ_sw = μ_w * (1 + 0.001270 * S)
    where S is salinity in ppt.  Accurate at typical ocean salinities (0–42 ppt).

    Args:
        temperature_c:  Water temperature in degrees Celsius (0 to 40 °C).
        salinity_ppt:   Practical salinity in parts per thousand (0 to 42 ppt).

    Returns:
        Dynamic viscosity in Pa·s.

    References:
        ITTC (2011), "Fresh Water and Seawater Properties," 7.5-02-01-03 Rev 02.
        Millero (1974), "The physical chemistry of seawater," Ann. Rev. Earth
        Planet. Sci. 2, 101–150.
    """
    t = temperature_c
    s = salinity_ppt

    # Pure water dynamic viscosity (ISO/ITTC polynomial)
    mu_w = 4.2844e-5 + 1.0 / (0.157 * (t + 64.993) ** 2 - 91.296)

    # Salinity correction factor (Millero 1974, calibrated to ITTC 2011 Table 1)
    salinity_factor = 1.0 + 0.001270 * s

    return float(mu_w * salinity_factor)


def seawater_kinematic_viscosity(
    temperature_c: float, salinity_ppt: float
) -> float:
    """Return seawater kinematic viscosity in m²/s at the given temperature and salinity.

    Computed as ν = μ / ρ using the dynamic viscosity and density functions
    defined in this module.

    Args:
        temperature_c:  Water temperature in degrees Celsius (0 to 40 °C).
        salinity_ppt:   Practical salinity in parts per thousand (0 to 42 ppt).

    Returns:
        Kinematic viscosity in m²/s.
    """
    mu = seawater_dynamic_viscosity(
        temperature_c=temperature_c, salinity_ppt=salinity_ppt
    )
    rho = seawater_density(
        temperature_c=temperature_c, salinity_ppt=salinity_ppt
    )
    return float(mu / rho)
