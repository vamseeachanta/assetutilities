# ABOUTME: Parses YAML/JSON config values into TrackedQuantity instances.
# ABOUTME: Infers units from field names and unit system conventions.

from __future__ import annotations

from typing import Any, Optional

from assetutilities.units.quantity import TrackedQuantity

UNIT_SYSTEMS: dict[str, dict[str, str]] = {
    "inch": {
        "length": "inch",
        "stress": "psi",
        "pressure": "psi",
        "force": "lbf",
        "moment": "lbf * inch",
        "temperature": "degF",
        "mass": "lb",
    },
    "SI": {
        "length": "m",
        "stress": "Pa",
        "pressure": "Pa",
        "force": "N",
        "moment": "N * m",
        "temperature": "degC",
        "mass": "kg",
    },
    "metric_engineering": {
        "length": "mm",
        "stress": "MPa",
        "pressure": "MPa",
        "force": "kN",
        "moment": "kN * m",
        "temperature": "degC",
        "mass": "kg",
    },
}

FIELD_QUANTITY_MAP: dict[str, str] = {
    "thickness": "length",
    "breadth": "length",
    "width": "length",
    "height": "length",
    "depth": "length",
    "diameter": "length",
    "radius": "length",
    "length": "length",
    "youngs_modulus": "stress",
    "yield_strength": "stress",
    "ultimate_strength": "stress",
    "stress": "stress",
    "pressure": "pressure",
    "wave_height": "length",
    "water_depth": "length",
    "force": "force",
    "weight": "force",
    "temperature": "temperature",
    "temp": "temperature",
    "mass": "mass",
}


def parse_config_value(
    value: Any,
    field_name: str,
    unit_system: str = "SI",
    explicit_unit: Optional[str] = None,
    source: str = "config",
) -> Any:
    """Parse a single config value into a TrackedQuantity when possible.

    If *explicit_unit* is provided it is used directly.  Otherwise the unit is
    inferred from *field_name* via ``FIELD_QUANTITY_MAP`` and the chosen
    *unit_system*.  If the field name is not recognised and no explicit unit is
    given, the raw *value* is returned unchanged.

    Parameters
    ----------
    value:
        The numeric (or non-numeric) value from a config dict.
    field_name:
        The key name in the config, used to infer the physical quantity.
    unit_system:
        One of the keys in ``UNIT_SYSTEMS`` (default ``"SI"``).
    explicit_unit:
        If provided, overrides any inference and uses this unit directly.
    source:
        Provenance label recorded in the TrackedQuantity.

    Returns
    -------
    TrackedQuantity or the raw value if no unit can be determined.
    """
    if not isinstance(value, (int, float)):
        return value

    if explicit_unit is not None:
        return TrackedQuantity(value, explicit_unit, source=source)

    quantity_type = FIELD_QUANTITY_MAP.get(field_name)
    if quantity_type is None:
        return value

    system = UNIT_SYSTEMS.get(unit_system)
    if system is None:
        raise ValueError(
            f"Unknown unit system '{unit_system}'. "
            f"Available systems: {list(UNIT_SYSTEMS.keys())}"
        )

    unit = system.get(quantity_type)
    if unit is None:
        return value

    return TrackedQuantity(value, unit, source=source)


def parse_config_section(
    config_dict: dict[str, Any],
    unit_system: str = "SI",
    source: str = "config",
) -> dict[str, Any]:
    """Parse all numeric values in a config dict into TrackedQuantity where possible.

    Non-numeric values pass through unchanged.  Each key is checked against
    ``FIELD_QUANTITY_MAP`` to determine whether a unit can be inferred.

    Parameters
    ----------
    config_dict:
        A flat dictionary of configuration key-value pairs.
    unit_system:
        One of the keys in ``UNIT_SYSTEMS`` (default ``"SI"``).
    source:
        Provenance label recorded in each TrackedQuantity.

    Returns
    -------
    A new dictionary with the same keys.  Numeric values whose field name is
    recognised are wrapped in TrackedQuantity; everything else is unchanged.
    """
    result: dict[str, Any] = {}
    for key, value in config_dict.items():
        result[key] = parse_config_value(
            value, key, unit_system=unit_system, source=source
        )
    return result
