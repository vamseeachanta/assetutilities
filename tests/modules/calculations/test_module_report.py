"""Numeric and publication checks for the calculations module report."""

import hashlib
import json
import re
import runpy
from pathlib import Path

import pytest

from assetutilities.calculations import lifecycle_cost

ROOT = Path(__file__).resolve().parents[3]
BUILDER = ROOT / "scripts/reports/build_calculations_report.py"
OUTPUT = ROOT / "docs/reports/modules/acalculations"
REBUILD = "PYTHONPATH=src python scripts/reports/build_calculations_report.py"


@pytest.fixture(scope="module")
def report_builder():
    assert BUILDER.is_file(), f"Missing report generator: {REBUILD}"
    return runpy.run_path(str(BUILDER))


def payload(html):
    return json.loads(
        re.search(
            r'<script id="report-data" type="application/json">(.*?)</script>',
            html,
            re.S,
        )[1]
    )


def test_replacement_hand_anchor(report_builder):
    # NIST 2025 §3.2.1: 1.03^5 = 1.1592740743;
    # 1000 / 1.1592740743 = 862.608784384164 USD. Absolute tolerance: 1e-8 USD.
    assert report_builder["calculate"]()["replacement_pv"] == pytest.approx(
        862.608784384164, abs=1e-8, rel=0
    )


def test_maintenance_hand_anchor(report_builder):
    # NIST 2025 §3.2.2.1: 100*(1.1592740743-1)/(.03*1.1592740743)
    # = 457.970718719453 USD. Absolute tolerance: 1e-8 USD.
    assert report_builder["calculate"]()["maintenance_pv"] == pytest.approx(
        457.970718719453, abs=1e-8, rel=0
    )


def test_annual_cost_hand_anchor(report_builder):
    # NIST 2025 §17.4: (862.608784384164+457.970718719453)*.03
    # *1.1592740743/(1.1592740743-1) = 288.354571400576 USD/year.
    # Absolute tolerance: 1e-8 USD/year.
    assert report_builder["calculate"]()["annual_cost"] == pytest.approx(
        288.354571400576, abs=1e-8, rel=0
    )


def test_headline_from_displayed_inputs(report_builder):
    data = report_builder["calculate"]()
    # The displayed source inputs retain the source precision, including timing.
    costs = [0, 100, 100, 100, 100, 1100]
    expected = sum(c / (1 + 0.03) ** t for t, c in enumerate(costs))
    assert f"{expected:.2f}" == f"{data['combined_pv']:.2f}"


def test_every_worked_number_consistency_check(report_builder):
    html = report_builder["render_report"]()
    data = payload(html)
    expected = report_builder["calculate"]()
    worked = re.search(r'<section id="s6">(.*?)</section>', html, re.S)[1]
    # Every numerical result and input in this section is bound to a named value.
    worked = re.sub(r"<h2>.*?</h2>", "", worked)
    stripped = re.sub(r'<span data-number="[^"]+">[^<]+</span>', "", worked)
    stripped = re.sub(r"<[^>]*>", "", stripped)
    assert not re.search(r"\d", stripped), "Unbound numeric text in worked example"
    for key, visible in re.findall(r'<span data-number="([^"]+)">([^<]+)</span>', html):
        assert visible == report_builder["display"](key, expected[key])
        assert data["values"][key] == pytest.approx(expected[key], abs=0.00000001)
    stream = [0, 100, 100, 100, 100, 1100]
    assert data["values"]["combined_pv"] == pytest.approx(
        lifecycle_cost.net_present_value(stream, 0.03), abs=1e-8
    )
    # Consistency checks call the module independently of the report builder.
    replacement = [0] * 5 + [1000]
    maintenance = [0] + [100] * 5
    for key, costs in [("replacement", replacement), ("maintenance", maintenance)]:
        present = lifecycle_cost.net_present_value(costs, 0.03)
        assert data["values"][key + "_pv"] == pytest.approx(present, abs=1e-8)
        assert data["values"][key + "_annual"] == pytest.approx(
            lifecycle_cost.annual_equivalent_cost(present, 0.03, 5), abs=1e-8
        )
    assert data["values"]["annual_cost"] == pytest.approx(
        lifecycle_cost.annual_equivalent_cost(data["values"]["combined_pv"], 0.03, 5),
        abs=1e-8,
    )
    for row in data["rows"]:
        year = row["year"]
        assert row["present_value"] == pytest.approx(
            lifecycle_cost.net_present_value([0] * year + [stream[year]], 0.03),
            abs=1e-8,
        )
        assert row["cumulative_pv"] == pytest.approx(
            lifecycle_cost.net_present_value(stream[: year + 1], 0.03), abs=1e-8
        )


