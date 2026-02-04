# ABOUTME: Public API for the engineering units tracking system.
# ABOUTME: Exports registry, tracked quantities, provenance, and audit logging.

"""Engineering units package with provenance tracking.

Provides a singleton pint UnitRegistry with custom energy and offshore units,
TrackedQuantity for unit-aware values with full provenance history, and
CalculationAuditLog for aggregating audit trails across calculations.
"""

from assetutilities.units.quantity import ProvenanceEntry, TrackedQuantity
from assetutilities.units.registry import get_registry
from assetutilities.units.traceability import CalculationAuditLog

__all__ = [
    "get_registry",
    "TrackedQuantity",
    "ProvenanceEntry",
    "CalculationAuditLog",
]

# Lazy import for computation module (Phase 2)
try:
    from assetutilities.units.computation import unit_checked  # noqa: F401

    __all__.append("unit_checked")
except ImportError:
    pass
