# ABOUTME: CalculationAuditLog aggregates provenance across a full calculation.
# ABOUTME: Records inputs, outputs, and intermediate steps for engineering audits.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from assetutilities.units.quantity import TrackedQuantity


@dataclass
class _Step:
    timestamp: str
    description: str


class CalculationAuditLog:
    """Collects inputs, outputs, and computation steps for auditability."""

    def __init__(self) -> None:
        self._inputs: dict[str, TrackedQuantity] = {}
        self._outputs: dict[str, TrackedQuantity] = {}
        self._steps: list[_Step] = []

    def add_input(self, name: str, tracked_quantity: TrackedQuantity) -> None:
        """Record a named input quantity."""
        self._inputs[name] = tracked_quantity

    def add_output(self, name: str, tracked_quantity: TrackedQuantity) -> None:
        """Record a named output quantity."""
        self._outputs[name] = tracked_quantity

    def add_step(self, description: str) -> None:
        """Record a computation step description."""
        self._steps.append(
            _Step(
                timestamp=datetime.now(timezone.utc).isoformat(),
                description=description,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full audit log to a dictionary."""
        return {
            "inputs": {
                name: tq.to_dict() for name, tq in self._inputs.items()
            },
            "outputs": {
                name: tq.to_dict() for name, tq in self._outputs.items()
            },
            "steps": [
                {"timestamp": s.timestamp, "description": s.description}
                for s in self._steps
            ],
        }

    def to_json(self) -> str:
        """Serialize the full audit log to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @property
    def input_names(self) -> list[str]:
        """List of recorded input names."""
        return list(self._inputs.keys())

    @property
    def output_names(self) -> list[str]:
        """List of recorded output names."""
        return list(self._outputs.keys())

    def filter_inputs(self, unit: str) -> dict[str, TrackedQuantity]:
        """Return inputs whose unit string matches *unit*."""
        return {
            name: tq
            for name, tq in self._inputs.items()
            if str(tq.units) == str(tq._quantity.units.__class__(unit))
        }

    def filter_outputs(self, unit: str) -> dict[str, TrackedQuantity]:
        """Return outputs whose unit string matches *unit*."""
        return {
            name: tq
            for name, tq in self._outputs.items()
            if str(tq.units) == str(tq._quantity.units.__class__(unit))
        }

    def to_csv(self) -> str:
        """Export inputs and outputs as a CSV string."""
        lines = ["role,name,magnitude,unit"]
        for name, tq in self._inputs.items():
            lines.append(f"input,{name},{tq.magnitude},{tq.units}")
        for name, tq in self._outputs.items():
            lines.append(f"output,{name},{tq.magnitude},{tq.units}")
        return "\n".join(lines)

    def summary(self) -> str:
        """Return a human-readable summary of the audit log."""
        lines = ["Calculation Audit Log"]
        lines.append(f"  Inputs ({len(self._inputs)}):")
        for name, tq in self._inputs.items():
            lines.append(f"    {name}: {tq.magnitude} {tq.units}")
        lines.append(f"  Outputs ({len(self._outputs)}):")
        for name, tq in self._outputs.items():
            lines.append(f"    {name}: {tq.magnitude} {tq.units}")
        lines.append(f"  Steps ({len(self._steps)}):")
        for step in self._steps:
            lines.append(f"    - {step.description}")
        return "\n".join(lines)
