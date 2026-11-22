"""Check constants report arithmetic, public basis and offline regeneration."""

import ast
import importlib.util
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

from assetutilities.constants import conversions

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/reports/build_constants_report.py"
DESTINATION = ROOT / "docs/reports/modules/aconstants"
REBUILD = "python scripts/reports/build_constants_report.py"


@pytest.fixture(scope="module")
def builder():
    spec = importlib.util.spec_from_file_location("constants_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload(page):
    match = re.search(
        r'<script id="calculation-data" type="application/json">(.*?)</script>',
        page,
        re.S,
    )
    assert match, f"Missing calculation data; rebuild with {REBUILD}"
    return json.loads(match[1])


def test_hand_anchor_published_length(builder):
    # NIST SP 811 (2008), B.7.2: 36 ft × 0.3048 m/ft.
    # By hand: (30 × 3048 + 6 × 3048) / 10000
    # = (91440 + 18288) / 10000 = 10.9728 m; absolute tolerance 1e-12 m.
    assert builder.calculate()["values"]["length_m"] == pytest.approx(
        10.9728, rel=0, abs=1e-12
    )


def test_hand_anchor_inch(builder):
    # NIST SP 811 (2008), B.8 inch entry and Table 5:
    # 1 in × 0.0254 m/in ÷ 0.001 m/mm = 25.4 mm.
    # Absolute tolerance 1e-12 mm.
    assert builder.calculate()["values"]["length_mm"] == pytest.approx(
        25.4, rel=0, abs=1e-12
    )


def test_hand_anchor_bar(builder):
    # NIST SP 811 (2008), B.8 bar entry and Table 5:
    # 1 bar × 100000 Pa/bar ÷ 1000000 Pa/MPa = 0.1 MPa.
    # Absolute tolerance 1e-12 MPa.
    assert builder.calculate()["values"]["pressure_mpa"] == pytest.approx(
        0.1, rel=0, abs=1e-12
    )


def test_worked_example_and_chart_consistency(builder):
    data = builder.calculate()
    basis = builder.basis()
    assert data["values"]["length_m"] == conversions.ft_to_m(
        basis["example"]["length_ft"]
    )
    assert data["values"]["length_mm"] == conversions.inch_to_mm(
        basis["supplementary_cases"]["inch"]
    )
    assert data["values"]["pressure_mpa"] == conversions.bar_to_mpa(
        basis["supplementary_cases"]["bar"]
    )
    assert data["values"]["returned_ft"] == conversions.m_to_ft(
        data["values"]["length_m"]
    )
    for point in data["curve"]:
        assert point["m"] == pytest.approx(
            conversions.ft_to_m(point["ft"]), rel=0, abs=1e-10
        )


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.numbers = {}
        self.headings = []
        self.number_value = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.links.append(attrs["href"][1:])
        if "data-number" in attrs:
            self.numbers.setdefault(attrs["data-number"], []).append(
                attrs["data-value"]
            )
            self.number_value = attrs["data-value"]
        if tag == "h2":
            self.headings.append(tag)
        assert tag not in {"h4", "h5", "h6", "b", "strong"}
        assert not (tag in {"script", "link"} and ("src" in attrs or "href" in attrs))

    def handle_data(self, data):
        if self.number_value is not None:
            assert data == self.number_value

    def handle_endtag(self, tag):
        if tag == "span":
            self.number_value = None


def test_every_displayed_example_number_and_headline(builder):
    data = builder.calculate()
    page = Page(builder.render())
    embedded = payload(builder.render())
    assert embedded["values"] == pytest.approx(data["values"], rel=0, abs=1e-10)
    assert page.numbers
    expected = {**data["inputs"], **data["values"]}
    for key, displays in page.numbers.items():
        for display in displays:
            # Compare at the displayed precision; full-precision text is not fixed.
            places = len(display.partition(".")[2])
            assert float(display) == pytest.approx(
                expected[key], rel=0, abs=0.5 * 10**-places
            )
    # The displayed input and cited conversion factor reproduce the headline.
    foot = float(page.numbers["length_ft"][0])
    factor = builder.basis()["definitions"]["metres_per_foot"]["value"]
    assert round(foot * factor, 4) == float(page.numbers["length_m"][0])
    assert (
        f"{data['values']['length_m']:.1f}"
        == builder.basis()["example"]["reference_display_m"]
    )


def test_offline_rebuild_matches_committed_report(builder, tmp_path):
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output-dir", str(tmp_path)],
        cwd=ROOT,
        check=True,
    )
    committed = (DESTINATION / "report.html").read_text(encoding="utf-8")
    rebuilt = (tmp_path / "report.html").read_text(encoding="utf-8")
    old, new = payload(committed), payload(rebuilt)
    for group in ("inputs", "values"):
        assert old[group] == pytest.approx(new[group], rel=0, abs=1e-10), REBUILD
    for old_point, new_point in zip(old["curve"], new["curve"]):
        assert old_point == pytest.approx(new_point, rel=0, abs=1e-10), REBUILD
    assert old["source_digests"] == new["source_digests"], REBUILD
    assert old["test_inventory"] == new["test_inventory"], REBUILD
    # Mask the already compared numeric payload. Visible values use displayed digits.
    pattern = r'(<script id="calculation-data" type="application/json">).*?(</script>)'
    assert re.sub(pattern, r"\1MASKED\2", committed, flags=re.S) == re.sub(
        pattern, r"\1MASKED\2", rebuilt, flags=re.S
    ), f"Stale report; rebuild with {REBUILD}"
    assert json.loads((DESTINATION / "changes.json").read_text(encoding="utf-8")) == (
        json.loads((tmp_path / "changes.json").read_text(encoding="utf-8"))
    ), REBUILD


def test_structure_sources_comments_and_public_text(builder):
    text = builder.render()
    page = Page(text)
    assert len(page.headings) == 10
    assert len(page.ids) == len(set(page.ids))
    assert set(page.links) <= set(page.ids)
    assert '<body class="hs-doc doc"' in text
    assert 'id="comments"' in text
    assert "showDirectoryPicker" in text
    assert "createWritable" in text
    assert "JSON.parse" in text and 'id="changes-data"' in text
    assert builder.basis()["http_status"] == 200
    for definition in builder.basis()["definitions"].values():
        assert definition["locator"]
    assert builder.basis()["example"]["locator"]
    assert builder.basis()["url"] in text
    evidence = json.loads((DESTINATION / "checks.json").read_text(encoding="utf-8"))
    assert evidence["existing_selection"]["passed"] == sum(
        builder.calculate()["test_inventory"].values()
    ), REBUILD
    assert evidence["report_selection"]["passed"] == sum(
        node.name.startswith("test_")
        for node in ast.walk(ast.parse(Path(__file__).read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef)
    ), REBUILD
    visible = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text, flags=re.S)
    for term in ("could", "should", "would"):
        assert not re.search(rf"\b{term}\b", visible, re.I), term


def test_utf8_lf_and_explicit_text_io():
    paths = [SCRIPT, Path(__file__), ROOT / "scripts/reports/constants_report.html"]
    paths += list(DESTINATION.glob("*"))
    for path in paths:
        raw = path.read_bytes()
        raw.decode("utf-8")
        assert b"\r" not in raw, path.name
    for path in (SCRIPT, Path(__file__)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            if node.func.attr in {"read_text", "write_text", "open"}:
                keywords = {item.arg: item.value for item in node.keywords}
                assert ast.literal_eval(keywords["encoding"]) == "utf-8"
                if node.func.attr in {"write_text", "open"}:
                    assert ast.literal_eval(keywords["newline"]) == "\n"
