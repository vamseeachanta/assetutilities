"""TDD coverage for the assetutilities repo-structure contract checker."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "maintenance" / "verify_repo_structure.py"
CONFIG = REPO_ROOT / "config" / "repo_structure.yml"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "tests.yml"
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"


def write_contract(tmp_path: Path) -> Path:
    contract = {
        "allowed_root_files": ["README.md", ".gitignore"],
        "allowed_root_dirs": ["src", "tests", "docs", "results"],
        "generated_roots": ["results", "reports"],
        "generated_exceptions": [
            {
                "path": "results",
                "category": "durable-evidence",
                "owner": "assetutilities-maintainers",
                "review_date": "2026-06-30",
                "follow_up_url": "https://github.com/vamseeachanta/assetutilities/issues/78",
                "reason": "Tracked legacy evidence awaiting classified migration.",
                "allowed_paths": ["results/evidence.csv"],
            }
        ],
    }
    path = tmp_path / "repo_structure.yml"
    path.write_text(yaml.safe_dump(contract), encoding="utf-8")
    return path


def run_checker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_checker_rejects_unapproved_root_entry(tmp_path: Path) -> None:
    config = write_contract(tmp_path)

    result = run_checker(
        "--config",
        str(config),
        "--tracked-files",
        "README.md",
        "src/assetutilities/__init__.py",
        "scratch.txt",
    )

    assert result.returncode == 1
    assert "unapproved root entry: scratch.txt" in result.stderr


def test_checker_rejects_tracked_generated_root_without_exception(tmp_path: Path) -> None:
    config = write_contract(tmp_path)

    result = run_checker(
        "--config",
        str(config),
        "--tracked-files",
        "README.md",
        "reports/build-output.html",
    )

    assert result.returncode == 1
    assert "tracked generated root lacks exception metadata: reports" in result.stderr


def test_checker_rejects_new_generated_artifact_under_exceptioned_root(
    tmp_path: Path,
) -> None:
    config = write_contract(tmp_path)

    result = run_checker(
        "--config",
        str(config),
        "--tracked-files",
        "README.md",
        "results/new-output.csv",
    )

    assert result.returncode == 1
    assert "tracked generated path lacks explicit allowance: results/new-output.csv" in result.stderr


def test_checker_rejects_untracked_unapproved_working_tree_root(
    tmp_path: Path,
) -> None:
    config = write_contract(tmp_path)

    result = run_checker(
        "--config",
        str(config),
        "--tracked-files",
        "README.md",
        "--working-tree-files",
        "scratch.txt",
    )

    assert result.returncode == 1
    assert "unapproved root entry: scratch.txt" in result.stderr


def test_checker_rejects_placeholder_exception_metadata(tmp_path: Path) -> None:
    config = tmp_path / "repo_structure.yml"
    config.write_text(
        yaml.safe_dump(
            {
                "allowed_root_files": ["README.md"],
                "allowed_root_dirs": ["results"],
                "generated_roots": ["results"],
                "generated_exceptions": [
                    {
                        "path": "results",
                        "category": "TODO",
                        "owner": "TBD",
                        "review_date": "YYYY-MM-DD",
                        "follow_up_url": "TODO",
                        "reason": "placeholder",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_checker("--config", str(config), "--tracked-files", "results/evidence.csv")

    assert result.returncode == 1
    assert "placeholder exception metadata" in result.stderr


def test_checker_accepts_current_approved_contract() -> None:
    result = run_checker("--config", str(CONFIG))

    assert result.returncode == 0, result.stderr
    assert "repo-structure contract passed" in result.stdout


def test_reference_scan_blocks_candidate_moves_with_live_consumers() -> None:
    scan_root = REPO_ROOT / ".pytest_repo_structure_reference_scan"
    shutil.rmtree(scan_root, ignore_errors=True)
    try:
        consumer = scan_root / "docs" / "note.md"
        consumer.parent.mkdir(parents=True)
        consumer.write_text("Keep results/evidence.csv linked.\n", encoding="utf-8")

        result = run_checker(
            "--reference-scan-root",
            str(scan_root),
            "--candidate-move",
            "results/evidence.csv",
        )
    finally:
        shutil.rmtree(scan_root, ignore_errors=True)

    assert result.returncode == 1
    assert "candidate move has live references: results/evidence.csv" in result.stderr


def test_ci_and_pre_commit_invoke_repo_structure_checker() -> None:
    command = "uv run python scripts/maintenance/verify_repo_structure.py"

    assert command in WORKFLOW.read_text(encoding="utf-8")
    assert "verify-repo-structure" in PRE_COMMIT.read_text(encoding="utf-8")
    assert "scripts/maintenance/verify_repo_structure.py" in PRE_COMMIT.read_text(
        encoding="utf-8"
    )
