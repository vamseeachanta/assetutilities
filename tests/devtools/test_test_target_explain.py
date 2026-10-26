# ABOUTME: Independent fixture expectations for the test-target explanation CLI.
# ABOUTME: Covers selection reasons, ordering, real-selector loading and read-only use.

"""Exercise the diagnostic without depending on the checkout's test homes."""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

# This file is in tests/devtools, two directory levels below the repository root.
COMMAND = Path(__file__).resolve().parents[2] / "scripts/diagnostics/explain_test_targets.py"


@pytest.fixture
def diagnostic():
    return runpy.run_path(str(COMMAND))


@pytest.fixture
def tree(tmp_path):
    # Independent fixture inventory: tests/{unit,data_store,docs,repo_structure},
    # tests/modules/{alpha,zeta,tests_wip}; source homes alpha,zeta,orphan;
    # docs/ and scripts/ci/. The module homes are deliberately empty directories:
    # select() requires a test home, not a collected test, for source routing.
    for directory in (
        "tests/unit",
        "tests/data_store",
        "tests/docs",
        "tests/repo_structure",
        "tests/modules/alpha",
        "tests/modules/zeta",
        "tests/modules/tests_wip",
        "src/assetutilities/alpha",
        "src/assetutilities/zeta",
        "src/assetutilities/orphan",
        "docs",
        "scripts/ci",
    ):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    # A root-level pytest file belongs in full selection. A decoy selector must
    # never be loaded: --root supplies selection directories, not executable code.
    (tmp_path / "tests/test_root.py").write_text("# fixture\n", encoding="utf-8")
    (tmp_path / "src/assetutilities/orphan/code.py").write_bytes(b"# source\n")
    (tmp_path / "docs/guide.md").write_bytes(b"fixture documentation\n")
    (tmp_path / "scripts/ci/select_test_targets.py").write_text(
        "raise RuntimeError('fixture selector must not execute')\n", encoding="utf-8"
    )
    return tmp_path


# Expected JSON is hand-enumerated from the fixture inventory above and the
# documented decision tree in scripts/ci/select_test_targets.py, not select().
# Always-on order is unit, data_store; module names sort before contract targets.
ALWAYS = ["tests/unit", "tests/data_store"]
FULL = [
    "tests/data_store",
    "tests/docs",
    "tests/modules",
    "tests/repo_structure",
    "tests/test_root.py",
    "tests/unit",
]


def selection(scope, targets):
    return {"scope": scope, "xdist": targets, "seq": []}


@pytest.mark.parametrize(
    "path,reason,expected",
    [
        (
            "src/assetutilities/orphan/code.py",
            "source-without-test-home",
            selection("skip", ALWAYS),
        ),
        (
            "src/assetutilities/alpha/code.py",
            "source-with-test-home",
            selection("modules", ALWAYS + ["tests/modules/alpha"]),
        ),
        (
            "src/assetutilities/modules/alpha/code.py",
            "source-with-test-home",
            selection("modules", ALWAYS + ["tests/modules/alpha"]),
        ),
        (
            "src/modules/alpha/code.py",
            "source-with-test-home",
            selection("modules", ALWAYS + ["tests/modules/alpha"]),
        ),
        (
            "src/assetutilities/modules/orphan/code.py",
            "source-without-test-home",
            selection("skip", ALWAYS),
        ),
        (
            "src/modules/orphan/code.py",
            "source-without-test-home",
            selection("skip", ALWAYS),
        ),
        ("pyproject.toml", "core", selection("full", FULL)),
        ("src/assetutilities/common/code.py", "core", selection("full", FULL)),
        (
            "config/repo_structure.yml",
            "contract",
            selection("modules", ALWAYS + ["tests/repo_structure"]),
        ),
        (
            "README.md",
            "contract",
            selection("modules", ALWAYS + ["tests/docs"]),
        ),
        (
            "tests/modules/zeta/test_code.py",
            "module-test",
            selection("modules", ALWAYS + ["tests/modules/zeta"]),
        ),
        (
            "tests/modules/tests_wip/test_code.py",
            "module-test",
            selection("modules", ALWAYS),
        ),
        ("docs/guide.md", "unclassified", selection("skip", ALWAYS)),
    ],
)
def test_individual_explanations(diagnostic, tree, path, reason, expected):
    assert diagnostic["explain"]([path], tree) == {
        "selection": expected,
        "paths": [{"path": path, "reason": reason, "selection": expected}],
    }


