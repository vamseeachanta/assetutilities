# ABOUTME: Tests for extended CalculationAuditLog filtering and export features.
# ABOUTME: Verifies unit-based filtering, CSV export, and name accessor properties.

import pytest

from assetutilities.units.quantity import TrackedQuantity
from assetutilities.units.traceability import CalculationAuditLog


@pytest.fixture
def populated_log():
    """Audit log with mixed-unit inputs and outputs."""
    log = CalculationAuditLog()
    log.add_input("length", TrackedQuantity(10.0, "m", source="drawing"))
    log.add_input("width", TrackedQuantity(5.0, "m", source="drawing"))
    log.add_input("pressure", TrackedQuantity(100.0, "Pa", source="gauge"))
    log.add_step("area = length * width")
    log.add_step("force = pressure * area")
    log.add_output("area", TrackedQuantity(50.0, "m**2", source="calc"))
    log.add_output("force", TrackedQuantity(5000.0, "N", source="calc"))
    log.add_output("stress", TrackedQuantity(100.0, "Pa", source="calc"))
    return log


class TestFilterInputs:
    def test_filter_inputs_by_unit(self, populated_log):
        # Arrange — fixture provides the log

        # Act
        result = populated_log.filter_inputs(unit="m")

        # Assert
        assert "length" in result
        assert "width" in result
        assert "pressure" not in result

    def test_filter_inputs_by_unit_no_match(self, populated_log):
        # Arrange — fixture provides the log

        # Act
        result = populated_log.filter_inputs(unit="kg")

        # Assert
        assert result == {}


class TestFilterOutputs:
    def test_filter_outputs_by_unit(self, populated_log):
        # Arrange — fixture provides the log

        # Act
        result = populated_log.filter_outputs(unit="Pa")

        # Assert
        assert "stress" in result
        assert "force" not in result
        assert "area" not in result


class TestCsvExport:
    def test_to_csv(self, populated_log):
        # Arrange — fixture provides the log

        # Act
        csv_str = populated_log.to_csv()

        # Assert
        lines = csv_str.strip().split("\n")
        header = lines[0]
        assert "role" in header
        assert "name" in header
        assert "magnitude" in header
        assert "unit" in header

    def test_to_csv_includes_all_entries(self, populated_log):
        # Arrange — 3 inputs + 3 outputs = 6 data rows

        # Act
        csv_str = populated_log.to_csv()

        # Assert
        lines = csv_str.strip().split("\n")
        data_rows = lines[1:]  # skip header
        assert len(data_rows) == 6


class TestNameProperties:
    def test_input_names_property(self, populated_log):
        # Arrange — fixture provides the log

        # Act
        names = populated_log.input_names

        # Assert
        assert isinstance(names, list)
        assert "length" in names
        assert "width" in names
        assert "pressure" in names
        assert len(names) == 3

    def test_output_names_property(self, populated_log):
        # Arrange — fixture provides the log

        # Act
        names = populated_log.output_names

        # Assert
        assert isinstance(names, list)
        assert "area" in names
        assert "force" in names
        assert "stress" in names
        assert len(names) == 3