def test_committed_report_rebuild_consistency(report_builder, tmp_path):
    report_builder["build"](tmp_path)
    committed = (OUTPUT / "report.html").read_text(encoding="utf-8")
    fresh = (tmp_path / "report.html").read_text(encoding="utf-8")
    # Numeric comparisons use displayed digits and rounded arrays; the remaining
    # document is compared exactly, so lost prose, stale sources and controls fail.
    message = f"Stale calculation evidence; rebuild: {REBUILD}"
    assert payload(committed) == payload(fresh), message
    assert committed == fresh, f"Stale report; rebuild: {REBUILD}"
    assert (OUTPUT / "changes.json").read_text(encoding="utf-8") == (
        tmp_path / "changes.json"
    ).read_text(encoding="utf-8"), f"Stale change panel; rebuild: {REBUILD}"


def test_calculation_source_digests(report_builder):
    data = payload(report_builder["render_report"]())
    assert len(data["sources"]) == len(
        list((ROOT / "src/assetutilities/calculations").glob("*.py"))
    )
    for source in data["sources"]:
        assert source["path"].startswith("src/assetutilities/calculations/")
        assert (
            source["sha256"]
            == hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest()
        ), f"Calculation source changed; rebuild: {REBUILD}"


def test_document_structure_and_sources(report_builder):
    html = report_builder["render_report"]()
    assert 'class="hs-doc doc"' in html
    assert len(re.findall(r'<section id="s\d+">', html)) == 10
    assert "Draft for maintainer review" in html
    assert "<h4" not in html and "<b>" not in html and "<strong>" not in html
    assert html.index("Revision history") < html.index('<section id="s2">')
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    for target in re.findall(r'href="#([^"]+)"', html):
        assert target in ids
    assert "NIST HB 135e2025" in html and "3.2.2.1" in html and "17.4" in html
    assert not re.search(r'<(?:script|link)[^>]+(?:src|href)="https?://', html)


def test_public_text_and_portable_output(report_builder, tmp_path):
    report_builder["build"](tmp_path)
    for name in ["report.html", "changes.json"]:
        content = (tmp_path / name).read_bytes()
        assert b"\r" not in content and content.endswith(b"\n")
        text = content.decode("utf-8")
        assert not re.search(r"\b(owner|Codex|Claude|could|should|would)\b", text, re.I)
        assert not re.search(r"(?:/home/|/mnt/|[A-Za-z]:\\)", text)


def test_chart_and_comment_contract(report_builder):
    html = report_builder["render_report"]()
    assert "No acceptance limit is specified" in html
    assert "data-point=" in html and 'tabindex="0"' in html
    assert "showSaveFilePicker" in html and "report.comments.json" in html
    assert "textContent" in html and "report_digest" in html
    assert "Downloads" in html and "load-comments" in html
    assert "changes-data" in html


def test_comment_identity_covers_document_prose(report_builder):
    html = report_builder["render_report"]()
    identity = re.search(r"const reportDigest = '([a-f0-9]{64})';", html)[1]
    masked = html.replace(
        f"const reportDigest = '{identity}';", f"const reportDigest = '{'0' * 64}';"
    )
    assert identity == hashlib.sha256(masked.encode("utf-8")).hexdigest()
    # A prose edit changes comment identity even when calculation data is unchanged.
    amended = masked.replace(
        "Calculations module analysis", "Calculations module description", 1
    )
    assert hashlib.sha256(amended.encode("utf-8")).hexdigest() != identity
