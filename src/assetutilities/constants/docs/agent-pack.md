# Constants module knowledge pack

| Header | Value |
|---|---|
| Module | constants |
| Repository | assetutilities |
| Path | `src/assetutilities/constants/` |
| Pack revision | 0 |
| Code revision | `18d7f7761db915f3a1b6e65416b625fa0fc9ce5b` |
| Analysis family | Engineering calculations; AQG r0 Python calculations; EC |
| Quality manager role | Calculations quality manager |
| Status | DRAFT |

## 1. Purpose and scope

The module supplies scalar engineering constants, frozen steel and casing records, unit conversions, surface seawater properties and gauge hydrostatic pressure; the routing registry marks the domain `active`, rather than declaring scientific validation. [src/assetutilities/constants/__init__.py:L10-L78] [src/assetutilities/constants/materials.py:L10-L24] [src/assetutilities/constants/casing_grades.py:L6-L20] [src/assetutilities/constants/conversions.py:L15-L196] [src/assetutilities/constants/seawater.py:L24-L127] [docs/registry/module-routing.yaml:L45-L50]

Density is documented for temperature 0–40 °C, salinity 0–42 ppt and surface pressure 0 dbar; viscosity documents the same temperature and salinity envelope, and these bounds are not checked by the function bodies. [src/assetutilities/constants/seawater.py:L6-L10] [src/assetutilities/constants/seawater.py:L24-L64] [src/assetutilities/constants/seawater.py:L67-L103]

Hydrostatic pressure uses fixed `RHO_SEAWATER` and nominal `G`, independently of temperature and salinity; its zero is gauge pressure at the surface. [src/assetutilities/constants/conversions.py:L189-L196]

The indicative environment constants carry site-specific comments and are not a site design basis. [src/assetutilities/constants/__init__.py:L72-L78]

## 2. Inputs and outputs

### Inputs

| Interface | Unit | Allowed range / default | Source |
|---|---|---|---|
| `seawater_density`, `seawater_dynamic_viscosity`, `seawater_kinematic_viscosity`: `temperature_c`, `salinity_ppt` | °C; ppt (g/kg) | Documented 0–40; 0–42; both required; no runtime bounds guard | [src/assetutilities/constants/seawater.py:L24-L64] [src/assetutilities/constants/seawater.py:L67-L127] |
| Pressure conversion scalar | psi, MPa, bar, kPa as named by each function | Required; arithmetic only, no explicit range guard | [src/assetutilities/constants/conversions.py:L15-L42] |
| Length conversion scalar | ft, m, inch, mm | Required; arithmetic only | [src/assetutilities/constants/conversions.py:L57-L74] |
| Force conversion scalar | N, kN, lbf, kip | Required; arithmetic only | [src/assetutilities/constants/conversions.py:L88-L115] |
| Mass conversion scalar | kg, lb, tonne, short ton | Required; arithmetic only | [src/assetutilities/constants/conversions.py:L130-L157] |
| Temperature conversion scalar | °C, °F, K | Required; arithmetic only, no absolute-zero guard | [src/assetutilities/constants/conversions.py:L165-L182] |
| `depth_to_pressure_kpa`: `depth_m` | m | Required; no negative-depth guard | [src/assetutilities/constants/conversions.py:L189-L196] |
| `get_steel_grade`: `name` | dimensionless string | Required, exact dictionary key; no default | [src/assetutilities/constants/materials.py:L140-L149] |
| `CasingGrade` constructor | name, MPa, MPa, group string | All four fields required; no validation method | [src/assetutilities/constants/casing_grades.py:L6-L20] |
| `SteelGrade` constructor | name, Pa, optional Pa, reference string | All four fields required; ultimate strength may be `None` | [src/assetutilities/constants/materials.py:L10-L24] |

### Outputs

