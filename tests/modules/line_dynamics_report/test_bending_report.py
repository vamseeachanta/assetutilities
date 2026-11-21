"""Shared-formula proof, independent formula checks and raw XML cache evidence."""

import hashlib
import json
from dataclasses import astuple, replace
from pathlib import Path
from zipfile import ZipFile

import pytest

from assetutilities.line_dynamics_report.bending_report import (
    DynamicsRow, ReportAllowables, ReportMetadata,
    calculate_bending_report, reduce_dynamics_row,
)
from extract_cached_values import (
    expand_formulas, expand_report, extract_report_fixture, extract_workbook,
    xml_formula_caches,
)
from formula_oracle import FormulaOracle


FIXTURES = Path(__file__).parent / "fixtures"
COMPACT = json.loads((FIXTURES / "bending_reports.json").read_text())
REPORTS = COMPACT["reports"]
SOURCE = Path(__file__).resolve().parents[1] / "excel_utilities" / "excel_to_image.xlsx"
RELATIVE_TOLERANCE = 1e-9
ABSOLUTE_TOLERANCE = 1e-12
TITLE_TEMPLATE = (
    "{prefix} Umbilical Installation - BM installation - {step}"
    " - Dynamic Analysis - {current_description}"
)


def calculate_fixture(payload, raw_sheet="RAW"):
    sheet = payload["formulas"][0]["sheet"]
    inputs = {(x["sheet"], x["cell"]): x["value"] for x in payload["inputs"]}
    raw_rows = tuple(DynamicsRow(*(
        inputs[raw_sheet, f"{c}{r}"] for c in ("B", "F", *"IJKLMNOPQRSTUVWX")
    )) for r in sorted(int(cell[1:]) for source, cell in inputs
                       if source == raw_sheet and cell.startswith("B")))
    criteria = ReportAllowables(*(inputs[sheet, c] for c in ("N3", "O3", "P3", "Q3")))
    metadata = ReportMetadata(sheet, inputs[sheet, "F2"], TITLE_TEMPLATE)
    report = calculate_bending_report(raw_rows, metadata, criteria)
    actual = {"G2": report.step_label, "B4": report.title}
    for row_number, row in enumerate(report.rows, 9):
        actual.update({f"{c}{row_number}": value for c, value in zip("BCDEFGHIJKLMNOPQRS", astuple(row))})
    for row_number, values in ((66, report.maxima), (67, report.minima), (68, report.allowables)):
        actual.update({f"{c}{row_number}": value for c, value in zip(
            ("H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA"), values,
        )})
    assert set(actual) == {item["cell"] for item in payload["formulas"]}
    return actual, raw_rows, metadata, criteria


def assert_equal(actual, expected, context):
    if isinstance(expected, (int, float)):
        assert actual == pytest.approx(expected, rel=RELATIVE_TOLERANCE, abs=ABSOLUTE_TOLERANCE), context
    else:
        assert actual == expected, context


def test_compact_formula_pattern_is_complete():
    assert len(REPORTS) == 16
    assert (FIXTURES / "bending_reports.json").stat().st_size < 20_000
    formulas = expand_formulas(COMPACT["formula_pattern"])
    assert len(formulas) == 1070
    normalized = [(x["cell"], x["formula"], x.get("array_ref")) for x in formulas]
    digest = hashlib.sha256(json.dumps(normalized, separators=(",", ":")).encode()).hexdigest()
    assert digest == COMPACT["formula_pattern"]["normalized_formula_sha256"]
    assert len(COMPACT["formula_pattern"]["table_columns"]) == 18
    assert len(COMPACT["formula_pattern"]["single_cells"]) == 62
    rows = COMPACT["synthetic_rows"]
    assert 3 <= len(rows) <= 5
    assert all(len(row) == len(COMPACT["raw_columns"]) == 18 for row in rows)
    for report in REPORTS:
        assert "rows" not in report
        assert len(expand_report(COMPACT, report)["inputs"]) == 22 + 26 * len(rows)


@pytest.mark.parametrize("report", REPORTS, ids=lambda report: report["sheet"])
def test_report_against_independent_formula_text(report):
    payload = expand_report(COMPACT, report)
    actual, raw_rows, metadata, criteria = calculate_fixture(payload)
    oracle = FormulaOracle(payload)
    compared = 0
    for item in payload["formulas"]:
        if item["cell"] == "B4":
            assert actual["B4"] is None
            continue
        assert_equal(actual[item["cell"]], oracle.value(item["cell"]), item)
        compared += 1
    assert compared == 61 + 18 * len(COMPACT["synthetic_rows"])
    titled = calculate_bending_report(raw_rows, replace(metadata, title_prefix="neutral"), criteria)
    assert titled.title == (
        f"neutral Umbilical Installation - BM installation - {titled.step_label}"
        f" - Dynamic Analysis - {metadata.current_description}"
    )
    custom = replace(metadata, title_prefix="Example", title_template="{prefix}: {step} ({current_description})")
    assert calculate_bending_report(raw_rows, custom, criteria).title == (
        f"Example: {titled.step_label} ({metadata.current_description})"
    )


