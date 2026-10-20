# Meeting audio and transcript summaries

The meetings utility turns a UTF-8 transcript, or a supported WAV recording,
into a JSON extractive summary. It retains the complete transcript as numbered
utterances so every highlight, decision candidate and action candidate can be
checked against its source. Processing is local; the utility makes no network
requests and does not download a speech model.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-19 | Add a local voice-to-summary workflow with traceable extracts. |

## Method and scope

1. Split text at line breaks or whitespace following `.`, `!` or `?`; preserve
   the text within each resulting utterance, stripping surrounding whitespace.
   Number nonempty utterances in input order, starting at one.
2. Select the first `max_utterances` utterances as highlights. The caller must
   supply this positive integer; there is no calibrated importance threshold.
3. Collect utterances starting with `Decision:` or `Action:` (case insensitive)
   as decision or action candidates. The spoken forms `decision ...` and
   `action ...` are also accepted, because recognition can omit punctuation.
   Candidates are collected from the entire transcript, independently of the
   highlight budget. The labels are conventions defined here, not inferred
   intent. No speaker, assignee or due date is invented.
4. For audio, feed WAV frames to a locally supplied Vosk model, keep each
   completed recognition result, and flush the final result. Separate completed
   results with newlines. Partial recognition results are not final evidence.

There are no engineering equations, fitted coefficients, confidence limits or
accuracy acceptance thresholds. Highlight selection is a deterministic leading
extract, not an abstractive or semantic summary. The output lists
`recognition_accuracy`, `speaker_identity`, `action_ownership` and `deadlines`
as `not_evaluated`. An empty input or audio with no recognized text is an error.

## Transcript example: inputs, method and answer

The synthetic input is [transcript.txt](../../examples/meetings/transcript.txt):

```text
Review the agenda.
Decision: use the checklist.
Action: prepare the checklist.
Discuss the next review.
```

Run from a source checkout, or omit `PYTHONPATH=src` with the package installed:

```sh
PYTHONPATH=src python -m assetutilities.cli.meetings transcript \
  examples/meetings/transcript.txt --max-utterances 2
```

By hand, splitting yields four utterances. A budget of two selects “Review the
agenda.” and “Decision: use the checklist.” as highlights. The decision candidate
is utterance two; the action candidate is utterance three, even though it is
outside the highlight budget. The complete expected JSON is
[expected.json](../../examples/meetings/expected.json). These counts and the
budget are synthetic example inputs and direct counts, not empirical constants.

```python
from assetutilities.cli.meetings import summarize_transcript

result = summarize_transcript("Agenda.\nAction: prepare notes.", max_utterances=1)
assert result.highlights[0].text == "Agenda."
assert result.action_items[0].number == 2
```

## Offline audio

Vosk is an optional Python dependency supplied by the caller's environment.
The transcript workflow uses only the Python standard library. Supply an
existing local model directory; no model name or language-based download is
used. Model availability, licence and suitability must be checked separately.

```sh
PYTHONPATH=src python -m assetutilities.cli.meetings audio recording.wav \
  --model models/speech --max-utterances 2 --output summary.json
```

`--output` creates a new file exclusively and refuses to overwrite an existing
file. Without it, JSON is written to standard output. Invalid input, missing
dependencies and recognition failures produce a nonzero exit status with no
JSON report. Inputs are never changed. The CLI does not record a microphone or
join a meeting.

Supported audio is uncompressed mono PCM WAV with a two-byte sample width;
the sample rate from the WAV header is passed to the recognizer. The frame
block size follows the upstream example (4,000 frames), and can be supplied
explicitly to the Python `transcribe_wav` function. These format values and the
block size come from the official
[Vosk Python example](https://github.com/alphacep/vosk-api/blob/master/python/example/test_simple.py)
(unversioned, accessed 2026-10-19), not an accuracy guarantee. The official
[installation and audio guidance](https://alphacephei.com/vosk/install)
(unversioned, accessed 2026-10-19) describes model and runtime requirements.
The model must support the actual recording's language and sample rate.

## Known limits and later slices

Sentence splitting is deliberately simple: abbreviations, timestamps and
speaker labels are not parsed. Repeated utterances remain separate evidence.
Unpunctuated text is one utterance per line or completed audio result, so an
extract can be long. A bare final recognition result can contain an entire
recording. Labels identify candidates for review, including negated or quoted
statements, and cannot establish an approved decision or assigned action.

The audio adapter is tested with a protocol double and synthetic PCM fixtures.
Real speech accuracy is not evaluated without a supplied model and a reference
transcript. Later slices include model-specific accuracy evaluation, diarization,
timestamps, richer sentence segmentation, semantic summarization and live capture.
No accuracy or speaker-attribution claim follows from the adapter tests.
