"""Validate contribution names and report refs requiring maintainer attention.

The monthly YYYYMM convention comes from issue #19. Topic branches remain
supported by the repository's pull-request workflow. No refs are modified.
Git fields: git-for-each-ref manual, FIELD NAMES (2026 online edition).
"""

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def validate_branch(branch, today):
    current = today.strftime("%Y%m")
    if not branch or branch == "main" or (branch.isdigit() and branch != current):
        raise ValueError(f"contribution branch must be a topic branch or {current}")


def audit(root, today):
    result = subprocess.run(
        [
            "git",
            "for-each-ref",
            "--format=%(refname)\t%(upstream)\t%(upstream:track)",
            "refs/heads",
            "refs/remotes",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    current = today.strftime("%Y%m")
    stale, unpublished = [], []
    for line in result.stdout.splitlines():
        ref, upstream, tracking = line.split("\t")
        local = ref.startswith("refs/heads/")
        name = (
            ref.removeprefix("refs/heads/")
            if local
            else ref.removeprefix("refs/remotes/").partition("/")[2]
        )
        # YYYYMM: four year digits and two month digits, per issue #19.
        if re.fullmatch(r"\d{6}", name) and name != current:
            stale.append(ref)
        if (
            local
            and name != "main"
            and (not upstream or "ahead" in tracking or "gone" in tracking)
        ):
            unpublished.append(ref)
    return {
        "current_month": current,
        "stale_monthly": sorted(stale),
        "unpublished_local": sorted(unpublished),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--branch")
    mode.add_argument("--audit", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    today = datetime.now(timezone.utc).date()
    if args.audit:
        print(json.dumps(audit(args.root, today), indent=2))
    else:
        validate_branch(args.branch, today)
        print("Contribution branch policy passed")


if __name__ == "__main__":
    main()
