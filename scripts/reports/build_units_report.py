"""Build the units analysis using documented inputs and actual module calls.

Rebuild: uv run python scripts/reports/build_units_report.py
The vendored stylesheet is the unchanged style block from the shared
digitalmodel:src/digitalmodel/reporting/assets/calc_report_format.html.
No source document is executed and no network or solver is accessed.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from importlib.metadata import version
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from assetutilities.units import CalculationAuditLog, TrackedQuantity

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DESTINATION = ROOT / "docs/reports/modules/aunits"
CALCULATION_SOURCES = (
    "src/assetutilities/units/quantity.py",
    "src/assetutilities/units/registry.py",
    "src/assetutilities/units/traceability.py",
)
CHANGES = {
    "document": "Units module analysis",
    "revision": "A",
    "date": "2026-10-22",
    "changes": [
        {
            "section": "3 and 6",
            "change": "The pressure–area example is expressed as force with explicit output units.",
            "reason": "The numerical result is separated from any allowable load or net-force assessment.",
        },
        {
            "section": "7 and Appendix A",
            "change": "Input handling, custom energy definitions and provenance limits are stated.",
            "reason": "Use of conversion results is bounded by the available physical basis.",
        },
    ],
}


def guide_input(variable: str, unit: str) -> float:
    """Read a literal teaching input without executing documentation examples."""
    guide = (ROOT / "docs/units-guide.md").read_text(encoding="utf-8")
    for block in re.findall(r"```python\n(.*?)```", guide, re.S):
        for statement in ast.parse(block).body:
            if not isinstance(statement, ast.Assign):
                continue
            if not any(
                isinstance(t, ast.Name) and t.id == variable for t in statement.targets
            ):
                continue
            for node in ast.walk(statement.value):
                if not isinstance(node, ast.Call) or not isinstance(
                    node.func, ast.Name
                ):
                    continue
                if node.func.id != "TrackedQuantity" or len(node.args) < 2:
                    continue
                if ast.literal_eval(node.args[1]) == unit:
                    return float(ast.literal_eval(node.args[0]))
    raise ValueError(
        f"Documented {variable} input in {unit} missing; review the example basis"
    )


def without_timestamps(value):
    """Keep operation/source/unit evidence without volatile clock fields."""
    if isinstance(value, dict):
        return {
            key: without_timestamps(item)
            for key, item in value.items()
            if key != "timestamp"
        }
    if isinstance(value, list):
        return [without_timestamps(item) for item in value]
    return value


def calculate() -> dict:
    pressure = TrackedQuantity(
        guide_input("pressure", "kPa"), "kPa", source="Public guide: Quick Start"
    )
    area = TrackedQuantity(
        guide_input("force", "m**2"), "m**2", source="Public guide: Quick Start"
    )
    thickness = TrackedQuantity(
        guide_input("thickness", "mm"), "mm", source="Public guide: TrackedQuantity"
    )
    force = (pressure.to("Pa") * area).to("kN")
    audit = CalculationAuditLog()
    audit.add_input("pressure", pressure)
    audit.add_input("area", area)
    audit.add_step(
        "Convert pressure to pascals, multiply by area, convert force to kilonewtons."
    )
    audit.add_output("force", force)
    values = {
        "pressure_kpa": pressure.magnitude,
        "area_m2": area.magnitude,
        "pressure_pa": pressure.to("Pa").magnitude,
        "force_n": force.to("N").magnitude,
        "force_kn": force.magnitude,
        "thickness_mm": thickness.magnitude,
        "thickness_m": thickness.to("m").magnitude,
    }
    curve = []
    # Illustrative sampling only: endpoints and three equally spaced interior areas.
    for index in range(5):
        sample_area = area * (index / 4)
        curve.append(
            {
                "area_m2": round(sample_area.magnitude, 4),
                "force_kn": round((pressure * sample_area).to("kN").magnitude, 4),
            }
        )
    return {
        "values": values,
        "curve": curve,
        "audit": without_timestamps(audit.to_dict()),
        "source_digests": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in CALCULATION_SOURCES
        },
        "versions": {name: version(name) for name in ("pint", "numpy")},
    }


def display_values(data: dict) -> dict[str, str]:
    precision = {
        "pressure_kpa": ".3f",
        "area_m2": ".1f",
        "pressure_pa": ".0f",
        "force_n": ".0f",
        "force_kn": ".1f",
        "thickness_mm": ".1f",
        "thickness_m": ".3f",
    }
    return {key: format(value, precision[key]) for key, value in data["values"].items()}


def render_report() -> str:
    data = calculate()
    display = display_values(data)
    environment = Environment(
        loader=FileSystemLoader(HERE, encoding="utf-8"),
        autoescape=select_autoescape(default=True),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    return environment.get_template("units_report.html.j2").render(
        data=data,
        display=display,
        style=(HERE / "units_house_style.css").read_text(encoding="utf-8"),
        changes=CHANGES,
    )


def build(destination: Path = DESTINATION) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "units-report.html").write_text(
        render_report(), encoding="utf-8", newline="\n"
    )
    (destination / "changes.json").write_text(
        json.dumps(CHANGES, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DESTINATION)
    build(parser.parse_args().output_dir)
