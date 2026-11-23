# Calculations knowledge pack

| Header | Value |
|---|---|
| Module | calculations |
| Repository | assetutilities |
| Path | `src/assetutilities/calculations` |
| Pack revision | 1 |
| Code revision | `8c8e83ef0f35400c050a45c9981b997e44b427dd` |
| Analysis family | Engineering calculations; AQG r0 Python calculations |
| Quality manager role | Calculations quality manager |
| Status | DRAFT |

## 1. Purpose and scope

The registry records engineering calculations with stability `active`; this is a routing designation, without a qualification claim. [docs/registry/module-routing.yaml:L25-L30]

| Area | Implemented scope and limits | Evidence |
|---|---|---|
| Riser VIV | Smooth-cylinder and bundle drag, shedding frequency, reduced velocity, lock-in, response ratio, fatigue sum, pressure-corrected tension and a frequency expression; the frequency expression has the dimensional defect D2 below. | [src/assetutilities/calculations/riser_viv.py:L41-L360] |
| Riser dynamics | Tow-out approximation, damping, correlation correction, piecewise drag, constant added mass, residual-collapse reduction and a response expression with the dimensional defect D2. | [src/assetutilities/calculations/riser_dynamics.py:L7-L233] |
| Riser arrays | Equivalent diameter, load factor, clipped shielding factor and strict spacing comparison. | [src/assetutilities/calculations/riser_array.py:L7-L107] |
| Drilling riser | Weight/tension arithmetic, pressure frequency adjustment, drag reduction, suppression damage, submerged weight, lock-in velocity, mud pressure and response power law. | [src/assetutilities/calculations/drilling_riser.py:L31-L328] |
| Drilling-riser integrity | Effective tension, thin-shell collapse, minimum tension, axial/combined utilization, offset moment and annual damage. | [src/assetutilities/calculations/drilling_riser_integrity.py:L7-L155] |
| Wellhead fatigue | S-N endurance, years, Miner sums, biaxial effective stress, exposure damage, tensioner load and stiffness life multiplier. | [src/assetutilities/calculations/wellhead_fatigue.py:L23-L219] |
| SCR fatigue | KC number, soil correction, TDZ damage, amplitude-to-range endurance and two empirical VIV screens. | [src/assetutilities/calculations/scr_fatigue.py:L26-L215] |
| TLP well system | Tendon tension, tensioner stroke, service-life damage, clearance, damping ratio and set-down. | [src/assetutilities/calculations/tlp_well_system.py:L18-L209] |
| Pipeline | Pressure capacity/utilization, combined buckling, equivalent stress and an arrest expression with the dimensional defect D2. | [src/assetutilities/calculations/pipeline_dnv.py:L54-L208] |
| Casing | Geometry, burst/collapse/tensile ratings, inverse pressure sizing and temperature wrapper; collapse uses nearest-grade tables and an approximate regime split. | [src/assetutilities/calculations/casing_pipe.py:L51-L369] |
| Lifecycle cost | Discounting, levelized and annual equivalent costs, maintenance, transport, downtime adjustment and installed-cost sum. | [src/assetutilities/calculations/lifecycle_cost.py:L7-L156] |
| Polynomial | Constructor and evaluator contain `pass`; the instance call returns `None`, rather than a polynomial value. | [src/assetutilities/calculations/polynomial.py:L1-L6] [tests/modules/calculations/test_polynomial.py:L4-L19] |

These are callable scalar/list calculations: for example, TDZ damage consumes lists and returns a float, and casing ratings return a dataclass rather than a file. [src/assetutilities/calculations/scr_fatigue.py:L88-L127] [src/assetutilities/calculations/casing_pipe.py:L338-L369]

Do not treat the simplified tow-out expression as a general catenary solution, or the stub as an implemented calculation. [src/assetutilities/calculations/riser_dynamics.py:L7-L44] [src/assetutilities/calculations/polynomial.py:L1-L6]

## 2. Inputs and outputs

Use the explicit function units below; no conversion is performed in the cited arithmetic. [src/assetutilities/calculations/riser_viv.py:L286-L319] [src/assetutilities/calculations/casing_pipe.py:L107-L125]

### Inputs

Defaults derived from standards are identified by their source locations rather than reproduced as values.

| Main input group | Unit | Domain actually enforced or stated | Default | Source and evidence |
|---|---|---|---|---|
| VIV `Re`, bundle count, spacing ratio | dimensionless | Positive `Re`; count at least 1; spacing is clamped in the expression rather than rejected outside the stated fit interval. | Required | Caller; [src/assetutilities/calculations/riser_viv.py:L41-L122] |
| VIV `U`, `D`, `St`, `f_n` | m/s, m, dimensionless, Hz | `D` positive; `f_n` positive for reduced velocity; signs of `U` and `St` are not checked. | `St` source default; others required | Caller; [src/assetutilities/calculations/riser_viv.py:L129-L177] |
| VIV `Vr`, `Ks` | dimensionless | Lock-in bounds are inclusive; `Ks` has no explicit domain guard. | Required | Caller; [src/assetutilities/calculations/riser_viv.py:L184-L234] |
| VIV `stress_ranges`, `cycle_counts` | Pa, cycles | Equal lengths required; nonpositive entries are silently omitted. | Required | Caller; [src/assetutilities/calculations/riser_viv.py:L241-L279] |
| VIV wall tension, internal/external pressure, diameter, thickness | N, Pa, m | No geometry guard in `effective_tension`. | Required | Caller; [src/assetutilities/calculations/riser_viv.py:L286-L319] |
| VIV mode, beam length, stiffness, line mass | count, m, N m², kg/m | Mode at least 1, length/mass positive; integrality and stiffness sign are not explicitly checked. | Required | Caller; [src/assetutilities/calculations/riser_viv.py:L326-L360] |
| Pipeline geometry, strengths, pressures, moment, axial force | m, Pa, N m, N | Functions do not validate a complete physical domain; combined loading substitutes zero terms for nonpositive capacities. | Material/fabrication/safety factors have source defaults | Caller or `MATERIAL_GRADES`; [src/assetutilities/calculations/pipeline_dnv.py:L20-L163] |
| Casing `od_in`, `wall_thickness_in`, `grade`, `temperature_f` | in, enum with psi strength, °F | Dataclass has no geometry validator; nearest table grade is used for collapse. | Temperature default in wrapper; other fields required | Caller and `PipeGrade`; [src/assetutilities/calculations/casing_pipe.py:L27-L76] [src/assetutilities/calculations/casing_pipe.py:L163-L252] [src/assetutilities/calculations/casing_pipe.py:L338-L369] |
| SCR velocity amplitude, period, diameter, KC | m/s, s, m, dimensionless | Velocity/KC nonnegative; period/diameter positive. | Required | Caller; [src/assetutilities/calculations/scr_fatigue.py:L26-L85] |
| SCR stress ranges/amplitude, cycles, KC lists, `a_param`, `m_param` | Consistent stress unit, cycles, dimensionless; intercept must match stress unit | TDZ lists equal length; S-N amplitude/intercept positive; range is twice amplitude in `scr_sn_fatigue_life`. | Required | Caller; [src/assetutilities/calculations/scr_fatigue.py:L88-L158] |
| Drilling weights, length, pressures, bore area, frequency | lbf/ft, lbf, ft, psi, in², Hz | Mud weight/depth nonnegative; zero weight/length returns vacuum frequency; negative radicand is clamped. | Drag factor/Strouhal and offset correction have defaults in signatures | Caller; [src/assetutilities/calculations/drilling_riser.py:L78-L165] [src/assetutilities/calculations/drilling_riser.py:L210-L328] |
| Integrity top tension, submerged weight, depth/length, geometry, modulus, capacities, sea states | N or lbf; N/m or lbf/ft; m or ft; Pa or psi; consistent moment units | Small-offset and thin-shell assumptions stated; no general range checks before divisions. | Required | Caller; [src/assetutilities/calculations/drilling_riser_integrity.py:L7-L155] |
| Dynamics drag/lift, density, diameter, speed, line mass, frequency, angle, lengths, ovality | dimensionless, kg/m³, m, m/s, kg/m, Hz, degrees | Tow-out weight/depth positive, angle in (0,90]; mass/frequency positive; correction lengths positive; ovality nonnegative. | Shape/KC and residual coefficient defaults in signatures | Caller; [src/assetutilities/calculations/riser_dynamics.py:L7-L233] |
| Array count, diameter, spacing and spacing multiplier | count, m, dimensionless | Count positive integer; diameter/spacing positive; ratio positive. | Spacing multiplier source default | Caller; [src/assetutilities/calculations/riser_array.py:L7-L107] |
| Wellhead range, curve parameters, annual cycles, blocks, frequency, exposure, stiffness, tensioner loads | psi; cycles; Hz; years; consistent stiffness; kips | Range, cycles/year, endurance and reduced stiffness positive where guarded; other inputs used directly. | Required | Caller; [src/assetutilities/calculations/wellhead_fatigue.py:L23-L219] |
| TLP pretension/load change, length/displacements, fatigue bins, service years, damping/stiffness/mass, clearance | N, m, consistent stress, cycles/year, years, N s/m, N/m, kg | Effective tension positive; length/diameters/stiffness/mass positive; fatigue lists equal length; positive offset must be below length. | Clearance minimum defaults to 0 m | Caller; [src/assetutilities/calculations/tlp_well_system.py:L18-L209] |
| Cost streams, output streams, rate, life, event cost/MTBF, day rate/days, downtime and cost components | Caller currency, output units, dimensionless annual rate, years, currency/day, days | Only downtime explicitly constrained to [0,1); no stream-length guard. | Required | Caller; [src/assetutilities/calculations/lifecycle_cost.py:L7-L156] |
| Polynomial evaluator arguments | No unit contract | No computation or validation implemented. | No functional default | Caller; [src/assetutilities/calculations/polynomial.py:L1-L6] |

