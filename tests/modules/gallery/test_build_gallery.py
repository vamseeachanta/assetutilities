"""Independent arithmetic and public-output contracts for synthetic demos."""

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]
SPEC = importlib.util.spec_from_file_location(
    "build_gallery", ROOT / "scripts/build_gallery.py"
)


def api():
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    return module


def test_hand_calculated_answers():
    """Synthetic definitions, not material properties or acceptance limits.

    S-N: range=2*5=10 MPa; A=1000000 MPa^3 cycles; m=3.
    N=1000000/10^3=1000 cycles. Same synthetic curve at 10 psi
    gives 1000 cycles when A is expressed in psi^3 cycles.
    Annual exposure=100 cycles/year, so life=1000/100=10 years.
    Reduced velocity=2 m/s / (2 Hz * 0.5 m)=2 (dimensionless).
    Present cost=100 + 110/(1+0.1)=200 currency units.
    Levelized cost=200/(10+11/1.1)=10 currency/output units.
    SI prefix: 1000 mm=1 m (NIST SP 811, 2008, section 4.3 table 5).
    """
    results = api().calculation_examples()
    assert results["scr_cycles"] == pytest.approx(1000)
    assert results["wellhead_cycles"] == pytest.approx(1000)
    assert results["wellhead_years"] == pytest.approx(10)
    assert results["reduced_velocity"] == pytest.approx(2)
    assert results["npv"] == pytest.approx(200)
    assert results["levelized_cost"] == pytest.approx(10)
    assert results["metres"] == pytest.approx(1)


@pytest.mark.parametrize(
    "html",
    [
        '<script src="https://example.invalid/a.js"></script>',
        '<SCRIPT SRC="//example.invalid/a.js"></SCRIPT>',
        '<link href="https:&#47;&#47;example.invalid/a.css" rel="stylesheet">',
        '<img src="https://example.invalid/p.png">',
        '<iframe src="https://example.invalid/"></iframe>',
        "<style>body{background:url(https://example.invalid/a)}</style>",
        '<base href="references/">',
        "<base>",
        '<META HTTP-EQUIV=" Refresh " content="0;url=next.html">',
        '<meta http-equiv="refresh">',
        '<div style="background:URL(image.png)"></div>',
        '<div style="@IMPORT &quot;theme.css&quot;"></div>',
        '<style>@IMPORT "theme.css";</style>',
        '<object data="document.html"></object>',
        '<embed src="document.html">',
        '<source srcset="small.png 1x, large.png 2x">',
        '<video poster="poster.png"></video>',
        '<audio src="audio.ogg"></audio>',
        '<svg><script xlink:href="script.js"/></svg>',
        '<img src="image.png" src="data:image/png;base64,AA==">',
        '<div style="background:url(image.png)" style="color:navy"></div>',
        '<meta http-equiv="refresh" http-equiv="none" content="0;url=next.html">',
        '<svg><use href="resource.svg#shape" href="#shape"/></svg>',
        '<div style="background:u\\72l(image.png)"></div>',
        '<div style="background:u/**/rl(image.png)"></div>',
        '<style>@im\\70ort "theme.css";</style>',
        "<style>body{background:u/**/rl(image.png)}</style>",
    ],
)
def test_external_resources_fail_closed(html):
    with pytest.raises(ValueError, match="resource"):
        api().check_self_contained(html)


@pytest.mark.parametrize(
    "tag",
    [
        "image",
        "use",
        "feImage",
        "linearGradient",
        "radialGradient",
        "pattern",
        "filter",
        "textPath",
        "mpath",
        "tref",
        "altGlyph",
        "cursor",
        "font-face-uri",
        "glyphRef",
        "animate",
        "animateMotion",
        "animateTransform",
        "set",
    ],
)
@pytest.mark.parametrize("attribute", ["href", "xlink:href"])
def test_svg_external_resources_fail_closed(tag, attribute):
    with pytest.raises(ValueError, match="resource"):
        api().check_self_contained(
            f'<svg><{tag} {attribute}="resource.svg#shape"/></svg>'
        )


@pytest.mark.parametrize(
    "html",
    [
        '<svg><USE HREF="resource.svg&#35;shape"/></svg>',
        '<svg><image XLINK:HREF="image.png"/></svg>',
    ],
)
def test_svg_resource_attribute_normalization(html):
    with pytest.raises(ValueError, match="resource"):
        api().check_self_contained(html)


@pytest.mark.parametrize(
    "html",
    [
        '<style>body{color:navy}</style><div style="color:navy">Text</div>',
        '<script>const mapUrl="unused.json";Plotly.newPlot("chart",[]);</script>',
        '<img src="data:image/png;base64,aGVsbG8=">',
        '<nav><a href="index.html">Gallery</a><a href="#answer">Answer</a></nav>',
        '<svg><use href="#shape"/><image xlink:href="#image"/></svg>',
        '<svg><a href="references.html">References</a></svg>',
        "<div style>Text</div><meta http-equiv>",
    ],
)
def test_self_contained_resources_and_navigation_allowed(html):
    api().check_self_contained(html)


