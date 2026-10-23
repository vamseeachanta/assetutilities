#!/usr/bin/env python3
"""Summarize recorded trial evidence; never execute or install a plugin."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

# Source: trial epic, "Success criteria (the go/no-go gate)":
# https://github.com/vamseeachanta/assetutilities/issues/81
CRITERIA = (
    "install_clean",
    "advisory_value",
    "plan_work",
    "compound_capture",
    "rollout_recommendation",
)
STATUSES = ("PASS", "FAIL", "NOT_EVALUATED")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_keys(value, keys):
    require(isinstance(value, dict), "expected an object")
    require(set(value) == set(keys), "missing or unknown fields")


def require_text(value):
    require(isinstance(value, str) and bool(value.strip()), "expected nonempty text")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("non-finite JSON number")


def verify_evidence(evidence, root):
    """Require the original evidence bytes to remain available locally."""
    require(isinstance(evidence, list), "evidence must be an array")
    seen = set()
    for item in evidence:
        require_keys(item, ("path", "sha256"))
        relative = item["path"]
        require_text(relative)
        path = PurePosixPath(relative)
        require(
            not path.is_absolute()
            and not PureWindowsPath(relative).drive
            and "\\" not in relative
            and all(part not in {"", ".", ".."} for part in relative.split("/")),
            "evidence paths must be relative without traversal",
        )
        require(relative not in seen, "duplicate evidence path")
        seen.add(relative)
        require(
            isinstance(item["sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None,
            "expected a lowercase SHA-256 digest",
        )
        artifact = (root / relative).resolve()
        require(root in artifact.parents, "evidence path escapes root")
        require(artifact.is_file(), "evidence must be a regular file")
        with artifact.open("rb") as stream:
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(65536), b""):
                digest.update(block)
        if digest.hexdigest() != item["sha256"]:
            raise ValueError("evidence digest mismatch")


def evaluate(record, root):
    """Summarize observations without conferring adoption authority."""
    require_keys(record, ("schema_version", "plugin", "criteria"))
    # Version of this local record format; unrelated to the plugin release.
    require(
        isinstance(record["schema_version"], int)
        and not isinstance(record["schema_version"], bool)
        and record["schema_version"] == 1,
        "unsupported schema version",
    )
    require_keys(record["plugin"], ("version", "revision"))
    require_text(record["plugin"]["version"])
    revision = record["plugin"]["revision"]
    require(
        revision is None
        or (isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision)),
        "plugin revision must be a full lowercase Git commit ID or null",
    )
    require_keys(record["criteria"], CRITERIA)
    root = root.resolve()
    require(root.is_dir(), "evidence root must be a directory")
    counts = {status: 0 for status in STATUSES}
    for name in CRITERIA:
        criterion = record["criteria"][name]
        require_keys(criterion, ("status", "reason", "evidence"))
        require(criterion["status"] in STATUSES, "unknown criterion status")
        require_text(criterion["reason"])
        if criterion["status"] != "NOT_EVALUATED" and not criterion["evidence"]:
            raise ValueError("observed criteria require evidence")
        if criterion["status"] == "PASS":
            require(
                revision is not None, "passing observations require a pinned revision"
            )
        verify_evidence(criterion["evidence"], root)
        counts[criterion["status"]] += 1
    ready = counts["PASS"] == len(CRITERIA)
    disposition = "ready_for_review" if ready else "defer"
    if counts["FAIL"]:
        disposition = "do_not_roll_out"
    return {
        "disposition": disposition,
        "ready_for_maintainer_review": ready,
        "counts": counts,
        "plugin": record["plugin"],
        "criteria": record["criteria"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--root", required=True, type=Path, help="Local evidence root")
    args = parser.parse_args(argv)
    try:
        record = json.loads(
            args.record.read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
        report = evaluate(record, args.root)
    except (OSError, RuntimeError):
        print(
            "invalid trial record: record or evidence unavailable or unresolvable",
            file=sys.stderr,
        )
        return 2
    except ValueError as exc:
        print(f"invalid trial record: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ready_for_maintainer_review"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
