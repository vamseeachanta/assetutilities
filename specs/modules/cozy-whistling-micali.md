---
title: Phase 3 — digitalmodel Pilot Integration
description: Apply @unit_checked decorator to plate_buckling.py and replace engineering_units.py
version: 0.1.0
module: engineering-units
work_item: WRK-095
session:
  id: cozy-whistling-micali
  agent: claude-opus-4.5
---

# Phase 3: digitalmodel Pilot Integration

## Scope

Three changes in the `digitalmodel` repo:

### 1. Replace `engineering_units.py` with re-exports

**File**: `digitalmodel/src/digitalmodel/infrastructure/common/engineering_units.py`

- Currently 30 lines of unused code (no imports found anywhere in the codebase)
- Creates a new `pint.UnitRegistry()` on every call (the bug identified in the spec)
- Replace with re-exports from `assetutilities.units`:
  - `get_registry`, `TrackedQuantity`, `unit_checked`
  - Keep backward-compatible `use_unit` function that delegates to the singleton registry
- **Risk**: Zero — no callers exist

### 2. Add `@unit_checked` to `ElasticBucklingCalculator` methods

**File**: `digitalmodel/src/digitalmodel/infrastructure/calculations/plate_buckling.py`

Add decorators to 4 methods on `ElasticBucklingCalculator`:

| Method | Unit Spec |
|--------|-----------|
| `calculate_base_factor` | `youngs_modulus="Pa", thickness="m", breadth="m"` (no `_return` — dimensionless ratio involved) |
| `calculate_longitudinal_buckling_stress` | `youngs_modulus="Pa", thickness="m", breadth="m", length="m", _return="Pa"` |
| `calculate_transverse_buckling_stress` | same as above |
| `calculate_shear_buckling_stress` | same as above |

**Why only ElasticBucklingCalculator**: It's the entry point — `SlendernessCalculator`, `UltimateStrengthCalculator`, and `UsageFactorCalculator` consume its outputs. Adding decorators there would mean double-converting. Start at the boundary.

**Changes required**:
- Add import: `from assetutilities.units import unit_checked`
- Add decorators to 4 methods (no method body changes)
- `poisson_ratio` and `edge_condition` are intentionally NOT in unit specs (dimensionless / enum)

### 3. Create unit-tracking integration tests

**File**: `digitalmodel/tests/test_plate_buckling_units.py` (new)

Tests:
- TrackedQuantity inputs produce same results as raw float inputs
- Passing psi auto-converts to Pa, mm auto-converts to m
- Unit mismatch (passing meters where Pa expected) raises DimensionalityError
- Output carries provenance chain from inputs through calculation
- All existing `test_plate_capacity.py` tests still pass (regression)

## Files Modified

| File | Change |
|------|--------|
| `digitalmodel/src/digitalmodel/infrastructure/common/engineering_units.py` | Replace with re-exports from assetutilities.units |
| `digitalmodel/src/digitalmodel/infrastructure/calculations/plate_buckling.py` | Add `@unit_checked` decorators + import |

## Files Created

| File | Purpose |
|------|---------|
| `digitalmodel/tests/test_plate_buckling_units.py` | Unit-tracking integration tests |

## Verification

1. `cd /mnt/github/workspace-hub/digitalmodel && uv run pytest tests/test_plate_capacity.py -v` — all existing tests pass
2. `cd /mnt/github/workspace-hub/digitalmodel && uv run pytest tests/test_plate_buckling_units.py -v` — new unit-tracking tests pass
3. Verify `from digitalmodel.infrastructure.common.engineering_units import get_registry, TrackedQuantity, unit_checked` works