| Interface | Output / convention | Source |
|---|---|---|
| Seawater functions | `float`: density kg/m³; dynamic viscosity Pa·s; kinematic viscosity m²/s | [src/assetutilities/constants/seawater.py:L24-L35] [src/assetutilities/constants/seawater.py:L64-L70] [src/assetutilities/constants/seawater.py:L103-L127] |
| Conversion functions | Scalar in the target unit named by each function | [src/assetutilities/constants/conversions.py:L15-L182] |
| Hydrostatic pressure | kPa, gauge; positive depth produces positive pressure for the stored positive density and gravity | [src/assetutilities/constants/conversions.py:L189-L196] [src/assetutilities/constants/__init__.py:L17-L28] |
| Steel lookup | `SteelGrade` or `None` for an unknown name; `STEEL_GRADES` is a mutable dictionary of frozen records | [src/assetutilities/constants/materials.py:L10-L24] [src/assetutilities/constants/materials.py:L120-L149] |
| Casing lookup | `CASING_GRADES` is a dictionary of frozen records with strength fields in MPa | [src/assetutilities/constants/casing_grades.py:L6-L34] |
| Shared constants | Mathematical dimensionless values; gravity m/s²; atmosphere kPa; densities kg/m³; elastic and yield properties Pa; thermal expansion /°C; pressure gradient kPa/m; environment lengths m | [src/assetutilities/constants/__init__.py:L10-L78] |

The interfaces above return scalars or records, with no coordinate frame, phase convention, file reader or writer in their implementations; depth is the only explicitly documented surface-origin quantity. [src/assetutilities/constants/materials.py:L140-L149] [src/assetutilities/constants/casing_grades.py:L6-L34] [src/assetutilities/constants/conversions.py:L15-L196] [src/assetutilities/constants/seawater.py:L24-L127]

## 3. Method and governing standards

The following are source-code attributions, not confirmation of conformity; clause text not checked against the licensed copy for each licensed standard below. [src/assetutilities/constants/__init__.py:L2-L2] [src/assetutilities/constants/materials.py:L27-L29] [src/assetutilities/constants/casing_grades.py:L1-L2]

| Method / data | Reference as recorded; edition and locator limits | Implementation |
|---|---|---|
| Steel records | API 5L, 46th edition; ISO 3183:2019; code names Table J.2 and PSL2; full titles and clause titles are not supplied | [src/assetutilities/constants/materials.py:L27-L71] |
| Casing records | API 5CT, 10th edition; ISO 11960:2020; code names Table C.1; full titles and clause titles are not supplied | [src/assetutilities/constants/casing_grades.py:L1-L2] [src/assetutilities/constants/casing_grades.py:L23-L34] |
| Seawater nominal constants / pressure | API RP 2A-WSD and DNV-RP-C205 Section 3; edition and clause title absent | [src/assetutilities/constants/__init__.py:L23-L28] [src/assetutilities/constants/conversions.py:L189-L196] |
| Density | Docstring attributes the surface polynomial to Fofonoff and Millard (1983), *Algorithms for the Computation of Fundamental Properties of Seawater*, UNESCO Technical Papers in Marine Science 44; body comments name IES 80 Eq. 13 | [src/assetutilities/constants/seawater.py:L15-L17] [src/assetutilities/constants/seawater.py:L43-L64] |
| Dynamic viscosity | Docstring names ITTC (2011), *Fresh Water and Seawater Properties*, procedure 7.5-02-01-03 Rev 02, and Millero (1974), *The physical chemistry of seawater*; body multiplies a temperature formula by a linear salinity factor | [src/assetutilities/constants/seawater.py:L67-L103] |
| Kinematic viscosity | Dynamic viscosity divided by density, using the two module functions | [src/assetutilities/constants/seawater.py:L106-L127] |
| Pressure conversion | NIST SP 811 is named; implementation uses a stored reciprocal pair for psi/MPa and arithmetic scaling for bar/kPa | [src/assetutilities/constants/conversions.py:L7-L42] |
| Length, force, mass | Code names ISO 31-1 for the international foot and NIST for force and mass; editions and detailed locators absent | [src/assetutilities/constants/conversions.py:L45-L157] |
| Temperature | Affine °C/°F and °C/K arithmetic | [src/assetutilities/constants/conversions.py:L160-L182] |
| Derived constants | `G_STEEL = E_STEEL / (2 * (1 + NU_STEEL))`; `SEAWATER_PRESSURE_GRADIENT = RHO_SEAWATER * G / 1000` | [src/assetutilities/constants/__init__.py:L39-L43] [src/assetutilities/constants/__init__.py:L69-L70] |
| Other material constants | Code names EN 10025-2, ASTM A36, API 5L, EN 1993-1-1, EN 1992-1-1 and DNV-OS-J101; steel records additionally specify ASTM A36/A36M-19 and ASTM A572/A572M-21 | [src/assetutilities/constants/__init__.py:L35-L62] [src/assetutilities/constants/materials.py:L75-L113] |

