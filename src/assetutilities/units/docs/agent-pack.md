# Units module knowledge pack

| Header | Value |
| --- | --- |
| Module | `units` |
| Repository | `assetutilities` |
| Path | `src/assetutilities/units` |
| Pack revision | 1, 2026-10-15 |
| Code revision | `8c8e83ef0f35400c050a45c9981b997e44b427dd` |
| Analysis family | Python calculations; registry family `EC` (engineering calculations) |
| Quality role | Calculations quality manager |
| Status | DRAFT; independent clearance pending |

## 1. Purpose and scope

Provenance tracking is implemented by `TrackedQuantity`: creation records a timestamp and source, conversion appends an entry, and arithmetic merges operand histories. [src/assetutilities/units/quantity.py:L51-L68] [src/assetutilities/units/quantity.py:L130-L147] [src/assetutilities/units/quantity.py:L161-L181]

Parsing wraps numeric configuration values by exact field-name lookup or an explicit Pint unit; `parse_config_section` traverses a flat dictionary rather than reading YAML or JSON files. [src/assetutilities/units/input_parser.py:L95-L116] [src/assetutilities/units/input_parser.py:L119-L148]

Policy validates exact units and converts to one of the configured systems; formatting produces strings, provenance text, and JSON/text audit exports. [src/assetutilities/units/policy.py:L28-L87] [src/assetutilities/units/output_formatter.py:L75-L111] [src/assetutilities/units/output_formatter.py:L113-L183]

The routing registry records stability as `active`; it does not establish independent engineering qualification. [docs/registry/module-routing.yaml:L61-L66]

The decorator converts tracked arguments to magnitudes, permits raw arguments unchanged, and wraps a return only when a return unit is supplied and an input was tracked. [src/assetutilities/units/computation.py:L47-L76]

## Revision history

| Revision | Date | Change and reason |
| --- | --- | --- |
| 0 | 2026-10-15 | Initial module knowledge pack. |
| 1 | 2026-10-15 | Reclassify round-trip evidence, expose the independent-check gap, define the family code and clarify source and unit-alias limits. |

## 2. Inputs and outputs

### Inputs

| Entry point | Input, unit and permitted form | Default and source | Evidence |
| --- | --- | --- | --- |
| `TrackedQuantity(value, unit, source, registry)` | Scalar or array magnitude in the explicit Pint unit string; no module range bound | Source empty; shared registry unless supplied | [src/assetutilities/units/quantity.py:L51-L68] [src/assetutilities/units/quantity.py:L241-L261] |
| `TrackedQuantity.to(unit)` | Target Pint unit expression; incompatible conversion delegated to Pint | Required | [src/assetutilities/units/quantity.py:L130-L147] |
| `parse_config_value` | Numeric magnitude, exact field name; explicit unit overrides inference; other values pass through | `unit_system="SI"`, `explicit_unit=None`, `source="config"` | [src/assetutilities/units/input_parser.py:L64-L70] [src/assetutilities/units/input_parser.py:L95-L116] |
| `parse_config_section` | Flat dictionary; numeric values interpreted in selected system | SI, source `config` | [src/assetutilities/units/input_parser.py:L119-L148] |
| `convert_energy_units` | Float in source unit; source/target exact keys of `EnergyUnitMapping` | All arguments required | [src/assetutilities/units/domains/energy.py:L8-L42] [src/assetutilities/units/domains/energy.py:L68-L85] |
| `convert_speed`, `convert_length`, `convert_temperature`, `convert_pressure` | Float or `None`, exact source/target keys of corresponding mapping | Targets `m/s`, `m`, `celsius`, `hPa` respectively | [src/assetutilities/units/domains/metocean.py:L10-L43] [src/assetutilities/units/domains/metocean.py:L80-L169] |
| `UnitSystemPolicy` | System key and two boolean controls; exact unit validation | `strict=False`, `auto_convert=True`; see section 6 | [src/assetutilities/units/policy.py:L28-L42] [src/assetutilities/units/policy.py:L54-L87] |
| `UnitFormatter.format_quantity` | Tracked value, optional target unit and `FormatTemplate` | Template: precision 4 decimal places, fixed notation, empty suffix; direct precision argument is ineffective | [src/assetutilities/units/output_formatter.py:L28-L30] [src/assetutilities/units/output_formatter.py:L75-L111] |