### Outputs

| Calculation group | Returned values and units | Evidence |
|---|---|---|
| VIV | Drag/reduced velocity/response/damage dimensionless; shedding Hz; lock-in bool; tension N; natural frequency claimed Hz but expression has units m/s (D2). | [src/assetutilities/calculations/riser_viv.py:L41-L360] |
| Pipeline | Pressure capacity Pa; pressure/combined utilization dimensionless; equivalent stress Pa; arrest output claimed Pa but expression has force dimensions (D2). | [src/assetutilities/calculations/pipeline_dnv.py:L54-L208] |
| Casing | ID in, area in², D/t dimensionless; burst/collapse psi; tension lbf; thickness in; temperature °F and derating dimensionless in ratings dataclass. | [src/assetutilities/calculations/casing_pipe.py:L51-L100] [src/assetutilities/calculations/casing_pipe.py:L259-L369] |
| Drilling / integrity | Drilling tension lbf, weight lbf/ft, frequency Hz, drag/damage/amplification dimensionless, speed ft/s, pressure psi; integrity uses the caller's consistent force/length/pressure units. | [src/assetutilities/calculations/drilling_riser.py:L31-L328] [src/assetutilities/calculations/drilling_riser_integrity.py:L7-L155] |
| Dynamics / arrays | Tension N; factors dimensionless; cross-flow output claimed m but expression has m/s dimensions (D2); array diameter m and spacing bool. | [src/assetutilities/calculations/riser_dynamics.py:L7-L233] [src/assetutilities/calculations/riser_array.py:L7-L107] |
| SCR | KC/correction/damage/amplitude ratio dimensionless, endurance cycles, screening `(bool, ratio)`. | [src/assetutilities/calculations/scr_fatigue.py:L26-L215] |
| Wellhead | Endurance cycles, life years, damage/multiplier dimensionless, equivalent stress psi, conductor load kips. | [src/assetutilities/calculations/wellhead_fatigue.py:L23-L219] |
| TLP | Tension N, stroke/set-down m, damage/damping dimensionless, interference `(bool, gap_m)`. | [src/assetutilities/calculations/tlp_well_system.py:L18-L209] |
| Lifecycle | NPV/maintenance/transport/installed cost in caller currency; levelized currency/output; annual equivalent currency/year; effective transit days. | [src/assetutilities/calculations/lifecycle_cost.py:L7-L156] |
| Polynomial | `None` from the stub. | [src/assetutilities/calculations/polynomial.py:L1-L6] [tests/modules/calculations/test_polynomial.py:L4-L14] |

The local conventions are depth below riser top positive, tow angle from horizontal in degrees, TLP vertical displacement/set-down positive downward, and pipeline axial force positive in tension while the implementation uses its magnitude. [src/assetutilities/calculations/drilling_riser_integrity.py:L7-L23] [src/assetutilities/calculations/riser_dynamics.py:L7-L44] [src/assetutilities/calculations/tlp_well_system.py:L45-L71] [src/assetutilities/calculations/tlp_well_system.py:L177-L209] [src/assetutilities/calculations/pipeline_dnv.py:L139-L163]

VIV effective tension subtracts internal-pressure area force and adds external-pressure area force; SCR endurance doubles stress amplitude, whereas the VIV fatigue argument is named a range but described as an amplitude (D3). [src/assetutilities/calculations/riser_viv.py:L253-L255] [src/assetutilities/calculations/riser_viv.py:L293-L319] [src/assetutilities/calculations/scr_fatigue.py:L130-L158]

Cost index zero is undiscounted; subsequent entries are discounted by their index. [src/assetutilities/calculations/lifecycle_cost.py:L7-L23]

U3 in section 10 records the unresolved global frame, phase, complete domain and serialization contracts.

## 3. Method and governing standards

Source attribution is distinguished from independent verification; U1 and U2 in section 10 remain open.

