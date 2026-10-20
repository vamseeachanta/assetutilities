"""Gallery contracts and independent arithmetic on synthetic examples."""

import importlib.util
import json
import math
import os
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/build_gallery.py"
PAGES = {
    "index",
    "pipeline_dnv",
    "scr_fatigue",
    "units_traceability",
    "workflow_envelope",
    "visualization_templates",
    "riser_viv",
    "wellhead_fatigue",
    "lifecycle_cost",
}


@pytest.fixture(scope="module")
def gallery():
    spec = importlib.util.spec_from_file_location("gallery", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Results(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.active = False
        self.value = ""
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.active = dict(attrs).get("id") == "results"

    def handle_endtag(self, tag):
        if tag == "script":
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.value += data


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("gallery")
    before = subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT)
    env = dict(os.environ, SOURCE_DATE_EPOCH="0", GITHUB_SHA="a" * 40)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out)],
        cwd=out,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    assert subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT) == before
    return out


def payload(out, name):
    return json.loads(Results((out / f"{name}.html").read_text()).value)


def test_complete_self_contained_gallery(built, gallery):
    assert {p.stem for p in built.glob("*.html")} == PAGES
    for page in built.glob("*.html"):
        html = page.read_text()
        for marker in ("Provenance", "Caveats", "Input echo", "Code references"):
            assert marker in html, (page.name, marker)
        assert "1970-01-01" in html
        assert "a" * 40 in html
        gallery.check_self_contained(html)
    for name in ("pipeline_dnv", "scr_fatigue"):
        html = (built / f"{name}.html").read_text()
        assert "screening_status" in html
        assert "PASS" in html and "FAIL" in html
        assert "NOT_EVALUATED" in html


@pytest.mark.parametrize(
    "html",
    [
        '<script SRC="https://example.org/a.js"></script>',
        "<link href='//example.org/a.css' rel='stylesheet'>",
        '<img src="https://example.org/a.png">',
        '<script src="local.js"></script>',
        '<iframe src="https://example.org"></iframe>',
        '<style>@import "https://example.org/a.css";</style>',
        "cdn.plot.ly",
        "plotly-latest",
    ],
)
def test_external_dependencies_rejected(gallery, html):
    with pytest.raises(ValueError):
        gallery.check_self_contained(html)


@pytest.mark.parametrize("field", ["caveats", "references", "inputs"])
def test_missing_evidence_rejected(gallery, field):
    args = {
        "title": "Example",
        "inputs": {"synthetic": True},
        "results": {},
        "caveats": "Synthetic only",
        "references": [gallery.pipeline.burst_pressure_capacity],
    }
    args[field] = [] if field == "references" else ""
    with pytest.raises(ValueError):
        gallery.render_page(gallery.Page(**args), {"git_sha": "unknown"})


