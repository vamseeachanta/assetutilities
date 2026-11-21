"""Read-only extraction of formulas, caches and direct constant dependencies.

The command regenerates only the layback fixture; report rows are synthetic
and maintained by hand. Only the two named source workbooks are supported.
No workbook is saved.
"""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.formula.translate import Translator
from openpyxl.utils.cell import get_column_letter, range_boundaries


def formula_text(cell: Any) -> str:
    """Preserve array formula text as well as ordinary formula text."""
    return cell.value if isinstance(cell.value, str) else cell.value.text


def extract_workbook(path: Path) -> Dict[str, Dict[str, Any]]:
    """Read twice; return one fixture per report, or one for the small workbook.

    D2 on reports is a title identifier: deliberately omit its identifying value.
    Every formula and cached value is preserved; missing caches remain JSON null.
    The hidden metadata sheet is represented only by its positional alias.
    """
    if path.name not in {"excel_to_image.xlsx", "custom_calculation_polynomial.xlsx"}:
        raise ValueError("Only the two neutral source workbook names are supported")
    formulas = load_workbook(path, data_only=False)
    cached = load_workbook(path, data_only=True)
    try:
        inventory = []
        formula_sheets = []
        for index, sheet in enumerate(formulas):
            cells = [c for row in sheet for c in row if c.data_type == "f"]
            if cells:
                formula_sheets.append(sheet)
            inventory.append({
                "sheet": sheet.title if not sheet.title.startswith("__$") else "hidden_metadata",
                "sheet_index": index + 1,
                "formula_cells": len(cells),
                "cached_formula_cells": sum(
                    cached[sheet.title][c.coordinate].value is not None for c in cells
                ),
            })
        result = {}
        for sheet in formula_sheets:
            records = []
            dependencies = {}
            normalized = []
            for row in sheet:
                for cell in row:
                    if cell.data_type != "f":
                        continue
                    text = formula_text(cell)
                    record = {
                        "sheet": sheet.title, "cell": cell.coordinate,
                        "formula": text,
                        "cached_value": cached[sheet.title][cell.coordinate].value,
                    }
                    if not isinstance(cell.value, str):
                        record["array_ref"] = cell.value.ref
                    records.append(record)
                    normalized.append((
                        cell.coordinate,
                        text.replace(sheet.title.removesuffix("_rpt") + "!", "RAW!"),
                        record.get("array_ref"),
                    ))
                    for token in Tokenizer(text).items:
                        if token.type != "OPERAND" or token.subtype != "RANGE":
                            continue
                        reference = token.value
                        target = sheet
                        if "!" in reference:
                            target_name, reference = reference.rsplit("!", 1)
                            target = formulas[target_name.strip("'")]
                        left, top, right, bottom = range_boundaries(reference)
                        for r in range(top, bottom + 1):
                            for c in range(left, right + 1):
                                coordinate = f"{get_column_letter(c)}{r}"
                                source = target[coordinate]
                                if source.data_type == "f":
                                    continue
                                item = {
                                    "sheet": target.title, "cell": coordinate,
                                    "value": source.value,
                                }
                                if target.title.endswith("_rpt") and coordinate == "D2":
                                    item["value"] = None
                                    item["redacted"] = "identifying title prefix"
                                dependencies[(target.title, coordinate)] = item
            result[sheet.title] = {
                "source": f"tests/modules/excel_utilities/{path.name}",
                "inventory": inventory,
                "defined_names": list(formulas.defined_names),
                "external_link_count": len(formulas._external_links),
                "normalized_formula_sha256": hashlib.sha256(
                    json.dumps(normalized, separators=(",", ":")).encode()
                ).hexdigest(),
                "formulas": records,
                "inputs": sorted(dependencies.values(), key=lambda x: (x["sheet"], x["cell"])),
            }
        return result
    finally:
        formulas.close()
        cached.close()


