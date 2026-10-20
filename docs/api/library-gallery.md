# Library demonstrations

The gallery runs library functions on synthetic inputs and renders their actual
answers. It publishes no existing reports or directories of data. Calculation
criteria that lack qualified source evidence remain `NOT_EVALUATED`.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| 1 | 2026-10-20 | Added reproducible examples and explicit source limits. |

## Build and inspect

From a development checkout with the documentation dependencies available:

```sh
uv run --group docs mkdocs build --strict
uv run python scripts/build_gallery.py --out site/gallery
uv run python -m pytest tests/modules/gallery tests/modules/reportgen -q
```

The Pages and documentation workflows run both build commands. Pages deployment
occurs after merge through the existing deployment workflow. A local build or
draft pull request does not establish that the updated site is live.

Generated pages, `answers.json` and `workflow.json` are build artifacts; they are
not committed. Each page carries an input echo, provenance, caveats and code
references. The workflow page displays the measured input and result hashes and
file metadata from `run_workflow`; `reproducible: null` means not checked.

## Worked arithmetic example

The inputs below are defined for illustration. They are not material properties,
published curve coefficients or acceptance limits. Expected answers follow from
the written arithmetic, independently of the implementation.

| Subject | Inputs | Method and answer | Implementing function |
|---|---|---|---|
| SCR fatigue | amplitude 5 MPa; A = 1000000 MPa³ cycles; m = 3 | range = 2 × 5 = 10 MPa; N = 1000000 / 10³ = 1000.0 cycles | `scr_sn_fatigue_life` |
| Wellhead fatigue | range 10 psi; A = 1000000 psi³ cycles; m = 3; 100 cycles/year | N = 1000000 / 10³ = 1000.0 cycles; life = 1000 / 100 = 10.0 years | `sn_cycles_to_failure`, `fatigue_life_years` |
| Reduced velocity | U = 2 m/s; frequency = 2 Hz; diameter = 0.5 m | Vr = 2 / (2 × 0.5) = 2.0 | `reduced_velocity` |
| Present cost | costs [100, 110]; annual rate 0.1 | 100 + 110 / 1.1 = 200.0 currency units | `net_present_value` |
| Levelized cost | same costs/rate; outputs [10, 11] | 200 / (10 + 11 / 1.1) = 10.0 currency/output units | `levelized_cost` |
| Unit trace | length 1000 mm | 1000 × 10⁻³ = 1.0 m, with conversion history | `TrackedQuantity.to` |

The arithmetic definitions appear in the implementing function docstrings under
`src/assetutilities/calculations/`. Their presence does not qualify a standards
implementation. The SI prefix is sourced from
[NIST SP 811 (2008), section 4.3, table 5](https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-4-two-classes-si-units-and-si-prefixes);
the current public table includes later additional prefixes, which this example
does not use.

## Coverage and limits

- Pipeline: explicit unevaluated pressure containment, combined loading and
  buckle arrest. `calculations/docs/agent-pack.md`, sections 3 and 10, records
  unverified clause attribution, safety-factor disagreements and an output
  dimension issue. No capacity or compliance verdict is published.
- SCR and VIV: synthetic S-N arithmetic and the reduced-velocity definition run;
  TDZ, lock-in and empirical amplitude acceptance await qualified sources.
- Wellhead and lifecycle cost: synthetic arithmetic runs with all parameters
  supplied; no engineering life or financial recommendation is established.
- Visualization: the same synthetic XY series passes through the library's
  Plotly and matplotlib template methods; a separate synthetic radius/angle
  series exercises the matplotlib polar template. Interactive JavaScript and
  PNG bytes are embedded. No external resource elements or CSS imports are accepted.
- Units: quantities and conversions retain their audit records.
- YAML workflow: the registered visualization example runs through the sandboxed
  workflow API. Only its metadata survives that API's temporary run directory.

The inline Plotly bundle contains dormant map URLs. This gallery uses Cartesian
traces only, disables the toolbar, and checks resource elements rather than
claiming that a bundled JavaScript program has no URL strings. No browser network
audit is claimed.

Further standards-based verdicts require independently qualified editions,
coefficients and domains. Existing data directories and private standards text
are never gallery inputs.
