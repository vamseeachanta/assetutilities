"""Create, capture, search and inspect a local knowledge vault.

Run with ``python -m assetutilities.cli.knowledge --help``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from assetutilities.common.knowledge_management import (
    capture_note,
    check_setup,
    initialize_vault,
    search_notes,
)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI status codes follow docs/modules/knowledge-management.md (2026)."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init", help="Create missing starter files")
    initialize.add_argument("vault", type=Path)
    capture = commands.add_parser(
        "capture", help="Capture a note with a required source"
    )
    capture.add_argument("vault", type=Path)
    capture.add_argument("slug")
    capture.add_argument("--title", required=True)
    capture.add_argument("--body-file", required=True, type=Path)
    capture.add_argument("--source", required=True)
    search = commands.add_parser("search", help="Search local Markdown notes")
    search.add_argument("vault", type=Path)
    search.add_argument("query", nargs="?", default="")
    doctor = commands.add_parser(
        "doctor", help="Inspect setup without launching an app"
    )
    doctor.add_argument("vault", type=Path)
    doctor.add_argument("--executable", type=Path)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "init":
            result = {"created": list(initialize_vault(arguments.vault))}
        elif arguments.command == "capture":
            result = {
                "created": capture_note(
                    arguments.vault,
                    arguments.slug,
                    title=arguments.title,
                    body=arguments.body_file.read_text(encoding="utf-8"),
                    source=arguments.source,
                )
            }
        elif arguments.command == "search":
            result = {
                "notes": [
                    asdict(note)
                    for note in search_notes(arguments.vault, arguments.query)
                ]
            }
        else:
            result = check_setup(arguments.vault, executable=arguments.executable)
    except ValueError as error:
        # UnicodeError can include supplied text; report only the error kind.
        message = (
            type(error).__name__ if isinstance(error, UnicodeError) else str(error)
        )
        print(f"Error: {message}", file=sys.stderr)
        return 1
    except OSError as error:
        # Operating-system messages may include private absolute paths.
        print(f"File operation failed ({type(error).__name__})", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
