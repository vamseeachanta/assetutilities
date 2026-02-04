# ABOUTME: Pint-backed adapter for energy unit conversions.
# ABOUTME: Matches the worldenergydata convert_units() signature using pint.

from __future__ import annotations

from assetutilities.units.registry import get_registry

EnergyUnitMapping: dict[str, str] = {
    # Thermal / energy units
    "BTU": "BTU",
    "MMBTU": "MMBTU",
    "THERM": "therm",
    "GJ": "GJ",
    "MWH": "MWh",
    "KWH": "kWh",
    "TOE": "TOE",
    "BOE": "BOE",
    # Liquid volume units
    "BBL": "oil_barrel",
    "BBL_OIL": "oil_barrel",
    "GAL": "gallon",
    "L": "liter",
    "M3": "m**3",
    # Gas volume units
    "MCF": "MCF",
    "MMCF": "MMCF",
    "BCF": "BCF",
    "TCF": "TCF",
    "SCF": "SCF",
    # Mass units
    "TONNE": "metric_ton",
    "SHORT_TON": "short_ton",
    "LONG_TON": "long_ton",
    "KG": "kg",
    "LB": "lb",
}


def convert_energy_units(
    value: float,
    from_unit_str: str,
    to_unit_str: str,
) -> float:
    """Convert *value* between energy / commodity units.

    Uses the ``EnergyUnitMapping`` to translate string enum values (matching
    the worldenergydata ``EnergyUnits`` enum) into pint unit names, then
    delegates the actual conversion to pint.

    Parameters
    ----------
    value:
        The numeric value to convert.
    from_unit_str:
        Source unit as a string key in ``EnergyUnitMapping``.
    to_unit_str:
        Target unit as a string key in ``EnergyUnitMapping``.

    Returns
    -------
    The converted value as a plain float.

    Raises
    ------
    ValueError
        If either unit string is not found in ``EnergyUnitMapping``.
    """
    from_pint = EnergyUnitMapping.get(from_unit_str)
    if from_pint is None:
        raise ValueError(
            f"Unknown energy unit '{from_unit_str}'. "
            f"Known units: {sorted(EnergyUnitMapping.keys())}"
        )

    to_pint = EnergyUnitMapping.get(to_unit_str)
    if to_pint is None:
        raise ValueError(
            f"Unknown energy unit '{to_unit_str}'. "
            f"Known units: {sorted(EnergyUnitMapping.keys())}"
        )

    ureg = get_registry()
    quantity = ureg.Quantity(value, from_pint)
    converted = quantity.to(to_pint)
    return float(converted.magnitude)
