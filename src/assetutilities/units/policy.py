# ABOUTME: Project-wide unit system enforcement policy.
# ABOUTME: Validates and optionally converts TrackedQuantity to a target unit system.

from __future__ import annotations

from typing import Any

from assetutilities.units.input_parser import UNIT_SYSTEMS
from assetutilities.units.quantity import TrackedQuantity


class UnitSystemPolicy:
    """Enforces a consistent unit system across a project.

    Parameters
    ----------
    system:
        Unit system name — must be a key in UNIT_SYSTEMS (e.g. "SI", "inch",
        "metric_engineering").
    strict:
        If True, ``enforce()`` raises an error when a value uses the wrong
        unit instead of silently converting.
    auto_convert:
        If True, ``enforce()`` converts values to the policy's expected unit.
        Ignored when *strict* is True and the unit does not match.
    """

    def __init__(
        self,
        system: str,
        strict: bool = False,
        auto_convert: bool = True,
    ) -> None:
        if system not in UNIT_SYSTEMS:
            raise ValueError(
                f"Unknown unit system '{system}'. "
                f"Available: {sorted(UNIT_SYSTEMS.keys())}"
            )
        self.system = system
        self.strict = strict
        self.auto_convert = auto_convert
        self._units = UNIT_SYSTEMS[system]

    def validate(
        self,
        tracked_quantity: TrackedQuantity,
        quantity_type: str,
    ) -> bool:
        """Check whether a TrackedQuantity uses the policy's expected unit.

        Returns True if the quantity's unit exactly matches the policy's unit
        for *quantity_type*, or if *quantity_type* is not defined in the policy.
        """
        expected = self._units.get(quantity_type)
        if expected is None:
            return True
        return str(tracked_quantity.units) == str(
            tracked_quantity._quantity.units.__class__(expected)
            if hasattr(tracked_quantity._quantity.units, "__class__")
            else expected
        )

    def enforce(
        self,
        tracked_quantity: TrackedQuantity,
        quantity_type: str,
    ) -> TrackedQuantity:
        """Enforce the policy on a TrackedQuantity.

        If the quantity type is unknown to the policy, returns unchanged.
        If strict mode is on and the unit doesn't match, raises ValueError.
        If auto_convert is on, converts to the expected unit.
        """
        expected = self._units.get(quantity_type)
        if expected is None:
            return tracked_quantity

        if self.validate(tracked_quantity, quantity_type):
            return tracked_quantity

        if self.strict and not self.auto_convert:
            raise ValueError(
                f"Unit policy violation: expected '{expected}' for "
                f"'{quantity_type}', got '{tracked_quantity.units}'"
            )

        return tracked_quantity.to(expected)
