#!/usr/bin/env python3
"""Verify the assetutilities repository structure contract.

The checker is intentionally conservative for issue #78 Phase 1: it enforces the
machine-readable contract and blocks unclassified generated-output roots without
moving or deleting files.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

import yaml

PLACEHOLDERS = {"", "todo", "tbd", "placeholder", "yyyy-mm-dd", "n/a", "none"}
REQUIRED_EXCEPTION_FIELDS = {
    "path",
    "category",
    "owner",
    "review_date",
    "follow_up_url",
    "reason",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config/repo_structure.yml",
        help="Path to repo-structure YAML contract.",
    )
    parser.add_argument(
        "--tracked-files",
        nargs="*",
        help="Explicit tracked-file list for tests. Defaults to `git ls-files`.",
    )
    parser.add_argument(
        "--working-tree-files",
        nargs="*",
        help=(
            "Explicit untracked working-tree path list for tests. "
            "Defaults to `git ls-files --others --exclude-standard`."
        ),
    )
    parser.add_argument(
        "--reference-scan-root",
        default=".",
        help="Root used for --candidate-move reference scans.",
    )
    parser.add_argument(
        "--candidate-move",
        action="append",
        default=[],
        help="Path that may be moved; fails if live references remain.",
    )
    return parser.parse_args(argv)


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=True,
    )
    return Path(result.stdout.strip())


def git_tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line]


def git_untracked_files(root: Path) -> list[str]:
    """Return untracked, non-ignored working-tree paths."""

    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def normalize_repo_relative(path: str) -> str:
    normalized = path.strip().replace("\\", "/").rstrip("/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def load_contract(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"repo-structure contract missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key in ("allowed_root_files", "allowed_root_dirs", "generated_roots"):
        data.setdefault(key, [])
    data.setdefault("generated_exceptions", [])
    return data


def first_path_part(path: str) -> str:
    return path.split("/", 1)[0]


def root_entries(paths: Iterable[str]) -> set[str]:
    return {first_path_part(path) for path in paths if path}


def exception_by_path(contract: dict) -> dict[str, dict]:
    return {
        str(item.get("path", "")).rstrip("/"): item
        for item in contract.get("generated_exceptions", [])
    }


def looks_placeholder(value: object) -> bool:
    text = str(value).strip().lower()
    return text in PLACEHOLDERS or text.startswith("todo") or text.startswith("tbd")


def validate_exception_metadata(exceptions: Iterable[dict]) -> list[str]:
    failures: list[str] = []
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    url_re = re.compile(r"^https://github\.com/.+/.+/issues/\d+$")

    for item in exceptions:
        path = str(item.get("path", "<missing>"))
        missing = REQUIRED_EXCEPTION_FIELDS.difference(item)
        if missing:
            failures.append(
                f"exception metadata missing required fields for {path}: "
                + ", ".join(sorted(missing))
            )
            continue
        for field in REQUIRED_EXCEPTION_FIELDS:
            if looks_placeholder(item.get(field)):
                failures.append(f"placeholder exception metadata for {path}: {field}")
        review_date = str(item.get("review_date", ""))
        if not date_re.match(review_date):
            failures.append(f"invalid exception review_date for {path}: {review_date}")
        follow_up_url = str(item.get("follow_up_url", ""))
        if not url_re.match(follow_up_url):
            failures.append(f"invalid exception follow_up_url for {path}: {follow_up_url}")
    return failures


def validate_contract(
    contract: dict,
    tracked_files: Sequence[str],
    working_tree_files: Sequence[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    tracked_files = [normalize_repo_relative(path) for path in tracked_files if path]
    working_tree_files = [
        normalize_repo_relative(path) for path in (working_tree_files or []) if path
    ]
    all_paths = [*tracked_files, *working_tree_files]
    allowed_root_files = set(contract["allowed_root_files"])
    allowed_root_dirs = set(contract["allowed_root_dirs"])
    generated_roots = {str(path).rstrip("/") for path in contract["generated_roots"]}
    exceptions = exception_by_path(contract)

    for entry in sorted(root_entries(all_paths)):
        if entry in allowed_root_files or entry in allowed_root_dirs:
            continue
        failures.append(f"unapproved root entry: {entry}")

    for generated_root in sorted(generated_roots):
        generated_paths = [
            path
            for path in tracked_files
            if path == generated_root or path.startswith(f"{generated_root}/")
        ]
        if not generated_paths:
            continue
        if generated_root not in exceptions:
            failures.append(
                f"tracked generated root lacks exception metadata: {generated_root}"
            )
            continue
        allowed_paths = {
            normalize_repo_relative(path)
            for path in exceptions[generated_root].get("allowed_paths", [])
        }
        for generated_path in sorted(generated_paths):
            if generated_path not in allowed_paths:
                failures.append(
                    "tracked generated path lacks explicit allowance: "
                    f"{generated_path}"
                )

    failures.extend(validate_exception_metadata(contract["generated_exceptions"]))
    return failures


def text_files(root: Path) -> Iterable[Path]:
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "htmlcov"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        yield path


def scan_candidate_references(root: Path, candidate: str) -> list[Path]:
    matches: list[Path] = []
    for path in text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if candidate in text:
            matches.append(path)
    return matches


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = repo_root()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path

    failures: list[str] = []

    if args.candidate_move:
        scan_root = Path(args.reference_scan_root)
        if not scan_root.is_absolute():
            scan_root = root / scan_root
        try:
            scan_root = scan_root.resolve()
            root_resolved = root.resolve()
            scan_root.relative_to(root_resolved)
        except ValueError:
            failures.append(f"reference scan root must stay inside repository: {scan_root}")
        else:
            for candidate in args.candidate_move:
                matches = scan_candidate_references(scan_root, candidate)
                if matches:
                    relative_matches = ", ".join(str(path) for path in matches[:5])
                    failures.append(
                        f"candidate move has live references: {candidate} ({relative_matches})"
                    )
    else:
        try:
            contract = load_contract(config_path)
            tracked_files = args.tracked_files or git_tracked_files(root)
            working_tree_files = (
                args.working_tree_files
                if args.working_tree_files is not None
                else git_untracked_files(root)
            )
            failures.extend(validate_contract(contract, tracked_files, working_tree_files))
        except (OSError, subprocess.CalledProcessError, ValueError, yaml.YAMLError) as exc:
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print("repo-structure contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
