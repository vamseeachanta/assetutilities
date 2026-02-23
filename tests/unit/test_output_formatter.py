# ABOUTME: Tests for the output formatter and audit trail export.
# ABOUTME: Validates display formatting, provenance rendering, and JSON/text export.

import json

import pytest

from assetutilities.units.output_formatter import UnitFormatter
from assetutilities.units.quantity import TrackedQuantity
from assetutilities.units.traceability import CalculationAuditLog


@pytest.fixture
def formatter():
    return UnitFormatter()


@pytest.fixture
def sample_quantity():
    return TrackedQuantity(100.0, "Pa", source="test")


@pytest.fixture
def sample_audit_log():
    log = CalculationAuditLog()
    log.add_input("pressure", TrackedQuantity(100.0, "Pa", source="input"))
    log.add_step("Applied Bernoulli equation")
    log.add_output("velocity", TrackedQuantity(10.0, "m/s", source="calc"))
    return log


class TestFormatQuantity:
    def test_default_formatting(self, formatter, sample_quantity):
        result = formatter.format_quantity(sample_quantity)
        assert "100.0000" in result
        assert "pascal" in result or "Pa" in result

    def test_custom_precision(self, formatter, sample_quantity):
        result = formatter.format_quantity(sample_quantity, precision=2)
        assert "100.00" in result

    def test_with_target_unit(self, formatter):
        tq = TrackedQuantity(1.0, "m", source="test")
        result = formatter.format_quantity(tq, target_unit="ft")
        assert "3.2808" in result or "3.281" in result
        assert "foot" in result or "ft" in result


class TestFormatWithProvenance:
    def test_includes_value_line(self, formatter, sample_quantity):
        result = formatter.format_with_provenance(sample_quantity)
        assert "Value:" in result
        assert "100.0" in result

    def test_includes_provenance_section(self, formatter, sample_quantity):
        result = formatter.format_with_provenance(sample_quantity)
        assert "Provenance:" in result
        assert "created" in result

    def test_conversion_adds_provenance_lines(self, formatter):
        tq = TrackedQuantity(1.0, "m", source="test")
        result = formatter.format_with_provenance(tq, target_unit="ft")
        assert "converted" in result


class TestExportAuditTrail:
    def test_json_export_is_valid(self, formatter, sample_audit_log):
        result = formatter.export_audit_trail(sample_audit_log, format="json")
        data = json.loads(result)
        assert "inputs" in data
        assert "outputs" in data
        assert "steps" in data
        assert "pressure" in data["inputs"]
        assert "velocity" in data["outputs"]

    def test_text_export_contains_summary(self, formatter, sample_audit_log):
        result = formatter.export_audit_trail(sample_audit_log, format="text")
        assert "Calculation Audit Log" in result
        assert "pressure" in result
        assert "velocity" in result

    def test_unknown_format_raises(self, formatter, sample_audit_log):
        with pytest.raises(ValueError, match="Unsupported format"):
            formatter.export_audit_trail(sample_audit_log, format="xml")
