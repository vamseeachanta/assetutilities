"""Check Python source conventions without importing application modules.

Rule source: docs/plans/2026-05-05-issue-41-clean-code.md:44-46,56-57
(no print calls in src and no bare exception handlers).
The legacy inventory is an exact multiset, not a per-file exemption. Changes
to it require review; this command deliberately has no baseline-update option.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

# IO_REPARSE_TAG_SYMLINK and IO_REPARSE_TAG_MOUNT_POINT on every platform.
LINK_REPARSE_TAGS = {0xA000000C, 0xA0000003}


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


def inspect_source(source: str | bytes) -> list[dict[str, str]]:
    """Return bare-handler and direct-print fingerprints, or a syntax failure.

    AST serialization excludes positions so comments and formatting do not
    invalidate a legacy entry. Arguments and handler bodies remain significant.
    Strings containing example conflict markers are valid Python, not conflicts.
    Compilation validates context-sensitive syntax without executing source.
    Byte input lets Python honor source encoding declarations and UTF-8 BOMs.
    """
    try:
        tree = ast.parse(source)
        compile(tree, "<unknown>", "exec", dont_inherit=True)
    except (SyntaxError, ValueError, MemoryError, RecursionError) as error:
        return [
            {
                "rule": "syntax",
                "fingerprint": str(getattr(error, "lineno", None) or "?"),
                "cause": type(error).__name__,
            }
        ]
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
    try:
        if not source_root.is_dir():
            raise ValueError("src: source root is missing or is not a directory")
    except OSError as error:
        raise ValueError(
            f"src: unable to inspect source root ({type(error).__name__})"
        ) from None
    findings = []
    files = []
    pending = [source_root]
    while pending:
        path = pending.pop()
        label = path.relative_to(root).as_posix()
        try:
            tag = getattr(path.lstat(), "st_reparse_tag", 0)
            if path.is_symlink() or tag in LINK_REPARSE_TAGS:
                raise ValueError(f"{label}: source path is a link")
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"{label}: source path escapes the root")
            if path.is_dir():
                pending.extend(path.iterdir())
            elif path.suffix == ".py":
                files.append(path)
        except (OSError, RuntimeError) as error:
            raise ValueError(
                f"{label}: unable to inspect source ({type(error).__name__})"
            ) from None
    if not files:
        raise ValueError("src: source root contains no Python files")
    for path in sorted(files):
        try:
            source = path.read_bytes()
        except OSError as error:
            raise ValueError(
                f"{path.relative_to(root).as_posix()}: "
                f"unable to read source ({type(error).__name__})"
            ) from None
        for item in inspect_source(source):
            findings.append({"path": path.relative_to(root).as_posix(), **item})
    return findings


def inventory(items: object) -> Counter:
    """Validate legacy records and retain duplicate occurrence counts."""
    if not isinstance(items, list):
        raise TypeError("baseline must be a list")
    result = Counter()
    for index, item in enumerate(items, start=1):
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "rule", "fingerprint"}
            or not all(isinstance(value, str) for value in item.values())
        ):
            raise ValueError(f"invalid baseline record {index}")
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
            raise ValueError(
                f"invalid baseline record {index}: invalid path, rule or fingerprint"
            )
        result[(path, rule, fingerprint)] += 1
    return result


def load_baseline(path: Path, root: Path) -> Counter:
    """Give baseline failures context without disclosing external paths."""
    try:
        label = path.absolute().relative_to(root.absolute()).as_posix()
    except ValueError:
        label = "<baseline>"
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{label}: invalid JSON at line {error.lineno}, column {error.colno}"
        ) from None
    except (OSError, UnicodeError) as error:
        raise ValueError(
            f"{label}: unable to read baseline ({type(error).__name__})"
        ) from None
    try:
        return inventory(items)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label}: {error}") from None


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
        expected = load_baseline(baseline, args.root)
        findings = scan_tree(args.root)
        syntax = [item for item in findings if item["rule"] == "syntax"]
        for item in syntax:
            print(
                f"FAIL: {item['path']}:{item['fingerprint']}: invalid Python syntax "
                f"({item.get('cause', 'SyntaxError')})"
            )
        actual = inventory([item for item in findings if item["rule"] != "syntax"])
        for label, delta in (("new", actual - expected), ("stale", expected - actual)):
            for (path, rule, fingerprint), count in sorted(delta.items()):
                print(
                    f"FAIL: {label} {rule}: {path} ({count} occurrence(s), {fingerprint})"
                )
        if syntax or actual != expected:
            return 1
    except ValueError as error:
        # Only contextual errors above reach this handler, never raw OS messages.
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: Python hygiene; {sum(expected.values())} inventoried legacy findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
