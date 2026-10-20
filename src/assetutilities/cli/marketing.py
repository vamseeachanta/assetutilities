"""Offline marketing review: python -m assetutilities.cli.marketing --help."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from assetutilities.common.marketing import calendar_report
from assetutilities.common.website_audit import audit_site


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _calendar(path: str, as_of: str) -> dict[str, Any]:
    payload = json.loads(
        Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object
    )
    return calendar_report(payload, as_of=as_of)


def main(argv: Sequence[str] | None = None) -> int:
    """Print deterministic JSON; invalid input exits with no partial report."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    calendar = commands.add_parser("calendar", help="review a manual content calendar")
    calendar.add_argument("calendar", help="UTF-8 JSON calendar")
    calendar.add_argument(
        "--as-of", required=True, help="timestamp with explicit offset"
    )
    site = commands.add_parser("site", help="inventory a local UTF-8 HTML export")
    site.add_argument("site", help="static export directory")
    review = commands.add_parser(
        "review", help="combine calendar and website inventory"
    )
    review.add_argument("calendar", help="UTF-8 JSON calendar")
    review.add_argument("site", help="static export directory")
    review.add_argument("--as-of", required=True, help="timestamp with explicit offset")
    args = parser.parse_args(argv)
    try:
        if args.command == "calendar":
            result = _calendar(args.calendar, args.as_of)
        elif args.command == "site":
            result = audit_site(args.site)
        else:
            result = {
                "calendar": _calendar(args.calendar, args.as_of),
                "website": audit_site(args.site),
            }
    except (OSError, ValueError, RuntimeError):
        # Keep input content and filesystem locations out of diagnostic output.
        print(
            "Invalid input: check the calendar schema, timestamp offsets, "
            "and readable UTF-8 input files.",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
