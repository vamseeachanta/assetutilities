"""Check Python source conventions without importing application modules.

The legacy inventory is an exact multiset, not a per-file exemption. Changes
to it require review; this command deliberately has no baseline-update option.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import tokenize
from collections import Counter
from pathlib import Path


def canonical_ast(value):
    """Serialize meaningful AST fields consistently across Python versions."""
    if isinstance(value, ast.AST):
        return {
            "type": type(value).__name__,
            **{
                key: canonical_ast(item)
                for key, item in ast.iter_fields(value)
                if item is not None and item != []
            },
        }
    if isinstance(value, list):
        return [canonical_ast(item) for item in value]
    if isinstance(value, (bytes, complex)) or value is Ellipsis:
        return {"literal": repr(value)}
    return value


def inspect_source(source: str) -> list[dict[str, str]]:
    """Return bare-handler and direct-print fingerprints, or a syntax failure.

    AST serialization excludes positions so comments and formatting do not
    invalidate a legacy entry. Arguments and handler bodies remain significant.
    Strings containing example conflict markers are valid Python, not conflicts.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [{"rule": "syntax", "fingerprint": str(error.lineno)}]
    findings = []
    for node in ast.walk(tree):
        rule = None
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            rule = "bare-except"
        elif isinstance(node, ast.Call):
            function = node.func
            if (
                isinstance(function, ast.Name)
                and function.id == "print"
                or (
                    isinstance(function, ast.Attribute)
                    and function.attr == "print"
                    and isinstance(function.value, ast.Name)
                    and function.value.id == "builtins"
                )
            ):
                rule = "print"
        if rule:
            serialized = json.dumps(canonical_ast(node), sort_keys=True)
            fingerprint = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            findings.append({"rule": rule, "fingerprint": fingerprint})
    return findings


def scan_tree(root: Path) -> list[dict[str, str]]:
    """Inspect every Python file below src; never execute package code."""
    source_root = root / "src"
    if not source_root.is_dir():
        raise ValueError("source root is missing")
    findings = []
    files = sorted(source_root.rglob("*.py"))
    if not files:
        raise ValueError("source root contains no Python files")
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("source path escapes the root or is a symlink")
        with tokenize.open(path) as stream:
            source = stream.read()
        for item in inspect_source(source):
            findings.append({"path": path.relative_to(root).as_posix(), **item})
    return findings


def inventory(items: object) -> Counter:
    """Validate legacy records and retain duplicate occurrence counts."""
    if not isinstance(items, list):
        raise TypeError("baseline must be a list")
    result = Counter()
    for item in items:
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "rule", "fingerprint"}
            or not all(isinstance(value, str) for value in item.values())
        ):
            raise ValueError("invalid baseline record")
        path, rule, fingerprint = item["path"], item["rule"], item["fingerprint"]
        if (
            not path.startswith("src/")
            or ".." in Path(path).parts
            or "\\" in path
            or not path.endswith(".py")
            or rule not in {"print", "bare-except"}
            or len(fingerprint) != hashlib.sha256().digest_size * 2
            or any(char not in "0123456789abcdef" for char in fingerprint)
        ):
            raise ValueError("invalid baseline path, rule or fingerprint")
        result[(path, rule, fingerprint)] += 1
    return result


def main(argv: list[str] | None = None) -> int:
    """Print stable PASS/FAIL diagnostics and return a failing status on errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args(argv)
    baseline = args.baseline or args.root / "scripts/hygiene/clean_code_baseline.json"
    try:
        expected = inventory(json.loads(baseline.read_text(encoding="utf-8")))
        findings = scan_tree(args.root)
        syntax = [item for item in findings if item["rule"] == "syntax"]
        for item in syntax:
            print(f"FAIL: {item['path']}:{item['fingerprint']}: invalid Python syntax")
        actual = inventory([item for item in findings if item["rule"] != "syntax"])
        for label, delta in (("new", actual - expected), ("stale", expected - actual)):
            for (path, rule, fingerprint), count in sorted(delta.items()):
                print(
                    f"FAIL: {label} {rule}: {path} ({count} occurrence(s), {fingerprint})"
                )
        if syntax or actual != expected:
            return 1
    except (OSError, TypeError, ValueError, SyntaxError) as error:
        # Avoid exposing absolute paths through OS exception messages.
        print(
            f"FAIL: unable to inspect source or baseline ({type(error).__name__})",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: Python hygiene; {sum(expected.values())} inventoried legacy findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