The inference systems are `inch` (inch, psi, lbf, lbf·inch, degF, lb), `SI` (m, Pa, N, N·m, degC, kg) and `metric_engineering` (mm, MPa, kN, kN·m, degC, kg), in length, stress/pressure, force, moment, temperature and mass order. [src/assetutilities/units/input_parser.py:L10-L38]

Unit strings are not normalized by the adapter lookup: energy uses uppercase keys; metocean uses the literal mapping spellings, including `nm` for nautical miles. [src/assetutilities/units/domains/energy.py:L8-L35] [src/assetutilities/units/domains/metocean.py:L10-L43]

No coordinate frame, origin, phase or physical sign convention is attached by quantity creation or these converter wrappers; the caller supplies physical meaning and signed magnitudes. [src/assetutilities/units/quantity.py:L51-L68] [src/assetutilities/units/domains/energy.py:L82-L85] [src/assetutilities/units/domains/metocean.py:L74-L77]

### Outputs

| Entry point | Output and unit convention | Evidence |
| --- | --- | --- |
| `to`, arithmetic | New tracked quantity; Pint-selected units; original history retained | [src/assetutilities/units/quantity.py:L130-L147] [src/assetutilities/units/quantity.py:L193-L239] |
| `parse_config_value`, `parse_config_section` | Tracked quantity or original raw value; dictionary preserves keys | [src/assetutilities/units/input_parser.py:L95-L116] [src/assetutilities/units/input_parser.py:L143-L148] |
| Domain converters | Plain float in requested target unit; metocean returns `None` immediately for `None` | [src/assetutilities/units/domains/energy.py:L82-L85] [src/assetutilities/units/domains/metocean.py:L57-L77] |
| `to_dict`, `from_dict` | `magnitude`, canonical unit string, provenance entries; arrays serialized as lists | [src/assetutilities/units/quantity.py:L243-L261] |
| `CalculationAuditLog` | JSON/dictionary with inputs, outputs, steps; CSV columns role/name/magnitude/unit | [src/assetutilities/units/traceability.py:L45-L62] [src/assetutilities/units/traceability.py:L90-L97] |
| Formatter and graph | Display string, provenance text, JSON/text audit; graph dictionary, DOT, SVG or HTML | [src/assetutilities/units/output_formatter.py:L99-L150] [src/assetutilities/units/output_formatter.py:L176-L183] [src/assetutilities/units/visualization.py:L75-L109] [src/assetutilities/units/visualization.py:L137-L143] |

## 3. Method and governing standards

`get_registry` lazily creates one Pint registry under a thread lock and adds custom energy definitions; conversion is delegated to `Quantity.to`, rather than a module-local numerical solver. [src/assetutilities/units/registry.py:L30-L43] [src/assetutilities/units/domains/energy.py:L82-L85] [src/assetutilities/units/domains/metocean.py:L74-L77]

UNVERIFIED: the physical applicability and published provenance of the custom BOE, MCF, SCF and TOE energy factors are not established by the source comments; gas-named quantities are defined as energy equivalents, not geometric gas volumes; issue pending (3). [src/assetutilities/units/registry.py:L12-L24]

UNVERIFIED: the standards edition and clause basis of Pint's inherited definitions, and a calculation `Citation` sidecar for custom definitions, are not established by this module; no standards qualification is claimed; issue pending (3). [src/assetutilities/units/registry.py:L12-L43]

Arithmetic addition/subtraction catches Pint dimensionality errors and wraps them as `UnitMismatchError`; multiplication/division directly use Pint and merge provenance. [src/assetutilities/units/quantity.py:L193-L239]

Dimension checks compare an explicit bracketed dimensionality string literally, or test compatibility with a supplied unit expression. [src/assetutilities/units/quantity.py:L104-L128]

Offshore field names and systems are exported as separate maps; the base parser only consults `FIELD_QUANTITY_MAP`, so importing the offshore maps does not extend parsing automatically. [src/assetutilities/units/domains/offshore.py:L8-L31] [src/assetutilities/units/input_parser.py:L101-L116]