UNVERIFIED: U1 — external accuracy, complete titles, editions, clause titles and viscosity accuracy claims remain unconfirmed; attribution comments alone do not validate the formula or tables; issue pending (3). [src/assetutilities/constants/seawater.py:L72-L92] [src/assetutilities/constants/materials.py:L27-L29] [src/assetutilities/constants/casing_grades.py:L1-L2]

No conflicting pair of explicit editions is present in these module references: some references omit editions, while the material and casing modules specify them; missing editions require confirmation rather than silent reconciliation; issue pending (3). [src/assetutilities/constants/__init__.py:L23-L36] [src/assetutilities/constants/materials.py:L27-L29] [src/assetutilities/constants/casing_grades.py:L1-L2]

The numeric functions and records carry comments or reference strings, but return no `Citation` sidecar; issue pending (3). [src/assetutilities/constants/materials.py:L10-L24] [src/assetutilities/constants/materials.py:L140-L149] [src/assetutilities/constants/casing_grades.py:L6-L20] [src/assetutilities/constants/conversions.py:L189-L196] [src/assetutilities/constants/seawater.py:L97-L127]

## 4. Validated worked examples

Validated examples: **0**; the cases below are **5 regression examples**, with expectations from repository formulas or identities rather than an independently opened reference; issue pending (3). [tests/unit/test_constants.py:L130-L133] [tests/unit/test_constants.py:L308-L309] [tests/unit/test_constants.py:L340-L357] [tests/unit/test_seawater.py:L136-L146]

| Case | Source and input | Expected output; tolerance and basis | Existing test node ID | Offline result at code revision |
|---|---|---|---|---|
| R1 temperature freezing | Repository affine formula; 0 °C | 32 °F; relative 1e-9, test-selected | `tests/unit/test_constants.py::TestTemperatureConversions::test_celsius_to_fahrenheit_freezing` | PASS at BASE and AFTER; [tests/unit/test_constants.py:L308-L309] |
| R2 surface gauge pressure | Repository pressure formula; depth 0 m | 0 kPa; test-default `pytest.approx` tolerance | `tests/unit/test_constants.py::TestDepthToPressure::test_zero_depth_returns_zero_gauge` | PASS at BASE and AFTER; [tests/unit/test_constants.py:L340-L342] |
| R3 pressure linearity | Repository proportionality; depths 100 and 200 m | Pressure ratio 2, dimensionless; relative 1e-9, test-selected | `tests/unit/test_constants.py::TestDepthToPressure::test_depth_pressure_linear` | PASS at BASE and AFTER; [tests/unit/test_constants.py:L353-L357] |
| R4 isotropic shear modulus | Repository identity; stored elastic modulus and Poisson ratio | `E / (2 * (1 + nu))` Pa; relative 1e-6, test-selected | `tests/unit/test_constants.py::TestSteelProperties::test_shear_modulus_derived_from_E_and_nu` | PASS at BASE and AFTER; [tests/unit/test_constants.py:L130-L133] |
| R5 kinematic identity | Repository identity; 15 °C, 35 ppt | `mu / rho` m²/s; relative 1e-9, test-selected | `tests/unit/test_seawater.py::TestSeawaterKinematicViscosity::test_kinematic_viscosity_equals_dynamic_over_density` | PASS at BASE and AFTER; [tests/unit/test_seawater.py:L136-L146] |

