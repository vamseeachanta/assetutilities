"""Check layback labels and extrema against every source formula cache."""

import json
from pathlib import Path

import pytest

from assetutilities.line_dynamics_report.layback_summary import (
    LaybackSummaryInputs,
    calculate_layback_summary,
)
from extract_cached_values import compact_layback_fixture, extract_workbook


FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = Path(__file__).resolve().parents[1] / "excel_utilities" / "custom_calculation_polynomial.xlsx"
RELATIVE_TOLERANCE = 1e-9
ABSOLUTE_TOLERANCE = 1e-12


def compare_layback_summary(payload):
    values = {item["cell"]: item["value"] for item in payload["inputs"]}
    series = [tuple(values.get(f"{column}{r}") for r in range(7, 42)) for column in "GHIJKL"]
    output = calculate_layback_summary(LaybackSummaryInputs(
        tuple(values[f"A{r}"] for r in (7, 13, 19, 25, 31, 37)), *series,
    ))
    actual = dict(zip((f"A{r}" for r in (6, 12, 18, 24, 30, 36)), output.labels))
    actual.update(dict(zip((f"{c}42" for c in "GHIJKL"), (
        output.exit_tension_max_te, output.departure_angle_max_deg,
        output.bottom_tension_max_te, output.bottom_tension_min_te,
        output.minimum_bend_radius_m, output.allowable_curve_radius_max_m,
    ))))
    assert set(actual) == {item["cell"] for item in payload["formulas"]}
    compared = 0
    for item in payload["formulas"]:
        expected = item["cached_value"]
        assert expected is not None, item
        value = actual[item["cell"]]
        if isinstance(expected, (int, float)):
            assert value == pytest.approx(expected, rel=RELATIVE_TOLERANCE, abs=ABSOLUTE_TOLERANCE), item
        else:
            assert value == expected, item
        compared += 1
    assert compared == 12


def test_layback_summary_fixture_caches():
    path = FIXTURES / "custom_calculation_polynomial.json"
    assert path.stat().st_size < 20_000
    compare_layback_summary(json.loads(path.read_text()))


def test_layback_summary_direct_workbook_caches():
    if not SOURCE.is_file():
        pytest.skip("Optional source workbook is absent")
    payload = extract_workbook(SOURCE)["Sheet1"]
    assert compact_layback_fixture(payload) == json.loads(
        (FIXTURES / "custom_calculation_polynomial.json").read_text()
    )
    compare_layback_summary(payload)
