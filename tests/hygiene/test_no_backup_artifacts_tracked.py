from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _tracked_files(*patterns: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", *patterns],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_no_tracked_backup_artifacts_under_src() -> None:
    assert _tracked_files(":(glob)src/**/*.bak", ":(glob)src/**/*.orig") == []


def test_no_visualizations_scratch_bat_files_in_tests_root() -> None:
    stem = "visualizations_" + "tests"
    assert _tracked_files(
        f"tests/{stem}.bat",
        f"tests/{stem}_temp.bat",
    ) == []


def test_gitignore_blocks_backup_patterns() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "*.bak" in text
    assert "*.orig" in text
