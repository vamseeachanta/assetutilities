"""Expectations are direct enumeration of synthetic utterances, not model output."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from assetutilities.cli.meetings import summarize_transcript


def test_worked_example():
    """Hand calculation: 4 lines; budget 2 selects lines 1,2; labels at 2,3."""
    examples = Path(__file__).resolve().parents[2] / "examples" / "meetings"
    result = summarize_transcript(
        (examples / "transcript.txt").read_text(), max_utterances=2
    )
    assert json.loads(json.dumps(asdict(result))) == json.loads(
        (examples / "expected.json").read_text()
    )


def test_sentence_boundaries_and_order():
    """Enumerate punctuation boundaries: One., Two!, Three?, Decision: proceed."""
    result = summarize_transcript(
        " One. Two!\n\nThree? Decision: proceed. ", max_utterances=3
    )
    assert [(item.number, item.text) for item in result.transcript] == [
        (1, "One."),
        (2, "Two!"),
        (3, "Three?"),
        (4, "Decision: proceed."),
    ]
    assert result.highlights == result.transcript[:3]
    assert result.decisions == (result.transcript[3],)


def test_candidates_include_items_beyond_budget():
    """First line is highlighted; decision/action labels occur on lines 2 and 3."""
    result = summarize_transcript(
        "Agenda\r\nDECISION use checklist\rAction: prepare notes", max_utterances=1
    )
    assert result.highlights[0].text == "Agenda"
    assert result.decisions[0].text == "DECISION use checklist"
    assert result.action_items[0].text == "Action: prepare notes"
    assert result.not_evaluated == (
        "recognition_accuracy",
        "speaker_identity",
        "action_ownership",
        "deadlines",
    )


@pytest.mark.parametrize(
    "text", ["A decision was discussed.", "Actionable topics.", "Decisionary notes."]
)
def test_only_explicit_initial_labels_are_candidates(text):
    result = summarize_transcript(text, max_utterances=1)
    assert not result.decisions
    assert not result.action_items


def test_repetitions_and_unicode_preserve_evidence():
    """Three input lines remain three extracts, including repeated text."""
    result = summarize_transcript("Café ready.\nCafé ready.\n行动", max_utterances=9)
    assert [item.text for item in result.highlights] == [
        "Café ready.",
        "Café ready.",
        "行动",
    ]
    assert [item.number for item in result.transcript] == [1, 2, 3]


@pytest.mark.parametrize("budget", [0, -1, True, 1.5, "2", None])
def test_invalid_budget(budget):
    with pytest.raises(ValueError, match="positive integer"):
        summarize_transcript("Agenda", max_utterances=budget)


@pytest.mark.parametrize("text", ["", " \t\r\n"])
def test_empty_transcript(text):
    with pytest.raises(ValueError, match="nonempty"):
        summarize_transcript(text, max_utterances=1)


def test_non_text_transcript():
    with pytest.raises(TypeError, match="text"):
        summarize_transcript(b"Agenda", max_utterances=1)


@pytest.mark.parametrize("label", ["Decision:", "Action :", "Action   :  "])
def test_bare_labels_have_no_candidate_content(label):
    result = summarize_transcript(label, max_utterances=1)
    assert not result.decisions
    assert not result.action_items
