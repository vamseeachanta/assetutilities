"""CLI end-to-end tests with synthetic inputs and independently counted output."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.cli.marketing import main

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "workflows" / "marketing"
AS_OF = "2026-10-20T12:00:00Z"


def test_worked_example_combines_calendar_and_site(capsys):
    """Hand calculation: 14:00+02:00 = 12:00 UTC, so one approved post is due.

    The other post is a draft. Both HTML files share the title Engineering guide.
    The guide omits a description and links to one absent file: two findings.
    """
    assert (
        main(
            [
                "review",
                str(EXAMPLE / "calendar.json"),
                str(EXAMPLE / "html-export"),
                "--as-of",
                AS_OF,
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["calendar"]["counts"] == {
        "draft": 1,
        "due": 1,
        "scheduled": 0,
        "published": 0,
    }
    assert report["calendar"]["channels"] == {"linkedin": 1, "x": 1}
    assert report["website"]["page_count"] == 2
    assert report["website"]["duplicate_titles"] == [
        {"title": "Engineering guide", "paths": ["guide.html", "index.html"]}
    ]
    guide, index = report["website"]["pages"]
    assert guide["findings"] == [
        {"code": "missing_description"},
        {"code": "broken_local_link", "href": "contact.html"},
    ]
    assert index["findings"] == []


@pytest.mark.parametrize("command", ["calendar", "site"])
def test_individual_commands_are_available(command, capsys):
    args = (
        ["calendar", str(EXAMPLE / "calendar.json"), "--as-of", AS_OF]
        if command == "calendar"
        else ["site", str(EXAMPLE / "html-export")]
    )
    assert main(args) == 0
    assert isinstance(json.loads(capsys.readouterr().out), dict)


def test_cli_runs_as_a_module():
    """Exercise the installed-style command in a fresh interpreter."""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "assetutilities.cli.marketing",
            "calendar",
            str(EXAMPLE / "calendar.json"),
            "--as-of",
            AS_OF,
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["counts"]["due"] == 1


@pytest.mark.parametrize(
    "body", ['{"posts":', '{"posts": null}', '{"posts": [], "posts": []}']
)
def test_invalid_json_or_schema_fails_without_partial_output(tmp_path, capsys, body):
    input_file = tmp_path / "calendar.json"
    input_file.write_text(body, encoding="utf-8")
    assert main(["calendar", str(input_file), "--as-of", AS_OF]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Invalid input" in captured.err
    assert str(tmp_path) not in captured.err


def test_missing_file_is_a_concise_error(tmp_path, capsys):
    assert main(["calendar", str(tmp_path / "missing.json"), "--as-of", AS_OF]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert str(tmp_path) not in captured.err


def test_combined_command_does_not_emit_partial_result_on_site_failure(
    tmp_path, capsys
):
    assert (
        main(
            ["review", str(EXAMPLE / "calendar.json"), str(tmp_path), "--as-of", AS_OF]
        )
        == 2
    )
    assert capsys.readouterr().out == ""


def test_requires_explicit_as_of():
    with pytest.raises(SystemExit) as exc:
        main(["calendar", str(EXAMPLE / "calendar.json")])
    assert exc.value.code == 2
