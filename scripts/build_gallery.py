"""Build library demonstrations; generated HTML is never a design assessment.

Only explicit library calls and synthetic inputs are used. Engineering criteria
without independently qualified sources remain NOT_EVALUATED. Output belongs in
the ignored site directory or an externally supplied build directory.
"""

from __future__ import annotations

import argparse
import base64
import copy
import inspect
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from pathlib import Path

from assetutilities.calculations import (
    lifecycle_cost,
    riser_viv,
    scr_fatigue,
    wellhead_fatigue,
)
from assetutilities.calculations import pipeline_dnv as pipeline
from assetutilities.units import CalculationAuditLog, TrackedQuantity
from assetutilities.workflow_api import run_workflow
from assetutilities.workflow_api.runner import (
    resolve_example_path,
    resolve_registry_row,
)

ROOT = Path(__file__).resolve().parents[1]
GIT_BINDINGS = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
COMMON_CAVEATS = (
    "Synthetic inputs; screening-level library demonstration only. "
    "Engineering acceptance: NOT_EVALUATED. No code-compliance assessment, "
    "material qualification, environmental data or design recommendation is supplied."
)


@dataclass
class Page:
    title: str
    inputs: dict
    results: dict
    caveats: str
    references: list
    body: str = ""
    method: str = "See the cited library implementation."


def json_text(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False)


def table(rows):
    if not rows:
        return "<p>No rows.</p>"
    columns = list(rows[0])
    head = "".join(f"<th scope='col'>{escape(c)}</th>" for c in columns)
    body = ""
    for row in rows:
        body += "<tr>"
        for col in columns:
            value = row.get(col, "")
            text = json_text(value) if isinstance(value, (dict, list)) else str(value)
            css = " class='" + text.lower() + "'" if text in {"PASS", "FAIL"} else ""
            body += f"<td{css}><pre>{escape(text)}</pre></td>"
        body += "</tr>"
    return f"<div class='table'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


class AssetScanner(HTMLParser):
    """Allow navigation links, but require all rendering assets to be inline."""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("src", "href", "srcset", "data", "poster", "xlink:href"):
            value = attrs.get(key, "").strip()
            if tag == "a" and key == "href":
                continue
            if value and not value.startswith(("data:", "#")):
                raise ValueError("Gallery contains a non-inline rendering dependency")
        if tag in {"iframe", "object", "embed", "base"}:
            raise ValueError("Gallery contains an unsupported embedded resource")
        self.check_css(attrs.get("style", ""))
        if tag == "style":
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if getattr(self, "in_style", False):
            self.check_css(data)

    @staticmethod
    def check_css(text):
        if re.search(r"@import|url\s*\(", text, re.IGNORECASE):
            raise ValueError("Gallery CSS must not load resources")


def check_self_contained(html):
    if any(token in html.lower() for token in ("cdn.plot.ly", "plotly-latest")):
        raise ValueError("Gallery contains a forbidden remote Plotly reference")
    AssetScanner().feed(html)


def git_output(*args):
    env = {key: value for key, value in os.environ.items() if key not in GIT_BINDINGS}
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, encoding="utf-8", env=env
    ).strip()


def provenance():
    try:
        package_version = version("assetutilities")
    except PackageNotFoundError:
        package_version = "unknown (not installed)"
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    generated = (
        datetime.fromtimestamp(int(epoch), timezone.utc)
        if epoch is not None
        else datetime.now(timezone.utc)
    )
    sha = os.environ.get("GITHUB_SHA") or git_output("rev-parse", "HEAD")
    # Derive repository links without embedding installation or account details.
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not repository:
        remote = git_output("remote", "get-url", "origin")
        match = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?$", remote)
        repository = match.group(1) if match else ""
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise ValueError("Cannot identify public source repository")
    if not re.fullmatch(r"[a-fA-F0-9]{40}", sha):
        raise ValueError("Git revision must be a full commit digest")
    return {
        "package_version": package_version,
        "git_sha": sha,
        "generated_utc": generated.isoformat(),
        "repository": repository,
        "uncommitted_changes": bool(git_output("status", "--porcelain")),
    }


