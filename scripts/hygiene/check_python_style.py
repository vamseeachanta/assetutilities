#!/usr/bin/env python3
"""Check canonical Python source without importing application dependencies."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat


SOURCE = "src/assetutilities"
BASELINE = "config/quality/python-hygiene-baseline.json"
CONFLICT = re.compile(rb"^(?:<{7}(?: .*)?|={7}|>{7}(?: .*)?|[|]{7}(?: .*)?)$")


def load_baseline(root: Path) -> dict[str, str]:
    """Load source-digest exceptions; malformed configuration never opts out."""
    path = root / BASELINE
    path.resolve().relative_to(root)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("expected a path-to-SHA-256 object")
    for path, digest in data.items():
        relative = PurePosixPath(path)
        if (
            relative.as_posix() != path
            or not path.startswith(SOURCE + "/")
            or ".." in relative.parts
            or "\\" in path
            or relative.suffix != ".py"
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValueError("expected canonical source paths and SHA-256 digests")
    return data


def style_findings(source: bytes, path: str) -> list[str]:
    """Return syntactic print calls and untyped exception handlers."""
    tree = ast.parse(source, filename=path)
    compile(tree, path, "exec")
    findings = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            findings.append(f"{path}:{node.lineno}: PY-PRINT use the module logger")
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(f"{path}:{node.lineno}: PY-EXCEPT catch a typed exception")
    return sorted(findings)


def check_file(path: Path, relative: str, baseline: dict[str, str]) -> list[str]:
    """Check fatal errors before applying unchanged-source style exceptions."""
    try:
        source = path.read_bytes()
    except OSError:
        return [f"{relative}:0: SOURCE cannot read source file"]
    findings = [
        f"{relative}:{line}: MERGE unresolved conflict marker"
        for line, text in enumerate(source.splitlines(), start=1)
        if CONFLICT.fullmatch(text)
    ]
    if path.suffix != ".py":
        return findings
    try:
        current = style_findings(source, relative)
    except (SyntaxError, ValueError) as exc:
        return findings + [
            f"{relative}:{getattr(exc, 'lineno', 0) or 0}: SYNTAX invalid Python"
        ]
    if relative in baseline:
        # Git may translate line endings on checkout; no other bytes normalize.
        digest = hashlib.sha256(source.replace(b"\r\n", b"\n")).hexdigest()
        if digest == baseline[relative] and current:
            return findings
        findings.append(f"{relative}:0: BASELINE remove stale legacy exception")
    return findings + current


def check(root: Path) -> list[str]:
    """Return policy violations in the canonical source package."""
    source_root = root / SOURCE
    try:
        parent_mode = (root / "src").lstat().st_mode
        source_mode = source_root.lstat().st_mode
    except FileNotFoundError:
        return [f"{SOURCE}:0: SOURCE required package directory is missing"]
    except OSError:
        return [f"{SOURCE}:0: SOURCE cannot inspect package directory"]
    if stat.S_ISLNK(parent_mode) or stat.S_ISLNK(source_mode):
        return [f"{SOURCE}:0: SOURCE symbolic source directories are not supported"]
    if not stat.S_ISDIR(source_mode):
        return [f"{SOURCE}:0: SOURCE required package directory is missing"]
    try:
        baseline = load_baseline(root)
    except (OSError, ValueError):
        return [f"{BASELINE}:0: BASELINE missing or invalid configuration"]
    findings = []
    visited = set()
    paths = [source_root]
    metadata = root / "pyproject.toml"
    try:
        metadata.lstat()
    except FileNotFoundError:
        pass  # Project metadata is optional in standalone source trees.
    except OSError:
        findings.append("pyproject.toml:0: SOURCE cannot inspect source entry")
    else:
        paths.insert(0, metadata)
    while paths:
        path = paths.pop()
        relative = path.relative_to(root).as_posix()
        try:
            mode = path.lstat().st_mode
        except OSError:
            findings.append(f"{relative}:0: SOURCE cannot inspect source entry")
            continue
        if stat.S_ISLNK(mode):
            findings.append(
                f"{relative}:0: SOURCE symbolic source entries are not supported"
            )
            continue
        if stat.S_ISDIR(mode):
            try:
                paths.extend(sorted(path.iterdir(), reverse=True))
            except OSError:
                findings.append(
                    f"{relative}:0: SOURCE cannot enumerate source directory"
                )
            continue
        if not stat.S_ISREG(mode) or path.suffix not in {
            ".py",
            ".yaml",
            ".yml",
            ".toml",
        }:
            continue
        if path.suffix == ".py":
            visited.add(relative)
        findings.extend(check_file(path, relative, baseline))
    for relative in sorted(baseline.keys() - visited):
        findings.append(f"{relative}:0: BASELINE source file no longer exists")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args()
    findings = check(args.root.resolve())
    for finding in findings:
        print(finding)
    if findings:
        return 1
    print("PASS: canonical Python source hygiene")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
