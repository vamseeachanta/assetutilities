"""Readiness truth tables use explicit hand-derived Boolean expectations.

No engineering coefficients or hardware acceptance limits are assumed.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.devtools import readiness


def complete_evidence():
    return {
        item.key: {"ready": True, "basis": "Recorded functional exercise"}
        for item in readiness.CHECKLIST
    }


def test_missing_evidence_is_not_evaluated():
    """An empty input establishes no check; unknown AND unknown is unknown."""
    report = readiness.assess_readiness({})
    assert report["status"] == "NOT_EVALUATED"
    assert {item["status"] for item in report["checks"]} == {"NOT_EVALUATED"}
    assert all(item["next_step"] for item in report["checks"])


def test_every_issue_item_is_represented():
    assert {item.key for item in readiness.CHECKLIST} == {
        "repository_access",
        "github_access",
        "git",
        "daily_git_cycle",
        "autocad",
        "freecad",
        "blender_access",
        "audio",
        "meeting_access",
        "meeting_scheduling",
        "python",
        "conda",
        "python_exercise",
        "notepad_plus_plus",
        "vscode",
    }


def test_all_true_is_ready():
    """Hand derivation: every required proposition is true, so their AND is true."""
    report = readiness.assess_readiness(complete_evidence())
    assert report["status"] == "READY"
    assert all(item["status"] == "READY" for item in report["checks"])
    assert all(item["next_step"] is None for item in report["checks"])


@pytest.mark.parametrize("key", [item.key for item in readiness.CHECKLIST])
def test_any_false_requires_action(key):
    """Hand derivation: a false operand makes the required conjunction false."""
    evidence = complete_evidence()
    evidence[key] = {"ready": False, "basis": "Functional exercise failed"}
    report = readiness.assess_readiness(evidence)
    assert report["status"] == "ACTION_REQUIRED"
    failed = next(item for item in report["checks"] if item["key"] == key)
    assert failed["status"] == "ACTION_REQUIRED"
    assert failed["next_step"]


def test_false_takes_precedence_over_unknown():
    report = readiness.assess_readiness(
        {"git": {"ready": False, "basis": "Not installed"}}
    )
    assert report["status"] == "ACTION_REQUIRED"


def test_unknown_prevents_ready():
    evidence = complete_evidence()
    evidence["blender_access"] = {"ready": None}
    assert readiness.assess_readiness(evidence)["status"] == "NOT_EVALUATED"


@pytest.mark.parametrize(
    "evidence",
    [
        [],
        None,
        {"unknown": {"ready": True}},
        {"git": True},
        {"git": {}},
        {"git": {"ready": "false", "basis": "Recorded"}},
        {"git": {"ready": 1, "basis": "Recorded"}},
        {"git": {"ready": False}},
        {"git": {"ready": True, "basis": " "}},
        {"git": {"ready": True, "basis": []}},
        {"git": {"ready": None, "extra": "unexpected"}},
    ],
)
def test_invalid_evidence_is_rejected(evidence):
    with pytest.raises(ValueError):
        readiness.assess_readiness(evidence)


def test_report_does_not_echo_private_evidence(tmp_path):
    private_basis = str(tmp_path / "private-record")
    report = readiness.assess_readiness(
        {"git": {"ready": True, "basis": private_basis}}
    )
    assert private_basis not in json.dumps(report)


def test_discovery_is_separate_from_readiness(monkeypatch):
    calls = []

    def which(command):
        calls.append(command)
        return "private-installation" if command == "python3" else None

    monkeypatch.setattr(readiness.shutil, "which", which)
    observations = readiness.discover_commands()
    assert observations["python"] is True
    assert observations["git"] is False
    assert "autocad" not in observations
    assert "private-installation" not in json.dumps(observations)
    assert set(calls) <= {
        "git",
        "python3",
        "python",
        "conda",
        "FreeCAD",
        "freecad",
        "blender",
        "code",
        "notepad++",
    }
    assert readiness.assess_readiness({})["status"] == "NOT_EVALUATED"


def test_discovery_uses_executable_lookup(tmp_path, monkeypatch):
    """A real empty PATH has no Git; a local executable makes it discoverable."""
    monkeypatch.setenv("PATH", str(tmp_path))
    assert readiness.discover_commands()["git"] is False
    command = tmp_path / ("git.exe" if os.name == "nt" else "git")
    command.write_text("unused executable placeholder", encoding="utf-8")
    command.chmod(command.stat().st_mode | 0o111)  # POSIX execute bits.
    assert readiness.discover_commands()["git"] is True


def test_cli_template_round_trip(tmp_path, capsys):
    assert readiness.main(["--template"]) == 0
    template = json.loads(capsys.readouterr().out)
    source = tmp_path / "evidence.json"
    source.write_text(json.dumps(template), encoding="utf-8")
    assert readiness.main(["--input", str(source), "--require-ready"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_EVALUATED"


def test_cli_ready_and_discovery(tmp_path, capsys, monkeypatch):
    source = tmp_path / "evidence.json"
    source.write_text(json.dumps(complete_evidence()), encoding="utf-8")
    monkeypatch.setattr(readiness.shutil, "which", lambda command: None)
    assert (
        readiness.main(["--input", str(source), "--discover", "--require-ready"]) == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "READY"
    assert not any(report["commands_on_path"].values())


@pytest.mark.parametrize(
    "contents", ["{", "[]", '{"git": true}', '{"git": null, "git": null}']
)
def test_cli_invalid_input_has_sanitized_error(tmp_path, capsys, contents):
    source = tmp_path / "private-evidence.json"
    source.write_text(contents, encoding="utf-8")
    with pytest.raises(SystemExit) as caught:
        readiness.main(["--input", str(source)])
    assert caught.value.code == 2  # argparse input-error convention.
    output = capsys.readouterr()
    assert output.out == ""
    assert str(source) not in output.err
    assert contents not in output.err


def test_cli_missing_file_has_sanitized_error(tmp_path, capsys):
    source = tmp_path / "missing.json"
    with pytest.raises(SystemExit):
        readiness.main(["--input", str(source)])
    assert str(source) not in capsys.readouterr().err


@pytest.mark.parametrize("option", ["--discover", "--require-ready"])
def test_template_rejects_assessment_options(option):
    with pytest.raises(SystemExit):
        readiness.main(["--template", option])


def test_module_cli(tmp_path):
    """The shipped invocation emits JSON and fails an incomplete readiness gate."""
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ, PYTHONPATH=str(root / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "assetutilities.devtools.readiness", "--require-ready"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "NOT_EVALUATED"


def test_worked_example(capsys):
    """By hand: Git true, daily cycle false, all others unknown => action."""
    root = Path(__file__).resolve().parents[2]
    example = root / "examples/devtools/readiness.json"
    assert readiness.main(["--input", str(example)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "ACTION_REQUIRED"
    by_key = {item["key"]: item["status"] for item in report["checks"]}
    assert by_key["git"] == "READY"
    assert by_key["daily_git_cycle"] == "ACTION_REQUIRED"
    assert by_key["blender_access"] == "NOT_EVALUATED"
