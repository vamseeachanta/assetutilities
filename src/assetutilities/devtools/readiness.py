"""Assess explicitly supplied onboarding evidence without changing the system.

Checklist scope: issue #42 and the remaining-work inventory in the repository's
issue-42 plan. This is operator attestation, not automatic certification.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    """A stable evidence key and the exercise needed to establish readiness."""

    key: str
    next_step: str


# Issue #42 supplies the checklist; no numerical hardware limits are inferred.
CHECKLIST = (
    Check(
        "repository_access", "Confirm the intended repository can be cloned and opened."
    ),
    Check("github_access", "Confirm authorized sign-in and contribution access."),
    Check("git", "Confirm Git is installed and a local practice commit succeeds."),
    Check(
        "daily_git_cycle", "Agree and rehearse the daily Git workflow; see issue #19."
    ),
    Check(
        "autocad", "Manually confirm installation, licence access and a sample task."
    ),
    Check("freecad", "Open and save a neutral practice model with FreeCAD."),
    Check(
        "blender_access",
        "Check version-specific Blender requirements and a sample task locally, "
        "or demonstrate authorized remote access and the same task.",
    ),
    Check("audio", "Confirm earphones and microphone work in a test call."),
    Check("meeting_access", "Join a test meeting and confirm audio controls."),
    Check("meeting_scheduling", "Demonstrate independent meeting scheduling."),
    Check("python", "Run a neutral Python exercise in the intended environment."),
    Check("conda", "Confirm the intended conda environment can be activated."),
    Check(
        "python_exercise",
        "Obtain a maintainer-assigned Python task and record its result.",
    ),
    Check("notepad_plus_plus", "Open, edit and save a practice file in Notepad++."),
    Check("vscode", "Open the intended workspace and edit a practice file in VS Code."),
)

# These aliases are discovery hints, not an exhaustive installation inventory.
COMMANDS = {
    "git": ("git",),
    "python": ("python3", "python"),
    "conda": ("conda",),
    "freecad": ("FreeCAD", "freecad"),
    "blender": ("blender",),
    "vscode": ("code",),
    "notepad_plus_plus": ("notepad++",),
}


def evidence_template() -> dict:
    """Return unassessed records; omissions and explicit nulls are equivalent."""
    return {item.key: {"ready": None, "basis": ""} for item in CHECKLIST}


def assess_readiness(evidence: dict) -> dict:
    """Reduce supplied evidence using the documented three-state truth table.

    A true/false observation requires a nonblank basis. Missing/null observations
    remain NOT_EVALUATED. A failed check takes precedence over unknown checks;
    READY requires every check to be true. No score or acceptance limit is used.
    Input values and basis text are deliberately omitted from the output.
    """
    keys = {item.key for item in CHECKLIST}
    if not isinstance(evidence, dict) or evidence.keys() - keys:
        raise ValueError("Evidence must contain only known checklist keys.")
    checks = []
    for item in CHECKLIST:
        record = evidence.get(item.key, {"ready": None})
        if (
            not isinstance(record, dict)
            or record.keys() - {"ready", "basis"}
            or "ready" not in record
        ):
            raise ValueError("Each observation requires ready and an optional basis.")
        ready = record["ready"]
        basis = record.get("basis", "")
        if ready is not None and not isinstance(ready, bool):
            raise ValueError("Readiness must be true, false or null.")
        if not isinstance(basis, str) or (ready is not None and not basis.strip()):
            raise ValueError("Evaluated observations require a nonblank basis.")
        status = (
            "NOT_EVALUATED"
            if ready is None
            else "READY"
            if ready
            else "ACTION_REQUIRED"
        )
        checks.append(
            {
                "key": item.key,
                "status": status,
                "next_step": None if ready is True else item.next_step,
            }
        )
    states = {item["status"] for item in checks}
    overall = (
        "ACTION_REQUIRED"
        if "ACTION_REQUIRED" in states
        else "NOT_EVALUATED"
        if "NOT_EVALUATED" in states
        else "READY"
    )
    return {"status": overall, "checks": checks}


def discover_commands() -> dict[str, bool]:
    """Return PATH presence only, without running tools or exposing their paths.

    Source: Python 3.14 Library Reference, shutil.which (accessed 2026-10-20).
    Lookup uses PATH and Windows PATHEXT; presence does not establish function.
    https://docs.python.org/3.14/library/shutil.html#shutil.which
    """
    return {
        key: any(shutil.which(alias) is not None for alias in aliases)
        for key, aliases in COMMANDS.items()
    }


def _unique_object(pairs: list[tuple]) -> dict:
    """Reject ambiguous JSON rather than silently accepting duplicate evidence."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate evidence key.")
        result[key] = value
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Write a JSON template or assessment; errors omit input paths and values."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--input", type=Path, help="Private JSON evidence file")
    mode.add_argument(
        "--template", action="store_true", help="Print blank evidence JSON"
    )
    parser.add_argument(
        "--discover", action="store_true", help="Also inspect command PATH"
    )
    parser.add_argument(
        "--require-ready", action="store_true", help="Fail unless all checks are ready"
    )
    args = parser.parse_args(argv)
    if args.template:
        if args.discover or args.require_ready:
            parser.error("Template mode cannot assess or discover readiness.")
        print(json.dumps(evidence_template(), indent=2))
        return 0  # Successful CLI execution; not a readiness score.
    try:
        evidence = (
            json.loads(
                args.input.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
            )
            if args.input
            else {}
        )
        report = assess_readiness(evidence)
    except (OSError, ValueError):
        parser.error(
            "Cannot assess evidence: provide readable JSON with valid checklist observations."
        )
    if args.discover:
        report["commands_on_path"] = discover_commands()
    print(json.dumps(report, indent=2))
    return int(args.require_ready and report["status"] != "READY")


if __name__ == "__main__":
    raise SystemExit(main())
