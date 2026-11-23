# ABOUTME: Engineering-friendly exception for unit dimension mismatches.
# ABOUTME: Wraps pint DimensionalityError with clear context about the failing operation.

from __future__ import annotations

from typing import Any, Optional


class UnitMismatchError(Exception):
    """Raised when an operation involves incompatible physical dimensions.

    Provides engineering-friendly messages like:
        "Cannot add 'pascal' to 'meter': incompatible dimensions
         [pressure] vs [length]"
    """

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.original_error = original_error

    @classmethod
    def from_dimensions(
        cls,
        operation: str,
        left_unit: Any,
        right_unit: Any,
        original_error: Optional[Exception] = None,
    ) -> UnitMismatchError:
        """Build a mismatch error with operation context.

        Parameters
        ----------
        operation:
            The arithmetic operation that failed (e.g. "add", "subtract").
        left_unit:
            Unit of the left operand.
        right_unit:
            Unit of the right operand.
        original_error:
            The underlying pint error, if any.
        """
        msg = (
            f"Cannot {operation} '{left_unit}' and '{right_unit}': "
            f"incompatible dimensions"
        )
        return cls(msg, original_error=original_error)
