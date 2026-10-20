"""Assess supplied hardware evidence without probing or configuring devices.

The field contract is documented in docs/commands/hardware-readiness.md.
All numeric acceptance targets are inputs; none are inferred from device names.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class _Criterion:
    observation: str
    requirement: str | None = None
    comparison: str = "functional"


# Source: issue #36 hardware checklist, as summarized in
# docs/plans/2026-05-05-issue-36-consolidate-hardware.md, Context.
# These are functional evidence fields, not vendor or standards limits.
_CHECKS = {
    "graphics": (_Criterion("functional"),),
    "audio": (_Criterion("playback"),),
    "shared_storage": (
        _Criterion("capacity_bytes", "minimum_capacity_bytes", "minimum"),
        _Criterion("smb_access"),
    ),
    "displays": (_Criterion("simultaneous_count", "minimum_count", "minimum"),),
    "remote_access": (_Criterion("login"), _Criterion("graphical_session")),
    "meeting_audio": (_Criterion("capture"), _Criterion("playback")),
    "wired_network": (
        _Criterion("link"),
        _Criterion("observation_seconds", "minimum_observation_seconds", "window"),
        _Criterion("outages", "maximum_outages", "maximum"),
    ),
    "kvm": (
        _Criterion("switched_computers", "minimum_computers", "minimum"),
        _Criterion("keyboard"),
        _Criterion("mouse"),
        _Criterion("video"),
    ),
}


def _validate(document: Any) -> None:
    """Validate the closed input contract without echoing arbitrary input."""
    if not isinstance(document, dict):
        raise TypeError("Readiness input must be an object")
    if document.keys() - {"requirements", "observations"}:
        raise ValueError("Unknown input section")
    for section, areas in document.items():
        if not isinstance(areas, dict):
            raise TypeError("Input sections must be objects")
        allowed_areas = {
            area
            for area, criteria in _CHECKS.items()
            if section == "observations" or any(c.requirement for c in criteria)
        }
        if areas.keys() - allowed_areas:
            raise ValueError("Unknown checklist area")
        for area, fields in areas.items():
            if not isinstance(fields, dict):
                raise TypeError("Checklist areas must be objects")
            criteria = {
                (c.observation if section == "observations" else c.requirement): c
                for c in _CHECKS[area]
                if section == "observations" or c.requirement is not None
            }
            if fields.keys() - criteria.keys():
                raise ValueError("Unknown checklist field")
            for field, value in fields.items():
                criterion = criteria[field]
                if section == "observations" and criterion.requirement is None:
                    if not isinstance(value, bool):
                        raise TypeError("Functional observations must be booleans")
                else:
                    # Counts, elapsed seconds and byte capacities are nonnegative
                    # integers by definition (input contract, not a device limit).
                    if not isinstance(value, int) or isinstance(value, bool):
                        raise TypeError("Measurements and targets must be integers")
                    if value < 0:
                        raise ValueError(
                            "Measurements and targets must be nonnegative integers"
                        )
                    if (
                        section == "requirements"
                        and criterion.comparison != "maximum"
                        and value == 0
                    ):
                        raise ValueError("Minimum targets must be positive")


def _status(failed: list, missing: list, insufficient: list) -> str:
    if failed:
        return "FAIL"
    if missing or insufficient:
        return "NOT_EVALUATED"
    return "PASS"


def assess_readiness(document: dict) -> dict:
    """Return all checklist results; missing targets or evidence cannot pass.

    FAIL takes precedence over NOT_EVALUATED, including when the same area has
    both a failed observation and missing evidence. A short network observation
    window is insufficient evidence, rather than proof of a hardware failure.
    """
    _validate(document)
    checks = []
    for area, criteria in _CHECKS.items():
        observations = document.get("observations", {}).get(area, {})
        requirements = document.get("requirements", {}).get(area, {})
        missing, failed, insufficient = [], [], []
        for criterion in criteria:
            observation_path = f"observations.{area}.{criterion.observation}"
            observation_present = criterion.observation in observations
            if not observation_present:
                missing.append(observation_path)
            requirement_present = (
                criterion.requirement is None or criterion.requirement in requirements
            )
            if not requirement_present:
                missing.append(f"requirements.{area}.{criterion.requirement}")
            if not observation_present or not requirement_present:
                continue
            actual = observations[criterion.observation]
            if criterion.requirement is None:
                if not actual:
                    failed.append(observation_path)
                continue
            target = requirements[criterion.requirement]
            if criterion.comparison == "window":
                if actual < target:
                    insufficient.append(observation_path)
            elif criterion.comparison == "minimum":
                if actual < target:
                    failed.append(observation_path)
            elif actual > target:
                failed.append(observation_path)
        checks.append(
            {
                "id": area,
                "status": _status(failed, missing, insufficient),
                "failed": failed,
                "missing": missing,
                "insufficient": insufficient,
            }
        )
    return {
        "status": _status(
            [c for c in checks if c["status"] == "FAIL"],
            [c for c in checks if c["status"] == "NOT_EVALUATED"],
            [],
        ),
        "checks": checks,
    }


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate input field")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("Non-finite JSON numbers are invalid")


def main(argv: Sequence[str] | None = None) -> int:
    """Read one JSON document and emit a report to standard output."""
    parser = argparse.ArgumentParser(prog="hardware-readiness", description=__doc__)
    parser.add_argument("input", type=Path, help="JSON observations and requirements")
    args = parser.parse_args(argv)
    try:
        with args.input.open(encoding="utf-8") as stream:
            document = json.load(
                stream,
                object_pairs_hook=_unique_fields,
                parse_constant=_reject_constant,
            )
        report = assess_readiness(document)
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        # Input contents and file locations can contain private information.
        parser.error(
            "Cannot assess input: provide a readable JSON file matching the field contract"
        )
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    # Command protocol defined in docs/commands/hardware-readiness.md.
    return {"PASS": 0, "FAIL": 1, "NOT_EVALUATED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