def xml_formula_caches(path: Path) -> list:
    """Inspect raw XML: an empty numeric v is not a cached empty string.

    Return sheets in workbook order, without exposing their source names.
    Values are taken from openpyxl separately; XML establishes cache presence.
    """
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as archive:
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheets = []
        for sheet in book.findall("s:sheets/s:sheet", ns):
            target = targets[sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]]
            member = target.lstrip("/") if target.startswith("/") else "xl/" + target
            root = ET.fromstring(archive.read(member))
            states = {}
            for cell in root.findall(".//s:c", ns):
                if cell.find("s:f", ns) is None:
                    continue
                value = cell.find("s:v", ns)
                if value is None:
                    state = "absent_v"
                elif cell.get("t") == "e":
                    state = "error_value"
                elif cell.get("t") == "str":
                    state = "string_value" if value.text else "empty_string"
                elif value.text is None:
                    state = "empty_v"
                else:
                    state = "numeric_value"
                states[cell.attrib["r"]] = state
            sheets.append(states)
        return sheets


def expand_formulas(pattern: dict, row_count: Optional[int] = None) -> list:
    """Expand the pattern, optionally shortening table and extrema ranges."""
    first, last = pattern["table_rows"]
    end = last if row_count is None else first + row_count - 1
    records = []
    for cell, text, ref in pattern["single_cells"]:
        if row_count is not None and text.startswith(("=MAX(", "=MIN(")):
            text = text.replace(f"{last})", f"{end})")
        records.append(dict(cell=cell, formula=text, **({"array_ref": ref} if ref else {})))
    for row in range(first, end + 1):
        for column, text in pattern["table_columns"]:
            address = f"{column}{row}"
            records.append({"cell": address, "formula": Translator(
                text, origin=f"{column}{first}",
            ).translate_formula(address)})
    return sorted(records, key=lambda x: (
        range_boundaries(x["cell"])[1], range_boundaries(x["cell"])[0],
    ))


def normalized_records(records: list, raw_sheet: str) -> list:
    return [{key: value.replace(raw_sheet + "!", "RAW!") if key == "formula" else value
             for key, value in record.items() if key in {"cell", "formula", "array_ref"}}
            for record in records]


def extract_report_fixture(path: Path) -> dict:
    """Extract full report inputs and formulas for comparisons in memory only.

    Sheet context is anonymized. Filename text is reduced to the two exact
    four-character fields the formulas read. Assert reconstruction against
    every source formula. These response rows must not be written to fixtures.
    """
    extracted = extract_workbook(path)
    xml_sheets = [states for states in xml_formula_caches(path) if states]
    payload = {"schema_version": 2, "raw_columns": ["B", "F", *"IJKLMNOPQRSTUVWX"],
               "raw_rows": [2, 57], "reports": []}
    for index, ((sheet, source), states) in enumerate(zip(extracted.items(), xml_sheets), 1):
        raw_sheet = sheet.removesuffix("_rpt")
        records = normalized_records(source["formulas"], raw_sheet)
        if index == 1:
            pattern = {
                "normalized_formula_sha256": source["normalized_formula_sha256"],
                "table_rows": [9, 64],
                "table_columns": [[x["cell"][:-1], x["formula"]] for x in records
                                  if x["cell"] in {f"{c}9" for c in "BCDEFGHIJKLMNOPQRS"}],
                "single_cells": [[x["cell"], x["formula"], x.get("array_ref")]
                                 for x in records if not 9 <= range_boundaries(x["cell"])[1] <= 64],
            }
            payload["formula_pattern"] = pattern
        if expand_formulas(payload["formula_pattern"]) != records:
            raise ValueError("Source formulas differ from the shared pattern")
        values = {(x["sheet"], x["cell"]): x["value"] for x in source["inputs"]}
        constants = {x["cell"]: x["value"] for x in source["inputs"]
                     if x["sheet"] == sheet and x["cell"] not in {"D2", "F2"}
                     and not (9 <= range_boundaries(x["cell"])[1] <= 64)}
        blanks = {x["cell"] for x in source["inputs"] if x["sheet"] == sheet
                  and 9 <= range_boundaries(x["cell"])[1] <= 64}
        expected_blanks = {f"{get_column_letter(c)}{r}" for c in range(20, 28)
                           for r in range(9, 65)}
        if blanks != expected_blanks or any(values[sheet, cell] is not None for cell in blanks):
            raise ValueError("Helper cells no longer match the shared blank range")
        if index == 1:
            payload["report_constants"] = constants
            payload["blank_ranges"] = ["T9:AA64"]
            payload["redacted_cells"] = ["D2"]
        if constants != payload["report_constants"]:
            raise ValueError("Report constants differ from the shared inputs")
        rows = []
        for row in range(2, 58):
            filename = values[raw_sheet, f"B{row}"]
            fields = [filename.split(token, 1)[1][:4] for token in ("Hs", "Tp")]
            neutral_filename = f"Hs{fields[0]}-Tp{fields[1]}"
            rows.append([neutral_filename] + [values[raw_sheet, f"{c}{row}"]
                                              for c in payload["raw_columns"][1:]])
        caches = {}
        for item in source["formulas"]:
            cell = item["cell"]
            state = states[cell]
            if state in {"absent_v", "empty_v"}:
                continue
            if cell == "B4":
                raise ValueError("Title cache needs private validation before publication")
            caches[cell] = "" if state == "empty_string" else item["cached_value"]
        payload["reports"].append({
            "sheet": f"report_case{index:02d}",
            "current_description": values[sheet, "F2"], "rows": rows,
            "cache_counts": dict(sorted(Counter(states.values()).items())),
            "cached_values": caches,
        })
    if len(payload["reports"]) != 16 or len(xml_sheets) != 16:
        raise ValueError("Expected sixteen source report sheets")
    return {key: payload[key] for key in (
        "schema_version", "formula_pattern", "raw_columns", "raw_rows",
        "report_constants", "blank_ranges", "redacted_cells", "reports",
    )}