| Method / implementing functions | Reference named by source; edition and clause locator | Assessment and evidence |
|---|---|---|
| Pipeline `_characteristic_strength`, `burst_pressure_capacity`, `pressure_containment_check`, `local_buckling_combined_loading`, `von_mises_equivalent_stress`, `buckle_arrest_capacity` | DNV-OS-F101, source description: submarine pipeline system design, 2013; Pressure containment, Local buckling combined loading, Von Mises equivalent stress, Buckle arrest capacity (source section locators D300/D500/D600/D800). | Source assigns those locators; clause text not checked against the licensed copy. The combined-loading docstring and implementation disagree about safety-factor placement (D3). [src/assetutilities/calculations/pipeline_dnv.py:L1-L14] [src/assetutilities/calculations/pipeline_dnv.py:L42-L208] |
| VIV `viv_fatigue_damage` | DNV-RP-C203, full title not recorded in module, 2016; source calls it the D-curve and Palmgren-Miner method, without a numbered clause. | Clause text not checked against the licensed copy; source converts Pa to MPa before computing endurance and silently skips nonpositive bins (D4). [src/assetutilities/calculations/riser_viv.py:L5-L13] [src/assetutilities/calculations/riser_viv.py:L238-L279] |
| Casing `burst_pressure_rating` | API Spec 5CT; edition and clause title not identified in source. | Source attributes a wall-tolerance factor to this specification; clause text not checked against the licensed copy. [src/assetutilities/calculations/casing_pipe.py:L104-L125] |
| Pipeline `MATERIAL_GRADES` | API 5L; edition and clause title not identified in source. | Source attributes its material lookup to this specification and DNV-OS-F101; clause text not checked against the licensed copy. [src/assetutilities/calculations/pipeline_dnv.py:L19-L29] |
| Casing burst/collapse/inverse sizing/temperature/rating wrapper | API TR 5C3, Technical Report on Equations and Calculations for Casing, Tubing, and Line Pipe Used as Casing or Tubing, 2008; ISO TR 10400, Equations and calculations for the properties of casing, tubing, drill pipe and line pipe used as casing or tubing, first edition 2007; collapse regime and temperature headings in source. | Source also names API BULL 5C3 without an edition; nearest-grade tables, approximate regime split and extrapolated temperature rule require qualification; clause text not checked against the licensed copy. [src/assetutilities/calculations/casing_pipe.py:L7-L14] [src/assetutilities/calculations/casing_pipe.py:L163-L252] [src/assetutilities/calculations/casing_pipe.py:L307-L369] |
| Integrity tension/collapse/utilization/damage functions | Source names guidance revisions and a thin-shell formula, without a public clause locator. | Restricted-source identifiers and their values are omitted here; sidecar entry: to be created (U1). [src/assetutilities/calculations/drilling_riser_integrity.py:L1-L2] [src/assetutilities/calculations/drilling_riser_integrity.py:L26-L155] |
| VIV drag, shedding, reduced velocity, lock-in, response, effective tension, beam expression | Source names Strouhal, Bearman, Griffin, Vandiver, Blevins and Achenbach; source mixes published-author attribution with restricted guidance. | Piecewise correlations, response envelope and pressure-area balance are implemented; no independent publication equation was opened to qualify their fitted coefficients (U1/U2); frequency has D2. [src/assetutilities/calculations/riser_viv.py:L5-L13] [src/assetutilities/calculations/riser_viv.py:L28-L234] [src/assetutilities/calculations/riser_viv.py:L286-L360] |
| Dynamics tow-out, damping, correlation, drag, added mass, residual factor, response | Source attributes methods to Vandiver, Huse, Norton and Smith; no complete public equation locator is supplied. | Arithmetic and piecewise/constant approximations are implemented, including unconditional added mass; cross-flow dimensions have D2. [src/assetutilities/calculations/riser_dynamics.py:L7-L233] |
| Array equivalent diameter, de-equivalencing, shielding, spacing | Source names restricted array guidance and Huse (1993). | Positive-input guards, exponential clipping and a strict `>` spacing test are implemented; calibration provenance remains U1. [src/assetutilities/calculations/riser_array.py:L7-L107] |
| Drilling tension, pressure adjustment, fairing, suppression, weight, speed, mud pressure, power-law response | Source attributes functions to Gardner, Kim, Grant, Jacobsen, D'Souza, Vandiver, Miller, Imas, Berner and Stahl. | Implementation is arithmetic screening; no claim of publication reproduction is made; Kim normalization differs from its docstring (D3). [src/assetutilities/calculations/drilling_riser.py:L31-L328] |
| Wellhead S-N, Miner, effective stress, exposure, tensioner and stiffness multiplier | Source attributes functions to Chen, Sweeney, Allen, Denison and Britton. | Caller-supplied curve parameters drive endurance; biaxial stress and exposure arithmetic are explicit. [src/assetutilities/calculations/wellhead_fatigue.py:L23-L219] |
| SCR KC, soil correction, TDZ, S-N and VIV screening | Source attributes empirical screens to Allen (1995), Brooks (1987) and an OTC paper; complete equation provenance remains U1. | KC arithmetic, corrected Miner summation, amplitude doubling and piecewise screening are implemented. [src/assetutilities/calculations/scr_fatigue.py:L26-L215] |
| TLP tension, stroke, accumulation, gap, damping and set-down | Source lists Javanmardi, Fox, Larimore, Carminati and Barton without individual equation locators. | Functions implement subtraction, distance geometry, S-N/Miner, clear gap and damping arithmetic. [src/assetutilities/calculations/tlp_well_system.py:L6-L11] [src/assetutilities/calculations/tlp_well_system.py:L18-L209] |
| Cost discounting, levelized cost, annuity, MTBF, transport, downtime and installed cost | BS 15663, Part 2, 2001 is named in the header; no clause title is supplied; restricted transport reference omitted. | Clause text not checked against the licensed copy; index-based discounting and direct sums/divisions implement the functions. [src/assetutilities/calculations/lifecycle_cost.py:L1-L156] |
| Polynomial | No reference or equation implemented. | Evaluator is a stub (D5). [src/assetutilities/calculations/polynomial.py:L1-L6] |

The SCR test fixture labels its parameters as a DNV D-curve without specifying edition, clause or stress unit for the intercept, whereas the VIV module declares an edition and performs an explicit stress conversion; these are unresolved provenance/unit gaps, rather than a demonstrated conflict between two identified editions (U1/U3). [src/assetutilities/tests/calculations/test_scr_fatigue.py:L21-L27] [src/assetutilities/calculations/riser_viv.py:L5-L13] [src/assetutilities/calculations/riser_viv.py:L270-L279]

### Duplicate-table and geometry audit

D6: the casing enum has no edition, while the separate MPa table names API 5CT, 10th Edition / ISO 11960:2020, Table C.1; these are different provenance contracts, not evidence that the enum inherits that edition. Their grade coverage also differs, so a name-based substitution is unsafe; converted strength agreement remains unverified under U1. Clause text not checked against the licensed copy. [src/assetutilities/calculations/casing_pipe.py:L23-L47] [src/assetutilities/constants/casing_grades.py:L1-L34]

D6: the pipeline lookup has no API 5L edition; the separate Pa records name API 5L, 46th Edition / ISO 3183:2019, Table J.2. The common X52, X60 and X70 records match, but X65 differs in both yield and ultimate strength. The package constants also differ from the pipeline lookup for X65 and X70, and from the immutable records for X70. This is a value/provenance defect, without choosing a preferred table; clause text not checked against the licensed copy. No tabulated strength is reproduced here. [src/assetutilities/calculations/pipeline_dnv.py:L17-L29] [src/assetutilities/constants/materials.py:L28-L72] [src/assetutilities/constants/__init__.py:L45-L54]

The helper and casing annular areas use the same full annulus expression in different units. The pipeline combined-loading axial resistance instead uses thin-wall area and safety factors; it must not be substituted for the exact area helper without a stated approximation. Helpers also implement second moment and section modulus, which the casing properties do not return. [src/assetutilities/math_helpers.py:L98-L152] [src/assetutilities/calculations/casing_pipe.py:L64-L76] [src/assetutilities/calculations/pipeline_dnv.py:L132-L163]

## 4. Validated worked examples

Validated examples: 0; the selected numerical expectations below come from repository assertions or repeated implementation expressions, without an independently checked source (U2). [src/assetutilities/tests/calculations/test_scr_fatigue.py:L35-L39] [src/assetutilities/tests/calculations/test_lifecycle_cost.py:L38-L42] [src/assetutilities/tests/calculations/test_riser_viv.py:L243-L249] [tests/modules/calculations/test_polynomial.py:L4-L9] [tests/benchmarks/test_scr_fatigue_benchmarks.py:L17-L38]

Regression examples: 6; input literals live in each cited test rather than an external input file, and the tolerance is the assertion's tolerance, without a separate engineering acceptance basis. [src/assetutilities/tests/calculations/test_scr_fatigue.py:L35-L39] [src/assetutilities/tests/calculations/test_lifecycle_cost.py:L38-L42] [src/assetutilities/tests/calculations/test_riser_viv.py:L243-L249] [tests/modules/calculations/test_polynomial.py:L4-L9] [tests/benchmarks/test_scr_fatigue_benchmarks.py:L17-L38]

