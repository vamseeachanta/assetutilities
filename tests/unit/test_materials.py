# ABOUTME: TDD tests for frozen-dataclass material properties library.
# ABOUTME: Covers API 5L grades X42-X80, structural steel A36/A572, and immutability.

import dataclasses
import pytest

from assetutilities.constants.materials import (
    SteelGrade,
    STEEL_GRADES,
    get_steel_grade,
)


# ---------------------------------------------------------------------------
# SteelGrade dataclass structure
# ---------------------------------------------------------------------------

class TestSteelGradeDataclass:
    def test_steel_grade_is_frozen_dataclass(self):
        """SteelGrade must be a frozen dataclass (immutable)."""
        assert dataclasses.is_dataclass(SteelGrade)
        grade = get_steel_grade("API 5L X65")
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            grade.smys_pa = 999  # must raise on mutation attempt

    def test_steel_grade_has_required_fields(self):
        grade = get_steel_grade("API 5L X65")
        assert hasattr(grade, "name")
        assert hasattr(grade, "smys_pa")
        assert hasattr(grade, "smus_pa")
        assert hasattr(grade, "reference")

    def test_steel_grade_name_is_string(self):
        grade = get_steel_grade("API 5L X65")
        assert isinstance(grade.name, str)

    def test_steel_grade_smys_is_float(self):
        grade = get_steel_grade("API 5L X65")
        assert isinstance(grade.smys_pa, float)

    def test_steel_grade_smus_is_float_or_none(self):
        grade = get_steel_grade("API 5L X65")
        assert isinstance(grade.smus_pa, (float, type(None)))


# ---------------------------------------------------------------------------
# API 5L pipeline grades X42 through X80
# ---------------------------------------------------------------------------

class TestAPI5LGrades:
    """Verify each API 5L grade SMYS against published minimum values.

    References: API 5L / ISO 3183 Table J.2 (PSL2 minimum).
    Values in Pa.
    """

    def test_x42_grade_exists(self):
        grade = get_steel_grade("API 5L X42")
        assert grade is not None

    def test_x42_smys_pa(self):
        # API 5L X42: 290 MPa SMYS
        grade = get_steel_grade("API 5L X42")
        assert grade.smys_pa == pytest.approx(290e6, rel=1e-6)

    def test_x52_grade_exists(self):
        grade = get_steel_grade("API 5L X52")
        assert grade is not None

    def test_x52_smys_pa(self):
        # API 5L X52: 358 MPa SMYS
        grade = get_steel_grade("API 5L X52")
        assert grade.smys_pa == pytest.approx(358e6, rel=1e-6)

    def test_x60_grade_exists(self):
        grade = get_steel_grade("API 5L X60")
        assert grade is not None

    def test_x60_smys_pa(self):
        # API 5L X60: 413 MPa SMYS
        grade = get_steel_grade("API 5L X60")
        assert grade.smys_pa == pytest.approx(413e6, rel=1e-6)

    def test_x65_grade_exists(self):
        grade = get_steel_grade("API 5L X65")
        assert grade is not None

    def test_x65_smys_pa(self):
        # API 5L X65: 448 MPa SMYS
        grade = get_steel_grade("API 5L X65")
        assert grade.smys_pa == pytest.approx(448e6, rel=1e-6)

    def test_x65_smus_pa(self):
        # API 5L X65: 530 MPa SMUS (PSL2)
        grade = get_steel_grade("API 5L X65")
        assert grade.smus_pa == pytest.approx(530e6, rel=1e-6)

    def test_x70_grade_exists(self):
        grade = get_steel_grade("API 5L X70")
        assert grade is not None

    def test_x70_smys_pa(self):
        # API 5L X70: 482 MPa SMYS
        grade = get_steel_grade("API 5L X70")
        assert grade.smys_pa == pytest.approx(482e6, rel=1e-6)

    def test_x80_grade_exists(self):
        grade = get_steel_grade("API 5L X80")
        assert grade is not None

    def test_x80_smys_pa(self):
        # API 5L X80: 552 MPa SMYS
        grade = get_steel_grade("API 5L X80")
        assert grade.smys_pa == pytest.approx(552e6, rel=1e-6)

    def test_api5l_grades_smys_ascending(self):
        grades = ["API 5L X42", "API 5L X52", "API 5L X60", "API 5L X65",
                  "API 5L X70", "API 5L X80"]
        smys_values = [get_steel_grade(g).smys_pa for g in grades]
        assert smys_values == sorted(smys_values)


# ---------------------------------------------------------------------------
# Structural steel grades A36 and A572
# ---------------------------------------------------------------------------

class TestStructuralSteelGrades:
    def test_a36_grade_exists(self):
        grade = get_steel_grade("ASTM A36")
        assert grade is not None

    def test_a36_smys_pa(self):
        # ASTM A36: 250 MPa (36 ksi) min yield
        grade = get_steel_grade("ASTM A36")
        assert grade.smys_pa == pytest.approx(250e6, rel=1e-6)

    def test_a572_grade50_exists(self):
        grade = get_steel_grade("ASTM A572 Grade 50")
        assert grade is not None

    def test_a572_grade50_smys_pa(self):
        # ASTM A572 Gr 50: 345 MPa (50 ksi) min yield
        grade = get_steel_grade("ASTM A572 Grade 50")
        assert grade.smys_pa == pytest.approx(345e6, rel=1e-6)

    def test_a572_grade60_exists(self):
        grade = get_steel_grade("ASTM A572 Grade 60")
        assert grade is not None

    def test_a572_grade60_smys_pa(self):
        # ASTM A572 Gr 60: 415 MPa (60 ksi) min yield
        grade = get_steel_grade("ASTM A572 Grade 60")
        assert grade.smys_pa == pytest.approx(415e6, rel=1e-6)

    def test_a572_grade65_exists(self):
        grade = get_steel_grade("ASTM A572 Grade 65")
        assert grade is not None

    def test_a572_grade65_smys_pa(self):
        # ASTM A572 Gr 65: 450 MPa (65 ksi) min yield
        grade = get_steel_grade("ASTM A572 Grade 65")
        assert grade.smys_pa == pytest.approx(450e6, rel=1e-6)


# ---------------------------------------------------------------------------
# STEEL_GRADES registry
# ---------------------------------------------------------------------------

class TestSteelGradesRegistry:
    def test_registry_is_dict(self):
        assert isinstance(STEEL_GRADES, dict)

    def test_registry_contains_all_api5l_grades(self):
        for label in ["API 5L X42", "API 5L X52", "API 5L X60",
                      "API 5L X65", "API 5L X70", "API 5L X80"]:
            assert label in STEEL_GRADES, f"Missing grade: {label}"

    def test_registry_contains_structural_grades(self):
        for label in ["ASTM A36", "ASTM A572 Grade 50"]:
            assert label in STEEL_GRADES, f"Missing grade: {label}"

    def test_all_registry_values_are_steel_grade_instances(self):
        for name, grade in STEEL_GRADES.items():
            assert isinstance(grade, SteelGrade), f"{name} is not SteelGrade"

    def test_get_steel_grade_returns_none_for_unknown(self):
        result = get_steel_grade("NonExistentGrade XYZ")
        assert result is None

    def test_all_registry_smys_positive(self):
        for name, grade in STEEL_GRADES.items():
            assert grade.smys_pa > 0, f"{name} has non-positive SMYS"