A lineage graph connects every input to every output for each logged step; it is an aggregate visualization, not proof of specific mathematical dependencies. [src/assetutilities/units/visualization.py:L22-L63]

## 4. Worked examples and validation status

Validated examples: 0. No independent hand or published-factor check is established; V1 checks consistency only and does not satisfy G2.

The following node IDs use inline test inputs; their offline outcomes are recorded at the pinned code revision, and tolerances are those enforced by the cited assertions. [tests/unit/test_integration.py:L53-L64] [tests/unit/test_input_parser.py:L15-L25] [tests/unit/test_domains_energy.py:L30-L32] [tests/unit/test_format_templates.py:L50-L59]

| ID and class | Source and inline input | Expected output and tolerance basis | Existing test node ID | Offline result |
| --- | --- | --- | --- | --- |
| V1 consistency round trip | Identity under forward/reverse conversion; 100 m → ft → m | 100 m, relative tolerance 1e-10 (absolute 1e-8 m); 3 provenance entries; checks reversibility, not an independent absolute factor | `tests/unit/test_integration.py::TestConfigToComputeRoundTrip::test_si_to_imperial_round_trip` | PASS at BASE and AFTER |
| R1 regression parsing | Literal fixture: thickness 0.025, SI | 0.025 m; shipped assertion uses `pytest.approx`; supplemental check requires 0 m error and exact canonical unit string | `tests/unit/test_input_parser.py::TestParseConfigValue::test_numeric_with_known_field_returns_tracked_quantity` | PASS at BASE and AFTER |
| R2 regression energy | Registry definition repeated in test: 1 BOE | 5.8 MMBTU, relative 1e-3; compatibility only, custom-factor applicability unverified | `tests/unit/test_domains_energy.py::TestEnergyConversionsMatchWorldEnergyData::test_boe_to_mmbtu` | PASS at BASE and AFTER |
| R3 regression formatting | Fixture 12.3456 m, explicit `FormatTemplate(precision=2)` | String contains `12.35`; 2 decimal places; substring assertion only | `tests/unit/test_format_templates.py::TestFormatterWithTemplate::test_formatter_with_template` | PASS at BASE and AFTER |

V1 evidence: [tests/unit/test_integration.py:L53-L64] R1 evidence: [tests/unit/test_input_parser.py:L15-L20] R2 evidence: [tests/unit/test_domains_energy.py:L30-L32] R3 evidence: [tests/unit/test_format_templates.py:L20-L23] [tests/unit/test_format_templates.py:L50-L59]

## 5. QA gates

A reachable source for AQG r0, sections 9–11, is unverified; see section 10, issue pending (6). The gate and ownership assignments below remain provisional until that source is available.

The cited AQG r0, section 10, Python calculations row assigns G0 inputs/units/citations, G1 imports/tests, G2 hand or published check, G3 and G4 not applicable; section 9 assigns G5 evidence traceability. (AQG r0, sections 9–10.)

Checks below define acceptance for future changes; a known defect probe is explicitly distinct from an existing passing regression test. [src/assetutilities/units/policy.py:L78-L87] [src/assetutilities/units/output_formatter.py:L99-L111]

