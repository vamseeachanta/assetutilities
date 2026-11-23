# ABOUTME: Provides the @unit_checked decorator for unit-safe computations.
# ABOUTME: Validates, converts, and tracks units across function boundaries.

from __future__ import annotations

import functools
import inspect
from datetime import datetime, timezone
from typing import Any, Callable

from assetutilities.units.quantity import ProvenanceEntry, TrackedQuantity
from assetutilities.units.registry import get_registry


def unit_checked(**unit_specs: str) -> Callable:
    """Decorator factory that validates and converts units on function arguments.

    Keyword arguments map parameter names to expected pint unit strings.  The
    special key ``_return`` specifies the unit to attach to the return value.

    When a parameter is a ``TrackedQuantity`` it is converted to the expected
    unit (recording provenance), and its magnitude is extracted before the
    function body runs.  Raw ``float`` / ``int`` arguments pass through
    unchanged for backward compatibility.  Mixed arguments (some tracked, some
    raw) are supported.

    The return value is wrapped in a ``TrackedQuantity`` if ``_return`` is
    specified **and** at least one input was a ``TrackedQuantity``.

    Example
    -------
    >>> @unit_checked(length="m", force="N", _return="Pa")
    ... def simple_stress(length, force, area):
    ...     return force / area
    """
    return_unit: str | None = unit_specs.pop("_return", None)

    def decorator(fn: Callable) -> Callable:
        sig = inspect.signature(fn)
        param_names = list(sig.parameters.keys())

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            had_tracked = False
            provenance_entries: list[ProvenanceEntry] = []
            converted_args: dict[str, Any] = {}

            for name, value in bound.arguments.items():
                expected_unit = unit_specs.get(name)

                if isinstance(value, TrackedQuantity):
                    had_tracked = True

                    if expected_unit is not None:
                        converted = value.to(expected_unit)
                        provenance_entries.extend(converted.provenance)
                        converted_args[name] = converted.magnitude
                    else:
                        provenance_entries.extend(value.provenance)
                        converted_args[name] = value.magnitude
                else:
                    converted_args[name] = value

            result = fn(**converted_args)

            if return_unit is not None and had_tracked:
                source = f"{fn.__module__}.{fn.__qualname__}"
                tq = TrackedQuantity(result, return_unit, source=source)
                # Prepend the input provenance so the full history is retained
                tq._provenance = provenance_entries + tq._provenance
                return tq

            return result

        return wrapper

    return decorator
