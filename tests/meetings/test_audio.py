"""Adapter expectations follow the official Vosk example linked in audio.py.

Synthetic samples are zero-valued bytes, not a speech accuracy benchmark.
"""

import json
import sys
import wave
from types import SimpleNamespace

import pytest

from assetutilities.cli.meetings import transcribe_wav


def make_wav(tmp_path, *, channels=1, width=2, frames=5):
    """Test inputs: arbitrary sample rate 8000, and `frames` silent PCM frames."""
    path = tmp_path / "recording.wav"
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(width)
        stream.setframerate(8000)
        stream.writeframes(b"\x00" * frames * width * channels)
    return path


def fake_vosk(monkeypatch, *, final='{"text": "action prepare notes"}'):
    state = {"blocks": [], "final_calls": 0, "result_calls": 0}

    class Recognizer:
        def __init__(self, model, sample_rate):
            state["sample_rate"] = sample_rate
            state["model"] = model

        def AcceptWaveform(self, data):
            state["blocks"].append(data)
            return len(state["blocks"]) == 1

        def Result(self):
            state["result_calls"] += 1
            return json.dumps({"text": "decision use checklist"})

        def FinalResult(self):
            state["final_calls"] += 1
            return final

    monkeypatch.setitem(
        sys.modules,
        "vosk",
        SimpleNamespace(Model=lambda path: path, KaldiRecognizer=Recognizer),
    )
    return state


def test_streaming_retains_completed_and_final_results(tmp_path, monkeypatch):
    """Hand count: 5 mono two-byte frames / block 2 -> byte lengths 4,4,2."""
    path = make_wav(tmp_path)
    model = tmp_path / "model"
    model.mkdir()
    state = fake_vosk(monkeypatch)
    text = transcribe_wav(path, model, block_frames=2)
    assert text == "decision use checklist\naction prepare notes"
    assert [len(block) for block in state["blocks"]] == [4, 4, 2]
    assert state["sample_rate"] == 8000
    assert state["model"] == str(model)
    assert state["result_calls"] == state["final_calls"] == 1
    assert path.read_bytes()  # Input remains present and readable.


@pytest.mark.parametrize("channels,width", [(2, 2), (1, 1), (1, 3)])
def test_reject_unsupported_pcm(tmp_path, monkeypatch, channels, width):
    path = make_wav(tmp_path, channels=channels, width=width)
    monkeypatch.setitem(sys.modules, "vosk", None)
    with pytest.raises(ValueError, match="mono.*PCM"):
        transcribe_wav(path, tmp_path)


def test_bad_wav(tmp_path):
    path = tmp_path / "invalid.wav"
    path.write_bytes(b"not a WAV")
    with pytest.raises(ValueError, match="WAV"):
        transcribe_wav(path, tmp_path)


def test_missing_model_never_requests_download(tmp_path):
    path = make_wav(tmp_path)
    with pytest.raises(ValueError, match="local model directory"):
        transcribe_wav(path, tmp_path / "missing")


def test_optional_dependency_missing(tmp_path, monkeypatch):
    path = make_wav(tmp_path)
    monkeypatch.setitem(sys.modules, "vosk", None)
    with pytest.raises(ValueError, match="optional vosk"):
        transcribe_wav(path, tmp_path)


@pytest.mark.parametrize("block_frames", [0, -1, True, 0.5])
def test_invalid_block_size(tmp_path, block_frames):
    with pytest.raises(ValueError, match="positive integer"):
        transcribe_wav(tmp_path / "unused.wav", tmp_path, block_frames=block_frames)


@pytest.mark.parametrize("final", ["not JSON", "[]", '{"text": 1}', "{}"])
def test_invalid_recognizer_result(tmp_path, monkeypatch, final):
    path = make_wav(tmp_path)
    fake_vosk(monkeypatch, final=final)
    with pytest.raises(ValueError, match="recognition result"):
        transcribe_wav(path, tmp_path)


def test_empty_audio_result(tmp_path, monkeypatch):
    path = make_wav(tmp_path, frames=0)
    state = fake_vosk(monkeypatch, final='{"text": ""}')
    assert transcribe_wav(path, tmp_path) == ""
    assert state["blocks"] == []
    assert state["final_calls"] == 1


def test_model_initialization_failure(tmp_path, monkeypatch):
    def fail_model(path):
        raise RuntimeError("invalid model")

    path = make_wav(tmp_path)
    monkeypatch.setitem(sys.modules, "vosk", SimpleNamespace(Model=fail_model))
    with pytest.raises(ValueError, match="recognition failed"):
        transcribe_wav(path, tmp_path)


def test_backend_value_error_is_sanitized(tmp_path, monkeypatch):
    def fail_model(path):
        raise ValueError("backend details must not become the public error")

    path = make_wav(tmp_path)
    monkeypatch.setitem(sys.modules, "vosk", SimpleNamespace(Model=fail_model))
    with pytest.raises(ValueError, match="^local audio recognition failed$"):
        transcribe_wav(path, tmp_path)


def test_audio_to_json_pipeline(tmp_path, monkeypatch, capsys):
    """Two finalized phrases -> decision at 1, action at 2; highlight budget 1."""
    from assetutilities.cli.meetings.cli import main

    path = make_wav(tmp_path)
    fake_vosk(monkeypatch)
    assert (
        main(["audio", str(path), "--model", str(tmp_path), "--max-utterances", "1"])
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["transcript"] == [
        {"number": 1, "text": "decision use checklist"},
        {"number": 2, "text": "action prepare notes"},
    ]
    assert result["highlights"] == result["decisions"] == result["transcript"][:1]
    assert result["action_items"] == result["transcript"][1:]


def test_silence_never_produces_report(tmp_path, monkeypatch, capsys):
    from assetutilities.cli.meetings.cli import main

    path = make_wav(tmp_path, frames=0)
    fake_vosk(monkeypatch, final='{"text": ""}')
    target = tmp_path / "summary.json"
    assert (
        main(
            [
                "audio",
                str(path),
                "--model",
                str(tmp_path),
                "--max-utterances",
                "1",
                "--output",
                str(target),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert not captured.out
    assert "nonempty" in captured.err
    assert not target.exists()