| Gate | Applicability | Module-specific check and numeric pass criterion | Executable evidence |
| --- | --- | --- | --- |
| G0 | Applicable | U01: `parse_config_value(0.025,"thickness")` returns 0.025 m with 0 m magnitude error and canonical meter unit | R1 node; [tests/unit/test_input_parser.py:L15-L20] |
| G0 | Applicable | U02: adding 1 Pa and 1 m produces exactly 1 `UnitMismatchError`, 0 numeric results (count) | `tests/unit/test_quantity.py::TestTrackedQuantityArithmetic::test_add_incompatible_raises`; [tests/unit/test_quantity.py:L52-L56] |
| G0 | Applicable | U03: `UnitSystemPolicy("SI").enforce(1000 mm,"length")` yields 1 m within 1e-6 m | `tests/unit/test_policy.py::TestPolicyEnforce::test_enforce_auto_convert_converts`; [tests/unit/test_policy.py:L57-L62] |
| G0 | Applicable | U04: strict policy rejects 1000 mm with exactly 1 exception (count), including when auto conversion is true; defect probe currently returns 1 m instead | Evaluate `UnitSystemPolicy("SI", strict=True).enforce(TrackedQuantity(1000,"mm"),"length")`; [src/assetutilities/units/policy.py:L20-L25] [src/assetutilities/units/policy.py:L78-L87] |
| G0 | Applicable | U10: `get_registry` custom definitions require published source, edition and applicability metadata; 0 unresolved definitions (count); current source gap remains open | Inspect definitions and resolve their source metadata; [src/assetutilities/units/registry.py:L12-L24] |
| G1 | Applicable | U05: import/execute all 17 direct-import test files and 7 routing tests; 0 failed test nodes (count) | Test inventory in section 10; [tests/docs/test_assetutilities_routing_contract.py:L49-L121] |
| G2 | Applicable; unmet | U06: an independent hand or published-factor check is required; 0 validated examples (count). V1 has round-trip error ≤1e-8 m at 100 m and exactly 3 provenance entries, but does not check an absolute conversion factor | V1 consistency evidence only; [tests/unit/test_integration.py:L53-L64]; issue pending (3) |
| G3 | NOT_APPLICABLE | No dynamics calculation in this conversion path | [src/assetutilities/units/quantity.py:L130-L147] [src/assetutilities/units/domains/metocean.py:L74-L77] |
| G4 | NOT_APPLICABLE | No diffraction input, mesh or hydrostatics calculation in this conversion path | [src/assetutilities/units/quantity.py:L130-L147] [src/assetutilities/units/domains/energy.py:L82-L85] |
| G5 | Applicable | U07: `format_quantity` with explicit template on 12.3456 m contains 12.35 with 2 decimal places (digits) | R3 node; [tests/unit/test_format_templates.py:L50-L59] |
| G5 | Applicable | U08: `CalculationAuditLog.to_csv` emits exactly 4 lines (count) for 2 inputs and 1 output; JSON contains both inputs, output and exactly 1 step (count) | `tests/unit/test_integration.py::TestAuditLogLifecycle::test_full_audit_cycle`; [tests/unit/test_integration.py:L86-L111] |
| G5 | Applicable | U09: `format_quantity(TrackedQuantity(100,"Pa"),precision=2)` emits exactly 2 fractional digits; defect probe currently emits 4 digits | Evaluate exact string, not substring; [src/assetutilities/units/output_formatter.py:L75-L111] [tests/unit/test_output_formatter.py:L38-L40] |

G5 requires retaining node outcomes and the code pin with audit evidence; a passing audit serialization test alone does not constitute independent clearance. (AQG r0, sections 9 and 11.)

## 6. Known failure modes and pitfalls

| Symptom | Cause and detection | Incident reference and date | Evidence |
| --- | --- | --- | --- |
| Silent conversion in strict mode or with both switches false | `enforce` raises only for strict true AND auto_convert false; U04; no existing detection test for the other switch combinations | issue pending (2); 2026-10-15 | [src/assetutilities/units/policy.py:L20-L25] [src/assetutilities/units/policy.py:L78-L87] [tests/unit/test_policy.py:L70-L86] |
| Direct precision ignored; current test still passes | Resolved template supplies precision; assertion accepts a substring of the wrong result; U09; no exact-output detection check exists in the shipped test | issue pending (1); 2026-10-15 | [src/assetutilities/units/output_formatter.py:L99-L111] [tests/unit/test_output_formatter.py:L38-L40] |
| `nm` silently changes meaning between entry points | Domain length mapping interprets `nm` as nautical miles; `TrackedQuantity` and explicit parser units use Pint, where `nm` means nanometres; no detection check exists | Contract limitation; callers shall use unambiguous unit names | [src/assetutilities/units/domains/metocean.py:L18-L26] [src/assetutilities/units/input_parser.py:L95-L116] [src/assetutilities/units/quantity.py:L51-L68] |
| Unknown fields and nonnumeric values remain raw | Parser returns before validation; U01 covers known fields only; callers shall reject untracked required inputs | Contract limitation, not a recorded incident | [src/assetutilities/units/input_parser.py:L95-L116] |
| Unknown policy quantity type passes validation | Missing policy rule returns true and enforcement returns original quantity | Contract limitation, not a recorded incident | [src/assetutilities/units/policy.py:L54-L56] [src/assetutilities/units/policy.py:L74-L76] |
| Raw decorator inputs bypass unit checks | Only tracked quantities are converted; U05 exercises backward compatibility, not physical validity of raw inputs | Contract limitation, not a recorded incident | [src/assetutilities/units/computation.py:L51-L76] [tests/unit/test_computation.py:L22-L31] |
| Custom gas/energy aliases mistaken for volumetric or universal commodity factors | Definitions express energy equivalents; U06 cannot validate these absolute factors | issue pending (3); 2026-10-15; no published-factor detection check exists | [src/assetutilities/units/registry.py:L15-L24] |
| Pressure template selection may fall back | Template matching is substring matching on dimensionality then unit text, not a quantity-type registry | Use explicit templates; no reported incident | [src/assetutilities/units/output_formatter.py:L53-L73] |