Execution record: the four test files listed in section 10 ran at the header revision with `uv run python -m pytest <four files> -q -rA -p no:cacheprovider --basetemp=<scratch> --override-ini addopts=`; BASE: 126 run, 126 passed, 0 failed, 0 skipped, 0 NOT_RUN; AFTER: 126 run, 126 passed, 0 failed, 0 skipped, 0 NOT_RUN; both ran on the uncommitted tree at the header revision. The identical `--override-ini addopts=` form clears configured extra options without changing test selection; no coverage artifacts were generated. Of the 126 cases, 121 exercise constants and 5 exercise the geometry helpers in the shared casing test file. [tests/test_casing_grades.py:L34-L71]

UNVERIFIED: U2 — the tests' seawater reference comments and material expectations have not been independently confirmed; they are not validated examples; issue pending (3). [tests/unit/test_seawater.py:L17-L26] [tests/unit/test_seawater.py:L100-L108] [tests/unit/test_materials.py:L50-L64]

## 5. QA gates

Gate applicability follows **AQG r0, Analysis QA gates, revision 0, sections 9–11**, family **Python calculations**.

| Gate | Applicability and route |
|---|---|
| G0 | Applicable: inputs, units and citations; C01–C03 below (AQG r0 §10). |
| G1 | Applicable: Python imports and offline tests, C11; no target-program file is written by the listed scalar functions (AQG r0 §10). [src/assetutilities/constants/conversions.py:L15-L196] [src/assetutilities/constants/seawater.py:L24-L127] |
| G2 | Applicable: hand or published checks, C21–C23; the current identity checks demonstrate internal consistency; independent reference closure remains issue pending (3) (AQG r0 §10). |
| G3 | NOT_APPLICABLE: Python calculations have no short-dynamics gate (AQG r0 §10). |
| G4 | NOT_APPLICABLE: Python calculations have no diffraction gate (AQG r0 §10). |
| G5 | Applicable: evidence traceability, C51; report use requires the evidence appendix and independent signature (AQG r0 §§9, 11). |

The following **8 checks** are executable criteria; a baseline defect is a finding to resolve, not a waiver or a scientific clearance.

| Check | Module-specific execution | Numeric pass criterion and unit | Evidence / gate |
|---|---|---|---|
| C01 | `tests/unit/test_seawater.py::TestSeawaterDensity::test_density_physical_range`, density over its temperature/salinity grid | Every result strictly between 990 and 1100 kg/m³; 0 outliers | Test assertions, G0; [tests/unit/test_seawater.py:L49-L56] |
| C02 | Compare `FY_X70` to `get_steel_grade("API 5L X70").smys_pa` | Absolute difference = 0 Pa | Direct equality check; baseline FAIL; G0; [src/assetutilities/constants/__init__.py:L53-L53] [src/assetutilities/constants/materials.py:L60-L65] |
| C03 | `tests/unit/test_materials.py::TestSteelGradesRegistry::test_get_steel_grade_returns_none_for_unknown` | Exactly 1 unknown-name lookup returns `None`; 0 false matches, count | Test assertion, G0; [tests/unit/test_materials.py:L186-L188] |
| C11 | Run all four module test files; imports occur during collection and test execution | 126 passed test cases; 0 failures, 0 collection errors, count | Detailed pytest results, G1; [tests/unit/test_constants.py:L7-L64] [tests/unit/test_seawater.py:L6-L10] [tests/unit/test_materials.py:L7-L11] [tests/test_casing_grades.py:L7-L71] |
| C21 | R1 `celsius_to_fahrenheit(0)` vs affine freezing expectation | Relative error ≤ 1e-9, dimensionless (output °F) | PASS regression, G2; [tests/unit/test_constants.py:L308-L309] |
| C22 | R4 `G_STEEL` vs `E / (2 * (1 + nu))` | Relative error ≤ 1e-6, dimensionless (output Pa) | PASS identity check, G2; [tests/unit/test_constants.py:L130-L133] |
| C23 | R5 `seawater_kinematic_viscosity` vs `mu / rho` | Relative error ≤ 1e-9, dimensionless (output m²/s) | PASS identity check, G2; [tests/unit/test_seawater.py:L136-L146] |
| C51 | Resolve every cited source range at the code pin and link every section-4 case to its recorded test result | 0 unresolved citations; 0 missing results, count | Citation resolver and test-result mapping, G5; [tests/unit/test_constants.py:L130-L133] [tests/unit/test_constants.py:L308-L309] [tests/unit/test_constants.py:L340-L357] [tests/unit/test_seawater.py:L136-L146] |

