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


def test_folder_ignore_template(monkeypatch):
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
    git_run = subprocess.run

    def run_binary_git(command, **kwargs):
        # Binary pipes preserve LF on Windows as well as on Unix.
        assert isinstance(kwargs["input"], bytes)
        assert not kwargs.get("text", False)
        return git_run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", run_binary_git)
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        cwd=ROOT,
        input="".join(prefix + path + "\n" for path in candidates).encode("utf-8"),
        capture_output=True,
        check=True,
    )
    assert result.stdout.decode("utf-8").splitlines() == [
        prefix + path for path in candidates[-3:]
    ]
