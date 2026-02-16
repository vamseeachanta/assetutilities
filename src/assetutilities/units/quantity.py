# ABOUTME: TrackedQuantity wraps pint.Quantity with provenance tracking.
# ABOUTME: Records creation, conversion, and arithmetic history for audit trails.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

import pint

from assetutilities.units.registry import get_registry


@dataclass
class ProvenanceEntry:
    """A single provenance record for a tracked quantity."""

    timestamp: datetime
    operation: str
    source: str
    from_unit: Optional[str] = None
    to_unit: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "source": self.source,
            "from_unit": self.from_unit,
            "to_unit": self.to_unit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceEntry:
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            operation=data["operation"],
            source=data["source"],
            from_unit=data.get("from_unit"),
            to_unit=data.get("to_unit"),
        )


class TrackedQuantity:
    """A pint.Quantity wrapper that records provenance for every operation."""

    def __init__(
        self,
        value: Any,
        unit: str,
        source: str = "",
        registry: Any = None,
    ) -> None:
        ureg = registry or get_registry()
        self._quantity = ureg.Quantity(value, unit)
        self._provenance: list[ProvenanceEntry] = [
            ProvenanceEntry(
                timestamp=datetime.now(timezone.utc),
                operation="created",
                source=source,
                from_unit=None,
                to_unit=str(self._quantity.units),
            )
        ]

    @property
    def magnitude(self) -> Any:
        """Raw numeric value (float or ndarray)."""
        return self._quantity.magnitude

    @property
    def units(self) -> Any:
        """Pint unit object."""
        return self._quantity.units

    @property
    def provenance(self) -> list[ProvenanceEntry]:
        """Full provenance history."""
        return list(self._provenance)

    @property
    def dimensions(self) -> str:
        """Human-readable dimensionality string (e.g. '[length]', '[mass] / [time] ** 2')."""
        return str(self._quantity.dimensionality)

    def is_compatible(self, other: Any) -> bool:
        """Check if this quantity is dimensionally compatible with *other*.

        *other* can be a TrackedQuantity or a unit string (e.g. ``"ft"``).
        """
        if isinstance(other, str):
            ureg = get_registry()
            other_qty = ureg.Quantity(1, other)
        elif isinstance(other, TrackedQuantity):
            other_qty = other._quantity
        else:
            other_qty = other
        return self._quantity.is_compatible_with(other_qty)

    def check_dimensions(self, expected: str) -> None:
        """Assert dimensional compatibility; raise ``ValueError`` on mismatch.

        *expected* can be a dimensionality string (e.g. ``"[length]"``) or a
        unit string (e.g. ``"ft"``).
        """
        ureg = get_registry()
        # Try as a dimensionality string first (contains '[')
        if "[" in expected:
            actual = str(self._quantity.dimensionality)
            if actual != expected:
                raise ValueError(
                    f"Dimension mismatch: quantity has {actual}, "
                    f"expected {expected}"
                )
        else:
            # Treat as a unit string
            ref_qty = ureg.Quantity(1, expected)
            if not self._quantity.is_compatible_with(ref_qty):
                actual = str(self._quantity.dimensionality)
                expected_dim = str(ref_qty.dimensionality)
                raise ValueError(
                    f"Dimension mismatch: quantity has {actual}, "
                    f"expected {expected_dim} (unit '{expected}')"
                )

    def to(self, unit: str) -> TrackedQuantity:
        """Convert to a different unit and record the conversion."""
        from_unit = str(self._quantity.units)
        converted = self._quantity.to(unit)

        result = TrackedQuantity.__new__(TrackedQuantity)
        result._quantity = converted
        result._provenance = list(self._provenance)
        result._provenance.append(
            ProvenanceEntry(
                timestamp=datetime.now(timezone.utc),
                operation="converted",
                source="",
                from_unit=from_unit,
                to_unit=str(converted.units),
            )
        )
        return result

    def __float__(self) -> float:
        return float(self._quantity.magnitude)

    def __repr__(self) -> str:
        return (
            f"TrackedQuantity({self._quantity.magnitude}, "
            f"'{self._quantity.units}', "
            f"provenance={len(self._provenance)})"
        )

    # --- Arithmetic ---

    @staticmethod
    def _from_pint(
        quantity: Any,
        operation: str,
        left_prov: list[ProvenanceEntry],
        right_prov: list[ProvenanceEntry],
    ) -> TrackedQuantity:
        """Build a TrackedQuantity from a raw pint Quantity after arithmetic."""
        result = TrackedQuantity.__new__(TrackedQuantity)
        result._quantity = quantity
        result._provenance = list(left_prov) + list(right_prov)
        result._provenance.append(
            ProvenanceEntry(
                timestamp=datetime.now(timezone.utc),
                operation=operation,
                source="",
                from_unit=None,
                to_unit=str(quantity.units),
            )
        )
        return result

    def _other_prov(self, other: Any) -> list[ProvenanceEntry]:
        if isinstance(other, TrackedQuantity):
            return list(other._provenance)
        return []

    def _other_qty(self, other: Any) -> Any:
        if isinstance(other, TrackedQuantity):
            return other._quantity
        return other

    def _arithmetic_op(
        self, other: Any, operation: str, op_func: Any
    ) -> TrackedQuantity:
        """Execute an arithmetic operation with engineering-friendly error handling."""
        try:
            result_qty = op_func(self._quantity, self._other_qty(other))
        except pint.errors.DimensionalityError as e:
            from assetutilities.units.exceptions import UnitMismatchError

            other_units = (
                other.units if isinstance(other, TrackedQuantity) else other
            )
            raise UnitMismatchError.from_dimensions(
                operation=operation,
                left_unit=self.units,
                right_unit=other_units,
                original_error=e,
            ) from e
        return self._from_pint(
            result_qty, operation, self._provenance, self._other_prov(other)
        )

    def __add__(self, other: Any) -> TrackedQuantity:
        return self._arithmetic_op(
            other, "add", lambda a, b: a + b
        )

    def __sub__(self, other: Any) -> TrackedQuantity:
        return self._arithmetic_op(
            other, "subtract", lambda a, b: a - b
        )

    def __mul__(self, other: Any) -> TrackedQuantity:
        return self._from_pint(
            self._quantity * self._other_qty(other),
            "multiply",
            self._provenance,
            self._other_prov(other),
        )

    def __truediv__(self, other: Any) -> TrackedQuantity:
        return self._from_pint(
            self._quantity / self._other_qty(other),
            "divide",
            self._provenance,
            self._other_prov(other),
        )

    # --- Serialization ---

    def to_dict(self) -> dict[str, Any]:
        mag = self._quantity.magnitude
        if isinstance(mag, np.ndarray):
            mag_serialized = mag.tolist()
        else:
            mag_serialized = mag
        return {
            "magnitude": mag_serialized,
            "unit": str(self._quantity.units),
            "provenance": [p.to_dict() for p in self._provenance],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrackedQuantity:
        tq = cls(data["magnitude"], data["unit"])
        tq._provenance = [
            ProvenanceEntry.from_dict(p) for p in data.get("provenance", [])
        ]
        return tq