@pytest.mark.parametrize("report", REPORTS, ids=lambda report: report["sheet"])
def test_report_source_cache_evidence(report):
    # These are empty numeric v elements, not cached Excel empty strings.
    assert report["cache_counts"] == {"empty_v": 1070}
    assert report["cached_values"] == {}


def test_full_source_reports_match_shared_pattern_and_formula_results():
    if not SOURCE.is_file():
        pytest.skip("Optional source workbook is absent")
    # Extraction proves all full normalized formula sets equal the stored pattern,
    # including array refs, and validates each shared constant and helper blank.
    extracted = extract_report_fixture(SOURCE)
    for key in ("formula_pattern", "raw_columns", "raw_rows", "report_constants",
                "blank_ranges", "redacted_cells"):
        assert extracted[key] == COMPACT[key]
    compared = 0
    for source_report, report in zip(extracted["reports"], REPORTS):
        for key in ("sheet", "current_description", "cache_counts", "cached_values"):
            assert source_report[key] == report[key]
        assert len(source_report["rows"]) == 56
        payload = expand_report(extracted, source_report)
        actual, _, _, _ = calculate_fixture(payload)
        oracle = FormulaOracle(payload)
        for item in payload["formulas"]:
            if item["cell"] != "B4":
                assert_equal(actual[item["cell"]], oracle.value(item["cell"]), item["cell"])
                compared += 1
    assert compared == 17104
    states = [sheet for sheet in xml_formula_caches(SOURCE) if sheet]
    assert len(states) == 16
    assert sum(len(sheet) for sheet in states) == 17120
    assert all(set(sheet.values()) == {"empty_v"} for sheet in states)


def test_original_inputs_match_source_formula_results():
    if not SOURCE.is_file():
        pytest.skip("Optional source workbook is absent")
    compared = 0
    for sheet, source in extract_workbook(SOURCE).items():
        # Use original filenames, full response rows and sheet context in memory.
        actual, _, _, _ = calculate_fixture(source, raw_sheet=sheet.removesuffix("_rpt"))
        oracle = FormulaOracle(source)
        for item in source["formulas"]:
            if item["cell"] != "B4":
                assert_equal(actual[item["cell"]], oracle.value(item["cell"]), item["cell"])
                compared += 1
    assert compared == 17104


def test_xml_cache_states_distinguish_missing_empty_text_and_errors(tmp_path):
    # A tiny OOXML example guards the distinction data_only alone cannot make.
    path = tmp_path / "cache_states.xlsx"
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", '''<workbook
          xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <sheets><sheet name="neutral" sheetId="1" r:id="rId1"/></sheets></workbook>''')
        archive.writestr("xl/_rels/workbook.xml.rels", '''<Relationships>
          <Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>''')
        archive.writestr("xl/worksheets/sheet1.xml", '''<worksheet
          xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1">
          <c r="A1"><f>1</f><v></v></c>
          <c r="B1" t="str"><f>""</f><v></v></c>
          <c r="C1" t="e"><f>1/0</f><v>#DIV/0!</v></c>
          <c r="D1"><f>1</f><v>1</v></c>
          <c r="E1"><f>1</f></c>
          <c r="F1" t="str"><f>"text"</f><v>text</v></c>
          </row></sheetData></worksheet>''')
    assert xml_formula_caches(path) == [{
        "A1": "empty_v", "B1": "empty_string", "C1": "error_value",
        "D1": "numeric_value", "E1": "absent_v", "F1": "string_value",
    }]


def test_current_direction_and_filename_boundary_behavior():
    _, rows, _, _ = calculate_fixture(expand_report(COMPACT, REPORTS[0]))
    raw = replace(rows[0], case_filename="Hs1.25-Tp06.9", reference_current_speed_m_per_s=2,
                  current_factor_dimensionless=0.5, reference_current_direction_deg=180)
    positive = reduce_dynamics_row(raw)
    assert positive.surface_current_speed_m_per_s == 1
    assert positive.current_direction_clockwise_from_north_deg == 270
    assert positive.wave_period_s == 6
    assert positive.wave_height_text_m == "1.25"
    for speed in (0, -2):
        assert reduce_dynamics_row(replace(raw, reference_current_speed_m_per_s=speed)).current_direction_clockwise_from_north_deg == 0
    assert reduce_dynamics_row(replace(raw, reference_current_direction_deg=810)).current_direction_clockwise_from_north_deg == -360
    assert reduce_dynamics_row(replace(raw, wave_direction_deg=0)).wave_direction_clockwise_from_north_deg == 450
    with pytest.raises(ValueError, match="Missing filename token"):
        reduce_dynamics_row(replace(raw, case_filename="no_tokens"))
