"""JSON command-line workflow for transcripts and optional offline audio."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Sequence

from .audio import transcribe_wav
from .summary import summarize_transcript


def _budget(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("budget must be a positive integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("budget must be a positive integer")
    return number


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Write JSON to stdout or exclusively create a new report file."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("transcript", "audio"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path)
        command.add_argument("--max-utterances", type=_budget, required=True)
        command.add_argument("--output", type=Path)
        if name == "audio":
            command.add_argument("--model", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "audio":
            text = transcribe_wav(args.input, args.model)
        else:
            text = args.input.read_text(encoding="utf-8-sig")
        report = summarize_transcript(text, max_utterances=args.max_utterances)
        output = json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"
        if args.output is None:
            sys.stdout.write(output)
        else:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(output)
    except FileExistsError:
        print("output already exists; choose a new report file", file=sys.stderr)
        return 1
    except UnicodeError:
        print("input must be a UTF-8 transcript", file=sys.stderr)
        return 1
    except OSError:
        print("unable to read input or create output", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0