## 7. Lessons log

| Date | Change reference | Lesson | Evidence | Pack change | Shared-log entry |
| --- | --- | --- | --- | --- | --- |
| 2026-10-15 | Pack revision 0 | A substring assertion does not establish requested decimal precision | [tests/unit/test_output_formatter.py:L38-L40] [src/assetutilities/units/output_formatter.py:L102-L111] | U09 and precision pitfall added | issue pending (1) |
| 2026-10-15 | Pack revision 0 | Round-trip success does not establish commodity factor provenance | [tests/unit/test_integration.py:L53-L64] [src/assetutilities/units/registry.py:L15-L24] | Validation class and factor gap separated | issue pending (3) |

## 8. Ownership

Review assignment: calculations quality manager; deputy role: calculations deputy quality manager; producing role: module documentation contributor; escalation route: calculations quality manager, then the maintainer for scope or acceptance changes. (AQG r0, section 11.)

UNVERIFIED: an appointed deputy and durable clearance record are not established; this draft assigns role names only and claims no completed second-provider review; issue pending (4).

## 9. Dependencies and duplicate conversions

The implementation uses Pint, NumPy and standard-library data/time/serialization utilities; the declared Pint constraint is `>=0.23,<1.0`. [src/assetutilities/units/quantity.py:L6-L15] [src/assetutilities/units/registry.py:L4-L6] [pyproject.toml:L65-L65]

SVG rendering optionally imports Graphviz and calls its renderer; HTML rendering builds a table without that dependency. [src/assetutilities/units/visualization.py:L105-L135] [src/assetutilities/units/visualization.py:L137-L194]

The routing inventory links units to constants/calculations and identifies `common` visualization helpers separately. [docs/maps/assetutilities-operator-map.md:L10-L16]

The duplicate-search scope is the repository, including `scripts/`; the following inventory distinguishes physical unit conversions, local factors and related coordinate transformations. Evidence is pinned per row.

