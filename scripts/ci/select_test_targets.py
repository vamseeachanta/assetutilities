#!/usr/bin/env python3
# ABOUTME: Single-source PR-gate test selector — maps changed files -> pytest targets.
# ABOUTME: Auto-discovers modules from the filesystem so new modules never drift.

"""Select pytest targets for the PR gate from a list of changed files.

Replaces the monolithic ``uv run python -m pytest tests`` job in
``.github/workflows/tests.yml`` with a per-domain fan-out: a PR runs one CI
job per touched domain instead of the whole tree. The module list is the
filesystem — a module is "mapped" iff ``tests/modules/<module>/`` exists.
Adding a module needs no CI edit, and the drift-guard test
(``tests/ci/test_select_test_targets.py``) fails if any
``tests/modules/<module>`` stops being selected.

Decision tree (first match wins):
  * a **core** path changed (engine, __main__, pyproject, uv.lock, conftest,
    pytest.ini, the workflow itself, this selector, base_configs, common) ->
    ``scope=full`` (whole tree fans out to every domain).
  * otherwise collect the modules touched under ``tests/modules/<m>/`` or the
    src homes (``src/assetutilities/<m>/``, ``src/assetutilities/modules/<m>/``,
    ``src/modules/<m>/``) — but only keep ones with a real
    ``tests/modules/<m>/`` dir — and route exact contract paths (e.g.
    ``config/repo_structure.yml`` -> ``tests/repo_structure``) ->
    ``scope=modules``.
  * if nothing test-relevant changed (docs / reports / notebooks only)
    -> ``scope=skip`` — still runs the cheap always-on cross-cutting set so the
    required check passes fast, never the full tree.

The always-on set (``tests/unit`` — the common/core unit tests) always runs, so
the matrix is never empty.

Usage::

    python3 scripts/ci/select_test_targets.py --files-from changed.txt
    git diff --name-only BASE...HEAD | python3 scripts/ci/select_test_targets.py -
    python3 scripts/ci/select_test_targets.py --emit-matrix --files-from changed.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Always-on cross-cutting set: the flat common/core unit suite. Runs for every
# PR (so the matrix is never empty) and is cheap.
ALWAYS_XDIST = [
    "tests/unit",
]

# Module domains that are WIP staging areas, not gating suites — never shard
# them into the CI matrix. `tests_wip` is a holding pen for not-yet-stable tests
# (e.g. plotly polar viz that errors in the engine). See issue #99.
MATRIX_IGNORE_DOMAINS = {
    "tests_wip",
}

# Changing any of these can affect every module -> run the whole tree.
CORE_EXACT = {
    "src/assetutilities/engine.py",
    "src/assetutilities/__main__.py",
    "src/assetutilities/__init__.py",
    "src/assetutilities/calculation.py",
    "src/assetutilities/math_helpers.py",
    "pyproject.toml",
    "uv.lock",
    "pytest.ini",
    "tests/conftest.py",
    ".github/workflows/tests.yml",
}
CORE_PREFIXES = (
    "src/assetutilities/base_configs/",
    "src/assetutilities/common/",
    "src/assetutilities/constants/",
    "src/assetutilities/units/",
    "scripts/ci/",  # the selector itself / its tests -> fail safe to full
)

# Exact non-module paths that should run a specific contract suite.
CONTRACT_ROUTES = {
    "config/repo_structure.yml": "tests/repo_structure",
}

# A module's source can live under any of these prefixes; the canonical TEST
# home is always tests/modules/<m>/ (we only shard a module that has one).
_MODULE_SRC_RES = (
    re.compile(r"^src/assetutilities/modules/([^/]+)/"),
    re.compile(r"^src/assetutilities/([^/]+)/"),
    re.compile(r"^src/modules/([^/]+)/"),
)
_MODULE_TEST_RE = re.compile(r"^tests/modules/([^/]+)/")


def _is_core(path: str) -> bool:
    return path in CORE_EXACT or path.startswith(CORE_PREFIXES)


def _has_tests(directory: Path) -> bool:
    """True if ``directory`` contains at least one pytest file.

    Keeps non-test support dirs (fixtures/, helpers/, mocks/, _archive/, …) and
    empty module stubs out of the domain matrix so they don't become empty
    shards. A dir that has test files but is otherwise excluded still becomes a
    shard — the CI step treats pytest's "no tests collected" (exit 5) as a pass,
    so such shards are harmless.
    """
    for pattern in ("test_*.py", "*_test.py"):
        if next(directory.rglob(pattern), None) is not None:
            return True
    return False


def select(changed: list[str], root: Path) -> dict:
    """Return {scope, xdist, seq} for the given changed files."""
    if any(_is_core(p) for p in changed):
        full = _full_tree(root)
        return {"scope": "full", "xdist": full, "seq": []}

    modules: set[str] = set()
    contracts: set[str] = set()
    relevant = False

    for p in changed:
        if p in CONTRACT_ROUTES:
            contracts.add(CONTRACT_ROUTES[p])
            relevant = True
            continue
        mt = _MODULE_TEST_RE.match(p)
        if mt:
            if mt.group(1) not in MATRIX_IGNORE_DOMAINS:
                modules.add(mt.group(1))
            relevant = True
            continue
        for rx in _MODULE_SRC_RES:
            ms = rx.match(p)
            if ms:
                # only map a src change to a module that has a test home
                if (root / "tests" / "modules" / ms.group(1)).is_dir():
                    modules.add(ms.group(1))
                    relevant = True
                break
        # anything else (reports/, notebooks/, *.md, docs/, scripts/ non-ci,
        # examples/) is not test-relevant.

    xdist = list(ALWAYS_XDIST)
    for mod in sorted(modules):
        xdist.append(f"tests/modules/{mod}")
    xdist.extend(sorted(contracts))

    xdist = _existing_unique(xdist, root)
    return {"scope": "modules" if relevant else "skip", "xdist": xdist, "seq": []}


def _existing_unique(targets: list[str], root: Path) -> list[str]:
    seen, out = set(), []
    for t in targets:
        if t not in seen and (root / t).is_dir():
            seen.add(t)
            out.append(t)
    return out


def _full_tree(root: Path) -> list[str]:
    """Flat list of every top-level test target (dirs + root test files)."""
    tests = root / "tests"
    out = []
    for child in sorted(tests.iterdir()):
        if child.is_dir() and child.name != "__pycache__":
            out.append(f"tests/{child.name}")
        elif (
            child.is_file() and child.name.startswith("test_") and child.suffix == ".py"
        ):
            out.append(f"tests/{child.name}")
    return out


def to_matrix(changed: list[str], root: Path) -> dict:
    """Build a GitHub-Actions matrix of per-domain shards from changed files.

    Each shard is ``{"name", "targets", "mode"}`` (mode is always ``xdist``
    here — assetutilities has no integration/perf split that needs sequential
    running). Fans work out so every domain runs as its own CI job — faster
    wall-clock and per-domain pass/fail isolation.

    * ``scope=full`` -> one shard per ``tests/modules/<domain>`` (with tests),
      one per other top-level ``tests/<dir>`` (with tests), plus a ``_root``
      shard for top-level test files.
    * ``scope=modules`` -> the always-on shard + one shard per touched module +
      one per routed contract.
    * ``scope=skip`` -> just the always-on shard (never empty).
    """
    result = select(changed, root)
    scope = result["scope"]
    shards: list[dict] = []

    if scope == "full":
        modules_dir = root / "tests" / "modules"
        if modules_dir.is_dir():
            for child in sorted(modules_dir.iterdir()):
                if (
                    child.is_dir()
                    and child.name != "__pycache__"
                    and child.name not in MATRIX_IGNORE_DOMAINS
                    and _has_tests(child)
                ):
                    shards.append(
                        {
                            "name": f"modules-{child.name}",
                            "targets": f"tests/modules/{child.name}",
                            "mode": "xdist",
                        }
                    )
        tests = root / "tests"
        root_files: list[str] = []
        for child in sorted(tests.iterdir()):
            if (
                child.is_dir()
                and child.name not in {"modules", "__pycache__"}
                and _has_tests(child)
            ):
                shards.append(
                    {
                        "name": child.name,
                        "targets": f"tests/{child.name}",
                        "mode": "xdist",
                    }
                )
            elif (
                child.is_file()
                and child.name.startswith("test_")
                and child.suffix == ".py"
            ):
                root_files.append(f"tests/{child.name}")
        if root_files:
            shards.append(
                {"name": "_root", "targets": " ".join(root_files), "mode": "xdist"}
            )
    else:
        # modules / skip: the always-on shard guarantees a non-empty matrix.
        always = _existing_unique(list(ALWAYS_XDIST), root)
        if always:
            shards.append(
                {"name": "_always", "targets": " ".join(always), "mode": "xdist"}
            )
        for tgt in result["xdist"]:
            if tgt in ALWAYS_XDIST:
                continue  # already in the always-on shard
            name = tgt.replace("tests/modules/", "modules-").replace("tests/", "")
            shards.append({"name": name, "targets": tgt, "mode": "xdist"})

    return {"scope": scope, "include": shards}


def _read_changed(args) -> list[str]:
    if args.files_from == "-":
        text = sys.stdin.read()
    elif args.files_from:
        text = Path(args.files_from).read_text(encoding="utf-8")
    else:
        return list(args.files)
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="*", help="changed file paths")
    ap.add_argument(
        "--files-from", help="read changed paths from FILE (or - for stdin)"
    )
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument(
        "--emit-matrix",
        action="store_true",
        help="emit a per-domain GitHub Actions matrix (matrix=<json>) instead "
        "of the flat xdist/seq target lists",
    )
    a = ap.parse_args(argv)
    changed = _read_changed(a)
    if a.emit_matrix:
        matrix = to_matrix(changed, Path(a.root))
        print(f"scope={matrix['scope']}")
        print(f"matrix={json.dumps({'include': matrix['include']})}")
        return 0
    result = select(changed, Path(a.root))
    print(f"scope={result['scope']}")
    print(f"xdist_targets={' '.join(result['xdist'])}")
    print(f"seq_targets={' '.join(result['seq'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
