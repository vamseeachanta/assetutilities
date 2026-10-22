"""Build the constants module report using public inputs and module calls.

Rebuild: python scripts/reports/build_constants_report.py
Only the standard library and this repository's constants module are required.
The stylesheet is reused unchanged from the existing units report exemplar.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DESTINATION = ROOT / "docs/reports/modules/aconstants"
sys.path.insert(0, str(ROOT / "src"))

from assetutilities.constants import conversions  # noqa: E402

TEST_FILES = (
    "tests/unit/test_constants.py",
    "tests/unit/test_seawater.py",
    "tests/unit/test_materials.py",
    "tests/test_casing_grades.py",
)
TEST_AREAS = (
    "Constants and conversions",
    "Seawater properties",
    "Steel records",
    "Casing records and shared geometry",
)
CHANGES = {
    "document": "Constants module analysis",
    "revision": "A",
    "date": "2026-10-22",
    "changes": [
        {
            "section": "4 and 6",
            "change": "The public length example is calculated through the conversion interface.",
            "reason": "Numerical conversion is distinguished from measurement precision.",
        },
        {
            "section": "8 and 10",
            "change": "Grade consistency, seawater scope and missing input checks are identified.",
            "reason": "Conversion evidence does not establish a material or environmental design basis.",
        },
    ],
}


def basis() -> dict:
    return json.loads((DESTINATION / "source-basis.json").read_text(encoding="utf-8"))


def calculate() -> dict:
    source = basis()
    length_ft = source["example"]["length_ft"]
    inch = source["supplementary_cases"]["inch"]
    bar = source["supplementary_cases"]["bar"]
    length_m = conversions.ft_to_m(length_ft)
    inventory = {}
    for name in TEST_FILES:
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        inventory[name] = sum(
            isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return {
        "inputs": {"length_ft": length_ft, "inch": inch, "bar": bar},
        "values": {
            "length_m": length_m,
            "length_mm": conversions.inch_to_mm(inch),
            "pressure_mpa": conversions.bar_to_mpa(bar),
            "returned_ft": conversions.m_to_ft(length_m),
        },
        "curve": [
            {
                "ft": length_ft * i / 6,
                "m": round(conversions.ft_to_m(length_ft * i / 6), 10),
            }
            for i in range(7)
        ],
        "source_digests": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted((ROOT / "src/assetutilities/constants").glob("*.py"))
        },
        "test_inventory": inventory,
    }


def number(key: str, value: float, places: int) -> str:
    displayed = f"{value:.{places}f}"
    return f'<span data-number="{key}" data-value="{displayed}">{displayed}</span>'


def render() -> str:
    data = calculate()
    source = basis()
    evidence = json.loads((DESTINATION / "checks.json").read_text(encoding="utf-8"))
    if evidence["existing_selection"]["passed"] != sum(data["test_inventory"].values()):
        raise ValueError(
            "Test inventory changed; rerun the recorded selection and rebuild with "
            "python scripts/reports/build_constants_report.py"
        )
    values = {**data["inputs"], **data["values"]}
    substitutions = {
        "STYLE": (HERE / "constants_house_style.css").read_text(encoding="utf-8"),
        "DATA": json.dumps(
            {
                **data,
                "values": {
                    key: round(value, 10) for key, value in data["values"].items()
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        "CHANGES": json.dumps(CHANGES, ensure_ascii=False, sort_keys=True),
        "SOURCE_URL": escape(source["url"], quote=True),
        "FOOT_FACTOR": str(source["definitions"]["metres_per_foot"]["value"]),
        "ROUNDED_M": number("length_m", data["values"]["length_m"], 1),
        "INVENTORY": "\n".join(
            f"<tr><td>{escape(area)}</td><td>{count}</td>"
            '<td>Test definitions; records in <a href="#repository-records">Section 9.2</a>.</td></tr>'
            for area, count in zip(TEST_AREAS, data["test_inventory"].values())
        ),
        "TEST_TOTAL": str(sum(data["test_inventory"].values())),
        "DIGESTS": "\n".join(
            f"<li><code>{escape(path)}</code>: <code>{digest}</code></li>"
            for path, digest in data["source_digests"].items()
        ),
        "SOURCE_REGISTER": "\n".join(
            f"<tr><td>{escape(name.replace('_', ' '))}</td><td>{item['value']}</td>"
            f"<td>Reference 1, {escape(item['locator'])}.</td></tr>"
            for name, item in source["definitions"].items()
        ),
    }
    for key, places in {
        "length_ft": 0,
        "inch": 0,
        "bar": 0,
        "length_m": 4,
        "length_mm": 1,
        "pressure_mpa": 1,
        "returned_ft": 0,
    }.items():
        substitutions[key.upper()] = number(key, values[key], places)
    dots = []
    for point in data["curve"]:
        x = round(80 + 560 * point["ft"] / values["length_ft"], 3)
        y = round(280 - 220 * point["m"] / values["length_m"], 3)
        label = (
            f"Length illustration; measured span; input {point['ft']:g} ft; "
            f"demand {point['m']:.4f} m; limit not applicable; unit conversion only."
        )
        dots.append(
            f'<circle cx="{x}" cy="{y}" r="7" tabindex="0" '
            f'data-detail="{escape(label, quote=True)}"><title>{label}</title></circle>'
        )
    substitutions["POINTS"] = "\n".join(dots)
    substitutions["CURVE"] = " ".join(
        f"{round(80 + 560 * p['ft'] / values['length_ft'], 3)},"
        f"{round(280 - 220 * p['m'] / values['length_m'], 3)}"
        for p in data["curve"]
    )
    substitutions["CHANGES_LIST"] = "\n".join(
        f"<li>Sections {escape(item['section'])}: {escape(item['change'])} "
        f"{escape(item['reason'])}</li>"
        for item in CHANGES["changes"]
    )
    return Template(
        (HERE / "constants_report.html").read_text(encoding="utf-8")
    ).substitute(substitutions)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "report.html").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(render())
    with (args.output_dir / "changes.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(json.dumps(CHANGES, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