| Location | Other conversion path or table | Evidence |
| --- | --- | --- |
| `constants/conversions.py` | Independent pressure, length, force, mass, temperature helpers; depth-to-pressure calculation | [src/assetutilities/constants/conversions.py:L7-L196] |
| `calculations/drilling_riser.py` | Local mud-weight/depth to pressure factor and use | [src/assetutilities/calculations/drilling_riser.py:L27-L28] [src/assetutilities/calculations/drilling_riser.py:L241-L266] |
| `calculations/riser_dynamics.py` | Degrees-to-radians inside `tow_out_catenary_tension` | [src/assetutilities/calculations/riser_dynamics.py:L6-L44] |
| `common/visualization/visualization_common.py` | Local degree/radian conversion for polar arrows and images | [src/assetutilities/common/visualization/visualization_common.py:L96-L104] [src/assetutilities/common/visualization/visualization_common.py:L291-L299] |
| `common/visualization/visualization_polar.py` | Local degree/radian conversion for polar data and axes | [src/assetutilities/common/visualization/visualization_polar.py:L150-L183] |
| `common/transform.py` | Coordinate projection via UTM/pyproj; related transformation, not a scalar unit table | [src/assetutilities/common/transform.py:L19-L88] |
| `tests/unit/test_domains_metocean.py` | Hardcoded speed, length and pressure factor tables; temperature offsets | [tests/unit/test_domains_metocean.py:L17-L20] [tests/unit/test_domains_metocean.py:L58-L63] [tests/unit/test_domains_metocean.py:L107-L120] [tests/unit/test_domains_metocean.py:L133-L138] |
| `tests/unit/test_domains_energy.py`, `test_computation.py` | Repeated commodity factors and pressure conversion expectation | [tests/unit/test_domains_energy.py:L30-L104] [tests/unit/test_computation.py:L46-L58] |
| `src/assetutilities/tests/calculations/test_riser_dynamics.py` | Local degrees-to-radians in the independent expected-value expression | [src/assetutilities/tests/calculations/test_riser_dynamics.py:L77-L85] |
| `docs/sub_mathcad/2024-mathcad_analysis.md` | Documentation example converts azimuth degrees to radians inside trigonometry; recorded as a duplicate expression only | [docs/sub_mathcad/2024-mathcad_analysis.md:L385-L388] |
| `tests/unit/test_constants.py`, `tests/test_casing_grades.py` | Expected conversion factors and inline inch/metre conversion in casing tests | [tests/unit/test_constants.py:L187-L290] [tests/test_casing_grades.py:L34-L42] |

Search observation: no physical unit-conversion function or table was found under `scripts/`; its unit-related code match routes units changes to tests, rather than converting quantities. [scripts/ci/select_test_targets.py:L75-L80]

## 10. Coverage and open items

### Files and tests read

All module Python files were read: `__init__`, `registry`, `quantity`, `computation`, `input_parser`, `policy`, `output_formatter`, `traceability`, `exceptions`, `visualization`, and `domains/__init__`, `domains/energy`, `domains/metocean`, `domains/offshore`. [src/assetutilities/units/__init__.py:L1-L32] [src/assetutilities/units/registry.py:L1-L43] [src/assetutilities/units/quantity.py:L1-L261] [src/assetutilities/units/computation.py:L1-L80] [src/assetutilities/units/input_parser.py:L1-L148] [src/assetutilities/units/policy.py:L1-L87] [src/assetutilities/units/output_formatter.py:L1-L183] [src/assetutilities/units/traceability.py:L1-L111] [src/assetutilities/units/exceptions.py:L1-L50] [src/assetutilities/units/visualization.py:L1-L194] [src/assetutilities/units/domains/__init__.py:L1-L6] [src/assetutilities/units/domains/energy.py:L1-L85] [src/assetutilities/units/domains/metocean.py:L1-L169] [src/assetutilities/units/domains/offshore.py:L1-L31]

Module documentation found and read: `docs/units-guide.md`, `docs/README.md`, `docs/maps/assetutilities-operator-map.md`, `docs/registry/module-routing.yaml`, `README.md`, `MODULE_STRUCTURE.md`; the raw documentation mention of Pint was also inspected. [docs/units-guide.md:L1-L309] [docs/README.md:L14-L14] [docs/maps/assetutilities-operator-map.md:L16-L16] [docs/registry/module-routing.yaml:L61-L66] [README.md:L39-L39] [MODULE_STRUCTURE.md:L56-L64] [docs/sub_latex/latex_various_methods.md:L47-L47]

