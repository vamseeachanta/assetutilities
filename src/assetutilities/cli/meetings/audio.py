"""Optional local Vosk adapter; no model downloads or network operations.

Format checks, frame size and final-result handling follow the official example:
https://github.com/alphacep/vosk-api/blob/master/python/example/test_simple.py
(unversioned, accessed 2026-10-19).
"""

import importlib
import json
import wave
from pathlib import Path

from .summary import _positive_integer


class _RecognitionResultError(ValueError):
    """Distinguish validated adapter errors from backend exception messages."""


def _result_text(result: str) -> str:
    try:
        data = json.loads(result)
    except (ValueError, TypeError) as exc:
        raise _RecognitionResultError(
            "invalid recognition result: expected JSON text"
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        raise _RecognitionResultError(
            "invalid recognition result: expected a text field"
        )
    return data["text"].strip()


# Source above: 4000 frames per block is a streaming choice, not an accuracy limit.
def transcribe_wav(
    audio_path: Path, model_path: Path, *, block_frames: int = 4000
) -> str:
    """Recognize uncompressed mono two-byte PCM WAV with an existing local model.

    Return completed recognition text separated by newlines. Empty recognition
    returns an empty string; summarization rejects it. The sample rate is read
    from the WAV header. Vosk is imported only for supported audio and a local
    model directory. The model must support the supplied recording's rate.
    """
    if not _positive_integer(block_frames):
        raise ValueError("block_frames must be a positive integer")
    try:
        stream = wave.open(str(audio_path), "rb")
    except (OSError, EOFError, wave.Error) as exc:
        raise ValueError("unable to read a PCM WAV recording") from exc

    with stream:
        # Official example above: 1 channel, 2 bytes/sample, no compression.
        if (
            stream.getnchannels() != 1
            or stream.getsampwidth() != 2
            or stream.getcomptype() != "NONE"
        ):
            raise ValueError("recording must be mono two-byte uncompressed PCM WAV")
        model_path = Path(model_path)
        if not model_path.is_dir():
            raise ValueError("an existing local model directory is required")
        try:
            vosk = importlib.import_module("vosk")
        except ImportError as exc:
            raise ValueError(
                "audio recognition requires the optional vosk package"
            ) from exc

        try:
            # Explicit local path avoids Vosk's model-name/language download mode.
            model = vosk.Model(str(model_path))
            recognizer = vosk.KaldiRecognizer(model, stream.getframerate())
            completed = []
            while True:
                block = stream.readframes(block_frames)
                if not block:
                    break
                if recognizer.AcceptWaveform(block):
                    completed.append(_result_text(recognizer.Result()))
            completed.append(_result_text(recognizer.FinalResult()))
        except _RecognitionResultError:
            raise
        except Exception as exc:
            raise ValueError("local audio recognition failed") from exc
    return "\n".join(text for text in completed if text)