| Case | Repository source / inputs | Expected value and tolerance | Existing test node ID | Offline observation at code revision |
|---|---|---|---|---|
| R1 KC | Velocity 1.5 m/s, period 10 s, diameter 0.5 m; repeated KC definition. | 30 dimensionless; relative 1e-9 dimensionless. | `src/assetutilities/tests/calculations/test_scr_fatigue.py::TestKeulaganCarpenterNumber::test_known_value` | PASS at BASE and AFTER; [src/assetutilities/tests/calculations/test_scr_fatigue.py:L35-L39] |
| R2 NPV | Costs [1000,1100] caller currency, rate 0.10; repeated discounting arithmetic. | 2000 caller currency; relative 1e-6 dimensionless. | `src/assetutilities/tests/calculations/test_lifecycle_cost.py::TestNetPresentValue::test_two_year_example_known_result` | PASS at BASE and AFTER; [src/assetutilities/tests/calculations/test_lifecycle_cost.py:L38-L42] |
| R3 Zero-pressure tension | Wall tension 1e6 N, pressures 0 Pa, geometry as test literals; implementation identity. | 1e6 N; relative 1e-6 dimensionless. | `src/assetutilities/tests/calculations/test_riser_viv.py::TestEffectiveTension::test_zero_pressure_equals_wall_tension` | PASS at BASE and AFTER; [src/assetutilities/tests/calculations/test_riser_viv.py:L243-L249] |
| R4 Polynomial stub | Instance evaluator argument 2.0, unit unspecified. | `None`; exact match, 0 mismatches (count). | `tests/modules/calculations/test_polynomial.py::TestPolynomial::test_evaluate_polynomial_valid_inputs_returns_none_as_stub` | PASS at BASE and AFTER; [tests/modules/calculations/test_polynomial.py:L4-L9] |
| R5 KC benchmark | Synthetic velocity/period/diameter literals in test; expected value repeats their product/quotient. | Unrounded `_U_M * _PERIOD / _DIAMETER`, dimensionless; relative 1e-9 dimensionless. | `tests/benchmarks/test_scr_fatigue_benchmarks.py::test_bench_keulegan_carpenter_number` | PASS at BASE and AFTER; [tests/benchmarks/test_scr_fatigue_benchmarks.py:L17-L26] |
| R6 Soil benchmark | Integer KC sweep 1 through 20, dimensionless. | 20 results (count), each at least 1 dimensionless; exact length. | `tests/benchmarks/test_scr_fatigue_benchmarks.py::test_bench_soil_interaction_fatigue_factor` | PASS at BASE and AFTER; [tests/benchmarks/test_scr_fatigue_benchmarks.py:L29-L38] |

The benchmark dependency is declared in the test group; selecting that group supplies the fixture and resolves B1. Timing is disabled while both benchmark functions and their assertions execute. [pyproject.toml:L171-L195]

### Offline execution record

Observed BASE results for `uv run --group test python -m pytest tests/modules/calculations tests/benchmarks/test_scr_fatigue_benchmarks.py src/assetutilities/tests/calculations -q -rA -p no:cacheprovider --benchmark-disable --basetemp=<scratch>/bt-base --override-ini addopts=`: 585 collected, 585 passed, 0 failed, 0 skipped, 0 NOT_RUN at `53ad6a0e80b475fadd9e99e341ce2cef07b8b42a`; test definitions at the unchanged code pin are catalogued in section 10.

Recorded AFTER on the uncommitted documentation tree above that same BASE with the identical selection and options, using a separate scratch basetemp: 585 collected, 585 passed, 0 failed, 0 skipped, 0 NOT_RUN; all node outcomes match BASE. The calculation sources and tests match the code pin byte for byte; their imports were checked as text and contain no licensed solver interface.

Coverage addopts are overridden identically on every test command to keep coverage output out of the worktree; test selection is unchanged. [pyproject.toml:L150-L154]

## 5. QA gates

Apply AQG r0, section 10, Python calculations, and section 9, QA appendix: G0 inputs/units/citations, G1 imports/tests, G2 hand or published check, G3/G4 not applicable, G5 evidence traceability.

The following criteria define checks for future calculation use; a pack syntax check does not clear an engineering gate.

| Gate | Applicability | Reason / checks |
|---|---|---|
| G0 | Applicable | Inputs, units and provenance; C01, C02, C03, C09. |
| G1 | Applicable | Offline imports and tests; C04, C05. |
| G2 | Applicable | Hand arithmetic and independent qualification; C06, C07, C08. |
| G3 | NOT_APPLICABLE | Short dynamic solver execution is outside this scalar calculation assessment; AQG r0 section 10, Python calculations. |
| G4 | NOT_APPLICABLE | Diffraction/mesh assessment is outside this scalar calculation assessment; AQG r0 section 10, Python calculations. |
| G5 | Applicable | Calculation-to-evidence traceability; C10, C11, C12. |

| Check ID | Executable check | Numeric pass criterion and unit | Evidence / present limitation | Gate |
|---|---|---|---|---|
| C01 | Run existing mismatch/domain tests for TDZ lists and KC inputs. | 0 failed assertions (count). | Offline pytest node results; [tests/modules/calculations/test_scr_fatigue.py:L14-L27] [tests/modules/calculations/test_scr_fatigue.py:L64-L66] | G0 |
| C02 | Audit the four requested standards against section 3: title, edition, clause and source locator. | 0 incomplete standard records (count). | Source audit; missing API editions/clauses and fatigue clause remain U1. [src/assetutilities/calculations/pipeline_dnv.py:L1-L29] [src/assetutilities/calculations/riser_viv.py:L5-L13] [src/assetutilities/calculations/casing_pipe.py:L107-L125] | G0 |
| C03 | Reduce dimensions of beam frequency, cross-flow amplitude and arrest expression using their documented inputs. | 0 mismatched output dimensions (count). | Dimensional ledger; observed 3 mismatches, D2. [src/assetutilities/calculations/riser_viv.py:L326-L360] [src/assetutilities/calculations/riser_dynamics.py:L193-L233] [src/assetutilities/calculations/pipeline_dnv.py:L186-L208] | G0 |
| C04 | Run the complete section-10 test selection and account for every collected node. | 0 failed or NOT_RUN nodes (count). | 585 passed at BASE and AFTER; R5/R6 execute with the declared test group and timing disabled. [tests/benchmarks/test_scr_fatigue_benchmarks.py:L23-L38] | G1 |
| C05 | Parse each calculation file's import AST and compare with the forbidden solver/interface list. | 0 solver/interface imports (count). | Static import ledger; imports are standard-library arithmetic/types. [src/assetutilities/calculations/casing_pipe.py:L17-L20] [src/assetutilities/calculations/riser_viv.py:L15-L16] | G1 |
| C06 | R1: calculate velocity × period / diameter independently of the function call and compare. | Relative error at most 1e-9 dimensionless. | R1 pytest record; arithmetic regression only. [src/assetutilities/tests/calculations/test_scr_fatigue.py:L35-L39] | G2 |
| C07 | R2: discount the two cost entries by hand and compare. | Relative error at most 1e-6 dimensionless. | R2 pytest record; arithmetic regression only. [src/assetutilities/tests/calculations/test_lifecycle_cost.py:L38-L42] | G2 |
| C08 | Count independently sourced, unit-complete worked examples with an offline result. | At least 1 validated example (count). | Currently 0; issue pending (1), U2. [src/assetutilities/tests/calculations/test_riser_viv.py:L310-L317] [src/assetutilities/tests/calculations/test_lifecycle_cost.py:L38-L42] | G2 |
| C09 | Inspect nonpositive fatigue-bin handling, nonpositive buckling resistance, unused added-mass options and unequal cost/output streams. | 0 silently accepted invalid states (count). | Static branches expose omissions; no comprehensive detection test exists, D4. [src/assetutilities/calculations/riser_viv.py:L270-L279] [src/assetutilities/calculations/pipeline_dnv.py:L154-L163] [src/assetutilities/calculations/riser_dynamics.py:L148-L166] [src/assetutilities/calculations/lifecycle_cost.py:L26-L46] | G0 |
| C10 | Resolve every pack citation with `git show <pin>:<path>` and bounds-check the cited line range. | 100 % resolvable citation occurrences; 0 invalid ranges (count). | Citation resolver record retained with the review evidence. | G5 |
| C11 | Check each open coverage item has an existing issue number or numbered issue draft. | 0 unreferenced open items (count). | Section 10 issue ledger; final issue numbers remain pending. | G5 |
| C12 | For every QA appendix row exporting `rate_casing_pipe` / `CasingPipeRatings`, retain the input fingerprint, `temperature_f` (°F), `derating_factor` (dimensionless), `burst_psi` and `collapse_psi` (psi), `tensile_yield_lbf` (lbf), standard locator, gate result and independent signature; compare the row with the returned dataclass. | 0 missing fields or units (count); 0 mismatched returned values (count). | Inspect fields and compare serialized rows against the function return; the return carries all five quantities, but automatic appendix production/signature remains unverified, U4. [src/assetutilities/calculations/casing_pipe.py:L83-L100] [src/assetutilities/calculations/casing_pipe.py:L338-L369] | G5 |

