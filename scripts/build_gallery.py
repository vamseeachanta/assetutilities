"""Build an allowlisted library gallery from synthetic calculations and outputs.

No directory of reports is copied. Only the examples below are published.
Unqualified standard coefficients and empirical acceptance criteria are omitted.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path

from assetutilities.calculations.lifecycle_cost import levelized_cost, net_present_value
from assetutilities.calculations.riser_viv import reduced_velocity
from assetutilities.calculations.scr_fatigue import scr_sn_fatigue_life
from assetutilities.calculations.wellhead_fatigue import (
    fatigue_life_years,
    sn_cycles_to_failure,
)
from assetutilities.units import CalculationAuditLog, TrackedQuantity
from assetutilities.workflow_api.envelope import (
    input_hash,
    make_provenance,
    utc_now_iso,
)

ROOT = Path(__file__).resolve().parents[1]
SI_SOURCE = (
    "https://www.nist.gov/pml/special-publication-811/"
    "nist-guide-si-chapter-4-two-classes-si-units-and-si-prefixes"
)
# Synthetic inputs are definitions of this example, not published properties.
# Independent arithmetic is written out in test_build_gallery.py.
INPUTS = {
    "sn": {"amplitude_MPa": 5, "A_MPa_power_m_cycles": 1000000, "m": 3},
    "wellhead": {
        "range_psi": 10,
        "A_psi_power_m_cycles": 1000000,
        "m": 3,
        "cycles_per_year": 100,
    },
    "viv": {"velocity_m_per_s": 2, "frequency_Hz": 2, "diameter_m": 0.5},
    "cost": {"costs": [100, 110], "outputs": [10, 11], "rate": 0.1},
    "units": {"length_mm": 1000},
}


def calculation_examples():
    """Run only arithmetic with explicit, synthetic caller parameters."""
    sn, wh, viv, cost = (INPUTS[k] for k in ("sn", "wellhead", "viv", "cost"))
    endurance = sn_cycles_to_failure(
        wh["range_psi"], wh["A_psi_power_m_cycles"], wh["m"]
    )
    length = TrackedQuantity(
        INPUTS["units"]["length_mm"], "mm", source="synthetic input"
    )
    return {
        "scr_cycles": scr_sn_fatigue_life(
            sn["amplitude_MPa"], sn["A_MPa_power_m_cycles"], sn["m"]
        ),
        "wellhead_cycles": endurance,
        "wellhead_years": fatigue_life_years(endurance, wh["cycles_per_year"]),
        "reduced_velocity": reduced_velocity(
            viv["velocity_m_per_s"], viv["frequency_Hz"], viv["diameter_m"]
        ),
        "npv": net_present_value(cost["costs"], cost["rate"]),
        "levelized_cost": levelized_cost(cost["costs"], cost["outputs"], cost["rate"]),
        # NIST SP 811 (2008), section 4.3, table 5: milli is the SI prefix.
        "metres": float(length.to("m").magnitude),
    }


def json_block(value):
    return (
        "<pre>"
        + escape(json.dumps(value, indent=2, default=str, allow_nan=False))
        + "</pre>"
    )


def table(headers, rows):
    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


_CSS_RESOURCE = re.compile(r"url\s*\(|@import|\\|/\*", re.I)


class _ResourceCheck(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == "base" or (
            tag == "meta"
            and any(
                key == "http-equiv" and (value or "").strip().lower() == "refresh"
                for key, value in attrs
            )
        ):
            raise ValueError("Redirecting resource in gallery page")
        if any(
            key == "style" and _CSS_RESOURCE.search(value or "") for key, value in attrs
        ):
            raise ValueError("External CSS resource in gallery page")
        if tag in (
            "image",
            "use",
            "feimage",
            "lineargradient",
            "radialgradient",
            "pattern",
            "filter",
            "textpath",
            "mpath",
            "tref",
            "altglyph",
            "cursor",
            "font-face-uri",
            "glyphref",
            "animate",
            "animatemotion",
            "animatetransform",
            "set",
        ):
            for key, value in attrs:
                if (
                    key in ("href", "xlink:href")
                    and value
                    and not value.strip().startswith("#")
                ):
                    raise ValueError("External SVG resource in gallery page")
        if tag in (
            "script",
            "link",
            "img",
            "iframe",
            "object",
            "embed",
            "source",
            "video",
            "audio",
        ):
            for key, value in attrs:
                if (
                    key in ("src", "href", "xlink:href", "data", "srcset", "poster")
                    and value
                    and not (
                        tag == "img"
                        and key == "src"
                        and value.startswith("data:image/png;base64,")
                    )
                ):
                    raise ValueError("External resource in gallery page")


def check_self_contained(html):
    """Check the gallery's supported resource syntax before writing output.

    Inline Plotly contains unused geo/map URL strings; those are not resource
    elements. The gallery emits only Cartesian traces and disables its toolbar.
    CSS escapes and comments are excluded from the gallery's supported styles.
    """
    _ResourceCheck().feed(html)
    for css in re.findall(r"<style[^>]*>(.*?)</style>", html, re.I | re.S):
        if _CSS_RESOURCE.search(css):
            raise ValueError("External CSS resource in gallery page")


def render_page(title, inputs, content, references, caveats, provenance):
    if not caveats.strip():
        raise ValueError("Caveats are required")
    if not references:
        raise ValueError("Code references are required")
    provenance = {**provenance, "input_hash": input_hash(inputs)}
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)}</title>"
        "<style>body{font:1em sans-serif;max-width:75em;margin:auto;padding:1.5em}"
        "table{border-collapse:collapse}td,th{border:1px solid #777;padding:.5em}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere}img{max-width:100%}</style>"
        '<nav><a href="index.html">Gallery</a> · <a href="../index.html">API reference</a></nav>'
        f"<h1>{escape(title)}</h1><p>Library demonstration on synthetic inputs.</p>"
        f"<h2>Input echo</h2>{json_block(inputs)}{content}"
        f"<h2>Provenance</h2>{json_block(provenance)}"
        f"<h2>Caveats</h2><p>{escape(caveats)}</p>"
        "<h2>Code references</h2><ul>"
        + "".join(f"<li><code>{escape(r)}</code></li>" for r in references)
        + "</ul></html>"
    )
    check_self_contained(html)
    return html


def workflow_content(envelope):
    if envelope.status != "ok":
        raise ValueError("Demonstration workflow failed; no gallery published")
    if not envelope.result.get("outputs"):
        raise ValueError("Demonstration workflow produced no output")
    return (
        "<p>The YAML workflow ran in a temporary directory. Only file metadata "
        "is retained by the workflow API; the image bytes are not retained. "
        "reproducible: null means not checked.</p>"
        + json_block(envelope.provenance)
        + json_block(envelope.determinism)
        + table(
            ["basename", "sha256", "size"],
            [
                [row[k] for k in ("basename", "sha256", "size")]
                for row in envelope.result["outputs"]
            ],
        )
    )


def visualization_content():
    """Use the library XY template with the same synthetic data in both engines."""
    import matplotlib.pyplot as plt
    import pandas as pd

    from assetutilities.common.visualization.visualization_templates_matplotlib import (
        VisualizationTemplates,
    )
    from assetutilities.common.visualization.visualization_xy import VisualizationXY
    from assetutilities.common.visualization.visualization_polar import (
        VisualizationPolar,
    )

    cfg = VisualizationTemplates().get_xy_line_input()
    # These are display choices and synthetic samples, not engineering criteria.
    cfg["settings"].update(
        title="Synthetic XY template",
        label="Synthetic series",
        xlabel="Input",
        ylabel="Output",
        color=["blue"],
        alpha=[1],
        linestyle=["-"],
        markerprops=[{"marker": "circle", "markersize": 5}],
        legend={"flag": False, "label": ["Synthetic"], "prop": {"size": 8}},
    )
    data = {"x_0": [0, 1, 2], "y_0": [0, 1, 4]}
    df = pd.DataFrame(data)
    engine = VisualizationXY()
    fig = engine.get_xy_plot_plotly(df, cfg["settings"], cfg)
    plotly = fig.to_html(
        full_html=False,
        include_plotlyjs=True,
        div_id="synthetic-xy",
        config={"displayModeBar": False, "responsive": True},
    )
    properties = engine.get_xy_plot_matplotlib(df, cfg["settings"], cfg, None)
    image = io.BytesIO()
    try:
        properties["fig"].savefig(image, format="png")
    finally:
        plt.close(properties["fig"])
    encoded = base64.b64encode(image.getvalue()).decode("ascii")
    # Synthetic radii and angles; angle conversion is a mathematical definition.
    polar_inputs = {"theta_deg": [0, 90, 180, 270], "radius": [1, 2, 1, 2]}
    polar_df = pd.DataFrame(
        {
            "theta_0": [math.radians(value) for value in polar_inputs["theta_deg"]],
            "r_0": polar_inputs["radius"],
        }
    )
    cfg["settings"].update(type="polar", traces=1, title="Synthetic polar template")
    properties = VisualizationPolar().get_polar_plot_matplotlib(
        polar_df, cfg["settings"], cfg
    )
    image = io.BytesIO()
    try:
        properties["fig"].savefig(image, format="png")
    finally:
        plt.close(properties["fig"])
    polar_png = base64.b64encode(image.getvalue()).decode("ascii")
    return (
        {"xy": data, "polar": polar_inputs},
        plotly
        + f'<img alt="Synthetic XY template rendered with matplotlib" src="data:image/png;base64,{encoded}">'
        + '<h2 id="synthetic-polar">Polar template</h2>'
        + f'<img alt="Synthetic polar template rendered with matplotlib" src="data:image/png;base64,{polar_png}">',
    )


def build(out):
    import yaml

    from assetutilities.workflow_api import run_workflow

    values = calculation_examples()
    audit = CalculationAuditLog()
    length = TrackedQuantity(
        INPUTS["units"]["length_mm"], "mm", source="synthetic input"
    )
    audit.add_input("length", length)
    audit.add_output("length", length.to("m"))
    audit.add_step(
        "Convert millimetres to metres using NIST SP 811 section 4.3 table 5"
    )
    envelope = run_workflow(workflow_id="visualization")
    workflow = workflow_content(envelope)
    chart_inputs, chart = visualization_content()
    provenance = make_provenance(None)
    provenance["generated_utc"] = utc_now_iso()
    provenance["basis"] = (
        "synthetic inputs; arithmetic demonstration; criteria not qualified"
    )
    generic = "Synthetic example, not a design assessment. No standard compliance or empirical calibration is established."
    code = "src/assetutilities/"
    pages = {
        "pipeline_dnv": (
            "Pipeline calculation coverage",
            {},
            table(
                ["Check", "Status", "Required evidence"],
                [
                    [name, "NOT_EVALUATED", reason]
                    for name, reason in (
                        (
                            "Pressure containment",
                            "Qualified edition, geometry, material and resistance factors",
                        ),
                        (
                            "Combined loading",
                            "Reconcile documented and implemented resistance factors",
                        ),
                        (
                            "Buckle arrest",
                            "Resolve output dimension before publishing a pressure",
                        ),
                    )
                ],
            ),
            [
                code + "calculations/pipeline_dnv.py",
                code + "calculations/docs/agent-pack.md, sections 3 and 10",
            ],
            "DNV-OS-F101 (2013), section 5: identification only. Licensed clauses are not reproduced. "
            + generic,
        ),
        "scr_fatigue": (
            "SCR fatigue arithmetic",
            INPUTS["sn"],
            table(
                ["Method", "Answer", "Status"],
                [
                    [
                        "N = A / (2 amplitude)^m",
                        f"{values['scr_cycles']:.1f} cycles",
                        "ARITHMETIC_ONLY",
                    ],
                    [
                        "TDZ soil correction and empirical VIV screening",
                        "Source coefficients required",
                        "NOT_EVALUATED",
                    ],
                ],
            ),
            [code + "calculations/scr_fatigue.py:scr_sn_fatigue_life"],
            generic,
        ),
        "riser_viv": (
            "Riser VIV arithmetic",
            INPUTS["viv"],
            table(
                ["Method", "Answer", "Status"],
                [
                    [
                        "Vr = U / (frequency diameter)",
                        f"{values['reduced_velocity']:.1f}",
                        "ARITHMETIC_ONLY",
                    ],
                    [
                        "Lock-in and amplitude assessment",
                        "Qualified criterion required",
                        "NOT_EVALUATED",
                    ],
                ],
            ),
            [code + "calculations/riser_viv.py:reduced_velocity"],
            generic,
        ),
        "wellhead_fatigue": (
            "Wellhead fatigue arithmetic",
            INPUTS["wellhead"],
            table(
                ["Method", "Answer"],
                [
                    ["N = A / range^m", f"{values['wellhead_cycles']:.1f} cycles"],
                    [
                        "Life = N / annual cycles",
                        f"{values['wellhead_years']:.1f} years",
                    ],
                ],
            ),
            [
                code
                + "calculations/wellhead_fatigue.py:sn_cycles_to_failure, fatigue_life_years"
            ],
            generic,
        ),
        "lifecycle_cost": (
            "Lifecycle cost arithmetic",
            INPUTS["cost"],
            table(
                ["Method", "Answer"],
                [
                    [
                        "Present cost = sum(cost[t] / (1 + rate)^t)",
                        f"{values['npv']:.1f} currency units",
                    ],
                    [
                        "Levelized cost = present cost / discounted output",
                        f"{values['levelized_cost']:.1f} currency/output units",
                    ],
                ],
            ),
            [code + "calculations/lifecycle_cost.py:net_present_value, levelized_cost"],
            generic,
        ),
        "units_traceability": (
            "Traceable units",
            INPUTS["units"],
            f'<p>SI prefixes: <a href="{SI_SOURCE}">NIST SP 811, section 4.3, table 5</a>. '
            f"Converted length: {values['metres']:.1f} m.</p>"
            + json_block(audit.to_dict()),
            [
                code + "units/quantity.py:TrackedQuantity",
                code + "units/traceability.py:CalculationAuditLog",
            ],
            generic,
        ),
        "visualization": (
            "Visualization templates",
            chart_inputs,
            chart,
            [
                code
                + "common/visualization/visualization_xy.py:get_xy_plot_plotly, get_xy_plot_matplotlib",
                code
                + "common/visualization/visualization_polar.py:get_polar_plot_matplotlib",
            ],
            "XY and polar template output only; no operability limits, measured data or map resources. "
            + generic,
        ),
        "workflow_envelope": (
            "YAML workflow evidence",
            yaml.safe_load(
                (ROOT / "examples/workflows/visualization/input.yml").read_text(
                    encoding="utf-8"
                )
            ),
            workflow,
            [
                code + "workflow_api/runner.py:run_workflow",
                "examples/workflows/visualization/input.yml",
            ],
            "The example chart inputs are synthetic; the envelope does not certify engineering adequacy. "
            + generic,
        ),
    }
    rendered = {}
    for slug, (title, inputs, content, refs, caveats) in pages.items():
        rendered[slug] = render_page(title, inputs, content, refs, caveats, provenance)
    links = (
        "<ul>"
        + "".join(
            f'<li><a href="{slug}.html">{escape(page[0])}</a></li>'
            for slug, page in pages.items()
        )
        + "</ul>"
    )
    rendered["index"] = render_page(
        "Library gallery",
        INPUTS,
        links,
        ["scripts/build_gallery.py", "tests/modules/gallery/test_build_gallery.py"],
        generic,
        provenance,
    )
    # Validate everything before writing; no partial successful gallery on failure.
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for slug, html in rendered.items():
        (out / f"{slug}.html").write_text(html, encoding="utf-8", newline="\n")
    (out / "workflow.json").write_text(
        json.dumps(envelope.to_dict(), indent=2), encoding="utf-8", newline="\n"
    )
    (out / "answers.json").write_text(
        json.dumps(values, indent=2), encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("site/gallery"))
    build(parser.parse_args().out)
