"""Independent source fixtures specify the clean-code gate's expected findings."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/hygiene/check_clean_code.py"


@pytest.fixture
def checker():
    spec = importlib.util.spec_from_file_location("clean_code", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "source, rules",
    [
        ("print('hello')\n", ["print"]),
        ("import builtins\nbuiltins.print('hello')\n", ["print"]),
        ("try:\n    work()\nexcept:\n    recover()\n", ["bare-except"]),
        ("try:\n    work()\nexcept ValueError:\n    recover()\n", []),
        ("# print('comment')\ntext = \"print('text')\"\n", []),
        ("text = '''\n<<<<<<< example\n=======\n>>>>>>> example\n'''\n", []),
        ("<<<<<<< branch\nx = 1\n=======\nx = 2\n>>>>>>> branch\n", ["syntax"]),
        ("def broken(:\n", ["syntax"]),
    ],
)
def test_source_rules(checker, source, rules):
    """Each literal statement above independently determines the expected rule."""
    assert [item["rule"] for item in checker.inspect_source(source)] == rules


def run_checker(root, baseline):
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        env.pop(name, None)
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--root",
            str(root),
            "--baseline",
            str(baseline),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


@pytest.fixture
def tree(tmp_path):
    source = tmp_path / "src/assetutilities/sample.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('legacy')\n", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    return tmp_path, source, baseline


def save_baseline(checker, tree):
    root, _, baseline = tree
    baseline.write_text(json.dumps(checker.scan_tree(root)), encoding="utf-8")


def test_exact_legacy_inventory_passes(checker, tree):
    save_baseline(checker, tree)
    result = run_checker(tree[0], tree[2])
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


@pytest.mark.parametrize(
    "source",
    [
        "print('legacy')\nprint('legacy')\n",
        "print('changed')\n",
        "value = 1\n",
        "<<<<<<< branch\n",
    ],
)
def test_inventory_cannot_hide_changes(checker, tree, source):
    """Two identical calls exceed one entry; changed or removed calls mismatch."""
    save_baseline(checker, tree)
    tree[1].write_text(source, encoding="utf-8")
    assert run_checker(tree[0], tree[2]).returncode == 1


def test_line_only_movement_preserves_fingerprint(checker, tree):
    save_baseline(checker, tree)
    tree[1].write_text("# explanation\n\nprint( 'legacy' )\n", encoding="utf-8")
    assert run_checker(tree[0], tree[2]).returncode == 0


@pytest.mark.parametrize("payload", ["{", "{}", '[{"rule": "syntax"}]'])
def test_invalid_baseline_fails_closed(tree, payload):
    tree[2].write_text(payload, encoding="utf-8")
    assert run_checker(tree[0], tree[2]).returncode != 0


def test_missing_source_root_fails_closed(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text("[]", encoding="utf-8")
    assert run_checker(tmp_path, baseline).returncode != 0


def test_repository_inventory():
    result = run_checker(ROOT, ROOT / "scripts/hygiene/clean_code_baseline.json")
    assert result.returncode == 0, result.stdout + result.stderr


def test_fingerprint_uses_version_independent_fields(checker):
    """The AST for print('legacy') has one Name and one string Constant.

    Empty optional fields are excluded explicitly: ast.dump changed how empty
    fields are displayed across Python versions and is not a portable inventory.
    """
    expected = {
        "type": "Call",
        "func": {"type": "Name", "id": "print", "ctx": {"type": "Load"}},
        "args": [{"type": "Constant", "value": "legacy"}],
    }
    digest = hashlib.sha256(
        json.dumps(expected, sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert checker.inspect_source("print('legacy')")[0]["fingerprint"] == digest


@pytest.mark.parametrize(
    "actual_count, expected_count, exit_code",
    [
        (1, 1, 0),
        (2, 1, 1),
        (0, 1, 1),
        (1, 0, 1),
        (0, 0, 0),
    ],
)
def test_cli_occurrence_accounting(
    checker, monkeypatch, actual_count, expected_count, exit_code
):
    """Hand calculation: equal counts pass; positive or negative deltas fail."""
    item = {"path": "src/example.py", **checker.inspect_source("print('x')")[0]}
    monkeypatch.setattr(
        Path, "read_text", lambda *a, **kw: json.dumps([item] * expected_count)
    )
    monkeypatch.setattr(checker, "scan_tree", lambda root: [item] * actual_count)
    assert checker.main([]) == exit_code


@pytest.mark.parametrize("payload", ["{", "{}", '[{"rule": "syntax"}]'])
def test_cli_invalid_inventory(checker, monkeypatch, payload):
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: payload)
    assert checker.main([]) == 1


def test_cli_syntax_cannot_be_inventoried(checker, monkeypatch):
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: "[]")
    monkeypatch.setattr(
        checker,
        "scan_tree",
        lambda root: [{"path": "src/example.py", "rule": "syntax", "fingerprint": "1"}],
    )
    assert checker.main([]) == 1
