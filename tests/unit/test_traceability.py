# ABOUTME: Tests for CalculationAuditLog provenance aggregation.
# ABOUTME: Verifies input/output recording, steps, and serialization.

import json

import pytest

from assetutilities.units.quantity import TrackedQuantity
from assetutilities.units.traceability import CalculationAuditLog


class TestCalculationAuditLog:
    def test_create_audit_log(self):
        log = CalculationAuditLog()
        assert log is not None

    def test_add_input(self):
        log = CalculationAuditLog()
        tq = TrackedQuantity(100.0, "Pa", source="gauge")
        log.add_input("pressure", tq)
        data = log.to_dict()
        assert "pressure" in data["inputs"]

    def test_add_output(self):
        log = CalculationAuditLog()
        tq = TrackedQuantity(50.0, "N", source="calc")
        log.add_output("force", tq)
        data = log.to_dict()
        assert "force" in data["outputs"]

    def test_add_step(self):
        log = CalculationAuditLog()
        log.add_step("Multiplied pressure by area")
        data = log.to_dict()
        assert len(data["steps"]) == 1
        assert data["steps"][0]["description"] == "Multiplied pressure by area"

    def test_to_json(self):
        log = CalculationAuditLog()
        tq = TrackedQuantity(10.0, "Pa", source="test")
        log.add_input("p", tq)
        log.add_step("test step")
        result = log.to_json()
        parsed = json.loads(result)
        assert "inputs" in parsed
        assert "steps" in parsed

    def test_summary(self):
        log = CalculationAuditLog()
        log.add_input("pressure", TrackedQuantity(100.0, "Pa", source="gauge"))
        log.add_output("force", TrackedQuantity(50.0, "N", source="calc"))
        log.add_step("F = P * A")
        text = log.summary()
        assert "Calculation Audit Log" in text
        assert "pressure" in text
        assert "force" in text
        assert "F = P * A" in text
