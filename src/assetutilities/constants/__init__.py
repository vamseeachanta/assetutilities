# ABOUTME: Shared engineering constants for offshore/structural calculations.
# ABOUTME: Sources: API RP 2A, DNV-RP-C205, EN 1993, ASTM, ISO 80000-3.

import math

# ---------------------------------------------------------------------------
# Mathematical / fundamental
# ---------------------------------------------------------------------------

PI = math.pi          # dimensionless
E = math.e            # dimensionless (Euler's number)

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

G = 9.81              # m/s² — gravitational acceleration (nominal)
G_PRECISE = 9.80665   # m/s² — standard gravity (ISO 80000-3)

STD_ATMOSPHERE_KPA = 101.325  # kPa — standard atmosphere (ISO 2533 / ICAO)

# ---------------------------------------------------------------------------
# Fluid properties — seawater
# Reference: API RP 2A-WSD, DNV-RP-C205 Section 3
# ---------------------------------------------------------------------------

RHO_SEAWATER = 1025.0    # kg/m³ — at 15°C, salinity 35 ppt
RHO_FRESHWATER = 1000.0  # kg/m³ — at 4°C

# Crude oil density range (light to heavy crude)
RHO_CRUDE_OIL_MIN = 700.0   # kg/m³ — light crude / condensate
RHO_CRUDE_OIL_MAX = 900.0   # kg/m³ — heavy crude

# ---------------------------------------------------------------------------
# Steel material properties
# References: EN 10025-2, ASTM A36, API 5L, EN 1993-1-1
# ---------------------------------------------------------------------------

E_STEEL = 207e9       # Pa  — Young's modulus (carbon steel)
NU_STEEL = 0.30       # —   — Poisson's ratio
RHO_STEEL = 7850.0    # kg/m³ — density
ALPHA_STEEL = 11.7e-6 # /°C  — coefficient of thermal expansion (EN 1993)
G_STEEL = E_STEEL / (2.0 * (1.0 + NU_STEEL))  # Pa — shear modulus

# Yield strengths by grade (minimum specified)
FY_A36 = 250e6   # Pa — ASTM A36 structural steel
FY_X52 = 358e6   # Pa — API 5L Grade X52 (52 ksi line pipe)
FY_X65 = 448e6   # Pa — API 5L Grade X65 (65 ksi line pipe)
FY_X70 = 483e6   # Pa — API 5L Grade X70 (70 ksi line pipe)
FY_X80 = 552e6   # Pa — API 5L Grade X80 (80 ksi line pipe)

# ---------------------------------------------------------------------------
# Concrete properties
# Reference: EN 1992-1-1, DNV-OS-J101
# ---------------------------------------------------------------------------

RHO_CONCRETE_NORMAL = 2400.0  # kg/m³ — normal weight reinforced concrete
RHO_CONCRETE_MARINE = 2250.0  # kg/m³ — marine weight coating concrete

# ---------------------------------------------------------------------------
# Offshore-specific derived constants
# Reference: API RP 2A-WSD, DNV-RP-C205
# ---------------------------------------------------------------------------

# Hydrostatic pressure gradient in seawater (gauge)
SEAWATER_PRESSURE_GRADIENT = RHO_SEAWATER * G / 1000.0  # kPa/m

# Design wave heights for API/DNV return periods (indicative; site-specific)
# 100-year return period — open-ocean reference values
WAVE_HEIGHT_100YR_GULF_M = 12.2   # m — Gulf of Mexico reference (API RP 2A)
WAVE_HEIGHT_100YR_NORTHSEA_M = 30.0  # m — northern North Sea reference

# Still-water level design variation (indicative)
STORM_SURGE_MAX_M = 3.0    # m — maximum storm surge allowance (site-specific)
TIDE_RANGE_MAX_M = 5.0     # m — maximum tidal range allowance (site-specific)
