# ABOUTME: Frozen dataclass definitions for steel material grades used in engineering.
# ABOUTME: Sources: API 5L / ISO 3183, ASTM A36, ASTM A572, EN 1993-1-1.

from __future__ import annotations

import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class SteelGrade:
    """Immutable record of minimum specified mechanical properties for a steel grade.

    Attributes:
        name:       Grade designation string (e.g. "API 5L X65").
        smys_pa:    Specified minimum yield strength in Pa.
        smus_pa:    Specified minimum ultimate strength in Pa (None if not published).
        reference:  Source standard or note.
    """

    name: str
    smys_pa: float
    smus_pa: Optional[float]
    reference: str


# ---------------------------------------------------------------------------
# API 5L / ISO 3183 pipeline steel grades
# Reference: API 5L 46th Edition / ISO 3183:2019 Table J.2 (PSL2 minimum values)
# ---------------------------------------------------------------------------

_API5L_X42 = SteelGrade(
    name="API 5L X42",
    smys_pa=290e6,      # 42 ksi → 290 MPa
    smus_pa=414e6,      # PSL2 minimum: 414 MPa
    reference="API 5L 46th Ed / ISO 3183:2019 Table J.2",
)

_API5L_X52 = SteelGrade(
    name="API 5L X52",
    smys_pa=358e6,      # 52 ksi → 358 MPa
    smus_pa=455e6,      # PSL2 minimum
    reference="API 5L 46th Ed / ISO 3183:2019 Table J.2",
)

_API5L_X60 = SteelGrade(
    name="API 5L X60",
    smys_pa=413e6,      # 60 ksi → 413 MPa
    smus_pa=517e6,      # PSL2 minimum
    reference="API 5L 46th Ed / ISO 3183:2019 Table J.2",
)

_API5L_X65 = SteelGrade(
    name="API 5L X65",
    smys_pa=448e6,      # 65 ksi → 448 MPa
    smus_pa=530e6,      # PSL2 minimum
    reference="API 5L 46th Ed / ISO 3183:2019 Table J.2",
)

_API5L_X70 = SteelGrade(
    name="API 5L X70",
    smys_pa=482e6,      # 70 ksi → 482 MPa
    smus_pa=565e6,      # PSL2 minimum
    reference="API 5L 46th Ed / ISO 3183:2019 Table J.2",
)

_API5L_X80 = SteelGrade(
    name="API 5L X80",
    smys_pa=552e6,      # 80 ksi → 552 MPa
    smus_pa=621e6,      # PSL2 minimum
    reference="API 5L 46th Ed / ISO 3183:2019 Table J.2",
)


# ---------------------------------------------------------------------------
# ASTM structural steel grades
# Reference: ASTM A36/A36M-19, ASTM A572/A572M-21
# ---------------------------------------------------------------------------

_ASTM_A36 = SteelGrade(
    name="ASTM A36",
    smys_pa=250e6,      # 36 ksi → 250 MPa
    smus_pa=400e6,      # min 58 ksi → 400 MPa
    reference="ASTM A36/A36M-19",
)

_ASTM_A572_GR42 = SteelGrade(
    name="ASTM A572 Grade 42",
    smys_pa=290e6,      # 42 ksi → 290 MPa
    smus_pa=414e6,      # min 60 ksi → 414 MPa
    reference="ASTM A572/A572M-21",
)

_ASTM_A572_GR50 = SteelGrade(
    name="ASTM A572 Grade 50",
    smys_pa=345e6,      # 50 ksi → 345 MPa
    smus_pa=448e6,      # min 65 ksi → 448 MPa
    reference="ASTM A572/A572M-21",
)

_ASTM_A572_GR60 = SteelGrade(
    name="ASTM A572 Grade 60",
    smys_pa=415e6,      # 60 ksi → 415 MPa
    smus_pa=517e6,      # min 75 ksi → 517 MPa
    reference="ASTM A572/A572M-21",
)

_ASTM_A572_GR65 = SteelGrade(
    name="ASTM A572 Grade 65",
    smys_pa=450e6,      # 65 ksi → 450 MPa
    smus_pa=550e6,      # min 80 ksi → 550 MPa
    reference="ASTM A572/A572M-21",
)


# ---------------------------------------------------------------------------
# Public registry — keyed by grade name string
# ---------------------------------------------------------------------------

STEEL_GRADES: dict[str, SteelGrade] = {
    grade.name: grade
    for grade in [
        # API 5L pipeline grades
        _API5L_X42,
        _API5L_X52,
        _API5L_X60,
        _API5L_X65,
        _API5L_X70,
        _API5L_X80,
        # ASTM structural grades
        _ASTM_A36,
        _ASTM_A572_GR42,
        _ASTM_A572_GR50,
        _ASTM_A572_GR60,
        _ASTM_A572_GR65,
    ]
}


def get_steel_grade(name: str) -> Optional[SteelGrade]:
    """Return the SteelGrade for the given grade name, or None if not found.

    Args:
        name: Grade designation string, e.g. "API 5L X65" or "ASTM A36".

    Returns:
        SteelGrade frozen dataclass, or None if grade is not in the registry.
    """
    return STEEL_GRADES.get(name)
