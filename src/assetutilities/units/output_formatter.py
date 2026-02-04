# ABOUTME: Display formatting and audit trail export for tracked quantities.
# ABOUTME: Converts TrackedQuantity to human-readable strings and exports logs.

from __future__ import annotations

import json
from typing import Any, Optional

from assetutilities.units.quantity import TrackedQuantity
from assetutilities.units.traceability import CalculationAuditLog


class UnitFormatter:
    """Formats TrackedQuantity values for display and exports audit trails."""

    def format_quantity(
        self,
        tracked_quantity: TrackedQuantity,
        target_unit: Optional[str] = None,
        precision: int = 4,
    ) -> str:
        """Format a TrackedQuantity as a human-readable string.

        Parameters
        ----------
        tracked_quantity:
            The quantity to format.
        target_unit:
            If provided, convert to this unit before formatting.
        precision:
            Number of decimal places (default 4).

        Returns
        -------
        A string like ``"12.3456 m"`` or ``"40.5049 ft"`` after conversion.
        """
        if target_unit is not None:
            tracked_quantity = tracked_quantity.to(target_unit)

        magnitude = tracked_quantity.magnitude
        units = tracked_quantity.units
        return f"{magnitude:.{precision}f} {units}"

    def format_with_provenance(
        self,
        tracked_quantity: TrackedQuantity,
        target_unit: Optional[str] = None,
    ) -> str:
        """Format a TrackedQuantity with its full provenance trail.

        Parameters
        ----------
        tracked_quantity:
            The quantity to format.
        target_unit:
            If provided, convert to this unit before formatting.

        Returns
        -------
        A multi-line string showing the value and each provenance entry.
        """
        if target_unit is not None:
            tracked_quantity = tracked_quantity.to(target_unit)

        lines: list[str] = []
        magnitude = tracked_quantity.magnitude
        units = tracked_quantity.units
        lines.append(f"Value: {magnitude} {units}")
        lines.append("Provenance:")

        for entry in tracked_quantity.provenance:
            parts = [f"  [{entry.timestamp.isoformat()}] {entry.operation}"]
            if entry.source:
                parts.append(f"source={entry.source}")
            if entry.from_unit:
                parts.append(f"from={entry.from_unit}")
            if entry.to_unit:
                parts.append(f"to={entry.to_unit}")
            lines.append(" | ".join(parts))

        return "\n".join(lines)

    def export_audit_trail(
        self,
        audit_log: CalculationAuditLog,
        format: str = "json",
    ) -> str:
        """Export a CalculationAuditLog to the requested format.

        Parameters
        ----------
        audit_log:
            The audit log to export.
        format:
            ``"json"`` for machine-readable output or ``"text"`` for
            human-readable output.

        Returns
        -------
        A string in the requested format.

        Raises
        ------
        ValueError
            If *format* is not ``"json"`` or ``"text"``.
        """
        if format == "json":
            return json.dumps(audit_log.to_dict(), indent=2)
        elif format == "text":
            return audit_log.summary()
        else:
            raise ValueError(
                f"Unsupported format '{format}'. Use 'json' or 'text'."
            )