def expand_report(payload: dict, report: dict) -> dict:
    """Expand synthetic or in-memory source rows for formula interpretation."""
    sheet = report["sheet"]
    rows = report.get("rows", payload.get("synthetic_rows"))
    row_count = len(rows)
    table_end = payload["formula_pattern"]["table_rows"][0] + row_count - 1
    inputs = [{"sheet": sheet, "cell": cell, "value": value}
              for cell, value in payload["report_constants"].items()]
    inputs += [{"sheet": sheet, "cell": "F2", "value": report["current_description"]},
               {"sheet": sheet, "cell": "D2", "value": None, "redacted": True}]
    for bounds in payload["blank_ranges"]:
        left, top, right, bottom = range_boundaries(bounds)
        inputs += [{"sheet": sheet, "cell": f"{get_column_letter(c)}{r}", "value": None}
                   for r in range(top, min(bottom, table_end) + 1) for c in range(left, right + 1)]
    for row, values in enumerate(rows, payload["raw_rows"][0]):
        inputs += [{"sheet": "RAW", "cell": f"{column}{row}", "value": value}
                   for column, value in zip(payload["raw_columns"], values)]
    return {"workbook_name": payload.get("workbook_name", "excel_to_image.xlsx"),
            "formulas": [{**item, "sheet": sheet,
                          "cached_value": report["cached_values"].get(item["cell"])}
                         for item in expand_formulas(payload["formula_pattern"], row_count)],
            "inputs": inputs}


def compact_layback_fixture(payload: dict) -> dict:
    """Store the shared sheet once, preserving every formula, cache and input."""
    sheet = payload["formulas"][0]["sheet"]
    compact = {**payload, "sheet": sheet}
    for key in ("formulas", "inputs"):
        assert all(record["sheet"] == sheet for record in payload[key])
        compact[key] = [{k: v for k, v in record.items() if k != "sheet"}
                        for record in payload[key]]
    return compact


def write_compact_fixture(path: Path, payload: dict) -> None:
    """Keep each row/record readable on one line, without repeated key names."""
    def compact(value):
        return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"))

    # Records inside lists stay on one line, as do scalar rows.
    def render(value, level=0):
        indent = "  " * level
        if isinstance(value, dict) and value:
            return "{\n" + ",\n".join(
                indent + "  " + json.dumps(key) + ": " + render(item, level + 1)
                for key, item in value.items()
            ) + "\n" + indent + "}"
        if isinstance(value, list) and any(isinstance(x, (list, dict)) for x in value):
            return "[\n" + ",\n".join(indent + "  " + compact(x) for x in value) + "\n" + indent + "]"
        return compact(value)
    path.write_text(render(payload) + "\n")


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("tests/modules/excel_utilities"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    polynomial = extract_workbook(args.source_dir / "custom_calculation_polynomial.xlsx")["Sheet1"]
    write_compact_fixture(args.output_dir / "custom_calculation_polynomial.json",
                          compact_layback_fixture(polynomial))


if __name__ == "__main__":
    main()