| Test file read | Test functions | Evidence |
| --- | --- | --- |
| `tests/unit/test_computation.py` | 9 | [tests/unit/test_computation.py:L1-L93] |
| `tests/unit/test_dimensions.py` | 16 | [tests/unit/test_dimensions.py:L1-L93] |
| `tests/unit/test_domains_energy.py` | 23 | [tests/unit/test_domains_energy.py:L1-L122] |
| `tests/unit/test_domains_metocean.py` | 33 | [tests/unit/test_domains_metocean.py:L1-L198] |
| `tests/unit/test_domains_offshore.py` | 16 | [tests/unit/test_domains_offshore.py:L1-L66] |
| `tests/unit/test_exceptions.py` | 9 | [tests/unit/test_exceptions.py:L1-L68] |
| `tests/unit/test_format_templates.py` | 8 | [tests/unit/test_format_templates.py:L1-L102] |
| `tests/unit/test_input_parser.py` | 15 | [tests/unit/test_input_parser.py:L1-L108] |
| `tests/unit/test_integration.py` | 12 | [tests/unit/test_integration.py:L1-L248] |
| `tests/unit/test_output_formatter.py` | 9 | [tests/unit/test_output_formatter.py:L1-L84] |
| `tests/unit/test_policy.py` | 15 | [tests/unit/test_policy.py:L1-L100] |
| `tests/unit/test_quantity.py` | 15 | [tests/unit/test_quantity.py:L1-L96] |
| `tests/unit/test_registry.py` | 11 | [tests/unit/test_registry.py:L1-L80] |
| `tests/unit/test_traceability.py` | 6 | [tests/unit/test_traceability.py:L1-L57] |
| `tests/unit/test_traceability_extended.py` | 7 | [tests/unit/test_traceability_extended.py:L1-L112] |
| `tests/unit/test_visualization.py` | 10 | [tests/unit/test_visualization.py:L1-L173] |
| `tests/unit/test_visualization_rendering.py` | 9 | [tests/unit/test_visualization_rendering.py:L1-L88] |

Run record for pack revision 1: BASE and AFTER each collected 230 nodes: 226 passed, 4 failed, 0 skipped, 0 NOT_RUN. The 223 module nodes comprise 222 passed and 1 environment failure; the 7 routing nodes comprise 4 passed and 3 baseline failures. The Graphviz Python package was installed, so `tests/unit/test_visualization_rendering.py::TestToSvg::test_svg_returns_string` ran and failed with `graphviz.backend.execute.ExecutableNotFound` because the system `dot` executable is absent. The three routing failures remain those listed below. Reading `origin/main` confirms the same routing assertions and missing domain entries, and the same SVG test and rendering code. No failure is introduced by these documentation edits.

Command form for both completed runs: `uv run --no-project --with 'pytest>=7.4,<9' --with pytest-asyncio --with numpy --with 'pint>=0.23,<1.0' --with pyyaml --with graphviz python -m pytest <17 module test paths listed above> tests/docs/test_assetutilities_routing_contract.py -q -rA -p no:cacheprovider --basetemp=<scratch>`. The first invocation with pytest 9 could not collect because `tests/conftest.py` implements the removed `pytest_ignore_collect(path, config)` hook signature; pytest 8 completed collection without modifying test selection or assertions. The code pin above remains unchanged.

### Open items and clearance conditions

| Item | Required disposition | Responsible role | Tracking |
| --- | --- | --- | --- |
| Direct precision ignored and weak substring regression | Add exact-output coverage and reconcile public precision semantics | Module maintainer | issue pending (1); section 6 |
| Strict/automatic policy combinations contradict documented controls | Cover all four switch combinations and reconcile enforcement semantics | Module maintainer | issue pending (2); section 6 |
| No validated example; unsourced custom factors and inherited definition basis | V1 is a consistency check, leaving G2 unmet and validated examples at 0. Resolve both section-3 UNVERIFIED claims; document published source/edition, factor applicability, and citation sidecar decision; add independent absolute benchmarks | Module maintainer | issue pending (3); [src/assetutilities/units/registry.py:L12-L43] |
| Appointed deputy and independent clearance | Resolve section-8 UNVERIFIED claim and replace pending issue references after issue creation | Calculations quality manager | issue pending (4) |
| Repository routing baseline | The operator map, registry and module structure omit the tracked workflow API domain; the three existing contract assertions fail unchanged at BASE | Module maintainer | issue pending (5); [tests/docs/test_assetutilities_routing_contract.py:L83-L103] [src/assetutilities/workflow_api/__init__.py:L9-L22] |
| AQG source and provisional assignments | UNVERIFIED: supply a reachable source for AQG r0, sections 9–11, before accepting its gate and ownership assignments | Calculations quality manager | issue pending (6); section 5 |
| External integration qualification | UNVERIFIED: the external adapter described by the guide is outside this checkout; no external adapter behavior is qualified here | Module maintainer | issue pending (4); [docs/units-guide.md:L275-L309] |

Scope: documentation and registry link only; no calculation constants are introduced.
