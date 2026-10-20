"""Gmail retention planning and explicit moves to Trash.

No message bodies, sender addresses, or credentials are included in plans.
Sources: Google Gmail API v1, Message resource, messages.list/get/trash,
Manage labels, and Filtering (retrieved 2026-10-20); see the cleanup guide.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.client import HTTPException, HTTPSConnection
from math import ceil, isfinite
from pathlib import Path
from typing import Protocol
from urllib.parse import quote, urlencode


class CleanupError(RuntimeError):
    """A sanitized operation failure; response bodies are never reported."""


def _identifier(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("Invalid message identifier")
    return value


@dataclass(frozen=True)
class Message:
    id: str
    received: datetime
    labels: frozenset[str]

    @classmethod
    def from_api(cls, raw: dict) -> Message:
        """Require complete metadata, including an explicit label list."""
        try:
            identifier = _identifier(raw["id"])
            labels = raw["labelIds"]
            milliseconds = raw["internalDate"]
            if not isinstance(labels, list) or not all(
                isinstance(label, str) for label in labels
            ):
                raise ValueError
            if not isinstance(milliseconds, str) or not re.fullmatch(
                r"[0-9]+", milliseconds
            ):
                raise ValueError
            # Gmail API v1 Message.internalDate: milliseconds since Unix epoch.
            received = datetime.fromtimestamp(0, timezone.utc) + timedelta(
                milliseconds=int(milliseconds)
            )
            return cls(identifier, received, frozenset(labels))
        except (KeyError, TypeError, ValueError, OverflowError):
            raise ValueError("Incomplete or invalid message metadata") from None


@dataclass(frozen=True)
class RetentionPolicy:
    days: int
    as_of: datetime

    def __post_init__(self) -> None:
        if type(self.days) is not int or self.days <= 0:
            raise ValueError("Retention days must be a positive integer")
        if self.as_of.utcoffset() is None:
            raise ValueError("The reference time must include a timezone")
        object.__setattr__(self, "as_of", self.as_of.astimezone(timezone.utc))
        # Evaluate now so an out-of-range interval fails before any API call.
        try:
            _ = self.cutoff
        except OverflowError:
            raise ValueError(
                "Retention interval exceeds the supported date range"
            ) from None

    @property
    def cutoff(self) -> datetime:
        return self.as_of - timedelta(days=self.days)

    @property
    def query(self) -> str:
        # Gmail Filtering: epoch seconds avoid Gmail's PST date interpretation.
        # Round upward for a superset; eligible() checks exact milliseconds.
        return (
            f"before:{ceil(self.cutoff.timestamp())} "
            "-is:starred -is:important -in:trash"
        )

    def eligible(self, message: Message) -> bool:
        # Issue #39: either protected label is sufficient, regardless of age.
        # Gmail Manage labels defines these system label identifiers.
        protected = {"STARRED", "IMPORTANT", "TRASH", "DRAFT"}
        if message.received.utcoffset() is None:
            raise ValueError("Message time must include a timezone")
        return message.received < self.cutoff and not protected.intersection(
            message.labels
        )


class Mailbox(Protocol):
    def list_ids(self, query: str) -> Iterator[str]: ...

    def get_message(self, identifier: str) -> Message: ...

    def trash(self, identifier: str) -> None: ...


@dataclass(frozen=True)
class CleanupPlan:
    policy: RetentionPolicy
    candidate_ids: tuple[str, ...]
    scanned: int


def build_plan(mailbox: Mailbox, policy: RetentionPolicy) -> CleanupPlan:
    """Finish discovery before any mutation, so pagination stays stable."""
    seen: set[str] = set()
    candidates = []
    for identifier in mailbox.list_ids(policy.query):
        if identifier in seen:
            continue
        seen.add(identifier)
        message = mailbox.get_message(identifier)
        if message.id != identifier:
            raise ValueError("Message identifier does not match the request")
        if policy.eligible(message):
            candidates.append(identifier)
    return CleanupPlan(policy, tuple(candidates), len(seen))


@dataclass(frozen=True)
class ApplyResult:
    trashed: tuple[str, ...]
    skipped: tuple[str, ...]
    failed_id: str | None = None


def apply_plan(mailbox: Mailbox, plan: CleanupPlan) -> ApplyResult:
    """Recheck each candidate and stop on error, retaining partial progress."""
    trashed, skipped = [], []
    for identifier in plan.candidate_ids:
        try:
            message = mailbox.get_message(identifier)
            if message.id != identifier:
                raise ValueError("Message identifier does not match the request")
            if not plan.policy.eligible(message):
                skipped.append(identifier)
                continue
            mailbox.trash(identifier)
            trashed.append(identifier)
        except (CleanupError, ValueError, OSError):
            return ApplyResult(tuple(trashed), tuple(skipped), identifier)
    return ApplyResult(tuple(trashed), tuple(skipped))


class GmailMailbox:
    """Small standard-library adapter; OAuth token acquisition stays external."""

    def __init__(self, token: str, timeout: float):
        if not token or any(character.isspace() for character in token):
            raise ValueError("A valid GMAIL_ACCESS_TOKEN is required")
        if not isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout seconds must be finite and positive")
        self._token = token
        self._timeout = timeout

    def _request(self, method: str, path: str, params: dict | None = None) -> dict:
        target = "/gmail/v1/users/me/messages" + path
        if params:
            target += "?" + urlencode(params)
        # A fixed HTTPS connection accepts no other URL scheme or redirects.
        connection = HTTPSConnection("gmail.googleapis.com", timeout=self._timeout)
        try:
            connection.request(
                method,
                target,
                body=b"" if method == "POST" else None,
                headers={"Authorization": "Bearer " + self._token},
            )
            response = connection.getresponse()
            if response.status != HTTPStatus.OK:
                # Never include response bodies, headers or credential values.
                raise CleanupError(f"Gmail request failed (HTTP {response.status})")
            result = json.load(response)
            if not isinstance(result, dict):
                raise CleanupError("Invalid Gmail response object")
            return result
        except (HTTPException, OSError, ValueError):
            raise CleanupError(
                "Gmail request failed or returned invalid JSON"
            ) from None
        finally:
            connection.close()

    def list_ids(self, query: str) -> Iterator[str]:
        # messages.list: includeSpamTrash includes both folders; policy excludes
        # Trash locally. No assumed page size or API batch limit is required.
        params = {"q": query, "includeSpamTrash": "true"}
        seen_tokens: set[str] = set()
        while True:
            page = self._request("GET", "", params)
            messages = page.get("messages", [])
            if not isinstance(messages, list):
                raise CleanupError("Invalid Gmail message list")
            for entry in messages:
                try:
                    yield _identifier(entry["id"])
                except (KeyError, TypeError, ValueError):
                    raise CleanupError("Invalid Gmail message list") from None
            token = page.get("nextPageToken")
            if not token:
                return
            if not isinstance(token, str) or token in seen_tokens:
                raise CleanupError("Invalid or repeated Gmail page token")
            seen_tokens.add(token)
            params["pageToken"] = token

    def get_message(self, identifier: str) -> Message:
        # Gmail Format full includes internalDate; partial-response fields omit
        # payload and headers. Minimal format provides only identifiers/labels.
        raw = self._request(
            "GET",
            "/" + quote(_identifier(identifier), safe=""),
            {"format": "full", "fields": "id,internalDate,labelIds"},
        )
        return Message.from_api(raw)

    def trash(self, identifier: str) -> None:
        # messages.trash moves one message; permanent delete is never called.
        self._request("POST", "/" + quote(_identifier(identifier), safe="") + "/trash")


class SnapshotMailbox:
    """Read-only metadata fixture for reproducible planning without a mailbox."""

    def __init__(self, path: Path):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise CleanupError("Snapshot must be a JSON array of message metadata")
        self._messages = {}
        for entry in raw:
            message = Message.from_api(entry)
            if message.id in self._messages:
                raise ValueError("Snapshot contains duplicate message identifiers")
            self._messages[message.id] = message

    def list_ids(self, query: str) -> Iterator[str]:
        return iter(self._messages)

    def get_message(self, identifier: str) -> Message:
        return self._messages[identifier]

    def trash(self, identifier: str) -> None:
        raise CleanupError("Snapshots cannot modify mail")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retention-days", type=int, required=True)
    parser.add_argument(
        "--as-of", help="ISO timestamp with timezone; default: now in UTC"
    )
    parser.add_argument("--snapshot", type=Path, help="Offline JSON metadata array")
    parser.add_argument("--timeout-seconds", type=float, help="Required for live Gmail")
    parser.add_argument(
        "--apply", action="store_true", help="Move eligible mail to Trash"
    )
    args = parser.parse_args(argv)
    if args.snapshot and args.apply:
        parser.error("--snapshot cannot be combined with --apply")
    if not args.snapshot and args.timeout_seconds is None:
        parser.error("Live Gmail requires --timeout-seconds")
    try:
        as_of = (
            datetime.fromisoformat(args.as_of.replace("Z", "+00:00"))
            if args.as_of
            else datetime.now(timezone.utc)
        )
        policy = RetentionPolicy(args.retention_days, as_of)
        mailbox = (
            SnapshotMailbox(args.snapshot)
            if args.snapshot
            else GmailMailbox(
                os.environ.get("GMAIL_ACCESS_TOKEN", ""), args.timeout_seconds
            )
        )
        plan = build_plan(mailbox, policy)
        output = {
            "mode": "apply" if args.apply else "dry-run",
            "as_of": policy.as_of.isoformat(),
            "cutoff": policy.cutoff.isoformat(),
            "retention_days": policy.days,
            "scanned": plan.scanned,
            "candidate_ids": plan.candidate_ids,
        }
        if args.apply:
            result = apply_plan(mailbox, plan)
            output.update(
                trashed_ids=result.trashed,
                skipped_ids=result.skipped,
                failed_id=result.failed_id,
            )
        print(json.dumps(output, indent=2))
        return int(args.apply and result.failed_id is not None)
    except (CleanupError, ValueError, OSError):
        # Inputs and remote errors can contain private data; do not echo them.
        print(
            "Cleanup failed: check metadata, dates, timeout and GMAIL_ACCESS_TOKEN; "
            "no further operations were attempted.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
