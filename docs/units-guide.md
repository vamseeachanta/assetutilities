# Engineering Units Guide

How to use the `assetutilities.units` package for unit-safe engineering calculations with full provenance tracking.

## Quick Start

```python
from assetutilities.units import (
    get_registry,
    TrackedQuantity,
    CalculationAuditLog,
    UnitMismatchError,
    UnitSystemPolicy,
    unit_checked,
)

# Create a tracked quantity
pressure = TrackedQuantity(101.325, "kPa", source="atmospheric")
depth = TrackedQuantity(100.0, "m", source="site_survey")

# Convert units — provenance is recorded automatically
pressure_pa = pressure.to("Pa")
print(pressure_pa.magnitude)  # 101325.0
print(len(pressure_pa.provenance))  # 2 (created + converted)

# Arithmetic preserves tracking
force = pressure * TrackedQuantity(4.0, "m**2", source="deck_area")
print(force.magnitude)  # 405.3 kN*m² → depends on pint resolution
```

## Core Components

### Unit Registry

The singleton registry includes standard SI/Imperial units plus custom energy and offshore units.

```python
from assetutilities.units import get_registry

ureg = get_registry()

# Standard units
q = ureg.Quantity(100, "m")

# Custom energy units (BOE, MCF, MMBTU, etc.)
energy = ureg.Quantity(1, "BOE")
print(energy.to("MMBTU"))  # 5.8 MMBTU
```

### TrackedQuantity

Wraps `pint.Quantity` with provenance tracking. Every creation, conversion, and arithmetic operation is recorded.

```python
from assetutilities.units import TrackedQuantity

# Create with source label
thickness = TrackedQuantity(25.0, "mm", source="drawing_rev3")

# Convert (records provenance)
thickness_m = thickness.to("m")
print(thickness_m.magnitude)  # 0.025

# Arithmetic (merges provenance from both operands)
length = TrackedQuantity(10.0, "m", source="field_measurement")
area = thickness_m * length

# Inspect provenance
for entry in area.provenance:
    print(f"  {entry.operation}: {entry.source} → {entry.to_unit}")

# Serialize for storage
data = area.to_dict()
restored = TrackedQuantity.from_dict(data)
```

### @unit_checked Decorator

Validates and converts units at function boundaries. Raw floats pass through for backward compatibility.

```python
from assetutilities.units import TrackedQuantity, unit_checked

@unit_checked(force="N", area="m**2", _return="Pa")
def calc_stress(force, area):
    return force / area

# With TrackedQuantity — converts and wraps result
f = TrackedQuantity(500.0, "kN", source="load_case_1")
a = TrackedQuantity(2.0, "m**2", source="section_props")
stress = calc_stress(f, a)
print(stress)  # TrackedQuantity(250000.0, 'pascal', provenance=...)

# With raw floats — backward compatible
stress_raw = calc_stress(500000.0, 2.0)
print(stress_raw)  # 250000.0 (plain float)
```

## Input Parsing

Parse config files (YAML/JSON) into tracked quantities with automatic unit inference.

```python
from assetutilities.units.input_parser import parse_config_section

config = {
    "water_depth": 120.0,
    "wave_height": 3.5,
    "temperature": 15.0,
    "analysis_name": "storm_case_1",  # non-numeric, passes through
}

parsed = parse_config_section(config, unit_system="SI", source="config.yml")
print(parsed["water_depth"])  # TrackedQuantity(120.0, 'meter', ...)
print(parsed["analysis_name"])  # "storm_case_1" (unchanged)
```

### Unit Systems

Three built-in unit systems for field name inference:

| System | Length | Stress | Force | Temperature |
|--------|--------|--------|-------|-------------|
| `SI` | m | Pa | N | degC |
| `inch` | inch | psi | lbf | degF |
| `metric_engineering` | mm | MPa | kN | degC |

## Error Handling

### UnitMismatchError

Engineering-friendly exception for dimension mismatches. Replaces raw pint errors with clear context.

```python
from assetutilities.units import TrackedQuantity, UnitMismatchError

pressure = TrackedQuantity(100.0, "Pa", source="gauge")
length = TrackedQuantity(5.0, "m", source="tape")

try:
    result = pressure + length
except UnitMismatchError as e:
    print(e)
    # "Cannot add 'pascal' and 'meter': incompatible dimensions"
    print(e.original_error)  # underlying pint.DimensionalityError
```

### UnitSystemPolicy

Enforce a consistent unit system across a project.