@pytest.mark.parametrize(
    "filename",
    [
        "scripts/build_gallery.py",
        "src/assetutilities/common/reportgen/citations.py",
        "src/assetutilities/workflow_api/runner.py",
        "tests/modules/gallery/test_build_gallery.py",
        "tests/modules/reportgen/test_citation_binding.py",
        "tests/workflow_api/test_runner.py",
    ],
)
def test_text_io_has_explicit_utf8_and_lf(filename):
    """Default encodings and platform newlines must not alter gallery bytes."""
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", getattr(node.func, "id", ""))
        keywords = {item.arg: item.value for item in node.keywords}
        if name in ("read_text", "write_text", "open"):
            mode = keywords.get("mode", node.args[1] if len(node.args) > 1 else None)
            mode = getattr(mode, "value", "r")
            if name == "open" and "b" in mode:
                continue
            encoding = getattr(keywords.get("encoding"), "value", None)
            if encoding != "utf-8":
                violations.append(f"{node.lineno}: {name} requires UTF-8")
            if name == "write_text" or (
                name == "open" and any(c in mode for c in "wax")
            ):
                if getattr(keywords.get("newline"), "value", None) != "\n":
                    violations.append(f"{node.lineno}: {name} requires LF")
        if name == "run" and getattr(keywords.get("text"), "value", False):
            if getattr(keywords.get("encoding"), "value", None) != "utf-8":
                violations.append(f"{node.lineno}: subprocess requires UTF-8")
    assert not violations, "\n".join(violations)


def test_missing_caveats_rejected():
    with pytest.raises(ValueError, match="Caveats"):
        api().render_page("Example", {}, "answer", [], "", {})


def test_failed_workflow_rejected():
    from assetutilities.workflow_api.envelope import ResultEnvelope

    bad = ResultEnvelope(
        workflow_id="example", status="error", result={}, provenance={}, determinism={}
    )
    with pytest.raises(ValueError, match="workflow"):
        api().workflow_content(bad)


def test_gallery_build(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/build_gallery.py"),
            "--out",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode == 0, result.stderr[-3000:]
    expected = {
        "index",
        "pipeline_dnv",
        "scr_fatigue",
        "riser_viv",
        "wellhead_fatigue",
        "lifecycle_cost",
        "units_traceability",
        "visualization",
        "workflow_envelope",
    }
    assert {p.stem for p in tmp_path.glob("*.html")} == expected
    for page in tmp_path.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        for marker in ("Provenance", "Caveats", "Input echo", "Code references"):
            assert marker in text
        api().check_self_contained(text)
        assert str(tmp_path) not in text
    assert "NOT_EVALUATED" in (tmp_path / "pipeline_dnv.html").read_text(
        encoding="utf-8"
    )
    assert "NOT_EVALUATED" in (tmp_path / "scr_fatigue.html").read_text(
        encoding="utf-8"
    )
    assert "Plotly.newPlot" in (tmp_path / "visualization.html").read_text(
        encoding="utf-8"
    )
    visualization = (tmp_path / "visualization.html").read_text(encoding="utf-8")
    assert "synthetic-polar" in visualization
    assert visualization.count('src="data:image/png;base64,') == 2
    envelope = json.loads((tmp_path / "workflow.json").read_text(encoding="utf-8"))
    assert envelope["status"] == "ok"
    assert envelope["result"]["outputs"]
    assert envelope["determinism"]["reproducible"] is None
    assert "not checked" in (tmp_path / "workflow_envelope.html").read_text(
        encoding="utf-8"
    )


def test_ci_builds_and_selects_gallery():
    import yaml

    for filename in ("docs.yml", "pages.yml"):
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows" / filename).read_text(encoding="utf-8")
        )
        steps = next(iter(workflow["jobs"].values()))["steps"]
        assert any("scripts/build_gallery.py" in s.get("run", "") for s in steps)
        events = workflow.get("on", workflow.get(True))
        for event in ("push", "pull_request"):
            if event in events:
                assert "scripts/build_gallery.py" in events[event]["paths"]
    selector = subprocess.run(
        [sys.executable, "scripts/ci/select_test_targets.py", "--files-from", "-"],
        input="scripts/build_gallery.py\ntests/modules/gallery/test_build_gallery.py\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=ROOT,
        check=True,
    )
    assert "tests/modules/gallery" in selector.stdout


def test_documentation_workflows_limit_token_permissions():
    import yaml

    workflows = ROOT / ".github/workflows"
    docs = yaml.safe_load((workflows / "docs.yml").read_text(encoding="utf-8"))
    pages = yaml.safe_load((workflows / "pages.yml").read_text(encoding="utf-8"))
    assert docs["permissions"] == {"contents": "read"}
    assert pages["permissions"] == {"contents": "read"}
    assert "permissions" not in pages["jobs"]["build"]
    assert pages["jobs"]["deploy"]["permissions"] == {
        "pages": "write",
        "id-token": "write",
    }
