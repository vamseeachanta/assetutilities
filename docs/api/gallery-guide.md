# Library demonstration gallery

The gallery runs existing library functions on synthetic inputs and renders
their results with provenance, input echoes, source links and limitations.
Engineering acceptance remains `NOT_EVALUATED`; library screening verdicts
describe the implementation's arithmetic only.

## Revision history

| Revision | Date | Change and reason |
| --- | --- | --- |
| 0 | 2026-10-19 | Add synthetic demonstrations to make library behavior inspectable. |
| 1 | 2026-10-22 | Correct equation and cost-source disclosures, mark low-KC damage unevaluated and improve portable builds. |

## Build and view

```bash
uv run --group docs mkdocs build --strict
uv run python scripts/build_gallery.py --out site/gallery
```

Open `site/gallery/index.html` locally, or use
<a href="../gallery/">the published gallery</a>. Build the gallery after MkDocs,
which clears its output directory. Generated HTML and PNG data stay in ignored
`site/`; the generator also accepts an external build directory for tests.
The build executes only the registered visualization workflow through
`run_workflow`, never the file-writing CLI form.

## What is demonstrated

| Page | Method and source in the repository | Limits |
| --- | --- | --- |
| Pipeline | `calculations/pipeline_dnv.py`: burst, pressure containment, combined loading, von Mises; source module cites DNV OS-F101 (2013) | The burst and combined-loading routines use library-simplified expressions and do not reproduce the cited standard equations. Containment screening inherits the simplified burst capacity; linked docstrings do not establish standard compliance for this demonstration. Synthetic factors are explicit inputs. Buckle arrest is `NOT_EVALUATED`. |
| SCR fatigue | `calculations/scr_fatigue.py`: S-N life, touchdown damage, VIV screening; cites OTC (1987, 2001) | Synthetic S-N curve. Low-KC damage is `NOT_EVALUATED` because its soil coefficient lacks an independently qualified basis. VIV coefficients are inherited implementation behavior, without independently qualified paper evidence. |
| Riser VIV | `calculations/riser_viv.py`: frequency and reduced velocity; cites Strouhal (1878) | Strouhal number is explicitly supplied; no lock-in or amplitude assessment. |
| Wellhead fatigue | `calculations/wellhead_fatigue.py`: S-N cycles, annual damage and life; cites OTC (1989) | Synthetic curve and cycle rate; no service-life prediction. |
| Lifecycle cost | `calculations/lifecycle_cost.py`: discounted cost and output; ISO 15663-2:2001 (BS EN ISO 15663-2:2001) | Library arithmetic only; arbitrary currency/output units and synthetic discount rates, with year zero first. |
| Traceable units | `units/quantity.py`, `units/registry.py`, `units/traceability.py` | SI prefix conversion and rectangle area; no physical design criterion. |
| Workflow envelope | `workflow_api/runner.py`, `workflow_api/envelope.py`, `docs/registry/workflows.yaml` | Real hashes and file metadata; temporary PNG bytes are discarded. `reproducible: null` means not checked. |
| Visualization templates | `common/visualization/`, `base_configs/modules/visualization/` | New synthetic data only: Plotly XY and matplotlib line, scatter and polar. No prebuilt result images or external map assets. |

Source names above identify the library's existing references, not independent
validation of those publications. No licensed standard tables are reproduced.
Every generated code link is pinned to the reported build revision and source
line. Review the implementing function before using a result outside this demo.

## Worked example: synthetic pressure containment

Inputs are deliberately small arithmetic fixtures, rather than a pipe grade:
diameter `D = 1.0 m`, thickness `t = 0.01 m`, yield strength `fy = 100.0 Pa`,
tensile strength `fu = 230.0 Pa`, and explicitly supplied strength, fabrication
and resistance factors all equal to unity. These are synthetic choices, not
recommended design values.

The method follows `pipeline_dnv.burst_pressure_capacity` and
`pressure_containment_check`. The source module cites DNV OS-F101 (2013), but
the burst and combined-loading routines use library-simplified expressions that
do not reproduce the cited standard equations. The following arithmetic tests
the implementation only. Its characteristic-strength divisor is used by the function;
the tensile branch is non-governing for these inputs, so the flow stress is
`100.0 Pa`.

```text
Pb = (2 × t / D) × flow stress × fabrication factor
   = (2 × 0.01 / 1.0) × 100.0 × 1.0 = 2.0 Pa
U  = pressure × material factor × safety-class factor / Pb
```

At `1.0 Pa`, `U = 0.5`, giving library screening `PASS`.
At `3.0 Pa`, `U = 1.5`, giving library screening `FAIL`.
The unity screening boundary is the utilization definition documented by the
implementing function. Neither result establishes engineering acceptance.
The test docstring writes out this calculation independently of the function.

For the units example, `500.0 mm` converts to `0.5 m` through the registry;
multiplying by `2.0 m` gives `1.0 m²`. The output retains both original sources,
the conversion entry and the multiplication entry in its provenance chain.

## Evidence and build behavior

Every page includes a git revision, installed package version, UTC generation
time, exact inputs, results, code references and caveats. `GITHUB_SHA` selects
the build revision; `SOURCE_DATE_EPOCH` fixes the page header timestamp.
Local edits set `uncommitted_changes` to true; source links refer to the reported
commit and may differ from the locally edited implementation.
Unit audit entries and workflow execution timestamps remain actual run times.
Whole-page byte reproducibility is therefore not claimed. The workflow API's
optional double-run reproducibility check is not requested by the gallery.

All rendering assets are inline: Plotly JavaScript and PNG data URIs. The unused
geographic asset endpoint embedded in Plotly's bundle is changed to a local
relative endpoint; geographic plots are unsupported. Rendering dependencies
outside the page, remote styles and known CDN references fail the build.
Navigation and source citations may link out. Every page is validated before
any page is written. The output directory should be dedicated to this build;
an earlier successful build is not removed on a later failure.

The docs check builds the gallery after strict MkDocs validation. The existing
Pages workflow uploads the combined site after both builds succeed. The
gallery tests reside in `tests/modules/gallery/`, which selects its domain in
the existing CI matrix without changing the selector.

## Later slices

Independent engineering qualification of empirical correlations, additional
datetime/CSV templates, geographic assets, and design-ready acceptance criteria
require separate evidence and tests. No public reachability claim is made until
the maintainers merge and the existing deployment succeeds.
