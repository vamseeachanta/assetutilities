"""Offline editorial calendar validation; no platform calls or implicit approval.

Timestamp syntax: RFC 3339 (2002), sections 4.2, 4.3 and 5.6.
https://www.rfc-editor.org/rfc/rfc3339#section-5.6
The supported profile uses whole seconds and a known UTC offset; fractional
seconds, leap seconds and the unknown offset -00:00 are rejected explicitly.
Workflow states and channels are this utility's input contract, not platform rules.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

# Field widths and ranges: RFC 3339 (2002), section 5.6, date-time grammar.
_HOUR = r"(?:[01][0-9]|2[0-3])"
_MINUTE = r"[0-5][0-9]"
_TIMESTAMP = re.compile(
    rf"[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}[Tt]{_HOUR}:{_MINUTE}:{_MINUTE}"
    rf"(?:[Zz]|[+-]{_HOUR}:{_MINUTE})"
)
_REQUIRED = {"id", "channel", "text", "scheduled_at", "status"}
_CHANNELS = ("linkedin", "x")
_DISPOSITIONS = ("draft", "due", "scheduled", "published")


def _timestamp(value: Any, field: str) -> datetime:
    if (
        not isinstance(value, str)
        or not _TIMESTAMP.fullmatch(value)
        or value.endswith("-00:00")
    ):
        raise ValueError(
            f"{field} requires a whole-second timestamp with a known offset"
        )
    try:
        return datetime.fromisoformat(value.upper().replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except (ValueError, OverflowError) as exc:
        raise ValueError(
            f"{field} contains an invalid or out-of-range timestamp"
        ) from exc


def _utc_text(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _web_url(value: Any) -> bool:
    """Require an absolute web target (RFC 3986, 2005, sections 3 and 4.3)."""
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return False
    try:
        parts = urlsplit(value)
        # Reading the property validates the port's numeric range.
        _ = parts.port
        authority = parts.netloc.rsplit("@", 1)[-1]
        return (
            parts.scheme in {"http", "https"}
            and bool(parts.hostname)
            # RFC 3986 section 3.2.3 permits only ASCII digits in a port.
            and re.fullmatch(r"(?:\[[^\]]+\]|[^:\[\]]+)(?::[0-9]*)?", authority)
            is not None
        )
    except ValueError:
        return False


def validate_calendar(payload: Any) -> list[dict[str, str]]:
    """Return independent, UTC-normalized rows sorted by time then unique id.

    Input is an object containing only ``posts``, a list. Every post requires
    id, channel, text, scheduled_at and status; url is optional. Unknown fields
    and duplicate ids are errors. Input content is never echoed in errors.
    """
    if not isinstance(payload, dict) or set(payload) != {"posts"}:
        raise ValueError("calendar requires only a posts field")
    if not isinstance(payload["posts"], list):
        raise ValueError("posts must be a list")
    rows = []
    seen = set()
    for item in payload["posts"]:
        if not isinstance(item, dict):
            raise ValueError("each post must be an object")
        for field in sorted(_REQUIRED):
            if field not in item:
                raise ValueError(f"post requires {field}")
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"post requires nonempty text for {field}")
        if set(item) - _REQUIRED - {"url"}:
            raise ValueError("post contains unsupported fields")
        if item["id"] != item["id"].strip():
            raise ValueError("id must not have surrounding whitespace")
        if item["id"] in seen:
            raise ValueError("duplicate post id")
        seen.add(item["id"])
        if item["channel"] not in _CHANNELS:
            raise ValueError("channel must be linkedin or x")
        if item["status"] not in {"draft", "approved", "published"}:
            raise ValueError("status must be draft, approved or published")
        target = item.get("url", "")
        if target != "" and not _web_url(target):
            raise ValueError("url must be an absolute HTTP or HTTPS target")
        rows.append(
            dict(
                item,
                url=target,
                scheduled_at=_utc_text(
                    _timestamp(item["scheduled_at"], "scheduled_at")
                ),
            )
        )
    return sorted(rows, key=lambda row: (row["scheduled_at"], row["id"]))


def calendar_report(payload: Any, *, as_of: str) -> dict[str, Any]:
    """Summarize manual state; only approved posts at or before as_of are due.

    All counts are literal row counts. A published status is a user assertion,
    not confirmation from a platform. No character or performance limits are
    assumed; those require platform-specific evidence in a later integration.
    """
    cutoff = _timestamp(as_of, "as_of")
    rows = validate_calendar(payload)
    for row in rows:
        disposition = row["status"]
        if disposition == "approved":
            disposition = (
                "due"
                if _timestamp(row["scheduled_at"], "scheduled_at") <= cutoff
                else "scheduled"
            )
        row["disposition"] = disposition
    counts = Counter(row["disposition"] for row in rows)
    channels = Counter(row["channel"] for row in rows)
    return {
        "as_of": _utc_text(cutoff),
        "counts": {key: counts[key] for key in _DISPOSITIONS},
        "channels": {key: channels[key] for key in _CHANNELS},
        "posts": rows,
        "platform_limits": "NOT_EVALUATED",
        "publication": "NOT_EVALUATED",
    }
