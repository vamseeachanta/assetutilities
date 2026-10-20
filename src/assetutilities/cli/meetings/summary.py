"""Deterministic leading extracts; method is defined in docs/modules/meetings.md."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    """Original utterance text with a one-based source number."""

    number: int
    text: str


@dataclass(frozen=True)
class MeetingSummary:
    """Extracts and candidates, with the complete transcript for review."""

    transcript: tuple[Evidence, ...]
    highlights: tuple[Evidence, ...]
    decisions: tuple[Evidence, ...]
    action_items: tuple[Evidence, ...]
    not_evaluated: tuple[str, ...]


def _positive_integer(value: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def summarize_transcript(text: str, *, max_utterances: int) -> MeetingSummary:
    """Select leading utterances and explicitly labelled decision/action candidates.

    The caller supplies the extract budget. This rule has no fitted constants
    or accuracy threshold. Labels must start an utterance; ownership and intent
    remain unevaluated. Candidate extracts are independent of the budget.
    """
    if not isinstance(text, str):
        raise TypeError("transcript must be text")
    if not _positive_integer(max_utterances):
        raise ValueError("max_utterances must be a positive integer")
    parts = (part.strip() for part in re.split(r"[\r\n]+|(?<=[.!?])\s+", text))
    transcript = tuple(
        Evidence(number, part)
        for number, part in enumerate((part for part in parts if part), start=1)
    )
    if not transcript:
        raise ValueError("transcript must contain nonempty text")

    def candidates(label: str) -> tuple[Evidence, ...]:
        pattern = re.compile(rf"^{label}(?:\s*:|\s+)\s*[^\s:]", re.IGNORECASE)
        return tuple(item for item in transcript if pattern.match(item.text))

    return MeetingSummary(
        transcript=transcript,
        highlights=transcript[:max_utterances],
        decisions=candidates("decision"),
        action_items=candidates("action"),
        not_evaluated=(
            "recognition_accuracy",
            "speaker_identity",
            "action_ownership",
            "deadlines",
        ),
    )
