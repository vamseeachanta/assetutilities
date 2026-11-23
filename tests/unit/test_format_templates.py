# ABOUTME: Tests for FormatTemplate and template-based formatting in UnitFormatter.
# ABOUTME: Verifies precision, notation, suffix, and template registration features.

import pint
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
    @pytest.mark.parametrize(
        "quantity_type, unit",
        [("", "dimensionless"), (" ", "dimensionless"), ("\t\n", "dimensionless")],
    )
    def test_blank_name_is_rejected(self, formatter, quantity_type, unit):
        """Rejected names leave the four-place default for unitless values."""
        with pytest.raises(ValueError, match="nonblank"):
            formatter.register_template(
                quantity_type, FormatTemplate(precision=2, suffix=" (incorrect)")
            )

        assert (
            formatter.format_quantity(TrackedQuantity(1.25, unit))
            == "1.2500 dimensionless"
        )

    def test_template_uses_quantity_registry(self, formatter):
        """Resolve a custom dimension in the registry that defines the quantity."""
        registry = pint.UnitRegistry()
        registry.define("custom_unit = [custom_dimension]")
        formatter.register_template(
            "custom_dimension", FormatTemplate(precision=2, suffix=" (custom)")
        )

        assert (
            formatter.format_quantity(
                TrackedQuantity(1.25, "custom_unit", registry=registry)
            )
            == "1.25 custom_unit (custom)"
        )

    def test_formatter_register_template(self, formatter, tq_pressure):
        """Hand calculation: fixture input 101325 gains .00 at two places.

        The fixture magnitude is retained without conversion; its physical
        interpretation is not used as a reference value in this test.
        """
        # Arrange
        template = FormatTemplate(precision=2, notation="fixed")
        formatter.register_template("pressure", template)

        # Act
        result = formatter.format_quantity(tq_pressure)

        # Assert
        assert result == "101325.00 pascal"

    @pytest.mark.parametrize(
        "unit, unit_text", [("Pa", "pascal"), ("psi", "pound_force_per_square_inch")]
    )
    @pytest.mark.parametrize("types", [("length", "pressure"), ("pressure", "length")])
    def test_pressure_template_matches_dimension(
        self, formatter, unit, unit_text, types
    ):
        """Pressure is force/area, not length, in either registration order.

        Basis: NIST SP 811 (2008), Tables 2 and 3 and Appendix B.8 (psi).
        Hand calculation: the chosen input 1.25 is unchanged (no conversion);
        two decimal places give 1.25, followed by the pressure marker.
        """
        for quantity_type in types:
            formatter.register_template(
                quantity_type, FormatTemplate(precision=2, suffix=f" ({quantity_type})")
            )

        result = formatter.format_quantity(TrackedQuantity(1.25, unit))

        assert result == f"1.25 {unit_text} (pressure)"

    @pytest.mark.parametrize(
        "unit, expected",
        [
            ("m", "1.25 meter (length)"),
            ("m**2", "1.2500 meter ** 2"),
            ("Pa", "1.2500 pascal"),
        ],
    )
    def test_length_template_excludes_derived_dimensions(
        self, formatter, unit, expected
    ):
        """Area has dimension L squared; pressure has dimension M/L/T squared.

        Basis: NIST SP 811 (2008), Tables 2 and 3. Hand calculation: no
        conversion of chosen input 1.25; append two zeros for the existing
        four-place default, or retain two places for the length template.
        """
        formatter.register_template(
            "length", FormatTemplate(precision=2, suffix=" (length)")
        )

        assert formatter.format_quantity(TrackedQuantity(1.25, unit)) == expected

    def test_explicit_template_overrides_registered_dimension(self, formatter):
        """Hand calculation: chosen input 1.25 stays 1.25 at two places."""
        formatter.register_template("pressure", FormatTemplate(suffix=" (registered)"))
        explicit = FormatTemplate(precision=2, suffix=" (explicit)")

        assert (
            formatter.format_quantity(TrackedQuantity(1.25, "Pa"), template=explicit)
            == "1.25 pascal (explicit)"
        )

    @pytest.mark.parametrize(
        "quantity_type, unit, unit_text",
        [
            ("unknown", "m", "meter"),
            ("met", "m", "meter"),
            ("pascal", "Pa", "pascal"),
            ("psi", "psi", "pound_force_per_square_inch"),
        ],
    )
    def test_unknown_name_does_not_match_unit_substring(
        self, formatter, quantity_type, unit, unit_text
    ):
        """Hand calculation: chosen input 1.25 plus two zeros gives 1.2500.

        An unrecognized dimension name must retain the four-place default;
        the partial unit name 'met' must not select a meter template.
        """
        formatter.register_template(
            quantity_type, FormatTemplate(suffix=" (incorrect)")
        )

        assert (
            formatter.format_quantity(TrackedQuantity(1.25, unit))
            == f"1.2500 {unit_text}"
        )