def code_links(references, evidence):
    links = []
    for function in references:
        path = Path(inspect.getsourcefile(function)).resolve().relative_to(ROOT)
        line = inspect.getsourcelines(function)[1]
        url = f"https://github.com/{evidence['repository']}/blob/{evidence['git_sha']}/{path.as_posix()}#L{line}"
        label = f"{function.__module__}.{function.__qualname__}"
        links.append(
            f"<li><a href='{escape(url, quote=True)}'>{escape(label)}</a></li>"
        )
    return "<ul>" + "".join(links) + "</ul>"


def render_page(page, evidence):
    if not page.caveats or not page.caveats.strip():
        raise ValueError("Every page requires caveats")
    if not page.references:
        raise ValueError("Every page requires code references")
    if not page.inputs:
        raise ValueError("Every page requires input echo")
    # JSON script data must not be able to close its containing HTML element.
    result_json = json_text(page.results).replace("<", "\\u003c")
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(page.title)} | Library gallery</title>
<style>
body{{font:1rem system-ui,sans-serif;max-width:72rem;margin:2rem auto;padding:0 1rem;color:#172d40}}
a{{color:#185cad}}h1,h2{{line-height:1.2}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
.table{{overflow-x:auto}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #aaa;padding:.5rem;text-align:left}}
.pass{{color:#17652b}}.fail{{color:#a11818}}img{{max-width:100%}}aside{{background:#f2f5f7;padding:1rem}}
</style><body><nav><a href="index.html">Gallery</a> · <a href="../index.html">API reference</a></nav>
<main><h1>{escape(page.title)}</h1><h2>Summary</h2>
<p>Existing library functions demonstrate synthetic inputs, methods and results.</p>
<h2>Revision history</h2><table><tr><th>Revision</th><th>Date</th><th>Change and reason</th></tr>
<tr><td>0</td><td>2026-10-19</td><td>Add synthetic demonstrations with traceable evidence.</td></tr>
<tr><td>1</td><td>2026-10-22</td><td>Correct source disclosures, low-KC limits and portable artifact handling.</td></tr></table>
<aside><h2>Caveats</h2><p>{escape(page.caveats)}</p></aside>
<h2>Method and sources</h2><p>{escape(page.method)}</p>{page.body}
<h2>Results</h2>{table([{"quantity": k, "value": v} for k, v in page.results.items()])}
<script id="results" type="application/json">{result_json}</script>
<details><summary>Input echo</summary><pre>{escape(json_text(page.inputs))}</pre></details>
<h2>Provenance</h2><pre>{escape(json_text(evidence))}</pre>
<h2>Code references</h2>{code_links(page.references, evidence)}</main></body></html>"""
    check_self_contained(html)
    return html


def plot_html(fig, name):
    from plotly.offline import get_plotlyjs

    # Plotly embeds an unused geographic asset endpoint even for Cartesian plots.
    # Disable that default for this offline XY/polar gallery; no geography is shown.
    javascript = get_plotlyjs().replace("https://cdn.plot.ly/", "./")
    fragment = fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=name,
        config={"displaylogo": False, "showLink": False},
    )
    return "<script>" + javascript + "</script>" + fragment


def curve(x, y, title, xlabel, ylabel):
    import plotly.graph_objects as go

    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines+markers"))
    fig.update_layout(title=title, xaxis_title=xlabel, yaxis_title=ylabel)
    return fig


def pipeline_page():
    # Synthetic arithmetic fixture, not a material grade or standard safety factor.
    # These library-simplified expressions do not reproduce standard equations.
    inputs = {
        "D": 1.0,
        "thickness_m": [0.01, 0.02, 0.03],
        "f_y": 100.0,
        "f_u": 230.0,
        "alpha_U": 1.0,
        "alpha_fab": 1.0,
        "gamma_m": 1.0,
        "gamma_SCPC": 1.0,
        "pressures_Pa": [1.0, 3.0],
        "bending_Nm": 0.1,
        "axial_N": 0.1,
        "delta_p_Pa": 0.1,
        "gamma_SC": 1.0,
        "stresses_Pa": {"sigma_l": 5.0, "sigma_h": 5.0, "tau": 0.0},
    }
    base = {k: inputs[k] for k in ("D", "f_y", "f_u", "alpha_U", "alpha_fab")}
    burst = [
        pipeline.burst_pressure_capacity(t=t, **base) for t in inputs["thickness_m"]
    ]
    checks = []
    for pressure in inputs["pressures_Pa"]:
        u = pipeline.pressure_containment_check(
            P_li=pressure,
            t=inputs["thickness_m"][0],
            gamma_m=inputs["gamma_m"],
            gamma_SCPC=inputs["gamma_SCPC"],
            **base,
        )
        # Unity is the utilization definition in pressure_containment_check (repo source).
        checks.append(
            {
                "check": "containment",
                "basis": "library-simplified burst expression; engineering acceptance NOT_EVALUATED",
                "pressure_Pa": pressure,
                "utilization": u,
                "screening_status": "PASS" if u <= 1.0 else "FAIL",
            }
        )
    buckling = pipeline.local_buckling_combined_loading(
        D=inputs["D"],
        t=inputs["thickness_m"][0],
        f_y=inputs["f_y"],
        M=inputs["bending_Nm"],
        S=inputs["axial_N"],
        delta_p=inputs["delta_p_Pa"],
        gamma_m=inputs["gamma_m"],
        gamma_SC=inputs["gamma_SC"],
    )
    # Unity is the library's combined-utilization definition (same module).
    combined = {
        "check": "combined loading",
        "utilization": buckling,
        "screening_status": "PASS" if buckling <= 1.0 else "FAIL",
    }
    results = {
        "burst_Pa": burst,
        "containment": checks,
        "local_buckling": combined,
        "von_mises_Pa": pipeline.von_mises_equivalent_stress(**inputs["stresses_Pa"]),
        "buckle_arrest": "NOT_EVALUATED: empirical coefficient not independently qualified",
    }
    return Page(
        "Pipeline calculation routines",
        inputs,
        results,
        COMMON_CAVEATS
        + " The burst and combined-loading routines use library-simplified expressions; "
        "they do not reproduce the cited standard equations. Containment screening inherits "
        "the simplified burst capacity. Linked docstrings do not establish standard compliance "
        "for this demonstration. Buckle arrest is not evaluated.",
        [
            pipeline.burst_pressure_capacity,
            pipeline.pressure_containment_check,
            pipeline.local_buckling_combined_loading,
            pipeline.von_mises_equivalent_stress,
            pipeline.buckle_arrest_capacity,
        ],
        plot_html(
            curve(
                inputs["thickness_m"],
                burst,
                "Synthetic burst capacity",
                "Wall thickness (m)",
                "Pressure (Pa)",
            ),
            "burst",
        )
        + table(checks + [combined]),
        "The source module cites DNV OS-F101 (2013); these burst and combined-loading "
        "expressions are library-simplified and do not reproduce its cited equations. "
        "Pb=(2t/D) min(fy alpha_U, fu alpha_U / material divisor) alpha_fab; "
        "U=P gamma_m gamma_SCPC/Pb. Library screening PASS/FAIL is not engineering acceptance.",
    )


def fatigue_page():
    # Synthetic S-N parameters, not a published material curve. Formula source:
    # scr_fatigue.py: scr_sn_fatigue_life and fatigue_damage_tdz docstrings.
    inputs = {
        "amplitudes_MPa": [10.0, 20.0, 40.0],
        "A": 8000.0,
        "m": 2.0,
        "range_MPa": 20.0,
        "cycles": 2.0,
        "kc": [10.0, 5.0],
        "vr": [2.0, 6.0],
    }
    life = [
        scr_fatigue.scr_sn_fatigue_life(a, inputs["A"], inputs["m"])
        for a in inputs["amplitudes_MPa"]
    ]
    damage = [
        scr_fatigue.fatigue_damage_tdz(
            [inputs["range_MPa"]], [inputs["cycles"]], [kc], inputs["A"], inputs["m"]
        )
        if kc >= 10.0
        else "NOT_EVALUATED: low-KC soil coefficient is not independently qualified"
        for kc in inputs["kc"]
    ]
    screening = []
    for vr in inputs["vr"]:
        risk, amplitude = scr_fatigue.brooks_viv_screening(vr)
        screening.append(
            {
                "reduced_velocity": vr,
                "risk": risk,
                "amplitude_ratio": amplitude,
                "screening_status": "FAIL" if risk else "PASS",
            }
        )
    return Page(
        "SCR fatigue and VIV screening",
        inputs,
        {"life_cycles": life, "damage": damage, "screening": screening},
        COMMON_CAVEATS
        + " Soil and VIV empirical coefficients are inherited from the library; "
        "the cited papers have not been independently qualified here. Low-KC damage is "
        "NOT_EVALUATED. S-N intercept units are MPa**m cycles.",
        [
            scr_fatigue.scr_sn_fatigue_life,
            scr_fatigue.fatigue_damage_tdz,
            scr_fatigue.brooks_viv_screening,
        ],
        plot_html(
            curve(
                inputs["amplitudes_MPa"],
                life,
                "Synthetic S-N life",
                "Amplitude (MPa)",
                "Life (cycles)",
            ),
            "sn",
        )
        + table(screening),
        "N=A/(2 amplitude)^m; D=sum(n/N) times implemented soil factor. "
        "Source: repository scr_fatigue.py; its VIV screening cites Brooks (1987) and soil model cites OTC (2001). "
        "PASS means no risk flagged by that implementation; empirical acceptance remains NOT_EVALUATED.",
    )


def units_page():
    # Synthetic exact SI prefix example; conversion factors come from the registry.
    length = TrackedQuantity(2.0, "m", source="Synthetic rectangle length")
    width = TrackedQuantity(500.0, "mm", source="Synthetic rectangle width")
    audit = CalculationAuditLog()
    audit.add_input("length", length)
    audit.add_input("width", width)
    converted = width.to("m")
    audit.add_step("Convert width from mm to m using the unit registry")
    area = length * converted
    audit.add_step("Multiply length by converted width; retain both provenance chains")
    audit.add_output("area", area)
    result = audit.to_dict()
    return Page(
        "Traceable units and quantities",
        {"length": length.to_dict(), "width": width.to_dict()},
        result,
        COMMON_CAVEATS
        + " This is the provenance showcase. Audit timestamps are actual operation times, "
        "even when the page header uses SOURCE_DATE_EPOCH; complete HTML is not byte-reproducible.",
        [TrackedQuantity.to, TrackedQuantity.__mul__, CalculationAuditLog.to_dict],
        table(
            [
                {"role": role, "name": name, **quantity}
                for role in ("inputs", "outputs")
                for name, quantity in result[role].items()
            ]
        )
        + table(result["steps"]),
        "Rectangle area = length × width. SI prefix conversion is delegated to the library registry. "
        "The audit log records creation, conversion, multiplication and output units without stripping provenance.",
    )


def workflow_page():
    input_path = resolve_example_path(resolve_registry_row("visualization")["input"])
    envelope = run_workflow(workflow_id="visualization")
    if envelope.status != "ok" or not envelope.result.get("outputs"):
        # Do not publish arbitrary exception messages, which can contain local paths.
        raise ValueError("Gallery workflow failed or emitted no outputs")
    result = envelope.to_dict()
    return Page(
        "YAML workflow and result envelope",
        {
            "workflow_id": "visualization",
            "yaml": input_path.read_text(encoding="utf-8"),
        },
        result,
        COMMON_CAVEATS + " reproducible: null means not checked. "
        "The workflow executes in a temporary directory; only file metadata survives. PNG bytes are not embedded. "
        "Hashes describe this build and can vary with rendering dependencies.",
        [run_workflow],
        table(envelope.result["outputs"]),
        "run_workflow resolves docs/registry/workflows.yaml and executes the registered synthetic visualization YAML. "
        "The real ResultEnvelope provenance and determinism fields are shown verbatim. "
        "Use the in-process API for this example; the CLI writes outputs next to its input.",
    )


def riser_page():
    # Synthetic required-input Strouhal number, not the module's default correlation.
    inputs = {"U": 2.0, "D": 0.5, "St": 0.25, "f_n": 1.0}
    result = {
        "frequency_Hz": riser_viv.strouhal_frequency(
            inputs["U"], inputs["D"], inputs["St"]
        ),
        "reduced_velocity": riser_viv.reduced_velocity(
            inputs["U"], inputs["f_n"], inputs["D"]
        ),
    }
    return Page(
        "Riser VIV dimensionless relationships",
        inputs,
        result,
        COMMON_CAVEATS
        + " No empirical lock-in, drag, amplitude or fatigue correlation is qualified.",
        [riser_viv.strouhal_frequency, riser_viv.reduced_velocity],
        method="f=St U/D; Vr=U/(fn D). Source: repository riser_viv.py, citing Strouhal (1878). "
        "St is supplied explicitly as a synthetic input; it is not a recommended coefficient.",
    )


def wellhead_page():
    # Synthetic S-N curve and loading, not material or operating data.
    inputs = {"delta_sigma_psi": 20.0, "A": 8000.0, "m": 2.0, "cycles_per_year": 2.0}
    cycles = wellhead_fatigue.sn_cycles_to_failure(
        inputs["delta_sigma_psi"], inputs["A"], inputs["m"]
    )
    return Page(
        "Wellhead fatigue arithmetic",
        inputs,
        {
            "life_cycles": cycles,
            "life_years": wellhead_fatigue.fatigue_life_years(
                cycles, inputs["cycles_per_year"]
            ),
            "damage": wellhead_fatigue.annual_fatigue_damage(
                inputs["cycles_per_year"], cycles
            ),
        },
        COMMON_CAVEATS
        + " Synthetic intercept units are psi**m cycles; no service life is predicted.",
        [
            wellhead_fatigue.sn_cycles_to_failure,
            wellhead_fatigue.fatigue_life_years,
            wellhead_fatigue.annual_fatigue_damage,
        ],
        method="N=A/(stress range)^m; life=N/(annual cycles); damage=annual cycles/N. "
        "Source: repository wellhead_fatigue.py, S-N relationship citing OTC (1989).",
    )


def cost_page():
    # Synthetic dimensionless currency/output units and rate, not economic forecasts.
    inputs = {
        "costs": [100.0, 110.0],
        "outputs": [10.0, 11.0],
        "discount_rate": 0.1,
        "rates": [0.0, 0.1, 0.2],
    }
    sensitivity = [
        {"rate": r, "npv": lifecycle_cost.net_present_value(inputs["costs"], r)}
        for r in inputs["rates"]
    ]
    return Page(
        "Lifecycle cost sensitivity",
        inputs,
        {
            "npv": lifecycle_cost.net_present_value(
                inputs["costs"], inputs["discount_rate"]
            ),
            "levelized": lifecycle_cost.levelized_cost(
                inputs["costs"], inputs["outputs"], inputs["discount_rate"]
            ),
            "sensitivity": sensitivity,
        },
        COMMON_CAVEATS
        + " Costs are positive, year-zero-first, in arbitrary currency units. "
        "No inflation, tax, uncertainty or investment recommendation is included.",
        [lifecycle_cost.net_present_value, lifecycle_cost.levelized_cost],
        plot_html(
            curve(
                inputs["rates"],
                [r["npv"] for r in sensitivity],
                "Synthetic cost sensitivity",
                "Discount rate",
                "Present cost (currency units)",
            ),
            "cost",
        ),
        "NPV=sum(Ct/(1+r)^t); levelized cost=NPV(cost)/NPV(output). "
        "Source designation: ISO 15663-2:2001 (BS EN ISO 15663-2:2001). "
        "The library arithmetic is demonstrated; no standard-derived coefficient is used.",
    )


def png_html(figure, alt):
    output = BytesIO()
    figure.savefig(output, format="png")
    return f'<img alt="{escape(alt, quote=True)}" src="data:image/png;base64,{base64.b64encode(output.getvalue()).decode()}">'


def templates_page():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    from assetutilities.common.visualization.visualization_polar import (
        VisualizationPolar,
    )
    from assetutilities.common.visualization.visualization_templates_matplotlib import (
        VisualizationTemplates,
    )
    from assetutilities.common.visualization.visualization_xy import VisualizationXY

    cfg = VisualizationTemplates().get_xy_line_input()
    # Only configuration is reused; replace every dataset and descriptive label.
    # Synthetic plotting coordinates carry no engineering acceptance meaning.
    cfg["data"] = {
        "type": "input",
        "groups": [
            {"x": [[0, 90, 180, 270]], "y": [[1, 2, 3, 2]], "label": "Synthetic series"}
        ],
    }
    cfg["settings"].update(
        title="Synthetic directional series",
        xlabel="Direction (degrees)",
        ylabel="Arbitrary response",
        legend={"flag": True, "label": ["Synthetic series"]},
    )
    echoed = copy.deepcopy(dict(cfg))
    xy = VisualizationXY()
    data, cfg = xy.get_data_df_and_plot_properties(cfg)
    fig = xy.get_xy_plot_plotly(data, cfg["settings"], cfg)
    body = plot_html(fig, "template-xy")
    for mode in ("line", "scatter"):
        cfg["settings"]["mode"] = mode
        props = xy.get_xy_plot_matplotlib(data, cfg["settings"], cfg, None)
        body += png_html(props["fig"], f"Library XY {mode} template on synthetic data")
        plt.close(props["fig"])
    polar = VisualizationPolar()
    polar_input = {
        "data": {
            "groups": [
                {
                    "theta": [[0, 90, 180, 270]],
                    "r": [[1, 2, 3, 2]],
                    "label": "Synthetic series",
                }
            ]
        }
    }
    echoed["polar"] = copy.deepcopy(polar_input)
    polar_data, _ = polar.get_polar_mapped_data_dict_from_input(polar_input)
    settings = {
        "type": "polar",
        "traces": 1,
        "alpha": [1],
        "color": ["blue"],
        "linestyle": ["-"],
        "legend": {"flag": True, "label": ["Synthetic series"]},
    }
    props = polar.get_polar_plot_matplotlib(pd.DataFrame(polar_data), settings, {})
    body += png_html(props["fig"], "Library polar template on synthetic data")
    plt.close(props["fig"])
    return Page(
        "Visualization template gallery",
        echoed,
        {
            "templates": [
                "Plotly XY",
                "matplotlib line",
                "matplotlib scatter",
                "matplotlib polar",
            ]
        },
        COMMON_CAVEATS + " Curves are illustrative, not measured operability limits. "
        "Geographic plots and external map assets are not supported in this offline gallery.",
        [
            VisualizationTemplates.get_xy_line_input,
            VisualizationXY.get_xy_plot_plotly,
            VisualizationXY.get_xy_plot_matplotlib,
            VisualizationPolar.get_polar_plot_matplotlib,
        ],
        body,
        "The library loads its XY YAML template and renders new synthetic data. "
        "Matplotlib figures are embedded PNG data URIs; Plotly JavaScript is inline. "
        "No prebuilt reports or tracked result images are read.",
    )


def build(out, no_caveats=False):
    evidence = provenance()
    if no_caveats:
        render_page(
            Page("Invalid", {"synthetic": True}, {}, "", [run_workflow]), evidence
        )
    builders = {
        "pipeline_dnv": pipeline_page,
        "scr_fatigue": fatigue_page,
        "units_traceability": units_page,
        "workflow_envelope": workflow_page,
        "visualization_templates": templates_page,
        "riser_viv": riser_page,
        "wellhead_fatigue": wellhead_page,
        "lifecycle_cost": cost_page,
    }
    pages = {name: builder() for name, builder in builders.items()}
    links = (
        "<ul>"
        + "".join(
            f"<li><a href='{name}.html'>{escape(page.title)}</a></li>"
            for name, page in pages.items()
        )
        + "</ul>"
    )
    pages["index"] = Page(
        "Library demonstration gallery",
        {"data_basis": "synthetic inputs only"},
        {"pages": list(pages)},
        COMMON_CAVEATS,
        [run_workflow],
        links,
        "Library demonstration on synthetic inputs. Follow each page for its input echo, "
        "library implementation, method, results and limitations.",
    )
    # Validate the entire build before writing any page; failure publishes no partial set.
    rendered = {name: render_page(page, evidence) for name, page in pages.items()}
    out.mkdir(parents=True, exist_ok=True)
    for name, html in rendered.items():
        with (out / f"{name}.html").open("w", encoding="utf-8", newline="\n") as output:
            output.write(html)
    print(f"Built {len(rendered)} self-contained gallery pages")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "site/gallery")
    parser.add_argument(
        "--_selftest-no-caveats", action="store_true", help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    # Isolate all child Git consumers, including workflow-envelope provenance.
    for key in GIT_BINDINGS:
        os.environ.pop(key, None)
    # Keep plotting caches outside source when the caller supplies a temp root.
    if "MPLCONFIGDIR" not in os.environ and os.environ.get("TMPDIR"):
        os.environ["MPLCONFIGDIR"] = str(Path(os.environ["TMPDIR"]) / "matplotlib")
    build(args.out, args._selftest_no_caveats)


if __name__ == "__main__":
    main()