## 6. Known failure modes and pitfalls
sweep: not run (legacy pack)

| ID / symptom | Cause and detection | Tracking and date | Evidence |
|---|---|---|---|
| D4 Silent fatigue-bin omission; zero buckling contribution; ignored options | Nonpositive fatigue bins are continued, nonpositive capacities contribute zero, and added-mass options do not alter the constant return; C09 detects these branches; no comprehensive detection check exists in the reviewed tests. | issue pending (4); 2026-10-15 | [src/assetutilities/calculations/riser_viv.py:L270-L279] [src/assetutilities/calculations/pipeline_dnv.py:L154-L163] [src/assetutilities/calculations/riser_dynamics.py:L148-L166] [src/assetutilities/tests/calculations/test_riser_viv.py:L197-L235] [src/assetutilities/tests/calculations/test_riser_dynamics.py:L298-L322] |
| D2 Plausible scalar with incorrect declared dimension | Using documented input dimensions, the beam expression yields m/s rather than Hz, cross-flow expression yields m/s rather than m, and arrest expression yields N rather than Pa; C03 detects all three; existing tests repeat formulas or check positivity. | issue pending (2); 2026-10-15 | [src/assetutilities/calculations/riser_viv.py:L326-L360] [src/assetutilities/calculations/riser_dynamics.py:L193-L233] [src/assetutilities/calculations/pipeline_dnv.py:L186-L208] [src/assetutilities/tests/calculations/test_riser_viv.py:L289-L317] [src/assetutilities/tests/calculations/test_pipeline_dnv.py:L244-L281] |
| D3 Docstring/implementation disagreement | Pipeline capacity docstring multiplies safety factors but code divides; Kim docstring includes length in normalization but code omits it except for a zero guard; VIV fatigue labels range as amplitude; C02/C03 contract audit, no complete detection check exists. | issue pending (3); 2026-10-15 | [src/assetutilities/calculations/pipeline_dnv.py:L132-L163] [src/assetutilities/calculations/drilling_riser.py:L92-L133] [src/assetutilities/calculations/riser_viv.py:L253-L255] |
| D1 Standards-like output without independently checked provenance | Casing collapse chooses nearest-grade coefficients and approximate regime division; temperature rule is extrapolated; SCR test parameters carry a curve label without an edition/unit locator; C02/C08 expose the gaps. | issue pending (1); 2026-10-15 | [src/assetutilities/calculations/casing_pipe.py:L163-L252] [src/assetutilities/calculations/casing_pipe.py:L307-L331] [src/assetutilities/tests/calculations/test_scr_fatigue.py:L21-L27] |
| D5 Polynomial returns `None` | Empty evaluator; R4 detects the current stub behavior and prevents interpreting test passage as numerical implementation. | issue pending (5); 2026-10-15 | [src/assetutilities/calculations/polynomial.py:L1-L6] [tests/modules/calculations/test_polynomial.py:L4-L19] |
| D6 Duplicate grade sources disagree | Edition attribution is missing in the calculation lookups; common pipeline grades have value disagreements with the shared constants. C02 detects missing edition records; compare common grade fields after explicit unit alignment, with 0 unexplained differences (count). No cross-table detection test exists. | issue pending (7); 2026-10-15 | [src/assetutilities/calculations/casing_pipe.py:L23-L47] [src/assetutilities/constants/casing_grades.py:L1-L34] [src/assetutilities/calculations/pipeline_dnv.py:L17-L29] [src/assetutilities/constants/materials.py:L28-L72] [src/assetutilities/constants/__init__.py:L45-L54] |

No incident issue was specified for this module; the issue searches found implementation-history issues #118 and #119 and demonstration issue #96, without an existing issue for D1–D6. These issue numbers are discovery context, not evidence that the formulas are independently validated.


## 7. Lessons log

Append new evidence rows; do not rewrite earlier lessons.

| Date | Entry ID | Lesson / pack change | Evidence | Shared-log reference |
|---|---|---|---|---|
| 2026-10-15 | unit-contract-audit | Formula-mirroring tests can pass despite a dimensional disagreement; section 4 uses regression classification and sections 5–6 require a dimensional audit. | [src/assetutilities/tests/calculations/test_riser_viv.py:L310-L317] [src/assetutilities/calculations/riser_viv.py:L326-L360] | Not created; issue pending (6). |
| 2026-10-15 | dependency-and-evidence-audit | Run arithmetic benchmarks with the declared test group; include duplicate grade sources and exact geometry helpers in dependency searches; bind G5 evidence fields to the casing rating return. | [pyproject.toml:L186-L194] [src/assetutilities/constants/materials.py:L28-L72] [src/assetutilities/math_helpers.py:L98-L152] [src/assetutilities/calculations/casing_pipe.py:L338-L369] | Not created; issue pending (6). |

## 8. Ownership

Required responsibilities for this draft:

- Calculations quality manager: assess the Python calculations gates and independent evidence.
- Calculations deputy quality manager: repeat citations and numerical checks independently.
- Engineering calculation maintainers: resolve formula, domain and provenance defects.
- Documentation maintainers: update the pack and its routing entry after reviewed changes.
- Escalation route: refer ambiguous standards, missing inputs, tolerance changes and unresolved checks to the calculations quality manager, then to the maintainer for a decision.

Actual deputy assignment, shared-log linkage and clearance remain open as U4; no clearance is asserted.

## 9. Dependencies

| Direction / dependency | Observed relationship | Inventory linkage / evidence |
|---|---|---|
| Upstream Python | `math`, `typing`, `dataclasses`, `enum` support the arithmetic and containers. | Standard-library dependencies, without an engineering-module inventory row; [src/assetutilities/calculations/casing_pipe.py:L17-L20] [src/assetutilities/calculations/riser_viv.py:L15-L16] [src/assetutilities/calculations/tlp_well_system.py:L14-L15] |
| Downstream Excel utility | Serial utility imports and instantiates `Polynomial`. | Enclosing routed module is `modules`; [src/assetutilities/modules/excel_utilities/excel_utilities.py:L24-L29] [docs/registry/module-routing.yaml:L55-L60] |
| Downstream parallel Excel utility | Parallel utility imports and instantiates `Polynomial`; these imports do not establish numerical use. | Enclosing routed module is `modules`; [src/assetutilities/modules/excel_utilities/excel_utilities_parallel.py:L21-L26] [docs/registry/module-routing.yaml:L55-L60] |
| Tests | Focused tests import calculation functions directly; benchmark cases need the benchmark fixture. | Test catalog in section 10; [tests/modules/calculations/test_riser_viv.py:L1-L12] [tests/benchmarks/test_scr_fatigue_benchmarks.py:L10-L38] |
| Input data | Selected regression cases use literals and local fixtures, not a benchmark dataset with an independently checked revision. | U2; [src/assetutilities/tests/calculations/test_scr_fatigue.py:L21-L39] [src/assetutilities/tests/calculations/test_lifecycle_cost.py:L38-L42] |


