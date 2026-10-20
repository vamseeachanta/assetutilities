"""Executable examples and real Git ignore semantics."""

import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_offline_config_example():
    """Hand overlay: item URL replaces default; output and save flag survive."""
    example = runpy.run_path(str(ROOT / "examples/release/offline_config.py"))[
        "example"
    ]
    assert example() == [
        {
            "url": "https://example.invalid/sample",
            "save_csv": True,
            "output_dir": "results",
            "label": "sample",
        }
    ]


def test_folder_ignore_template():
    """Git's pattern rules predict only generated/non-YAML paths are ignored.

    Source: gitignore manual, Pattern format, negation and directory patterns.
    No fixture files or Git metadata need to be written for check-ignore.
    """
    prefix = "examples/source-layout/runs/"
    candidates = [
        ".gitignore",
        "inputs/case.yml",
        "inputs/case.yaml",
        "inputs/result.csv",
        "outputs/result.csv",
        "logs/run.log",
    ]
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        cwd=ROOT,
        input="".join(prefix + path + "\n" for path in candidates),
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.splitlines() == [prefix + path for path in candidates[-3:]]
