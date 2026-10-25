"""Read-only Compound Engineering trial recommendation; see issues #81 and #86.

This checks an explicitly supplied assessment, not plugin output or approval.
It cannot enable skills, install a plugin, edit repositories or publish a PR.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

# Issue #84 (2026), "Skills to run": all advisory evaluations are required.
ADVISORY_SKILLS = (
    "ce-code-review",
    "ce-debug",
    "ce-simplify-code",
    "ce-doc-review",
)
# Issue #85 (2026), "Steps": loop review has a separate assessment, not a new skill.
PIPELINE_SKILLS = ("ce-plan", "ce-work", "ce-code-review", "ce-compound")
PIPELINE_ASSESSMENTS = ("ce-plan", "ce-work", "ce-code-review-loop", "ce-compound")
PREREQUISITES = ("install", "worktree")
STATUSES = {"PASS", "FAIL", "NOT_EVALUATED"}


def _records(value: object, names: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != names:
        raise ValueError("Assessment names must match the documented trial.")
    for record in value.values():
        if not isinstance(record, dict) or set(record) != {
            "status",
            "evidence",
            "reason",
        }:
            raise ValueError("Each assessment needs status, evidence and reason.")
        status = record["status"]
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("Unknown assessment status.")
        if not isinstance(record["reason"], str) or not record["reason"].strip():
            raise ValueError("Each assessment needs a substantive reason.")
        evidence = record["evidence"]
        if not isinstance(evidence, list) or any(
            not isinstance(ref, str) or not ref.strip() for ref in evidence
        ):
            raise ValueError("Evidence must be a list of substantive references.")
        if status != "NOT_EVALUATED" and not evidence:
            raise ValueError("An observed result requires evidence references.")
    return value


def assess(evidence: object) -> dict:
    """Derive a recommendation without treating a claim as authorization.

    Issues #81 and #86 (2026), "Success criteria" and "Acceptance criteria",
    require installation/isolation evidence, advisory findings and loop output.
    The conservative mapping here is a proposed decision rule: full adoption
    requires all trial assessments to PASS; partial adoption keeps only passing
    advisory skills after the prerequisites PASS. Missing evidence blocks use.
    No numerical score, coefficient or acceptance threshold is assumed.
    """
    if not isinstance(evidence, dict) or set(evidence) != {
        "prerequisites",
        "skills",
    }:
        raise ValueError("Trial evidence needs prerequisites and skills.")
    prerequisites = _records(evidence["prerequisites"], set(PREREQUISITES))
    skills = _records(
        evidence["skills"], set(ADVISORY_SKILLS) | set(PIPELINE_ASSESSMENTS)
    )
    records = {**prerequisites, **skills}
    failed = sorted(name for name, item in records.items() if item["status"] == "FAIL")
    unknown = sorted(
        name for name, item in records.items() if item["status"] == "NOT_EVALUATED"
    )
    ready = all(item["status"] == "PASS" for item in prerequisites.values())
    keep = []
    verdict, mode = "drop", "none"
    if ready:
        keep = sorted(
            name for name in ADVISORY_SKILLS if skills[name]["status"] == "PASS"
        )
        if all(item["status"] == "PASS" for item in skills.values()):
            keep = sorted(set(ADVISORY_SKILLS) | set(PIPELINE_SKILLS))
            verdict, mode = "adopt", "full"
        elif keep:
            verdict, mode = "adopt-partial", "advisory"
    return {
        "verdict": verdict,
        "mode": mode,
        "keep": keep,
        "failed": failed,
        "not_evaluated": unknown,
    }


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate evidence field.")
        result[key] = value
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Print a JSON recommendation; valid no-go results are successful reads."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="Reviewed trial assessment JSON")
    args = parser.parse_args(argv)
    try:
        evidence = json.loads(
            args.evidence.read_text(encoding="utf-8").removeprefix("\ufeff"),
            object_pairs_hook=_unique_object,
        )
        result = assess(evidence)
    except (OSError, ValueError, RecursionError):
        # Do not echo input data or filesystem details into public logs.
        sys.stderr.write(
            "Invalid trial evidence. Supply the documented evidence format.\n"
        )
        return 2
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
