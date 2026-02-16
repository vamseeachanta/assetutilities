# ABOUTME: Tests for FormatTemplate and template-based formatting in UnitFormatter.
# ABOUTME: Verifies precision, notation, suffix, and template registration features.

import pytest

from assetutilities.units.output_formatter import FormatTemplate, UnitFormatter
from assetutilities.units.quantity import TrackedQuantity


@pytest.fixture
def formatter():
    return UnitFormatter()


@pytest.fixture
def tq_pressure():
    return TrackedQuantity(101325.0, "Pa", source="standard_atm")


@pytest.fixture
def tq_length():
    return TrackedQuantity(12.3456, "m", source="measurement")


class TestFormatTemplateCreation:
    def test_create_format_template(self):
        # Arrange & Act
        template = FormatTemplate(precision=2, notation="fixed")

        # Assert
        assert template.precision == 2
        assert template.notation == "fixed"

    def test_format_template_scientific(self):
        # Arrange & Act
        template = FormatTemplate(precision=3, notation="scientific")

        # Assert
        assert template.precision == 3
        assert template.notation == "scientific"

    def test_format_template_with_suffix(self):
        # Arrange & Act
        template = FormatTemplate(precision=2, suffix=" (abs)")

        # Assert
        assert template.suffix == " (abs)"


class TestFormatterWithTemplate:
    def test_formatter_with_template(self, formatter, tq_length):
        # Arrange
        template = FormatTemplate(precision=2)

        # Act
        result = formatter.format_quantity(tq_length, template=template)

        # Assert
        assert "12.35" in result

    def test_formatter_default_precision_unchanged(self, formatter, tq_length):
        # Arrange — no template, default precision=4

        # Act
        result = formatter.format_quantity(tq_length)

        # Assert
        assert "12.3456" in result

    def test_format_template_with_suffix_applied(self, formatter, tq_pressure):
        # Arrange
        template = FormatTemplate(precision=2, suffix=" (abs)")

        # Act
        result = formatter.format_quantity(tq_pressure, template=template)

        # Assert
        assert "(abs)" in result

    def test_format_template_scientific_notation(self, formatter):
        # Arrange
        tq = TrackedQuantity(1230000.0, "Pa", source="test")
        template = FormatTemplate(precision=2, notation="scientific")

        # Act
        result = formatter.format_quantity(tq, template=template)

        # Assert
        assert "e+" in result.lower()


class TestFormatterTemplateRegistration:
    def test_formatter_register_template(self, formatter, tq_pressure):
        # Arrange
        template = FormatTemplate(precision=2, notation="fixed")
        formatter.register_template("pressure", template)

        # Act
        result = formatter.format_quantity(tq_pressure)

        # Assert
        assert "101325.00" in result
