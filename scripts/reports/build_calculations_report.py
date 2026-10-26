"""Build the calculations report from public examples and actual module calls.

Rebuild from the repository root:
    PYTHONPATH=src python scripts/reports/build_calculations_report.py

Presentation source: the shared calculation report's calc_report_format.html
stylesheet, copied unchanged into calculations_house_style.css. The report uses
no remote fonts, JavaScript libraries, solver or network requests.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from assetutilities.calculations import lifecycle_cost

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DESTINATION = ROOT / "docs/reports/modules/acalculations"

# NIST HB 135e2025 (August 2025), §3.2.1 Eq. (3-6) and §3.2.2.1
# Eq. (3-7): the replacement and recurring-maintenance examples respectively.
# These are teaching-example inputs, not current prescribed discount rates.
REPLACEMENT = 1000
MAINTENANCE = 100
RATE = 0.03
YEARS = 5
NIST_URL = "https://nvlpubs.nist.gov/nistpubs/hb/2025/NIST.HB.135e2025.pdf"

CHANGES = {
    "document": "Calculations module analysis",
    "revision": "A",
    "date": "2026-10-22",
    "status": "Draft for maintainer review",
    "changes": [
        {
            "section": "s3",
            "description": "Present replacement and maintenance costs are combined to show the amount required at the base date.",
            "reason": "Cost timing is made explicit before annual costs are compared.",
        },
        {
            "section": "s6",
            "description": "Published replacement and maintenance examples are calculated separately and then combined as an illustration.",
            "reason": "Published reference cases remain distinguishable from their combined illustration.",
        },
        {
            "section": "s8",
            "description": "Use limits and additional evidence required for structural calculations are stated.",
            "reason": "Arithmetic checks do not establish structural qualification.",
        },
    ],
}


def display(key: str, value: float) -> str:
    """Apply the declared precision without changing any calculation input."""
    if key == "rate_percent":
        return f"{value:.1f}"
    if key == "years" or key.startswith("year_"):
        return str(int(value))
    return f"{value:,.2f}"


def calculate() -> dict[str, float]:
    """Call the public module for every result; retain full precision here."""
    replacement = [0] * YEARS + [REPLACEMENT]
    maintenance = [0] + [MAINTENANCE] * YEARS
    combined = [a + b for a, b in zip(replacement, maintenance)]
    replacement_pv = lifecycle_cost.net_present_value(replacement, RATE)
    maintenance_pv = lifecycle_cost.net_present_value(maintenance, RATE)
    combined_pv = lifecycle_cost.net_present_value(combined, RATE)
    values = {
        "replacement": REPLACEMENT,
        "maintenance": MAINTENANCE,
        "rate_percent": RATE * 100,
        "years": YEARS,
        "replacement_pv": replacement_pv,
        "maintenance_pv": maintenance_pv,
        "combined_pv": combined_pv,
        "annual_cost": lifecycle_cost.annual_equivalent_cost(combined_pv, RATE, YEARS),
        "replacement_annual": lifecycle_cost.annual_equivalent_cost(
            replacement_pv, RATE, YEARS
        ),
        "maintenance_annual": lifecycle_cost.annual_equivalent_cost(
            maintenance_pv, RATE, YEARS
        ),
    }
    for year, cost in enumerate(combined):
        values[f"year_{year}"] = year
        values[f"payment_{year}"] = cost
        isolated = [0] * year + [cost]
        values[f"present_{year}"] = lifecycle_cost.net_present_value(isolated, RATE)
        values[f"cumulative_{year}"] = lifecycle_cost.net_present_value(
            combined[: year + 1], RATE
        )
    return values


def inventory() -> list[dict]:
    """Inventory source files and existing tests without importing other areas."""
    records = []
    for source in sorted((ROOT / "src/assetutilities/calculations").glob("*.py")):
        test = ROOT / "tests/modules/calculations" / f"test_{source.stem}.py"
        tree = (
            ast.parse(test.read_text(encoding="utf-8"))
            if test.exists()
            else ast.Module(body=[], type_ignores=[])
        )
        count = sum(
            isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
        records.append(
            {
                "path": source.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "name": source.stem,
                "tests": count,
            }
        )
    return records


def report_data() -> dict:
    values = calculate()
    # Rounded evidence prevents irrelevant platform last-digit differences.
    rows = [
        {
            "year": year,
            "payment": values[f"payment_{year}"],
            "present_value": round(values[f"present_{year}"], 8),
            "cumulative_pv": round(values[f"cumulative_{year}"], 8),
        }
        for year in range(YEARS + 1)
    ]
    return {
        "revision": CHANGES["revision"],
        "values": {key: round(value, 8) for key, value in values.items()},
        "rows": rows,
        "sources": inventory(),
        "basis": {
            "document": "NIST HB 135e2025",
            "edition": "August 2025",
            "url": NIST_URL,
            "clauses": ["3.2.1", "3.2.2.1", "17.4"],
            "intended_use": "Published-example arithmetic; no project qualification",
            "source_observed": "2026-10-22",
            "units": {"money": "USD", "rate": "annual decimal", "time": "year"},
        },
    }


def render_report() -> str:
    data = report_data()
    values = calculate()
    environment = Environment(
        loader=FileSystemLoader(HERE),
        autoescape=select_autoescape(default=True),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    environment.globals["number"] = lambda key: display(key, values[key])
    html = environment.get_template("calculations_report.html.j2").render(
        data=data,
        changes=CHANGES,
        style=(HERE / "calculations_house_style.css").read_text(encoding="utf-8"),
        nist_url=NIST_URL,
        existing_tests=sum(item["tests"] for item in data["sources"]),
        report_id="0" * 64,
    )
    identity = hashlib.sha256(html.encode("utf-8")).hexdigest()
    return html.replace(
        f"const reportDigest = '{'0' * 64}';", f"const reportDigest = '{identity}';"
    )


def build(destination: Path = DESTINATION) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "report.html").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write(render_report())
    with (destination / "changes.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write(json.dumps(CHANGES, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    build(parser.parse_args().output_dir)