### Other implementations and callers

The cross-repository implementation map at revision `947fa50ff9a9e210de7e8f90e01b37add85c5954` supplies the five family IDs below. Its paths belong to another repository: none exists at this pack's code pin, so none is imported as local evidence. The local search covered the whole tracked repository, including `scripts/`, using each family's algorithm, vocabulary and key signals, then direct grade, pipe-geometry and entry-point searches. The local implementations below are missing from that map; extending it remains issue pending (6). The family membership is supported by the cited function bodies, rather than by similarly named foreign paths.

| Map family | Foreign entries absent at this pin | Local scope |
|---|---:|---|
| `catenary-mooring-line-statics` | 137 | Tow-out approximation only; no general catenary solver. |
| `effective-tension-riser-stack-up` | 264 | Effective tension, weight and tensioner arithmetic. |
| `wind-and-current-force-routes` | 131 | Drag/load coefficients and response screens. |
| `sn-curves-and-miner-damage` | 387 | S-N endurance and fatigue accumulation. |
| `api-5ct-5l-grade-tables` | 39 | Casing and pipeline grade lookups. |

Agreement means agreement with this pack's unit, domain and provenance controls, not engineering validation. Independent means a separate implementation; wrapper means it calls another local method. No byte-identical function bodies were found among the listed local implementations after removing docstrings and AST locations; similar expressions are not classified as copies. The external map's defect flags cannot be transferred to absent paths; the local tow-out approximation is not a catenary hand-check reference, and local defects D1–D6 remain applicable as recorded in section 6.