def test_mixed_input_preserves_target_and_input_order(diagnostic, tree):
    # Hand calculation: orphan/docs add no targets, zeta and alpha sort, then
    # docs and repo_structure contracts sort. Repeated alpha adds no target.
    rows = [
        (
            "src/assetutilities/zeta/code.py",
            "source-with-test-home",
            "modules",
            ALWAYS + ["tests/modules/zeta"],
        ),
        ("docs/guide.md", "unclassified", "skip", ALWAYS),
        (
            "config/repo_structure.yml",
            "contract",
            "modules",
            ALWAYS + ["tests/repo_structure"],
        ),
        (
            "src/assetutilities/orphan/code.py",
            "source-without-test-home",
            "skip",
            ALWAYS,
        ),
        (
            "tests/modules/alpha/test_code.py",
            "module-test",
            "modules",
            ALWAYS + ["tests/modules/alpha"],
        ),
        ("README.md", "contract", "modules", ALWAYS + ["tests/docs"]),
        (
            "tests/modules/alpha/test_code.py",
            "module-test",
            "modules",
            ALWAYS + ["tests/modules/alpha"],
        ),
    ]
    expected = {
        "selection": selection(
            "modules",
            ALWAYS
            + [
                "tests/modules/alpha",
                "tests/modules/zeta",
                "tests/docs",
                "tests/repo_structure",
            ],
        ),
        "paths": [
            {"path": path, "reason": reason, "selection": selection(scope, targets)}
            for path, reason, scope, targets in rows
        ],
    }
    paths = [row[0] for row in rows]
    assert diagnostic["explain"](paths, tree) == expected
    assert diagnostic["explain"](paths, tree) == expected


def test_core_does_not_hide_individual_skip(diagnostic, tree):
    assert diagnostic["explain"](["pyproject.toml", "docs/guide.md"], tree) == {
        "selection": selection("full", FULL),
        "paths": [
            {
                "path": "pyproject.toml",
                "reason": "core",
                "selection": selection("full", FULL),
            },
            {
                "path": "docs/guide.md",
                "reason": "unclassified",
                "selection": selection("skip", ALWAYS),
            },
        ],
    }


def snapshot(root):
    """Record directory entries, file bytes and modification timestamps."""
    return {
        path.relative_to(root).as_posix(): (
            path.is_dir(),
            None if path.is_dir() else path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in [root, *root.rglob("*")]
    }


def test_cli_json_is_repeatable_and_fixture_is_unchanged(tree):
    before = snapshot(tree)
    args = [
        sys.executable,
        "-B",
        str(COMMAND),
        "--root",
        str(tree),
        "src/assetutilities/orphan/code.py",
        "src/assetutilities/alpha/code.py",
    ]
    first = subprocess.run(args, cwd=tree, check=True, text=True, capture_output=True)
    second = subprocess.run(args, cwd=tree, check=True, text=True, capture_output=True)
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    assert json.loads(first.stdout) == {
        "selection": selection("modules", ALWAYS + ["tests/modules/alpha"]),
        "paths": [
            {
                "path": "src/assetutilities/orphan/code.py",
                "reason": "source-without-test-home",
                "selection": selection("skip", ALWAYS),
            },
            {
                "path": "src/assetutilities/alpha/code.py",
                "reason": "source-with-test-home",
                "selection": selection("modules", ALWAYS + ["tests/modules/alpha"]),
            },
        ],
    }
    assert snapshot(tree) == before


def test_cli_requires_changed_paths(tree):
    result = subprocess.run(
        [sys.executable, "-B", str(COMMAND), "--root", str(tree)],
        cwd=tree,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert "required" in result.stderr