```python
from assetutilities.units import TrackedQuantity, UnitSystemPolicy

# Auto-convert mode (default)
policy = UnitSystemPolicy(system="SI", auto_convert=True)
thickness_mm = TrackedQuantity(25.0, "mm", source="drawing")
thickness_si = policy.enforce(thickness_mm, "length")
print(thickness_si)  # 0.025 m (converted, provenance recorded)

# Strict mode — raises on wrong units
strict_policy = UnitSystemPolicy(system="SI", strict=True, auto_convert=False)
try:
    strict_policy.enforce(thickness_mm, "length")
except ValueError as e:
    print(e)  # "Unit policy violation: expected 'm' for 'length', got 'millimeter'"

# Validate without converting
print(policy.validate(thickness_mm, "length"))  # False (mm ≠ m)
```

## Audit Trail

### CalculationAuditLog

Aggregate provenance across an entire calculation for engineering audits.

```python
from assetutilities.units import TrackedQuantity, CalculationAuditLog

audit = CalculationAuditLog()

# Record inputs
E = TrackedQuantity(210e9, "Pa", source="material_cert")
t = TrackedQuantity(0.025, "m", source="drawing")
audit.add_input("E", E)
audit.add_input("t", t)

# Record computation steps
audit.add_step("Calculate buckling stress: sigma_cr = k * E * (t/D)^2")

# Record outputs
sigma_cr = TrackedQuantity(145.8e6, "Pa", source="calculated")
audit.add_output("sigma_cr", sigma_cr)

# Human-readable summary
print(audit.summary())

# JSON export
print(audit.to_json())

# CSV export
print(audit.to_csv())

# Filter by unit
meter_inputs = audit.filter_inputs(unit="m")
print(meter_inputs)  # {"t": TrackedQuantity(0.025, "m", ...)}
```

## Lineage Visualization

Build a directed graph of quantity lineage from an audit log.

```python
from assetutilities.units.visualization import LineageGraph

graph = LineageGraph.from_audit_log(audit)

# Inspect nodes and edges
for node in graph.nodes:
    print(f"  {node['role']}: {node['name']} = {node['value']} {node['unit']}")

for edge in graph.edges:
    print(f"  {edge['source']} → {edge['target']}: {edge['operation']}")

# Export to Graphviz DOT format
dot_str = graph.to_dot()
# Save to file and render: dot -Tsvg lineage.dot -o lineage.svg

# Export to dict for JSON serialization
data = graph.to_dict()
```

## Output Formatting

### FormatTemplate

Control per-quantity-type formatting (precision, scientific notation, suffixes).

```python
from assetutilities.units.output_formatter import FormatTemplate, UnitFormatter

formatter = UnitFormatter()

# One-off template
pressure = TrackedQuantity(101325.0, "Pa", source="calc")
tmpl = FormatTemplate(precision=2, notation="scientific", suffix=" (abs)")
print(formatter.format_quantity(pressure, template=tmpl))
# "1.01e+05 pascal (abs)"

# Register templates for auto-resolution
formatter.register_template("pressure", FormatTemplate(precision=1))
formatter.register_template("length", FormatTemplate(precision=3))

length = TrackedQuantity(12.3456, "m", source="survey")
print(formatter.format_quantity(length))  # "12.346 meter"
```

## Adding Custom Units

Register domain-specific units in the singleton registry.

```python
from assetutilities.units import get_registry

ureg = get_registry()

# Define a custom unit
ureg.define("barrel_per_day = barrel / day = bpd")

q = ureg.Quantity(1000, "bpd")
print(q.to("m**3 / s"))
```

## OrcaFlex Integration (rock-oil-field)

The `rock_oil_field.units.orcaflex_adapter` wraps OrcaFlex parameters with unit tracking.

```python
from rock_oil_field.units.orcaflex_adapter import (
    wrap_orcaflex_value,
    unwrap_for_orcaflex,
    wrap_model_parameters,
    wrap_environment,
)

# Wrap a single value
depth = wrap_orcaflex_value(150.0, "length", source="model_config")
print(depth)  # TrackedQuantity(150.0, 'meter', provenance=1)

# Convert and unwrap for OrcaFlex input
depth_mm = depth.to("mm")
raw_m = unwrap_for_orcaflex(depth_mm, "length")
print(raw_m)  # 150.0 (back to meters)

# Batch wrap model parameters
params = wrap_model_parameters({
    "water_depth": (150.0, "length"),
    "mooring_stiffness": (1200.0, "stiffness"),
    "riser_mass": (25.0, "mass"),
})

# Wrap environment config with unit inference
env = wrap_environment({
    "wave_height": 3.5,
    "water_depth": 120.0,
    "temperature": 15.0,
}, unit_system="SI")
```