## 6. Known failure modes and pitfalls
sweep: not run (legacy pack)

| Symptom / cause | Detection | Evidence and tracking | Date recorded |
|---|---|---|---|
| Silent extrapolation: documented seawater limits are not runtime guards; callers can supply temperatures or salinities outside the stated envelope | C01 checks only its finite grid; no invalid-input detection check exists in the seawater test file | issue pending (2); [src/assetutilities/constants/seawater.py:L24-L64] [src/assetutilities/constants/seawater.py:L94-L103] [tests/unit/test_seawater.py:L17-L146] | 2026-10-15 |
| Silent lookup miss: unknown steel grade returns `None`; caller must check before reading fields | C03 explicitly checks the miss | [src/assetutilities/constants/materials.py:L140-L149] [tests/unit/test_materials.py:L186-L188] | 2026-10-15 |
| X70 strength differs between scalar constant and steel registry; separate tests assert each representation | C02 detects the disagreement; existing isolated tests do not cross-check | issue pending (1); [src/assetutilities/constants/__init__.py:L53-L53] [src/assetutilities/constants/materials.py:L60-L65] [tests/unit/test_constants.py:L147-L149] [tests/unit/test_materials.py:L102-L105] | 2026-10-15 |
| Frozen records do not freeze the surrounding dictionaries | C03 does not detect dictionary mutation; no dictionary-mutation detection check exists in these tests | issue pending (2); [src/assetutilities/constants/materials.py:L10-L24] [src/assetutilities/constants/materials.py:L120-L137] [src/assetutilities/constants/casing_grades.py:L6-L34] [tests/unit/test_materials.py:L169-L192] | 2026-10-15 |
| Nominal density pressure route and temperature/salinity-dependent density route represent different input assumptions; switching them silently changes the calculation basis | R2/R3 check the fixed-density route; no coupled-density detection check exists | issue pending (2); [src/assetutilities/constants/conversions.py:L189-L196] [src/assetutilities/constants/seawater.py:L24-L64] | 2026-10-15 |
| Scientific attribution and accuracy comments lack emitted provenance and independently confirmed references | C51 detects broken repository citations; no external-reference validation check exists in the module tests | issue pending (3); [src/assetutilities/constants/seawater.py:L72-L103] [src/assetutilities/constants/materials.py:L10-L24] [tests/unit/test_seawater.py:L100-L108] | 2026-10-15 |

No incident issue was supplied for this module; confirmed code findings above use numbered issue drafts rather than an invented incident history.

## 7. Lessons log

| Date | Entry | Lesson | Evidence | Pack change / shared-log entry |
|---|---|---|---|---|
| 2026-10-15 | Initial pack | Separate tests can preserve inconsistent representations; add a cross-representation check before using either X70 path as a reference | [tests/unit/test_constants.py:L147-L149] [tests/unit/test_materials.py:L102-L105] | Sections 5–6; issue pending (1); shared-log entry pending in issue pending (4) |

## 8. Ownership

Review roles for this draft: calculations quality manager; proposed deputy: calculations deputy quality manager; producing role: engineering calculations contributor; escalation: maintainer, through the quality manager for reference or tolerance disputes (AQG r0 §11).

UNVERIFIED: U3 — deputy, producing-role assignments and the shared evidence integration are proposed rather than confirmed repository assignments; issue pending (4). [docs/registry/module-routing.yaml:L45-L50]

## 9. Dependencies

The module uses Python `math` for mathematical constants, `dataclasses` for frozen records and `typing.Optional` for steel lookup typing; conversion pressure reads `RHO_SEAWATER` and `G` from the module, while kinematic viscosity calls density and dynamic viscosity internally. [src/assetutilities/constants/__init__.py:L4-L11] [src/assetutilities/constants/materials.py:L4-L24] [src/assetutilities/constants/casing_grades.py:L3-L20] [src/assetutilities/constants/conversions.py:L4-L4] [src/assetutilities/constants/conversions.py:L189-L196] [src/assetutilities/constants/seawater.py:L121-L127]

