#!/usr/bin/env python3
# ABOUTME: Explain aggregate and per-path CI test selections without running tests.
# ABOUTME: Reuse the real selector while inspecting an optional selection root.

"""Explain test-target selection as deterministic JSON.

Usage::

    python scripts/diagnostics/explain_test_targets.py --root . docs/guide.md
    python scripts/diagnostics/explain_test_targets.py src/assetutilities/cli/run.py

``selection`` contains the aggregate selector result. ``paths`` preserves input
order (including duplicates), with a reason and independent ``selection`` for
each changed path. A source-without-test-home reason exposes the current skip
behavior; it does not repair routing or establish repository-wide reachability.
Only the standard library and the existing selector are used. No tests or Git
commands run, and no files are written.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy

# This script is in scripts/diagnostics, two levels below the repository root.
REPO_ROOT = Path(__file__).resolve().parents[2]
SELECTOR = REPO_ROOT / "scripts/ci/select_test_targets.py"


def _reason(path: str, root: Path, selector: dict) -> str:
    """Classify a path using the selector's own predicates in precedence order."""
    if selector["_is_core"](path):
        return "core"
    if path in selector["CONTRACT_ROUTES"]:
        return "contract"
    if selector["_MODULE_TEST_RE"].match(path):
        return "module-test"
    for pattern in selector["_MODULE_SRC_RES"]:
        match = pattern.match(path)
        if match:
            if (root / "tests" / "modules" / match.group(1)).is_dir():
                return "source-with-test-home"
            return "source-without-test-home"
    return "unclassified"


def explain(changed: list[str], root: Path) -> dict:
    """Return aggregate and per-path selections without altering selector policy."""
    # run_path reads the actual .py script without writing import bytecode.
    # The selection root must never determine which Python code is executed.
    selector = runpy.run_path(str(SELECTOR))
    select = selector["select"]
    return {
        "selection": select(changed, root),
        "paths": [
            {
                "path": path,
                "reason": _reason(path, root, selector),
                "selection": select([path], root),
            }
            for path in changed
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="selection filesystem root (the selector is always loaded beside this script)",
    )
    parser.add_argument("paths", nargs="+", help="repo-relative changed paths")
    args = parser.parse_args(argv)
    print(json.dumps(explain(args.paths, args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
