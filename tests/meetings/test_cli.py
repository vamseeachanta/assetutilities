"""CLI integration with synthetic transcripts and a local recognition double."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from assetutilities.cli.meetings.cli import main


def test_transcript_stdout(tmp_path, capsys):
    path = tmp_path / "transcript.txt"
    path.write_text("\ufeffAgenda.\nAction: prepare notes.", encoding="utf-8")
    assert main(["transcript", str(path), "--max-utterances", "1"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["highlights"] == [{"number": 1, "text": "Agenda."}]
    assert output["action_items"] == [{"number": 2, "text": "Action: prepare notes."}]


def test_output_file_refuses_overwrite(tmp_path, capsys):
    path = tmp_path / "transcript.txt"
    path.write_text("Agenda.")
    target = tmp_path / "summary.json"
    args = ["transcript", str(path), "--max-utterances", "1", "--output", str(target)]
    assert main(args) == 0
    original = target.read_bytes()
    assert json.loads(original)["highlights"][0]["text"] == "Agenda."
    assert main(args) == 1
    assert target.read_bytes() == original
    assert "exists" in capsys.readouterr().err


@pytest.mark.parametrize("content", [b"", b"\xff"])
def test_invalid_transcript_never_creates_output(tmp_path, capsys, content):
    path = tmp_path / "transcript.txt"
    path.write_bytes(content)
    target = tmp_path / "summary.json"
    assert (
        main(
            ["transcript", str(path), "--max-utterances", "1", "--output", str(target)]
        )
        == 1
    )
    assert not target.exists()
    assert not capsys.readouterr().out


def test_missing_input(tmp_path, capsys):
    assert main(["transcript", str(tmp_path / "missing"), "--max-utterances", "1"]) == 1
    assert not capsys.readouterr().out


@pytest.mark.parametrize("budget", ["0", "-1", "1.5"])
def test_invalid_budget(tmp_path, budget):
    with pytest.raises(SystemExit) as error:
        main(["transcript", str(tmp_path / "unused"), "--max-utterances", budget])
    assert error.value.code == 2


def test_audio_requires_model(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["audio", str(tmp_path / "unused"), "--max-utterances", "1"])
    assert error.value.code == 2


def test_audio_pipeline(tmp_path, capsys, monkeypatch):
    from assetutilities.cli.meetings import cli

    def transcribe(path, model):
        assert path == tmp_path / "recording.wav"
        assert model == tmp_path / "model"
        return "Agenda\nDecision use checklist\nAction prepare notes"

    monkeypatch.setattr(cli, "transcribe_wav", transcribe)
    assert (
        main(
            [
                "audio",
                str(tmp_path / "recording.wav"),
                "--model",
                str(tmp_path / "model"),
                "--max-utterances",
                "1",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["decisions"][0]["number"] == 2
    assert result["action_items"][0]["number"] == 3


def test_module_entry_point():
    """Expected JSON is independently enumerated in the example documentation."""
    root = Path(__file__).resolve().parents[2]
    expected = json.loads((root / "examples/meetings/expected.json").read_text())
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "assetutilities.cli.meetings",
            "transcript",
            "examples/meetings/transcript.txt",
            "--max-utterances",
            "2",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == expected
    assert not result.stderr