def test_no_caveats_cli_fails(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(tmp_path), "--_selftest-no-caveats"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert not list(tmp_path.glob("*.html"))


def test_pipeline_hand_calculation(built):
    """Repo pipeline_dnv.burst_pressure_capacity algebra, synthetic inputs.

    D=1 m, t=0.01 m, fy=100 Pa, fu=230 Pa, alpha_U=alpha_fab=1.
    fcb=min(100,230/1.15)=100 Pa; Pb=2*0.01/1*100=2 Pa.
    With both gamma inputs 1, pressures 1 and 3 Pa give U=0.5 and 1.5.
    These are arithmetic checks, not a validation of DNV code compliance.
    With unit resistance factors, moment capacity=pi/4 Nm, pressure capacity
    =2 Pa and axial capacity=pi N. For each applied component 0.1, combined
    U=(0.1/(pi/4))**2 + 0.1/2 + 0.1/pi. Equal normal stresses 5 Pa and zero
    shear give von Mises stress sqrt(25-25+25)=5 Pa.
    """
    result = payload(built, "pipeline_dnv")
    assert result["burst_Pa"][0] == pytest.approx(2)
    assert [r["utilization"] for r in result["containment"]] == pytest.approx(
        [0.5, 1.5]
    )
    assert result["von_mises_Pa"] == pytest.approx(5)
    expected_combined = (0.1 / (math.pi / 4)) ** 2 + 0.1 / 2 + 0.1 / math.pi
    assert result["local_buckling"]["utilization"] == pytest.approx(expected_combined)


def test_fatigue_hand_calculation(built):
    """Repo scr_sn_fatigue_life and fatigue_damage_tdz, synthetic S-N inputs.

    A=8000 MPa**2 cycles, m=2, amplitude=10 MPa: N=8000/(2*10)^2=20.
    At KC=10 the implemented soil factor is unity. Two cycles at range 20
    give D=2/20=0.1. No material curve or fatigue acceptance is asserted.
    """
    result = payload(built, "scr_fatigue")
    assert result["life_cycles"][0] == pytest.approx(20)
    assert result["damage"][0] == pytest.approx(0.1)


def test_units_hand_calculation(built):
    """SI milli prefix: 500 mm=0.5 m; 2 m*0.5 m=1 m**2 (exact algebra).

    Conversion is delegated to the registry; no rounded factor is embedded.
    """
    result = payload(built, "units_traceability")
    assert result["outputs"]["area"]["magnitude"] == pytest.approx(1)
    operations = [p["operation"] for p in result["outputs"]["area"]["provenance"]]
    assert "converted" in operations and "multiply" in operations


def test_workflow_is_real_and_unchecked(built):
    result = payload(built, "workflow_envelope")
    assert result["status"] == "ok"
    assert result["determinism"]["reproducible"] is None
    assert len(result["provenance"]["input_hash"]) == 64
    outputs = result["result"]["outputs"]
    assert outputs and all(o["size"] > 0 and len(o["sha256"]) == 64 for o in outputs)
    assert all(
        set(o) == {"basename", "relative_path", "sha256", "size"} for o in outputs
    )
    assert all(o["relative_path"].startswith("Plot/") for o in outputs)


def test_workflow_error_fails_closed(gallery, monkeypatch):
    from assetutilities.workflow_api.envelope import ResultEnvelope

    monkeypatch.setattr(
        gallery,
        "run_workflow",
        lambda **_: ResultEnvelope(
            workflow_id="visualization",
            status="error",
            result={},
            provenance={},
            determinism={},
            warnings=["Synthetic error"],
        ),
    )
    with pytest.raises(ValueError, match="workflow"):
        gallery.workflow_page()


def test_additional_calculations_by_hand(built):
    """Repo function algebra with synthetic inputs (not published design data).

    Strouhal: f=St*U/D=0.25*2/0.5=1 Hz; Vr=2/(1*0.5)=4.
    Wellhead: N=8000/20**2=20; life=20/2=10 years; damage=2/20=0.1.
    NPV at r=0.1: 100+110/1.1=200; output PV=10+11/1.1=20;
    levelized cost=200/20=10 currency units per output unit.
    """
    assert payload(built, "riser_viv")["frequency_Hz"] == pytest.approx(1)
    assert payload(built, "riser_viv")["reduced_velocity"] == pytest.approx(4)
    well = payload(built, "wellhead_fatigue")
    assert well == pytest.approx({"life_years": 10, "damage": 0.1, "life_cycles": 20})
    cost = payload(built, "lifecycle_cost")
    assert cost["npv"] == pytest.approx(200)
    assert cost["levelized"] == pytest.approx(10)


def test_template_gallery_has_embedded_images(built):
    html = (built / "visualization_templates.html").read_text()
    assert html.count("data:image/png;base64,") >= 3
    assert "Plotly.newPlot" in html


def test_ci_build_order():
    """Build HTML after MkDocs (which clears its destination), before upload."""
    import yaml

    for filename, job in (("pages.yml", "build"), ("docs.yml", "docs")):
        config = yaml.safe_load((ROOT / ".github/workflows" / filename).read_text())
        events = config.get("on", config.get(True))
        for event in ("push", "pull_request"):
            if event in events:
                assert "scripts/build_gallery.py" in events[event]["paths"]
        steps = config["jobs"][job]["steps"]
        docs = next(i for i, s in enumerate(steps) if s.get("name") == "Build docs")
        build = next(
            i for i, s in enumerate(steps) if "build_gallery.py" in s.get("run", "")
        )
        assert docs < build
        if filename == "pages.yml":
            upload = next(
                i
                for i, s in enumerate(steps)
                if "upload-pages-artifact" in s.get("uses", "")
            )
            assert build < upload
