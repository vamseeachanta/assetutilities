"""Independent arithmetic and public-output contracts for synthetic demos."""

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
    ],
)
def test_external_resources_fail_closed(html):
    with pytest.raises(ValueError, match="resource"):
        api().check_self_contained(html)


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
        text = page.read_text()
        for marker in ("Provenance", "Caveats", "Input echo", "Code references"):
            assert marker in text
        api().check_self_contained(text)
        assert str(tmp_path) not in text
    assert "NOT_EVALUATED" in (tmp_path / "pipeline_dnv.html").read_text()
    assert "NOT_EVALUATED" in (tmp_path / "scr_fatigue.html").read_text()
    assert "Plotly.newPlot" in (tmp_path / "visualization.html").read_text()
    visualization = (tmp_path / "visualization.html").read_text()
    assert "synthetic-polar" in visualization
    assert visualization.count('src="data:image/png;base64,') == 2
    envelope = json.loads((tmp_path / "workflow.json").read_text())
    assert envelope["status"] == "ok"
    assert envelope["result"]["outputs"]
    assert envelope["determinism"]["reproducible"] is None
    assert "not checked" in (tmp_path / "workflow_envelope.html").read_text()


def test_ci_builds_and_selects_gallery():
    import yaml

    for filename in ("docs.yml", "pages.yml"):
        workflow = yaml.safe_load((ROOT / ".github/workflows" / filename).read_text())
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
        capture_output=True,
        cwd=ROOT,
        check=True,
    )
    assert "tests/modules/gallery" in selector.stdout