| Family | Path · function/class/data · definition line | Implements | Relation | Agrees with key controls | Covering pack / evidence |
|---|---|---|---|---|---|
| `catenary-mooring-line-statics` | `src/assetutilities/calculations/riser_dynamics.py` · `tow_out_catenary_tension` · L7 | Tow-out tension approximation; not a general catenary reference. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_dynamics.py:L7-L44] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/riser_viv.py` · `effective_tension` · L286 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_viv.py:L286-L319] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/drilling_riser.py` · `gardner_bottom_tension` · L31 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser.py:L31-L56] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/drilling_riser.py` · `gardner_top_tension` · L59 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser.py:L59-L75] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/drilling_riser.py` · `berner_riser_effective_tension` · L301 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser.py:L301-L328] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/drilling_riser.py` · `dsouza_flex_riser_effective_weight` · L191 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser.py:L191-L207] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/drilling_riser_integrity.py` · `riser_effective_tension` · L7 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser_integrity.py:L7-L23] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/drilling_riser_integrity.py` · `minimum_top_tension` · L47 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser_integrity.py:L47-L70] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/tlp_well_system.py` · `tendon_effective_tension` · L18 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/tlp_well_system.py:L18-L42] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/tlp_well_system.py` · `riser_tensioner_stroke` · L45 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/tlp_well_system.py:L45-L71] |
| `effective-tension-riser-stack-up` | `src/assetutilities/calculations/wellhead_fatigue.py` · `denison_conductor_tensioner_load` · L168 | Pressure/weight/tension or tensioner arithmetic. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/wellhead_fatigue.py:L168-L186] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_viv.py` · `drag_coefficient_smooth_cylinder` · L41 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_viv.py:L41-L79] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_viv.py` · `drag_coefficient_bundle` · L86 | Hydrodynamic coefficient, geometry/load factor or response screen. | wrapper | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_viv.py:L86-L122] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_dynamics.py` · `hydrodynamic_damping_ratio` · L47 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_dynamics.py:L47-L82] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_dynamics.py` · `norton_drag_coefficient` · L113 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_dynamics.py:L113-L145] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_dynamics.py` · `vandiver_added_mass_coefficient` · L148 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_dynamics.py:L148-L166] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_dynamics.py` · `crossflow_psd_amplitude` · L193 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_dynamics.py:L193-L233] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/drilling_riser.py` · `grant_faired_drag_coefficient` · L136 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser.py:L136-L165] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_array.py` · `equivalent_diameter` · L7 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_array.py:L7-L27] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_array.py` · `de_equivalencing_factor` · L30 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_array.py:L30-L48] |
| `wind-and-current-force-routes` | `src/assetutilities/calculations/riser_array.py` · `hydrodynamic_shadow_factor` · L51 | Hydrodynamic coefficient, geometry/load factor or response screen. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_array.py:L51-L78] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/riser_viv.py` · `viv_fatigue_damage` · L241 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_viv.py:L241-L279] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/scr_fatigue.py` · `fatigue_damage_tdz` · L88 | S-N/Miner endurance, life, accumulation or correction. | wrapper | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/scr_fatigue.py:L88-L127] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/scr_fatigue.py` · `scr_sn_fatigue_life` · L130 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/scr_fatigue.py:L130-L158] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/scr_fatigue.py` · `soil_interaction_fatigue_factor` · L59 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/scr_fatigue.py:L59-L85] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/wellhead_fatigue.py` · `sn_cycles_to_failure` · L23 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/wellhead_fatigue.py:L23-L47] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/wellhead_fatigue.py` · `fatigue_life_years` · L50 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/wellhead_fatigue.py:L50-L72] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/wellhead_fatigue.py` · `annual_fatigue_damage` · L75 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/wellhead_fatigue.py:L75-L95] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/wellhead_fatigue.py` · `accumulate_fatigue_damage` · L98 | S-N/Miner endurance, life, accumulation or correction. | wrapper | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/wellhead_fatigue.py:L98-L114] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/wellhead_fatigue.py` · `viv_wellhead_fatigue_damage` · L137 | S-N/Miner endurance, life, accumulation or correction. | wrapper | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/wellhead_fatigue.py:L137-L165] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/wellhead_fatigue.py` · `britton_fatigue_life_multiplier` · L189 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/wellhead_fatigue.py:L189-L219] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/drilling_riser_integrity.py` · `annual_fatigue_damage` · L135 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser_integrity.py:L135-L155] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/tlp_well_system.py` · `wellhead_fatigue_accumulation` · L74 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/tlp_well_system.py:L74-L111] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/riser_dynamics.py` · `viv_fatigue_correction_factor` · L85 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/riser_dynamics.py:L85-L110] |
| `sn-curves-and-miner-damage` | `src/assetutilities/calculations/drilling_riser.py` · `jacobsen_suppression_damage_ratio` · L168 | S-N/Miner endurance, life, accumulation or correction. | independent | not checked; see sections 5–6 | This pack; [src/assetutilities/calculations/drilling_riser.py:L168-L188] |
| `api-5ct-5l-grade-tables` | `src/assetutilities/calculations/casing_pipe.py` · `PipeGrade` · L27 | Casing yield lookup in psi. | independent | no; edition missing, D6 | This pack; [src/assetutilities/calculations/casing_pipe.py:L23-L47] |
| `api-5ct-5l-grade-tables` | `src/assetutilities/calculations/pipeline_dnv.py` · `MATERIAL_GRADES` · L24 | Pipeline yield/ultimate lookup in Pa. | independent | no; provenance and value differences, D6 | This pack; [src/assetutilities/calculations/pipeline_dnv.py:L17-L29] |
| `api-5ct-5l-grade-tables` | `src/assetutilities/constants/casing_grades.py` · `CasingGrade` / `CASING_GRADES` · L7 / L23 | Separate casing grade records in MPa. | independent | not checked after unit conversion; edition stated, coverage differs, D6 | none; [src/assetutilities/constants/casing_grades.py:L1-L34] |
| `api-5ct-5l-grade-tables` | `src/assetutilities/constants/materials.py` · `SteelGrade` / `STEEL_GRADES` · L11 / L120 | Separate API 5L grade records in Pa. | independent | no; X65 differs from pipeline lookup, D6 | none; [src/assetutilities/constants/materials.py:L11-L24] [src/assetutilities/constants/materials.py:L28-L72] [src/assetutilities/constants/materials.py:L120-L137] |
| `api-5ct-5l-grade-tables` | `src/assetutilities/constants/materials.py` · `get_steel_grade` · L140 | Lookup of immutable grade records. | wrapper | no; returns the differing table unchanged, D6 | none; [src/assetutilities/constants/materials.py:L140-L149] |
| `api-5ct-5l-grade-tables` | `src/assetutilities/constants/__init__.py` · `FY_X42` through `FY_X80` · L49–L54 | Separate pipeline yield constants in Pa. | independent | no; X65/X70 differences, D6 | none; [src/assetutilities/constants/__init__.py:L45-L54] |
| Supplemental pipe geometry | `src/assetutilities/math_helpers.py` · `pipe_cross_section_area` · L110 | Exact annulus area in m². | independent | yes for area expression after unit alignment; helper validates geometry | none; [src/assetutilities/math_helpers.py:L98-L122] [src/assetutilities/calculations/casing_pipe.py:L64-L76] |
| Supplemental pipe geometry | `src/assetutilities/math_helpers.py` · `pipe_moment_of_inertia` · L125 | Annular second moment in m⁴. | independent | not checked; no corresponding casing return | none; [src/assetutilities/math_helpers.py:L125-L137] [src/assetutilities/calculations/casing_pipe.py:L51-L76] |
| Supplemental pipe geometry | `src/assetutilities/math_helpers.py` · `pipe_section_modulus` · L140 | Elastic modulus in m³ via inertia. | wrapper | not checked; no corresponding casing return | none; [src/assetutilities/math_helpers.py:L140-L152] [src/assetutilities/calculations/casing_pipe.py:L51-L76] |
| Supplemental pipe geometry | `src/assetutilities/calculations/casing_pipe.py` · `CasingPipeProperties.cross_sectional_area_in2` · L69 | Exact annulus area in in². | independent | yes for expression; geometry guards differ | This pack; [src/assetutilities/calculations/casing_pipe.py:L51-L76] |
| Supplemental pipe geometry | `src/assetutilities/calculations/pipeline_dnv.py` · `local_buckling_combined_loading` · L119 | Thin-wall axial and bending resistances. | independent | no; safety-factor contract D3; not exact geometry | This pack; [src/assetutilities/calculations/pipeline_dnv.py:L119-L163] |

SHEAR7 references, read as text only:

| Occurrence | Meaning in source | Version / dependency status | Citation |
|---|---|---|---|
| Module reference list | Names a pinned-pinned beam model. | Version unspecified; attribution only. | [src/assetutilities/calculations/riser_viv.py:L11-L11] |
| Frequency section heading | Labels the beam model. | Version unspecified; attribution only. | [src/assetutilities/calculations/riser_viv.py:L323-L323] |
| Frequency docstring equation label | Associates the expression with an Euler-Bernoulli beam. | Version unspecified; dimensional discrepancy D2. | [src/assetutilities/calculations/riser_viv.py:L334-L335] |
| Frequency docstring compatibility claim | Claims consistency with mode-shape inputs. | Version unspecified; external compatibility unverified under U1. | [src/assetutilities/calculations/riser_viv.py:L337-L339] |
| Supporting test reference list | Names a manual as the frequency reference. | Version unspecified; no manual was opened. | [src/assetutilities/tests/calculations/test_riser_viv.py:L4-L9] |

The frequency function performs local arithmetic and contains no solver call. [src/assetutilities/calculations/riser_viv.py:L326-L360]

Dependency inventory rows beyond the enclosing routing entries, and solver-version compatibility, remain open under U4/U1.

## 10. Coverage and open items

### Read coverage

The complete source-file catalog follows; each file was read as text at the pinned revision.

| Source file | Read extent / evidence |
|---|---|
| `src/assetutilities/calculations/casing_pipe.py` | [src/assetutilities/calculations/casing_pipe.py:L1-L369] |
| `src/assetutilities/calculations/drilling_riser.py` | [src/assetutilities/calculations/drilling_riser.py:L1-L328] |
| `src/assetutilities/calculations/drilling_riser_integrity.py` | [src/assetutilities/calculations/drilling_riser_integrity.py:L1-L155] |
| `src/assetutilities/calculations/lifecycle_cost.py` | [src/assetutilities/calculations/lifecycle_cost.py:L1-L156] |
| `src/assetutilities/calculations/pipeline_dnv.py` | [src/assetutilities/calculations/pipeline_dnv.py:L1-L208] |
| `src/assetutilities/calculations/polynomial.py` | [src/assetutilities/calculations/polynomial.py:L1-L6] |
| `src/assetutilities/calculations/riser_array.py` | [src/assetutilities/calculations/riser_array.py:L1-L107] |
| `src/assetutilities/calculations/riser_dynamics.py` | [src/assetutilities/calculations/riser_dynamics.py:L1-L233] |
| `src/assetutilities/calculations/riser_viv.py` | [src/assetutilities/calculations/riser_viv.py:L1-L360] |
| `src/assetutilities/calculations/scr_fatigue.py` | [src/assetutilities/calculations/scr_fatigue.py:L1-L215] |
| `src/assetutilities/calculations/tlp_well_system.py` | [src/assetutilities/calculations/tlp_well_system.py:L1-L209] |
| `src/assetutilities/calculations/wellhead_fatigue.py` | [src/assetutilities/calculations/wellhead_fatigue.py:L1-L219] |

The following documentation was found by module-path/name searches and read; generic mentions of calculations in unrelated documentation are excluded from module evidence.

| Documentation / routing surface | Evidence |
|---|---|
| `README.md` | [README.md:L1-L33] |
| `MODULE_STRUCTURE.md` | [MODULE_STRUCTURE.md:L43-L70] |
| `docs/README.md` | [docs/README.md:L1-L56] |
| `docs/maps/assetutilities-operator-map.md` | [docs/maps/assetutilities-operator-map.md:L1-L25] |
| `docs/registry/module-routing.yaml` | [docs/registry/module-routing.yaml:L25-L30] |

### Test catalog

Observed collection at BASE and AFTER totals 585 nodes across 24 files: 585 PASS, 0 failed, 0 skipped and 0 NOT_RUN; no cases were deselected or newly marked skipped.

| Test file | Collected nodes | Offline result at BASE and AFTER | Definition evidence |
|---|---|---|---|
| `tests/modules/calculations/test_casing_pipe.py` | 10 | 10 PASS | [tests/modules/calculations/test_casing_pipe.py:L1-L65] |
| `tests/modules/calculations/test_drilling_riser.py` | 14 | 14 PASS | [tests/modules/calculations/test_drilling_riser.py:L1-L79] |
| `tests/modules/calculations/test_drilling_riser_integrity.py` | 11 | 11 PASS | [tests/modules/calculations/test_drilling_riser_integrity.py:L1-L56] |
| `tests/modules/calculations/test_lifecycle_cost.py` | 11 | 11 PASS | [tests/modules/calculations/test_lifecycle_cost.py:L1-L55] |
| `tests/modules/calculations/test_pipeline_dnv.py` | 8 | 8 PASS | [tests/modules/calculations/test_pipeline_dnv.py:L1-L41] |
| `tests/modules/calculations/test_polynomial.py` | 3 | 3 PASS | [tests/modules/calculations/test_polynomial.py:L1-L19] |
| `tests/modules/calculations/test_riser_array.py` | 11 | 11 PASS | [tests/modules/calculations/test_riser_array.py:L1-L52] |
| `tests/modules/calculations/test_riser_dynamics.py` | 15 | 15 PASS | [tests/modules/calculations/test_riser_dynamics.py:L1-L71] |
| `tests/modules/calculations/test_riser_viv.py` | 19 | 19 PASS | [tests/modules/calculations/test_riser_viv.py:L1-L82] |
| `tests/modules/calculations/test_scr_fatigue.py` | 23 | 23 PASS | [tests/modules/calculations/test_scr_fatigue.py:L1-L115] |
| `tests/modules/calculations/test_tlp_well_system.py` | 12 | 12 PASS | [tests/modules/calculations/test_tlp_well_system.py:L1-L59] |
| `tests/modules/calculations/test_wellhead_fatigue.py` | 13 | 13 PASS | [tests/modules/calculations/test_wellhead_fatigue.py:L1-L64] |
| `src/assetutilities/tests/calculations/test_casing_pipe.py` | 35 | 35 PASS | [src/assetutilities/tests/calculations/test_casing_pipe.py:L1-L258] |
| `src/assetutilities/tests/calculations/test_drilling_riser.py` | 57 | 57 PASS | [src/assetutilities/tests/calculations/test_drilling_riser.py:L1-L406] |
| `src/assetutilities/tests/calculations/test_drilling_riser_integrity.py` | 38 | 38 PASS | [src/assetutilities/tests/calculations/test_drilling_riser_integrity.py:L1-L287] |
| `src/assetutilities/tests/calculations/test_lifecycle_cost.py` | 40 | 40 PASS | [src/assetutilities/tests/calculations/test_lifecycle_cost.py:L1-L295] |
| `src/assetutilities/tests/calculations/test_pipeline_dnv.py` | 29 | 29 PASS | [src/assetutilities/tests/calculations/test_pipeline_dnv.py:L1-L281] |
| `src/assetutilities/tests/calculations/test_riser_array.py` | 23 | 23 PASS | [src/assetutilities/tests/calculations/test_riser_array.py:L1-L138] |
| `src/assetutilities/tests/calculations/test_riser_dynamics.py` | 40 | 40 PASS | [src/assetutilities/tests/calculations/test_riser_dynamics.py:L1-L428] |
| `src/assetutilities/tests/calculations/test_riser_viv.py` | 44 | 44 PASS | [src/assetutilities/tests/calculations/test_riser_viv.py:L1-L325] |
| `src/assetutilities/tests/calculations/test_scr_fatigue.py` | 43 | 43 PASS | [src/assetutilities/tests/calculations/test_scr_fatigue.py:L1-L305] |
| `src/assetutilities/tests/calculations/test_tlp_well_system.py` | 38 | 38 PASS | [src/assetutilities/tests/calculations/test_tlp_well_system.py:L1-L358] |
| `src/assetutilities/tests/calculations/test_wellhead_fatigue.py` | 46 | 46 PASS | [src/assetutilities/tests/calculations/test_wellhead_fatigue.py:L1-L331] |
| `tests/benchmarks/test_scr_fatigue_benchmarks.py` | 2 | 2 PASS | [tests/benchmarks/test_scr_fatigue_benchmarks.py:L1-L38] |

The package-test marker was also read. [src/assetutilities/tests/calculations/__init__.py:L1-L2]

### Open coverage ledger

Each item is assigned to the calculations maintainers; numbered drafts are pending issue creation, and this draft does not assert final quality clearance.

| Item | Claim or work remaining | Tracking | Detection / closure |
|---|---|---|---|
| U1 | UNVERIFIED: full standards titles/editions/clauses, empirical attribution, external SHEAR7 compatibility and Citation-sidecar compliance are not independently established; restricted-source material has sidecar entry: to be created. | issue pending (1) | C02; obtain permissible source locators and sidecar IDs, without publishing restricted values. |
| U2 | UNVERIFIED: independent engineering validation is not established for the selected regression examples; repeating code equations is insufficient. | issue pending (1) | C08; add an independently sourced, unit-complete case with tolerance basis and test node. |
| U3 | UNVERIFIED: complete per-argument physical domains, global coordinate origin/frame/phase conventions, fatigue intercept units and file-format unit contracts are not established. | issue pending (3) | Audit contracts beyond the main input/output groups; resolve D3 before claiming complete coverage. |
| U4 | UNVERIFIED: deputy assignment, dependency inventory linkage, shared-log reference and automatic fingerprinted QA appendix production are not established. | issue pending (6) | C12; establish assignments and durable evidence records before clearance. |
| D1 | Qualify approximate collapse regime selection, nearest-grade fallback and temperature extrapolation, with precise public attribution. [src/assetutilities/calculations/casing_pipe.py:L163-L252] [src/assetutilities/calculations/casing_pipe.py:L307-L331] | issue pending (1) | C02/C08; independent reference checks. |
| D2 | Resolve all three output-dimension mismatches; passing formula-mirroring tests are insufficient. [src/assetutilities/calculations/riser_viv.py:L326-L360] [src/assetutilities/calculations/riser_dynamics.py:L193-L233] [src/assetutilities/calculations/pipeline_dnv.py:L186-L208] | issue pending (2) | C03; 0 dimension mismatches. |
| D3 | Align docstrings, code and units for pipeline safety factors, Kim normalization and fatigue range/amplitude. [src/assetutilities/calculations/pipeline_dnv.py:L132-L163] [src/assetutilities/calculations/drilling_riser.py:L92-L133] [src/assetutilities/calculations/riser_viv.py:L253-L255] | issue pending (3) | Contract reconciliation and independent checks. |
| D4 | Define invalid-state behavior for omitted fatigue bins, zero capacities, ignored added-mass options and unequal lifecycle streams. [src/assetutilities/calculations/riser_viv.py:L270-L279] [src/assetutilities/calculations/pipeline_dnv.py:L154-L163] [src/assetutilities/calculations/riser_dynamics.py:L148-L166] [src/assetutilities/calculations/lifecycle_cost.py:L26-L46] | issue pending (4) | C09; explicit domain tests, 0 silent invalid-state acceptances. |
| D5 | Define the polynomial API or document its unsupported status beyond the stub-return tests. [src/assetutilities/calculations/polynomial.py:L1-L6] [tests/modules/calculations/test_polynomial.py:L4-L19] | issue pending (5) | R4 exposes the stub; a numerical acceptance check is still needed. |
| D6 | Reconcile edition attribution, grade coverage and inconsistent shared pipeline grade records without silently choosing one source. [src/assetutilities/constants/casing_grades.py:L1-L34] [src/assetutilities/constants/materials.py:L28-L72] [src/assetutilities/constants/__init__.py:L45-L54] [src/assetutilities/calculations/pipeline_dnv.py:L17-L29] | issue pending (7) | C02 and explicit cross-table unit-aligned comparison; 0 unexplained differences. |

Issue-search context: #118 and #119 record completed implementations; #96 concerns demonstration work; none supplies an independently checked numerical benchmark for the selected examples.