The routing surface associates constants with units and calculations; the four direct test consumers are listed in section 10, and the casing test file also exercises `math_helpers` geometry outside this module. [docs/maps/assetutilities-operator-map.md:L10-L16] [tests/unit/test_constants.py:L7-L64] [tests/unit/test_seawater.py:L6-L10] [tests/unit/test_materials.py:L7-L11] [tests/test_casing_grades.py:L7-L71]

### Other implementations in this repository

The repository search covered tracked text, including `scripts/`, using method symbols, grade registry symbols, conversion coefficients and seawater polynomial terms; the following additional computational routes warrant comparison rather than being used as independent validated references.

| Family | Other implementation | Relationship and limits |
|---|---|---|
| Unit conversion | `TrackedQuantity.to` | Separate Pint conversion route for compatible units; preserves provenance entries. [src/assetutilities/units/quantity.py:L130-L147] |
| Length, temperature, pressure conversion | Metocean `_convert` and `convert_length`, `convert_temperature`, `convert_pressure` | Pint-backed route; unit mapping and conversion are separate from constants arithmetic. [src/assetutilities/units/domains/metocean.py:L18-L77] [src/assetutilities/units/domains/metocean.py:L103-L169] |
| Grade data | `calculations.pipeline_dnv.MATERIAL_GRADES` | Another grade table; design references and strength basis need comparison before interchange. [src/assetutilities/calculations/pipeline_dnv.py:L19-L29] |
| Hydrostatic pressure | `calculations.drilling_riser.miller_mud_column_pressure` | Computes pressure for user-supplied mud weight and depth in field units, with non-negative guards; different density inputs from fixed seawater pressure. [src/assetutilities/calculations/drilling_riser.py:L239-L266] |
| Grade data inside this module | Scalar `FY_*` and `materials.STEEL_GRADES` | Parallel representations, including the confirmed X70 inconsistency. [src/assetutilities/constants/__init__.py:L45-L54] [src/assetutilities/constants/materials.py:L27-L71] |

The internal viscosity calls and pressure-conversion helpers are module coverage in sections 3 and 5; they are not additional implementations merely because they are helpers. [src/assetutilities/constants/seawater.py:L121-L127] [src/assetutilities/constants/conversions.py:L35-L42]

### Cross-repository implementation-map inventory

Source for every row of the next table: **digitalmodel, implementation map, revision `b5acbe5f61ed4c755c1f7ea4fafa4611bd14e407`, `docs/registry/implementation-map.yaml`, lines 21641–22012, family `api-5ct-5l-grade-tables`**; its own header pins the searched source revision to `947fa50ff9a9e210de7e8f90e01b37add85c5954` (same map, lines 1–3).

All **39** entries of that family are retained below, including examples, callers and tests; the relation column reproduces the map classification, rather than asserting that each row independently computes grade data (digitalmodel implementation map, revision `b5acbe5f61ed4c755c1f7ea4fafa4611bd14e407`, family `api-5ct-5l-grade-tables`, lines 21641–22012).

