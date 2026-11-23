#!/usr/bin/env python3
"""Retain before/after inputs and compare hygiene results with hand counts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


CHECKER = Path(__file__).resolve().parents[2] / "scripts/hygiene/check_python_style.py"
BEFORE = 'try:\n    print("Process START")\nexcept:\n    pass\n'
AFTER = (
    "import logging\n\nlogger = logging.getLogger(__name__)\n"
    'try:\n    logger.info("Process START")\nexcept ValueError:\n    raise\n'
)


def prepare_tree(root: Path, source: str) -> None:
    """Write a standalone input tree; no package imports or Git state are needed."""
    package = root / "src/assetutilities"
    package.mkdir(parents=True)
    (package / "example.py").write_text(source, encoding="utf-8")
    quality = root / "config/quality"
    quality.mkdir(parents=True)
    (quality / "python-hygiene-baseline.json").write_text("{}\n", encoding="utf-8")


def run_check(root: Path) -> dict[str, int]:
    """Count diagnostic lines independently of the checker implementation."""
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    (root / "checker.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    findings = sum(": " in line for line in result.stdout.splitlines())
    # PASS is a status line, not a source diagnostic.
    findings -= sum(line.startswith("PASS:") for line in result.stdout.splitlines())
    return {"findings": findings, "exit_code": result.returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("output directory already exists; select an unused directory")
    results = {}
    for name, source in (("before", BEFORE), ("after", AFTER)):
        tree = output / name
        prepare_tree(tree, source)
        results[name] = run_check(tree)
    (output / "results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    # Independent hand calculation: BEFORE has one print call and one bare
    # handler (one + one = two); AFTER has neither (zero + zero = zero).
    expected = {
        "before": {"findings": 2, "exit_code": 1},
        "after": {"findings": 0, "exit_code": 0},
    }
    if results != expected:
        print("FAIL: worked-example results differ from the hand count")
        return 1
    print("PASS: before has 2 findings; after has 0 findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
