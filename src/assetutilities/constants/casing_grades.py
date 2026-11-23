# ABOUTME: API 5CT casing and tubing grade mechanical properties.
# ABOUTME: Source: API 5CT 10th Edition / ISO 11960:2020 Table C.1.
from dataclasses import dataclass


@dataclass(frozen=True)
class CasingGrade:
    """Immutable record of minimum specified mechanical properties for an API 5CT grade.

    Attributes:
        name:        Grade designation string (e.g. "J55").
        smys_mpa:    Specified Minimum Yield Strength in MPa.
        suts_mpa:    Specified Minimum Ultimate Tensile Strength in MPa.
        grade_group: API 5CT group ("1" through "4").
    """

    name: str
    smys_mpa: float
    suts_mpa: float
    grade_group: str


CASING_GRADES: dict[str, CasingGrade] = {
    "H40": CasingGrade("H40", smys_mpa=276, suts_mpa=414, grade_group="1"),
    "J55": CasingGrade("J55", smys_mpa=379, suts_mpa=517, grade_group="1"),
    "K55": CasingGrade("K55", smys_mpa=379, suts_mpa=655, grade_group="1"),
    "N80": CasingGrade("N80", smys_mpa=552, suts_mpa=689, grade_group="1"),
    "L80": CasingGrade("L80", smys_mpa=552, suts_mpa=655, grade_group="2"),
    "C90": CasingGrade("C90", smys_mpa=621, suts_mpa=689, grade_group="2"),
    "T95": CasingGrade("T95", smys_mpa=655, suts_mpa=724, grade_group="2"),
    "C110": CasingGrade("C110", smys_mpa=758, suts_mpa=828, grade_group="3"),
    "P110": CasingGrade("P110", smys_mpa=758, suts_mpa=862, grade_group="1"),
    "Q125": CasingGrade("Q125", smys_mpa=862, suts_mpa=931, grade_group="4"),
}
