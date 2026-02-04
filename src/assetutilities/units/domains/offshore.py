# ABOUTME: Offshore engineering field-to-quantity mappings and unit systems.
# ABOUTME: Extends base maps with wall thickness, buckling stress, hydrostatic pressure, etc.

from __future__ import annotations

from assetutilities.units.input_parser import FIELD_QUANTITY_MAP, UNIT_SYSTEMS

OFFSHORE_FIELD_MAP: dict[str, str] = {
    **FIELD_QUANTITY_MAP,
    # Geometry
    "wall_thickness": "length",
    "plate_thickness": "length",
    "stiffener_height": "length",
    # Stress
    "buckling_stress": "stress",
    "von_mises_stress": "stress",
    "hoop_stress": "stress",
    # Pressure
    "hydrostatic_pressure": "pressure",
    "internal_pressure": "pressure",
    "external_pressure": "pressure",
    # Force
    "buoyancy_force": "force",
    "tension": "force",
    "compression": "force",
}

OFFSHORE_UNIT_SYSTEMS: dict[str, dict[str, str]] = {
    system_name: dict(system_units)
    for system_name, system_units in UNIT_SYSTEMS.items()
}
