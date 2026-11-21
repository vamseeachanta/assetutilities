"""Exercise the hygiene CLI in disposable source trees, without importing them."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/hygiene/check_python_style.py"


@pytest.fixture
def source_tree(tmp_path: Path) -> Path:
    (tmp_path / "src/assetutilities").mkdir(parents=True)
    (tmp_path / "config/quality").mkdir(parents=True)
    (tmp_path / "config/quality/python-hygiene-baseline.json").write_text("{}\n")
    return tmp_path


def write_source(root: Path, source: str, name: str = "example.py") -> Path:
    path = root / "src/assetutilities" / name
    path.write_bytes(source.encode("utf-8"))
    return path


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_flags_multiline_print_and_bare_handler(source_tree: Path) -> None:
    """Hand count: one print call + one untyped handler = two findings."""
    write_source(
        source_tree, 'try:\n    print(\n        "message"\n    )\nexcept:\n    pass\n'
    )
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert result.stdout.count("PY-PRINT") == 1
    assert result.stdout.count("PY-EXCEPT") == 1
    assert "src/assetutilities/example.py:2:" in result.stdout
    assert "src/assetutilities/example.py:5:" in result.stdout


def test_ignores_comments_strings_and_typed_handlers(source_tree: Path) -> None:
    """Hand count: quoted/commented spellings contain no calls or handlers."""
    write_source(
        source_tree,
        'import logging\n# print("comment")\ntext = "except: print()"\n'
        "try:\n    logging.info(text)\nexcept ValueError:\n    raise\n",
    )
    result = run_checker(source_tree)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def record_legacy(root: Path, path: Path) -> None:
    baseline = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
    }
    (root / "config/quality/python-hygiene-baseline.json").write_text(
        json.dumps(baseline)
    )


def test_unchanged_legacy_file_passes_but_an_edit_requires_cleanup(
    source_tree: Path,
) -> None:
    """An unchanged-source exception covers the original call, never an edit."""
    path = write_source(source_tree, 'print("legacy")\n')
    record_legacy(source_tree, path)
    assert run_checker(source_tree).returncode == 0
    path.write_text('print("legacy")\nprint("new")\n')
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert result.stdout.count("PY-PRINT") == 2
    assert "BASELINE" in result.stdout


def test_cleaned_legacy_file_requires_removing_its_exception(source_tree: Path) -> None:
    path = write_source(source_tree, 'print("legacy")\n')
    record_legacy(source_tree, path)
    path.write_text('"""Clean source."""\n')
    assert "BASELINE" in run_checker(source_tree).stdout
    (source_tree / "config/quality/python-hygiene-baseline.json").write_text("{}\n")
    assert run_checker(source_tree).returncode == 0


def test_crlf_checkout_preserves_a_legacy_exception(source_tree: Path) -> None:
    """Git line-ending conversion does not introduce or remove style findings."""
    path = write_source(source_tree, 'print("legacy")\n')
    record_legacy(source_tree, path)
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    result = run_checker(source_tree)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "baseline",
    [
        "[]",
        '{"../outside.py": "bad"}',
        '{"src/assetutilities/missing.py": "' + "a" * 64 + '"}',
    ],
)
def test_invalid_or_stale_baseline_fails(source_tree: Path, baseline: str) -> None:
    write_source(source_tree, '"""Clean source."""\n')
    (source_tree / "config/quality/python-hygiene-baseline.json").write_text(baseline)
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert "BASELINE" in result.stdout
    assert "Traceback" not in result.stderr


def test_missing_source_root_fails(tmp_path: Path) -> None:
    result = run_checker(tmp_path)
    assert result.returncode == 1
    assert "SOURCE" in result.stdout


@pytest.mark.parametrize(
    "source", ["def invalid(:\n", 'print("text")\n\x00', "return 1\n"]
)
def test_syntax_errors_fail_without_tracebacks(source_tree: Path, source: str) -> None:
    path = write_source(source_tree, source)
    record_legacy(source_tree, path)
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert "SYNTAX" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("name", ["example.py", "settings.yaml", "settings.yml"])
def test_conflict_markers_are_never_baselined(source_tree: Path, name: str) -> None:
    """Three manually inserted markers produce exactly three MERGE findings."""
    source = "\n".join(['"""', "<" * 7 + " branch", "=" * 7, ">" * 7 + " main", '"""'])
    path = write_source(source_tree, source, name)
    if path.suffix == ".py":
        record_legacy(source_tree, path)
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert result.stdout.count("MERGE") == 3


def test_project_metadata_conflict_is_detected(source_tree: Path) -> None:
    (source_tree / "pyproject.toml").write_text("<" * 7 + " branch\n")
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert "pyproject.toml:1: MERGE" in result.stdout


def test_reads_python_encoding_declarations(source_tree: Path) -> None:
    path = write_source(source_tree, "")
    path.write_bytes(b'# coding: latin-1\ntext = "caf\xe9"\n')
    assert run_checker(source_tree).returncode == 0


def test_missing_baseline_fails(source_tree: Path) -> None:
    (source_tree / "config/quality/python-hygiene-baseline.json").rename(
        source_tree / "config/quality/saved.json"
    )
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert "BASELINE" in result.stdout


def test_clean_file_cannot_be_granted_a_legacy_exception(source_tree: Path) -> None:
    path = write_source(source_tree, '"""No legacy findings."""\n')
    record_legacy(source_tree, path)
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert "BASELINE" in result.stdout


def test_symbolic_source_file_is_rejected(source_tree: Path) -> None:
    target = source_tree / "outside.py"
    target.write_text('"""Not canonical source."""\n')
    path = source_tree / "src/assetutilities/example.py"
    try:
        path.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links are unavailable")
    result = run_checker(source_tree)
    assert result.returncode == 1
    assert "SOURCE" in result.stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="gate requires Bash")
def test_source_gate_invokes_checker_with_inherited_git_bindings(
    tmp_path: Path,
) -> None:
    """The gate must inspect this checkout even with conflicting Git bindings."""
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        env[key] = str(tmp_path / "unrelated")
    env["PYTHON"] = sys.executable
    caller = tmp_path / "caller.txt"
    caller.write_text("preserve caller files\n")
    before = caller.read_bytes()
    git_pointer = ROOT / ".git"
    metadata_before = git_pointer.read_bytes() if git_pointer.is_file() else None
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/hygiene/check-source-hygiene.sh")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: canonical Python source hygiene" in result.stdout
    assert caller.read_bytes() == before
    if metadata_before is not None:
        assert git_pointer.read_bytes() == metadata_before


@pytest.mark.skipif(
    shutil.which("bash") is None or os.name == "nt", reason="POSIX gate test"
)
def test_git_command_failure_is_not_reported_as_clean(tmp_path: Path) -> None:
    fake_git = tmp_path / "git"
    fake_git.write_text("#!/bin/sh\nexit 1\n")
    fake_git.chmod(0o755)
    env = dict(
        os.environ,
        PATH=str(tmp_path) + os.pathsep + os.environ["PATH"],
        PYTHON=sys.executable,
    )
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/hygiene/check-source-hygiene.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "no tracked backup artifacts (command failed)" in result.stderr


def test_worked_example_records_hand_counted_before_and_after(tmp_path: Path) -> None:
    """Independent count: one print + one bare handler before, neither after."""
    output = tmp_path / "worked-example"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples/hygiene/clean_code.py"),
            "--output-dir",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    results = json.loads((output / "results.json").read_text())
    assert results == {
        "before": {"findings": 2, "exit_code": 1},
        "after": {"findings": 0, "exit_code": 0},
    }
    assert (output / "before/src/assetutilities/example.py").is_file()
    assert (output / "after/src/assetutilities/example.py").is_file()


def test_worked_example_preserves_an_existing_output_directory(tmp_path: Path) -> None:
    sentinel = tmp_path / "preserve.txt"
    sentinel.write_text("existing data\n")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples/hygiene/clean_code.py"),
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "output directory already exists" in result.stderr
    assert sentinel.read_text() == "existing data\n"
    assert not (tmp_path / "before").exists()


@pytest.mark.skipif(
    os.name == "nt" or os.geteuid() == 0,
    reason="requires unprivileged POSIX directory permissions",
)
def test_unreadable_nested_directory_fails(source_tree: Path) -> None:
    nested = source_tree / "src/assetutilities/nested"
    nested.mkdir()
    write_source(source_tree, 'print("hidden")\n', "nested/example.py")
    assert "PY-PRINT" in run_checker(source_tree).stdout
    permissions = nested.stat().st_mode
    try:
        nested.chmod(0)
        result = run_checker(source_tree)
    finally:
        nested.chmod(permissions)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "src/assetutilities/nested:0: SOURCE" in result.stdout
    assert "PASS" not in result.stdout
    assert "Traceback" not in result.stderr
    assert "PY-PRINT" in run_checker(source_tree).stdout


@pytest.mark.parametrize("operation", ["iterdir", "stat"])
def test_source_inspection_errors_fail(
    source_tree: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    """Report enumeration and metadata errors even with privileged access."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("hygiene_checker", CHECKER)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    nested = source_tree / "src/assetutilities/nested"
    nested.mkdir()
    path = write_source(source_tree, '"""Clean source."""\n', "nested/example.py")
    target = nested if operation == "iterdir" else path
    original = getattr(Path, operation)

    def unavailable(self: Path, *args, **kwargs):
        if self == target:
            raise PermissionError("inspection unavailable")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, operation, unavailable)
    findings = checker.check(source_tree)
    relative = target.relative_to(source_tree).as_posix()
    assert any(finding.startswith(f"{relative}:0: SOURCE") for finding in findings)
