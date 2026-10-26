"""Gallery contracts and independent arithmetic on synthetic examples."""

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path, PureWindowsPath

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


def write_utf8(path, text):
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(text)


def source_status(root):
    """Capture Git state and tracked or untracked nonignored source bytes."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, env=env
    )
    diff = subprocess.check_output(["git", "diff", "--binary"], cwd=root, env=env)
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
        cwd=root,
        env=env,
        check=False,
        capture_output=True,
    ).stdout
    names = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        env=env,
    ).split(b"\0")
    fingerprints = []
    for name in sorted(set(names) - {b""}):
        path = root / os.fsdecode(name)
        data = None
        if path.is_symlink():
            data = os.fsencode(os.readlink(path))
        elif path.is_file():
            data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest() if data is not None else None
        fingerprints.append((name, digest))
    return status, diff, head, fingerprints


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("gallery")
    before = source_status(ROOT)
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    env.update(SOURCE_DATE_EPOCH="0", GITHUB_SHA="a" * 40)
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
    assert source_status(ROOT) == before
    return out


def payload(out, name):
    return json.loads(Results((out / f"{name}.html").read_text(encoding="utf-8")).value)


def test_complete_self_contained_gallery(built, gallery):
    assert {p.stem for p in built.glob("*.html")} == PAGES
    for page in built.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        for marker in ("Provenance", "Caveats", "Input echo", "Code references"):
            assert marker in html, (page.name, marker)
        assert "1970-01-01" in html
        assert "a" * 40 in html
        gallery.check_self_contained(html)
    for name in ("pipeline_dnv", "scr_fatigue"):
        html = (built / f"{name}.html").read_text(encoding="utf-8")
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


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("caveats", "", "Every page requires caveats"),
        ("caveats", " \t", "Every page requires caveats"),
        ("references", [], "Every page requires code references"),
        ("inputs", {}, "Every page requires input echo"),
    ],
)
def test_missing_evidence_rejected(gallery, field, value, message):
    args = {
        "title": "Example",
        "inputs": {"synthetic": True},
        "results": {},
        "caveats": "Synthetic only",
        "references": [gallery.pipeline.burst_pressure_capacity],
    }
    args[field] = value
    with pytest.raises(ValueError, match=f"^{message}$"):
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
    assert "requires caveats" in result.stderr
    assert not list(tmp_path.glob("*.html"))


def test_pipeline_discloses_simplified_expressions(built):
    html = (built / "pipeline_dnv.html").read_text(encoding="utf-8")
    guide = (ROOT / "docs/api/gallery-guide.md").read_text(encoding="utf-8")
    for text in (html, guide):
        assert "library-simplified" in text
        assert "do not reproduce" in text
        assert "burst and combined-loading" in text
    for row in payload(built, "pipeline_dnv")["containment"]:
        assert "library-simplified burst" in row["basis"]


def test_code_links_use_posix_paths(gallery, monkeypatch):
    class WindowsSourcePath(PureWindowsPath):
        def resolve(self):
            return self

    monkeypatch.setattr(gallery, "Path", WindowsSourcePath)
    monkeypatch.setattr(gallery, "ROOT", PureWindowsPath("."))
    monkeypatch.setattr(
        gallery.inspect, "getsourcefile", lambda _: "src/calculations/example.py"
    )
    evidence = {"repository": "example/library", "git_sha": "a" * 40}
    html = gallery.code_links([gallery.riser_viv.strouhal_frequency], evidence)
    assert "/src/calculations/example.py#L" in html
    assert "\\" not in html


def test_workflow_input_echo_is_utf8(gallery, monkeypatch, tmp_path):
    import yaml

    from assetutilities.workflow_api import runner

    original_read = Path.read_text

    def locale_read(path, encoding=None, errors=None):
        return original_read(path, encoding=encoding or "cp1252", errors=errors)

    row = runner.resolve_registry_row("visualization").copy()
    expected = runner.resolve_example_path(row["input"]).read_text(encoding="utf-8")
    expected += "\n# Synthetic label: · ×\n"
    row["input"] = "registered-input.yml"
    write_utf8(tmp_path / row["input"], expected)
    registry = tmp_path / "docs/registry/workflows.yaml"
    registry.parent.mkdir(parents=True)
    write_utf8(registry, yaml.safe_dump({"workflows": [row]}))
    monkeypatch.setattr(runner, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(Path, "read_text", locale_read)
    echo = gallery.workflow_page().inputs["yaml"]
    assert echo == expected
    assert yaml.safe_load(echo) == runner.build_cfg(row, None)


def test_gallery_writes_utf8_and_lf(gallery, monkeypatch, tmp_path):
    original_open = Path.open
    writes = []

    def record_open(path, *args, **kwargs):
        if path.parent == tmp_path and path.suffix == ".html":
            writes.append(kwargs)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", record_open)
    gallery.build(tmp_path)
    assert len(writes) == len(PAGES)
    assert all(w.get("encoding") == "utf-8" for w in writes)
    assert all(w.get("newline") == "\n" for w in writes)
    for page in tmp_path.glob("*.html"):
        data = page.read_bytes()
        assert b"\r" not in data
        assert "·" in data.decode("utf-8")


def test_source_status_detects_untracked_output(tmp_path):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    subprocess.run(["git", "init", "-q", str(tmp_path)], env=env, check=True)
    before = source_status(tmp_path)
    write_utf8(tmp_path / "unexpected.txt", "synthetic output")
    assert source_status(tmp_path) != before
    assert b"?? unexpected.txt" in source_status(tmp_path)[0]


def test_source_status_detects_changes_to_an_already_dirty_file(tmp_path):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    subprocess.run(["git", "init", "-q", str(tmp_path)], env=env, check=True)
    source = tmp_path / "source.txt"
    write_utf8(source, "initial")
    subprocess.run(["git", "add", "source.txt"], cwd=tmp_path, env=env, check=True)
    write_utf8(source, "first edit")
    before = source_status(tmp_path)
    write_utf8(source, "second edit")
    assert source_status(tmp_path) != before


def test_source_status_detects_changes_to_an_existing_untracked_file(tmp_path):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    subprocess.run(["git", "init", "-q", str(tmp_path)], env=env, check=True)
    source = tmp_path / "unexpected.txt"
    write_utf8(source, "initial")
    before = source_status(tmp_path)
    write_utf8(source, "changed")
    assert source_status(tmp_path) != before


def test_git_output_ignores_inherited_bindings(gallery, monkeypatch):
    expected = gallery.git_output("rev-parse", "HEAD")
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.setenv(key, "missing-git-directory")
    assert gallery.git_output("rev-parse", "HEAD") == expected


def test_cli_clears_bindings_for_workflow_provenance(gallery, monkeypatch, tmp_path):
    expected = gallery.git_output("rev-parse", "HEAD")
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.setenv(key, "missing-git-directory")
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--out", str(tmp_path)])
    gallery.main()
    result = payload(tmp_path, "workflow_envelope")
    assert result["provenance"]["code_version"]["git_sha"] == expected


def test_lifecycle_cost_designation(gallery):
    guide = (ROOT / "docs/api/gallery-guide.md").read_text(encoding="utf-8")
    for text in (gallery.cost_page().method, guide):
        assert "ISO 15663-2:2001" in text
        assert "BS 15663-2 (2001)" not in text


def test_low_kc_damage_requires_qualified_soil_coefficient(built):
    result = payload(built, "scr_fatigue")
    assert result["damage"][0] == pytest.approx(0.1)
    assert str(result["damage"][1]).startswith("NOT_EVALUATED:")


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
    html = (built / "visualization_templates.html").read_text(encoding="utf-8")
    assert html.count("data:image/png;base64,") >= 3
    assert "Plotly.newPlot" in html


def test_ci_build_order():
    """Build HTML after MkDocs (which clears its destination), before upload."""
    import yaml

    for filename, job in (("pages.yml", "build"), ("docs.yml", "docs")):
        config = yaml.safe_load(
            (ROOT / ".github/workflows" / filename).read_text(encoding="utf-8")
        )
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
