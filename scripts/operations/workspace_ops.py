#!/usr/bin/env python3
"""Read-only workspace inventory and evidence assessment for issue #122.

This is an operations script, independent of the installed library. Requirements
are derived from #122 and the child issues cited in REQUIREMENTS (2026 snapshot).
No retirement, retention or freshness threshold is inferred. Evidence expiry is
supplied by the maintainer. Evidence references are assertions, not authenticated
proof of installation, data integrity or access.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Sequence

# Issue numbers identify sources, not numerical acceptance limits.
REQUIREMENTS = {
    "repositories": (
        35,
        "Record repository and branch inventory, issue destinations, "
        "and reviewed consolidation decisions.",
    ),
    "data": (
        33,
        "Reference the existing data catalog, authoritative storage, "
        "access test and a successful restore or integrity check.",
    ),
    "hardware": (
        36,
        "Record reproducible setup and checks for shared hardware, "
        "network, displays, audio and authorized remote access.",
    ),
    "agents": (
        30,
        "Reference versioned agent configuration and evidence of "
        "its use in a normal workflow.",
    ),
    "meetings": (
        56,
        "Record an authorized capture, transcript and reviewed "
        "summary workflow, including consent and retention.",
    ),
    "knowledge": (
        38,
        "Record the selected knowledge tool, installation checks "
        "and a repeatable capture and retrieval routine.",
    ),
    "email": (
        39,
        "Record scheduled retention and a dry run demonstrating that "
        "starred and important messages remain protected.",
    ),
    "onboarding": (
        42,
        "Record tool, repository access, environment and hardware "
        "checks completed by a new team member.",
    ),
    "process": (
        37,
        "Reference a repeatable onboarding checklist, responsibilities "
        "and an independently completed handoff.",
    ),
    "marketing": (
        40,
        "Record responsibility and a cadence for public channels "
        "and website maintenance.",
    ),
}
STATUSES = ("PASS", "FAIL", "NOT_EVALUATED")
RECORD_FIELDS = {
    "state",
    "responsible_role",
    "evidence_ref",
    "observed_on",
    "valid_until",
    "next_action",
}


def inventory(roots: Sequence[Path]) -> dict:
    """List Git markers at explicit roots and their immediate children only.

    Both checkout directories and worktree/submodule marker files are candidates.
    Markers are not opened, and their contents or Git health are not verified.
    Child and marker symlinks are excluded. Overlapping roots are deduplicated.
    """
    repositories = []
    seen = set()
    for root_index, root in enumerate(roots):
        try:
            root = Path(root).resolve()
        except (OSError, RuntimeError):
            raise ValueError("inventory root cannot be resolved") from None
        if not root.is_dir():
            raise ValueError("inventory root is unavailable or is not a directory")
        children = sorted(root.iterdir(), key=lambda path: path.name)
        for candidate in [root, *children]:
            if candidate.is_symlink() or not candidate.is_dir() or candidate in seen:
                continue
            marker = candidate / ".git"
            if marker.is_symlink():
                continue
            if marker.is_dir():
                kind = "directory"
            elif marker.is_file():
                kind = "file"
            else:
                continue
            seen.add(candidate)
            repositories.append(
                {
                    "root_index": root_index,
                    "path": candidate.relative_to(root).as_posix(),
                    "marker": kind,
                }
            )
    return {
        "repositories": repositories,
        "coverage": "Explicit roots and immediate children; Git markers only. "
        "Nested repositories, Git health, branches and data are not verified.",
    }


def _date(value: object, field: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"invalid {field}: expected an ISO calendar date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid {field}: expected an ISO calendar date") from None


def _evaluate(record: dict, as_of: date) -> tuple[str, str]:
    if not isinstance(record, dict) or record.keys() - RECORD_FIELDS:
        raise ValueError("invalid record fields")
    if any(not isinstance(value, str) for value in record.values()):
        raise ValueError("invalid record value: expected text")
    state = record.get("state", "")
    if state not in {"", "complete", "pending", "blocked"}:
        raise ValueError("invalid state: expected complete, pending or blocked")
    observed = (
        _date(record["observed_on"], "observed_on")
        if record.get("observed_on")
        else None
    )
    expiry = (
        _date(record["valid_until"], "valid_until")
        if record.get("valid_until")
        else None
    )
    if observed and observed > as_of:
        raise ValueError("invalid observed_on: later than as_of")
    if observed and expiry and expiry < observed:
        raise ValueError("invalid valid_until: earlier than observed_on")
    if state in {"pending", "blocked"}:
        return "FAIL", f"Work is {state}; completion is not established."
    if not state:
        return "NOT_EVALUATED", "No state has been recorded."
    required = ("responsible_role", "evidence_ref", "observed_on", "valid_until")
    missing = [field for field in required if not record.get(field, "").strip()]
    if missing:
        return "NOT_EVALUATED", "Missing " + ", ".join(missing) + "."
    # valid_until is an exclusive, caller-supplied calendar date; no default age.
    if expiry <= as_of:
        return "NOT_EVALUATED", "Evidence review has expired."
    return (
        "PASS",
        "Current completion evidence is recorded; independent review is required.",
    )


def assess(manifest: dict) -> dict:
    """Evaluate every child requirement, including those omitted from the input."""
    if not isinstance(manifest, dict) or manifest.keys() - {"as_of", "records"}:
        raise ValueError("invalid manifest fields")
    as_of = _date(manifest.get("as_of"), "as_of")
    records = manifest.get("records", {})
    if not isinstance(records, dict) or records.keys() - REQUIREMENTS.keys():
        raise ValueError("invalid records: expected known requirement identifiers")
    checks = []
    actions = []
    for identifier, (issue, criterion) in REQUIREMENTS.items():
        record = records.get(identifier, {})
        status, reason = _evaluate(record, as_of)
        check = {
            "id": identifier,
            "issue": issue,
            "status": status,
            "reason": reason,
            "criterion": criterion,
            "responsible_role": record.get("responsible_role", "").strip()
            or "unassigned",
            "evidence_ref": record.get("evidence_ref", "").strip(),
            "observed_on": record.get("observed_on", ""),
            "valid_until": record.get("valid_until", ""),
        }
        checks.append(check)
        if status != "PASS":
            actions.append(
                {
                    "id": identifier,
                    "issue": issue,
                    "status": status,
                    "responsible_role": check["responsible_role"],
                    "next_action": record.get("next_action", "").strip() or criterion,
                }
            )
    # Counts are cardinalities, with FAIL taking precedence over missing evidence.
    summary = {
        status: sum(check["status"] == status for check in checks)
        for status in STATUSES
    }
    overall = (
        "FAIL"
        if summary["FAIL"]
        else ("NOT_EVALUATED" if summary["NOT_EVALUATED"] else "PASS")
    )
    return {
        "as_of": as_of.isoformat(),
        "overall": overall,
        "summary": summary,
        "checks": checks,
        "actions": actions,
    }


def _cell(value: object) -> str:
    text = html.escape(" ".join(str(value).split()))
    return re.sub(r"([\\`*_{}\[\]()!|])", r"\\\1", text)


def render_markdown(report: dict) -> str:
    """Render a snapshot with escaped table text."""
    lines = [
        "# Workspace operations assessment",
        "",
        "## Summary",
        "",
        f"As of {report['as_of']}: **{report['overall']}**.",
        "",
        "; ".join(f"{status}: {report['summary'][status]}" for status in STATUSES)
        + ".",
        "",
        "## Revision history",
        "",
        "| Revision | Date | Change and reason |",
        "|---|---|---|",
        f"| Initial | {report['as_of']} | Evidence snapshot for operations review. |",
        "",
        "## Checks",
        "",
        "| Requirement | Source | Status | Responsible role | Evidence | Review dates | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for check in report["checks"]:
        cells = (
            check["id"],
            f"#{check['issue']}",
            check["status"],
            check["responsible_role"],
            check["evidence_ref"],
            f"{check['observed_on']} / {check['valid_until']}",
            check["reason"],
        )
        lines.append("| " + " | ".join(map(_cell, cells)) + " |")
    lines += [
        "",
        "## Actions",
        "",
        "| Requirement | Responsible role | Next action |",
        "|---|---|---|",
    ]
    for action in report["actions"]:
        cells = (action["id"], action["responsible_role"], action["next_action"])
        lines.append("| " + " | ".join(map(_cell, cells)) + " |")
    if not report["actions"]:
        lines.append(
            "| All requirements | maintainer | Independently review the evidence. |"
        )
    lines += [
        "",
        "## Limits",
        "",
        "This snapshot evaluates supplied records. It does not authenticate evidence, "
        "check external services, migrate data, change access or remove repositories.",
        "Each generated snapshot is a new document. Preserve earlier snapshots and "
        "append a revision row when reissuing a retained report.",
        "",
    ]
    return "\n".join(lines)


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("invalid JSON: duplicate object key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("invalid JSON: non-finite value")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory_parser = commands.add_parser(
        "inventory", help="List local Git marker candidates"
    )
    inventory_parser.add_argument("roots", type=Path, nargs="+")
    assess_parser = commands.add_parser(
        "assess", help="Assess an operations evidence record"
    )
    assess_parser.add_argument("manifest", type=Path)
    assess_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        if args.command == "inventory":
            print(json.dumps(inventory(args.roots), indent=2))
            return 0
        with args.manifest.open(encoding="utf-8") as stream:
            manifest = json.load(
                stream,
                object_pairs_hook=_unique_object,
                parse_constant=_invalid_constant,
            )
        report = assess(manifest)
    except (OSError, UnicodeError):
        parser.exit(
            2, "error: invalid or unreadable input; inspect the local input file.\n"
        )
    except ValueError:
        # Do not echo input values, private paths or JSON parser excerpts.
        parser.exit(
            2, "error: invalid operations input; check the documented schema.\n"
        )
    if args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
