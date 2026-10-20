"""CLI integration against temporary local files; nothing launches Obsidian.

Expected file sets and matches are manually enumerated, as described by the
worked example in docs/modules/knowledge-management.md (2026).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.cli.knowledge import main


def test_cli_worked_example(tmp_path, capsys):
    """Two captured files minus one nonmatching file leaves one search result."""
    root = tmp_path / "vault"
    assert main(["init", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["created"] == [
        "Home.md",
        "Templates/Note.md",
    ]
    body = tmp_path / "input.md"
    body.write_text("Backlinks connect notes.\n", encoding="utf-8")
    assert (
        main(
            [
                "capture",
                str(root),
                "link-basics",
                "--title",
                "Link basics",
                "--body-file",
                str(body),
                "--source",
                "Local handbook",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == {
        "created": "Inbox/note-link-basics.md"
    }
    body.write_text("Review captured notes.\n", encoding="utf-8")
    assert (
        main(
            [
                "capture",
                str(root),
                "review",
                "--title",
                "Review checklist",
                "--body-file",
                str(body),
                "--source",
                "Local checklist",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(["search", str(root), "backlinks"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "notes": [{"path": "Inbox/note-link-basics.md", "title": "Link basics"}]
    }
    assert main(["doctor", str(root), "--executable", str(tmp_path / "absent")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["vault"] == "READY"
    assert report["application"] == "NOT_FOUND"
    assert report["launch"] == "NOT_EVALUATED"


def test_cli_errors_do_not_expose_absolute_paths(tmp_path, capsys):
    missing = tmp_path / "missing"
    assert main(["search", str(missing)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert str(tmp_path) not in captured.err
    assert "initialized vault" in captured.err


def test_cli_reports_io_errors_without_traceback(tmp_path, capsys):
    root = tmp_path / "vault"
    assert main(["init", str(root)]) == 0
    capsys.readouterr()
    assert (
        main(
            [
                "capture",
                str(root),
                "example",
                "--title",
                "Title",
                "--body-file",
                str(tmp_path / "absent"),
                "--source",
                "Reference",
            ]
        )
        == 1
    )
    error = capsys.readouterr().err
    assert "FileNotFoundError" in error
    assert str(tmp_path) not in error
    assert "Traceback" not in error


def test_cli_source_is_required(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(
            [
                "capture",
                str(tmp_path),
                "example",
                "--title",
                "Title",
                "--body-file",
                "input.md",
            ]
        )
    assert error.value.code == 2  # argparse usage-error contract.


def test_cli_runs_as_module(tmp_path):
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ, PYTHONPATH=str(root / "src"))
    # Fixture isolation: inherited Git bindings must not select another checkout.
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        environment.pop(key, None)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "assetutilities.cli.knowledge",
            "init",
            str(tmp_path / "vault"),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["created"] == ["Home.md", "Templates/Note.md"]


def test_documented_example_uses_committed_inputs(tmp_path, capsys):
    """Hand inventory: only the link-basics input, title or source matches backlinks.

    The expected JSON is written independently alongside the inputs. The review
    note is a negative control; templates and navigation are excluded.
    """
    examples = (
        Path(__file__).resolve().parents[2]
        / "examples"
        / "workflows"
        / "knowledge_management"
    )
    root = tmp_path / "vault"
    assert main(["init", str(root)]) == 0
    for slug, title, source in (
        ("link-basics", "Link basics", "Synthetic example: link basics"),
        ("review", "Review checklist", "Synthetic example: review checklist"),
    ):
        assert (
            main(
                [
                    "capture",
                    str(root),
                    slug,
                    "--title",
                    title,
                    "--body-file",
                    str(examples / f"{slug}.md"),
                    "--source",
                    source,
                ]
            )
            == 0
        )
    capsys.readouterr()
    assert main(["search", str(root), "backlinks"]) == 0
    assert json.loads(capsys.readouterr().out) == json.loads(
        (examples / "expected-search.json").read_text(encoding="utf-8")
    )