| Path in digitalmodel | Symbol / table | Source line indexed by map | Map relation |
|---|---|---|---|
| `docs/domains/orcaflex/templates/components/materials/steel.csv` | `table` | 1 | independent |
| `examples/demos/asset_integrity/ffs_lookup_build.py` | `PIPE_METHODS` | 27 | example |
| `examples/demos/asset_integrity/ffs_lookup_build.py` | `build_records` | 40 | example |
| `examples/demos/gtm/calc_values.py` | `PIPE_SIZES` | 19 | example |
| `examples/demos/gtm/demo_02_wall_thickness_multicode.py` | `_load_engineering_modules` | 58 | example |
| `examples/domains/structural/wall_thickness_example.py` | `run_single_design_check` | 44 | example |
| `examples/domains/structural/wall_thickness_example.py` | `run_phase_analysis` | 133 | example |
| `scripts/capabilities/build_casing_design_explorer.py` | `table` | 58 | independent |
| `src/digitalmodel/base_configs/modules/pipe_capacity/pipe_capacity.yml` | `table` | 14 | independent |
| `src/digitalmodel/base_configs/modules/vertical_riser/vertical_riser.yml` | `table` | 31 | independent |
| `src/digitalmodel/data_systems/data/steel_material.yml` | `table` | 16 | independent |
| `src/digitalmodel/data_systems/data_procurement/riser/database_clients/pipe_db_client.py` | `PipeSpecificationClient` | 45 | independent |
| `src/digitalmodel/data_systems/data_procurement/riser/database_clients/pipe_db_client.py` | `PipeSpecificationClient._initialize_pipe_database` | 134 | caller |
| `src/digitalmodel/data_systems/data_procurement/riser/database_clients/pipe_db_client.py` | `PipeSpecificationClient._generate_pipe_spec` | 159 | independent |
| `src/digitalmodel/infrastructure/templates/api_std_2rd_template.yml` | `table` | 24 | independent |
| `src/digitalmodel/materials/grades.py` | `_E_LINE_PIPE` | 28 | independent |
| `src/digitalmodel/orcaflex/mooring_design.py` | `MOORING_MATERIAL_LIBRARY` | 174 | independent |
| `src/digitalmodel/orcaflex/mooring_design.py` | `MooringLineSegment` | 343 | independent |
| `src/digitalmodel/orcaflex/mooring_design.py` | `MooringLineDesign.estimate_catenary` | 385 | independent |
| `src/digitalmodel/orcaflex/mooring_design.py` | `MooringLineDesign.check_mbl` | 405 | independent |
| `src/digitalmodel/orcaflex/mooring_design.py` | `MooringLineDesign.check_mbl_with_safety_factor` | 522 | independent |
| `src/digitalmodel/orcaflex/riser_config.py` | `PIPE_GRADES` | 59 | independent |
| `src/digitalmodel/orcaflex/riser_config.py` | `RiserPipeProperties.steel_mass_per_m` | 111 | independent |
| `src/digitalmodel/orcaflex/riser_config.py` | `RiserPipeProperties.bending_stiffness` | 140 | independent |
| `src/digitalmodel/orcaflex/riser_config.py` | `RiserPipeProperties.axial_stiffness` | 147 | independent |
| `src/digitalmodel/solvers/orcaflex/modular_generator/builders/linetype_builder.py` | `MATERIAL_PROPERTIES` | 20 | independent |
| `src/digitalmodel/structural/analysis/__init__.py` | `table` | 49 | independent |
| `src/digitalmodel/structural/analysis/cli.py` | `check` | 83 | independent |
| `src/digitalmodel/structural/analysis/cli.py` | `sweep` | 199 | independent |
| `src/digitalmodel/structural/analysis/cli.py` | `phases` | 273 | independent |
| `src/digitalmodel/structural/analysis/cli.py` | `list_grades` | 329 | independent |
| `src/digitalmodel/structural/analysis/cli.py` | `lookup` | 366 | independent |
| `src/digitalmodel/structural/analysis/wall_thickness_parametric.py` | `API_5L_GRADES` | 40 | independent |
| `src/digitalmodel/structural/analysis/wall_thickness_parametric.py` | `ParametricSweep.run` | 66 | independent |
| `src/digitalmodel/subsea/catenary_riser/models.py` | `STEEL_API_5L_X65` | 57 | independent |
| `src/digitalmodel/subsea/pipeline/pipeline_pressure.py` | `MATERIAL_LIBRARY` | 137 | independent |
| `src/digitalmodel/subsea/pipeline/pipeline_pressure_workflow.py` | `WallThicknessSizingWorkflow.run` | 279 | independent |
| `src/digitalmodel/well/tubulars/casing_design.py` | `table` | 50 | independent |
| `tests/fixtures/test_vectors/mooring_risers/riser_material_properties.yaml` | `table` | 36 | test_helper |

The map's family list contains no dedicated seawater-property or scalar-unit-conversion family; this is a map coverage limit, not evidence that no such implementation exists (digitalmodel implementation map, revision `b5acbe5f61ed4c755c1f7ea4fafa4611bd14e407`, family index).

UNVERIFIED: U4 — equivalence and scientific correctness of the cross-repository routes have not been checked; the table records the map inventory only; issue pending (3) (digitalmodel implementation map, revision `b5acbe5f61ed4c755c1f7ea4fafa4611bd14e407`, family `api-5ct-5l-grade-tables`).

