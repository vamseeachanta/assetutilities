"""Assess declared process evidence against explicit, caller-supplied criteria.

Scope source: issue #37, "Scalability | Process, People"; see
docs/modules/devtools/process-readiness.md for the assessment contract (2026).
References are recorded declarations, never fetched or authenticated here.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any, Sequence


# Issue #37 names these areas; it supplies no numerical acceptance limits.
AREAS = ("sales", "process", "productivity")
STATUSES = ("PASS", "FAIL", "NOT_EVALUATED")


def _object(value: Any, allowed: set[str], required: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    if set(value) - allowed or required - set(value):
        raise ValueError(f"{label} has unknown or missing fields")
    return value


def _text(value: Any, label: str, optional: bool = False) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")


def _number(value: Any, label: str) -> None:
    if type(value) not in (int, float):
        raise ValueError(f"{label} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")


def _unique_records(value: Any, label: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    seen = set()
    for record in value:
        if not isinstance(record, dict):
            raise ValueError(f"{label} entries must be objects")
        identifier = record.get("id")
        _text(identifier, f"{label} identifier")
        if identifier in seen:
            raise ValueError(f"{label} identifiers must be unique")
        seen.add(identifier)
    return value


def _validate(register: Any) -> None:
    _object(register, {"roles", "processes"}, {"roles", "processes"}, "register")
    roles = register["roles"]
    if not isinstance(roles, list):
        raise ValueError("roles must be an array")
    for role in roles:
        _text(role, "role")
    if len(set(roles)) != len(roles):
        raise ValueError("roles must be unique")
    processes = _unique_records(register["processes"], "processes")
    if not processes:
        raise ValueError("processes must not be empty")
    for process in processes:
        _object(
            process,
            {
                "id",
                "area",
                "accountable_role",
                "backup_role",
                "procedure_ref",
                "handoff_ref",
                "metrics",
            },
            {"id", "area"},
            "process",
        )
        _text(process["area"], "area")
        if process["area"] not in AREAS:
            raise ValueError("area must be sales, process or productivity")
        for field in (
            "accountable_role",
            "backup_role",
            "procedure_ref",
            "handoff_ref",
        ):
            _text(process.get(field), field, optional=True)
        for field in ("accountable_role", "backup_role"):
            if process.get(field) is not None and process[field] not in roles:
                raise ValueError("assigned roles must be registered")
        for metric in _unique_records(process.get("metrics", []), "metrics"):
            _object(
                metric,
                {"id", "unit", "value", "evidence_ref", "criterion"},
                {"id", "unit"},
                "metric",
            )
            _text(metric["unit"], "metric unit")
            _text(metric.get("evidence_ref"), "metric evidence", optional=True)
            if metric.get("value") is not None:
                _number(metric["value"], "metric value")
            criterion = metric.get("criterion")
            if criterion is not None:
                _object(
                    criterion,
                    {"operator", "target", "source_ref"},
                    {"operator", "target"},
                    "criterion",
                )
                if criterion["operator"] not in ("at_most", "at_least"):
                    raise ValueError("criterion operator must be at_most or at_least")
                _number(criterion["target"], "criterion target")
                _text(criterion.get("source_ref"), "criterion source", optional=True)


def assess(register: dict) -> dict:
    """Return deterministic findings; malformed input raises ValueError.

    PASS confirms declarations or a supplied inequality only. FAIL takes
    precedence over NOT_EVALUATED, which takes precedence over PASS. Missing
    evidence never passes. Neither input records nor their references are changed.
    """
    _validate(register)
    checks: list[dict] = []

    def add(process, check, status, reason, action=None, **details):
        checks.append(
            {
                "area": process["area"],
                "process_id": process.get("id"),
                "check": check,
                "status": status,
                "reason": reason,
                "action": action,
                **details,
            }
        )

    for process in register["processes"]:
        accountable = process.get("accountable_role")
        backup = process.get("backup_role")
        for field, check in (
            ("accountable_role", "accountability"),
            ("procedure_ref", "procedure"),
            ("handoff_ref", "handoff"),
        ):
            if process.get(field) is None:
                add(
                    process,
                    check,
                    "NOT_EVALUATED",
                    "Declaration missing.",
                    f"Supply {field}.",
                )
            else:
                add(
                    process,
                    check,
                    "PASS",
                    "Declaration supplied.",
                    reference=process[field],
                )
        if accountable is None or backup is None:
            add(
                process,
                "backup",
                "NOT_EVALUATED",
                "Role coverage is incomplete.",
                "Supply accountable_role and backup_role.",
            )
        elif accountable == backup:
            add(
                process,
                "backup",
                "FAIL",
                "Backup repeats the accountable role.",
                "Assign a distinct registered backup role.",
            )
        else:
            add(
                process,
                "backup",
                "PASS",
                "Distinct backup role declared.",
                reference=backup,
            )
        if not process.get("metrics"):
            add(
                process,
                "measurement",
                "NOT_EVALUATED",
                "No measurement declared.",
                "Supply a metric, evidence and a sourced criterion.",
            )
        for metric in process.get("metrics", []):
            criterion = metric.get("criterion")
            missing = []
            if metric.get("value") is None:
                missing.append("value")
            if metric.get("evidence_ref") is None:
                missing.append("evidence_ref")
            if criterion is None:
                missing.append("criterion")
            elif criterion.get("source_ref") is None:
                missing.append("criterion source_ref")
            details = {"measurement": copy.deepcopy(metric)}
            if missing:
                add(
                    process,
                    f"metric:{metric['id']}",
                    "NOT_EVALUATED",
                    "Measurement basis is incomplete.",
                    "Supply " + ", ".join(missing) + ".",
                    **details,
                )
                continue
            # Assessment contract (2026), Measurement criteria: compare directly
            # in the supplied unit; every target and its source are required input.
            if criterion["operator"] == "at_most":
                passed = metric["value"] <= criterion["target"]
            else:
                passed = metric["value"] >= criterion["target"]
            add(
                process,
                f"metric:{metric['id']}",
                "PASS" if passed else "FAIL",
                "Supplied criterion met." if passed else "Supplied criterion not met.",
                None
                if passed
                else "Review the measurement against its cited criterion.",
                **details,
            )

    present = {process["area"] for process in register["processes"]}
    for area in AREAS:
        if area not in present:
            add(
                {"area": area},
                "area_coverage",
                "NOT_EVALUATED",
                "No process declared for this area.",
                "Supply a process for this area.",
            )
    summary = {
        status: sum(c["status"] == status for c in checks) for status in STATUSES
    }
    status = (
        "FAIL"
        if summary["FAIL"]
        else ("NOT_EVALUATED" if summary["NOT_EVALUATED"] else "PASS")
    )
    return {"status": status, "summary": summary, "checks": checks}


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("non-finite JSON number")


def load_register(path: Path) -> dict:
    """Load strict UTF-8 JSON and validate the register before returning it."""
    register = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_invalid_constant,
    )
    _validate(register)
    return register


def main(argv: Sequence[str] | None = None) -> int:
    """CLI contract (2026): exit 0=PASS, 1=non-pass, 2=input error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("register", type=Path, help="UTF-8 JSON process register")
    args = parser.parse_args(argv)
    try:
        report = assess(load_register(args.register))
    except (OSError, UnicodeError, ValueError):
        print(
            "Invalid register: unreadable file or invalid UTF-8, JSON or schema.",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
