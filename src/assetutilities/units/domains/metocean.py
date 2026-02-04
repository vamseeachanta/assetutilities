# ABOUTME: Pint-backed adapter for metocean unit conversions (speed, length, temperature, pressure).
# ABOUTME: Matches the worldenergydata UnitConverter API using pint.

from __future__ import annotations

from typing import Optional

from assetutilities.units.registry import get_registry

SpeedUnitMapping: dict[str, str] = {
    "m/s": "m/s",
    "knots": "knot",
    "km/h": "km/hr",
    "mph": "mph",
    "ft/s": "ft/s",
}

LengthUnitMapping: dict[str, str] = {
    "m": "m",
    "feet": "ft",
    "cm": "cm",
    "inches": "inch",
    "nm": "nautical_mile",
    "km": "km",
    "mm": "mm",
}

TempUnitMapping: dict[str, str] = {
    "celsius": "degC",
    "fahrenheit": "degF",
    "kelvin": "kelvin",
}

PressureUnitMapping: dict[str, str] = {
    "hPa": "hectopascal",
    "mbar": "millibar",
    "inHg": "inHg",
    "mmHg": "mmHg",
    "Pa": "Pa",
    "kPa": "kPa",
    "atm": "atm",
    "psi": "psi",
}


def _convert(
    value: Optional[float],
    from_unit_str: str,
    to_unit_str: str,
    mapping: dict[str, str],
    quantity_label: str,
) -> Optional[float]:
    """Shared conversion helper for all metocean quantity types.

    Returns ``None`` when *value* is ``None``.
    """
    if value is None:
        return None

    from_pint = mapping.get(from_unit_str)
    if from_pint is None:
        raise ValueError(
            f"Unknown {quantity_label} unit '{from_unit_str}'. "
            f"Known units: {sorted(mapping.keys())}"
        )

    to_pint = mapping.get(to_unit_str)
    if to_pint is None:
        raise ValueError(
            f"Unknown {quantity_label} unit '{to_unit_str}'. "
            f"Known units: {sorted(mapping.keys())}"
        )

    ureg = get_registry()
    quantity = ureg.Quantity(value, from_pint)
    converted = quantity.to(to_pint)
    return float(converted.magnitude)


def convert_speed(
    value: Optional[float],
    from_unit_str: str,
    to_unit_str: str = "m/s",
) -> Optional[float]:
    """Convert a speed value between metocean unit conventions.

    Parameters
    ----------
    value:
        The numeric speed value, or ``None``.
    from_unit_str:
        Source unit key (e.g. ``"knots"``, ``"m/s"``).
    to_unit_str:
        Target unit key (default ``"m/s"``).

    Returns
    -------
    Converted speed as float, or ``None`` if *value* is ``None``.
    """
    return _convert(value, from_unit_str, to_unit_str, SpeedUnitMapping, "speed")


def convert_length(
    value: Optional[float],
    from_unit_str: str,
    to_unit_str: str = "m",
) -> Optional[float]:
    """Convert a length value between metocean unit conventions.

    Parameters
    ----------
    value:
        The numeric length value, or ``None``.
    from_unit_str:
        Source unit key (e.g. ``"feet"``, ``"m"``).
    to_unit_str:
        Target unit key (default ``"m"``).

    Returns
    -------
    Converted length as float, or ``None`` if *value* is ``None``.
    """
    return _convert(value, from_unit_str, to_unit_str, LengthUnitMapping, "length")


def convert_temperature(
    value: Optional[float],
    from_unit_str: str,
    to_unit_str: str = "celsius",
) -> Optional[float]:
    """Convert a temperature value between metocean unit conventions.

    Parameters
    ----------
    value:
        The numeric temperature value, or ``None``.
    from_unit_str:
        Source unit key (e.g. ``"fahrenheit"``, ``"celsius"``).
    to_unit_str:
        Target unit key (default ``"celsius"``).

    Returns
    -------
    Converted temperature as float, or ``None`` if *value* is ``None``.
    """
    return _convert(value, from_unit_str, to_unit_str, TempUnitMapping, "temperature")


def convert_pressure(
    value: Optional[float],
    from_unit_str: str,
    to_unit_str: str = "hPa",
) -> Optional[float]:
    """Convert a pressure value between metocean unit conventions.

    Parameters
    ----------
    value:
        The numeric pressure value, or ``None``.
    from_unit_str:
        Source unit key (e.g. ``"psi"``, ``"hPa"``).
    to_unit_str:
        Target unit key (default ``"hPa"``).

    Returns
    -------
    Converted pressure as float, or ``None`` if *value* is ``None``.
    """
    return _convert(value, from_unit_str, to_unit_str, PressureUnitMapping, "pressure")