## 10. Coverage and open items

### Coverage inventory

| Read surface | Extent and evidence |
|---|---|
| Entire constants source tree | All five Python files: `__init__.py`, `casing_grades.py`, `conversions.py`, `materials.py`, `seawater.py`; no data-loading call or subfolder data input appears in those implementations. [src/assetutilities/constants/__init__.py:L1-L79] [src/assetutilities/constants/casing_grades.py:L1-L34] [src/assetutilities/constants/conversions.py:L1-L196] [src/assetutilities/constants/materials.py:L1-L149] [src/assetutilities/constants/seawater.py:L1-L127] |
| Direct tests | `tests/unit/test_constants.py`, `tests/unit/test_seawater.py`, `tests/unit/test_materials.py`, `tests/test_casing_grades.py`; all test definitions read, including geometry cases outside constants. [tests/unit/test_constants.py:L1-L357] [tests/unit/test_seawater.py:L1-L146] [tests/unit/test_materials.py:L1-L192] [tests/test_casing_grades.py:L1-L71] |
| Canonical docs naming the module | `README.md`, `MODULE_STRUCTURE.md`, `docs/README.md`, `docs/maps/assetutilities-operator-map.md`, `docs/registry/module-routing.yaml`; found by module-path and engineering-method searches. [README.md:L36-L36] [MODULE_STRUCTURE.md:L53-L53] [docs/README.md:L14-L14] [docs/maps/assetutilities-operator-map.md:L13-L13] [docs/registry/module-routing.yaml:L45-L50] |
| Other documentation search hits read | Generic constant naming guidance and a separate seawater-resistivity inventory are not documentation of this module's algorithms. [docs/plans/2026-05-05-issue-41-clean-code.md:L29-L36] [docs/sub_python/naming_conventions.md:L68-L72] [docs/modules/repositories/responsibility.md:L237-L237] [docs/modules/repositories/responsibility.md:L305-L305] |
| Local alternative routes | Units quantity/metocean conversion, pipeline grade data and mud-column pressure; evidence in section 9. [src/assetutilities/units/quantity.py:L130-L147] [src/assetutilities/units/domains/metocean.py:L18-L77] [src/assetutilities/calculations/pipeline_dnv.py:L19-L29] [src/assetutilities/calculations/drilling_riser.py:L239-L266] |
| Packaging | Package data includes base configuration YAML/CSV globs, not this Markdown pack. [pyproject.toml:L113-L122] |

### Open items

Every item below is assigned to the maintainer for disposition; draft numbers remain until issues are opened.

| Item | Limit or required next step | Tracking |
|---|---|---|
| O1 | Reconcile X70 scalar/record strength basis; C02 currently detects a baseline mismatch | issue pending (1); [src/assetutilities/constants/__init__.py:L53-L53] [src/assetutilities/constants/materials.py:L60-L65] |
| O2 | Define bounds, nonfinite-input, negative-depth and mutable-registry policy; document fixed versus computed density route | issue pending (2); [src/assetutilities/constants/seawater.py:L24-L64] [src/assetutilities/constants/conversions.py:L189-L196] [src/assetutilities/constants/materials.py:L120-L149] |
| O3 — U1, U2, U4 | Confirm scientific references, full titles, editions, clause titles, viscosity attribution and accuracy; add independent benchmark cases and emitted citation evidence; audit map-route equivalence before using it as a reference | issue pending (3); [src/assetutilities/constants/seawater.py:L15-L20] [src/assetutilities/constants/seawater.py:L72-L103] [src/assetutilities/constants/materials.py:L27-L29] [tests/unit/test_seawater.py:L100-L108] |
| O4 — U3 | Confirm deputy and producing roles, escalation contacts, shared-log entry and report evidence integration | issue pending (4); [docs/registry/module-routing.yaml:L45-L50] |
| O5 | Existing routing-contract assertions fail because the package domain inventory omits `workflow_api`; this does not change constants outputs | issue pending (5); [tests/docs/test_assetutilities_routing_contract.py:L83-L103] [docs/registry/module-routing.yaml:L12-L68] |
