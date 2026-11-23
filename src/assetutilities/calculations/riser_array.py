# ABOUTME: Riser array design calculations per BP Riser Array Design Guidelines v2.
# ABOUTME: Covers equivalent diameter, de-equivalencing, shadow factor, and spacing.

import math


def equivalent_diameter(n: int, diameter: float) -> float:
    """Compute the equivalent hydrodynamic diameter for a bundle of n risers.

    Uses the BP Riser Array guideline formula:
        D_eq = sqrt(n) * D

    Args:
        n: Number of risers in the array (positive integer).
        diameter: Individual riser outer diameter (m).

    Returns:
        Equivalent array diameter (m).

    Raises:
        ValueError: If n is not a positive integer or diameter is not positive.
    """
    if not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    if diameter <= 0.0:
        raise ValueError("diameter must be positive")
    return math.sqrt(n) * diameter


def de_equivalencing_factor(n: int) -> float:
    """Compute the load de-equivalencing factor from array to individual riser.

    When an array of n risers is represented by a single equivalent riser,
    the equivalent load must be divided back among individual risers using:
        factor = 1 / sqrt(n)

    Args:
        n: Number of risers in the array (positive integer).

    Returns:
        De-equivalencing factor (dimensionless, 0 < factor <= 1).

    Raises:
        ValueError: If n is not a positive integer.
    """
    if not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    return 1.0 / math.sqrt(n)


def hydrodynamic_shadow_factor(spacing_ratio: float) -> float:
    """Compute the hydrodynamic shadow factor between parallel risers in current.

    The downstream riser is partially shielded by the upstream riser. The
    shadow factor (0 to 1) scales the effective drag on the downstream riser:
        - factor = 1.0 : no shielding (large spacing or reference riser)
        - factor < 1.0 : partial shielding from upstream riser

    Uses the empirical exponential decay model:
        shadow = 1 - exp(-alpha * (s/D - 1))
    with alpha = 0.55, calibrated against Huse (1993) experimental data for
    tandem risers. This gives ~0 shielding at large spacing and significant
    shielding near 2D separation.

    Args:
        spacing_ratio: Centre-to-centre spacing normalised by diameter (s/D).

    Returns:
        Shadow factor (0 < factor <= 1.0).

    Raises:
        ValueError: If spacing_ratio is not positive.
    """
    if spacing_ratio <= 0.0:
        raise ValueError("spacing_ratio must be positive")
    ALPHA = 0.55
    factor = 1.0 - math.exp(-ALPHA * (spacing_ratio - 1.0))
    return max(0.0, min(1.0, factor))


def check_minimum_spacing(
    centre_to_centre: float,
    diameter: float,
    min_multiplier: float = 3.0,
) -> bool:
    """Check whether the riser centre-to-centre spacing meets the minimum requirement.

    The BP Riser Array Design Guidelines v2 specify a minimum spacing of 3D
    (three diameters) between adjacent riser centrelines.

    Args:
        centre_to_centre: Measured spacing between riser centrelines (m).
        diameter: Riser outer diameter (m).
        min_multiplier: Required minimum spacing as a multiple of D (default 3.0).

    Returns:
        True if the spacing exceeds the minimum requirement, False otherwise.

    Raises:
        ValueError: If diameter or centre_to_centre are not positive.
    """
    if diameter <= 0.0:
        raise ValueError("diameter must be positive")
    if centre_to_centre <= 0.0:
        raise ValueError("centre_to_centre must be positive")
    minimum_spacing = min_multiplier * diameter
    return centre_to_centre > minimum_spacing
