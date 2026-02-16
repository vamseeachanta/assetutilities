# ABOUTME: Display formatting and audit trail export for tracked quantities.
# ABOUTME: Converts TrackedQuantity to human-readable strings and exports logs.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from assetutilities.units.quantity import TrackedQuantity
from assetutilities.units.traceability import CalculationAuditLog


@dataclass
class FormatTemplate:
    """Per-quantity-type formatting rules.

    Parameters
    ----------
    precision:
        Number of significant digits or decimal places.
    notation:
        ``"fixed"`` for standard decimal, ``"scientific"`` for exponential.
    suffix:
        Optional string appended after the unit (e.g. ``" (abs)"``).
    """

    precision: int = 4
    notation: str = "fixed"
    suffix: str = ""


class UnitFormatter:
    """Formats TrackedQuantity values for display and exports audit trails."""

    def __init__(self) -> None:
        self._templates: dict[str, FormatTemplate] = {}

    def register_template(
        self, quantity_type: str, template: FormatTemplate
    ) -> None:
        """Register a format template for a quantity type.

        Parameters
        ----------
        quantity_type:
            Dimension name to match (e.g. ``"pressure"``, ``"length"``).
        template:
            Formatting rules to apply for this quantity type.
        """
        self._templates[quantity_type] = template

    def _resolve_template(
        self,
        tracked_quantity: TrackedQuantity,
        template: Optional[FormatTemplate],
    ) -> FormatTemplate:
        """Resolve which template to use for formatting."""
        if template is not None:
            return template

        dimensionality = str(tracked_quantity._quantity.dimensionality)
        for qty_type, registered in self._templates.items():
            if qty_type in dimensionality:
                return registered

        # Check unit string for registered quantity types
        unit_str = str(tracked_quantity.units)
        for qty_type, registered in self._templates.items():
            if qty_type in unit_str:
                return registered

        return FormatTemplate()

    def format_quantity(
        self,
        tracked_quantity: TrackedQuantity,
        target_unit: Optional[str] = None,
        precision: int = 4,
        template: Optional[FormatTemplate] = None,
    ) -> str:
        """Format a TrackedQuantity as a human-readable string.

        Parameters
        ----------
        tracked_quantity:
            The quantity to format.
        target_unit:
            If provided, convert to this unit before formatting.
        precision:
            Number of decimal places (default 4). Overridden by *template*.
        template:
            If provided, uses the template's precision, notation, and suffix.

        Returns
        -------
        A string like ``"12.3456 m"`` or ``"40.5049 ft"`` after conversion.
        """
        if target_unit is not None:
            tracked_quantity = tracked_quantity.to(target_unit)

        tmpl = self._resolve_template(tracked_quantity, template)
        magnitude = tracked_quantity.magnitude
        units = tracked_quantity.units

        if tmpl.notation == "scientific":
            fmt_spec = f".{tmpl.precision}e"
        else:
            fmt_spec = f".{tmpl.precision}f"

        return f"{magnitude:{fmt_spec}} {units}{tmpl.suffix}"

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
