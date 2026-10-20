"""Retention examples are synthetic; expected dates are hand calculations.

For the main example, 2024 is a leap year: subtracting the issue's 365 days
from 2025-01-01 UTC gives 2024-01-02 UTC. Equality is retained because the
issue specifies *older than*, rather than *at least* the retention period.
Gmail timestamp units and labels: Google Gmail API v1, Message resource and
Manage labels (links in docs/sub_gmail/cleanup.md, retrieved 2026-10-20).
"""

from datetime import datetime, timedelta, timezone

import pytest

from assetutilities import email_cleanup
from assetutilities.email_cleanup import (
    CleanupError,
    GmailMailbox,
    Message,
    RetentionPolicy,
    apply_plan,
    build_plan,
    main,
)

AS_OF = datetime(2025, 1, 1, tzinfo=timezone.utc)
# Issue #39 supplies the example retention period; it is not a default.
DAYS = 365


def message(identifier="old", received=None, labels=()):
    return Message(
        identifier,
        received or datetime(2024, 1, 1, tzinfo=timezone.utc),
        frozenset(labels),
    )


class Mailbox:
    def __init__(self, messages):
        self.messages = {item.id: item for item in messages}
        self.trashed = []

    def list_ids(self, query):
        self.query = query
        return iter(self.messages)

    def get_message(self, identifier):
        return self.messages[identifier]

    def trash(self, identifier):
        self.trashed.append(identifier)


def test_cutoff_is_elapsed_days_in_utc():
    assert RetentionPolicy(DAYS, AS_OF).cutoff == datetime(
        2024, 1, 2, tzinfo=timezone.utc
    )


@pytest.mark.parametrize("labels", [(), ("INBOX",), ("SPAM",)])
def test_old_unprotected_mail_is_eligible(labels):
    assert RetentionPolicy(DAYS, AS_OF).eligible(message(labels=labels))


@pytest.mark.parametrize(
    "labels", [("STARRED",), ("IMPORTANT",), ("STARRED", "IMPORTANT"), ("TRASH",)]
)
def test_protected_or_already_trashed_mail_is_retained(labels):
    assert not RetentionPolicy(DAYS, AS_OF).eligible(message(labels=labels))


@pytest.mark.parametrize(
    "received",
    [
        datetime(2024, 1, 2, tzinfo=timezone.utc),
        datetime(2024, 12, 31, tzinfo=timezone.utc),
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    ],
)
def test_boundary_recent_and_future_mail_is_retained(received):
    assert not RetentionPolicy(DAYS, AS_OF).eligible(message(received=received))


def test_one_millisecond_before_boundary_is_eligible():
    """Hand calculation: Jan 2 midnight minus 1 ms is Jan 1 23:59:59.999."""
    received = datetime(2024, 1, 1, 23, 59, 59, 999000, tzinfo=timezone.utc)
    assert RetentionPolicy(DAYS, AS_OF).eligible(message(received=received))


def test_offset_is_normalized_before_subtracting_days():
    """03:00 at UTC+03:00 is midnight UTC, hence the same Jan 2 cutoff."""
    offset = timezone(timedelta(hours=3))
    policy = RetentionPolicy(DAYS, datetime(2025, 1, 1, 3, tzinfo=offset))
    assert policy.cutoff == datetime(2024, 1, 2, tzinfo=timezone.utc)


@pytest.mark.parametrize("days", [0, -1, True, 1.5, "365"])
def test_retention_requires_positive_integer_input(days):
    with pytest.raises(ValueError):
        RetentionPolicy(days, AS_OF)


def test_naive_clock_is_rejected():
    with pytest.raises(ValueError):
        RetentionPolicy(DAYS, datetime(2025, 1, 1))


def test_plan_checks_each_message_and_does_not_modify_mail():
    """Only old is eligible: starred/important protected, boundary equal."""
    mailbox = Mailbox(
        [
            message(),
            message("starred", labels=("STARRED",)),
            message("important", labels=("IMPORTANT",)),
            message("boundary", datetime(2024, 1, 2, tzinfo=timezone.utc)),
        ]
    )
    plan = build_plan(mailbox, RetentionPolicy(DAYS, AS_OF))
    assert plan.candidate_ids == ("old",)
    assert mailbox.trashed == []
    assert plan.scanned == len(mailbox.messages)
    # Hand calculation: 1970..2023 has 54*365+13 leap days; Jan 2 adds 1.
    # Multiplying days by 24*60*60 gives 1704153600 seconds (API search units).
    assert mailbox.query == "before:1704153600 -is:starred -is:important -in:trash"


def test_apply_rechecks_age_labels_and_records_skipped_ids():
    mailbox = Mailbox([message(), message("changed")])
    plan = build_plan(mailbox, RetentionPolicy(DAYS, AS_OF))
    mailbox.messages["changed"] = message("changed", labels=("IMPORTANT",))
    result = apply_plan(mailbox, plan)
    assert result.trashed == ("old",)
    assert result.skipped == ("changed",)
    assert result.failed_id is None
    assert mailbox.trashed == ["old"]


def test_apply_failure_stops_and_preserves_partial_progress():
    mailbox = Mailbox([message(), message("fail"), message("later")])
    plan = build_plan(mailbox, RetentionPolicy(DAYS, AS_OF))
    original = mailbox.trash

    def trash(identifier):
        if identifier == "fail":
            raise CleanupError("Request failed")
        original(identifier)

    mailbox.trash = trash
    result = apply_plan(mailbox, plan)
    assert result.trashed == ("old",)
    assert result.failed_id == "fail"
    assert mailbox.trashed == ["old"]


def test_discovery_deduplicates_ids():
    mailbox = Mailbox([message()])
    mailbox.list_ids = lambda query: iter(["old", "old"])
    plan = build_plan(mailbox, RetentionPolicy(DAYS, AS_OF))
    assert plan.candidate_ids == ("old",)
    assert plan.scanned == len(mailbox.messages)


def test_discovery_rejects_mismatched_response():
    mailbox = Mailbox([message()])
    mailbox.get_message = lambda identifier: message("different")
    with pytest.raises(ValueError):
        build_plan(mailbox, RetentionPolicy(DAYS, AS_OF))
    assert mailbox.trashed == []


def test_gmail_pagination_and_minimal_metadata(monkeypatch):
    """Two API pages enumerate old and spam; no thread endpoint is used."""
    mailbox = GmailMailbox("unused", timeout=1)
    requests = []
    responses = iter(
        [
            {"messages": [{"id": "old"}], "nextPageToken": "next"},
            {"messages": [{"id": "spam"}]},
        ]
    )

    def request(method, path, params=None):
        requests.append((method, path, params))
        return next(responses)

    monkeypatch.setattr(mailbox, "_request", request)
    assert list(mailbox.list_ids("query")) == ["old", "spam"]
    assert requests[0][2]["includeSpamTrash"] == "true"
    assert requests[1][2]["pageToken"] == "next"
    assert requests[0][2]["q"] == "query"


def test_gmail_get_and_trash_request_contract(monkeypatch):
    """Epoch 0 ms is 1970-01-01 UTC per the Gmail Message resource."""
    mailbox = GmailMailbox("unused", timeout=1)
    requests = []

    def request(method, path, params=None):
        requests.append((method, path, params))
        return {"id": "old", "internalDate": "0", "labelIds": ["INBOX"]}

    monkeypatch.setattr(mailbox, "_request", request)
    parsed = mailbox.get_message("old")
    assert parsed.received == datetime(1970, 1, 1, tzinfo=timezone.utc)
    assert parsed.labels == frozenset({"INBOX"})
    assert requests[0][2] == {
        "format": "full",
        "fields": "id,internalDate,labelIds",
    }
    mailbox.trash("old")
    assert requests[-1] == ("POST", "/old/trash", None)


@pytest.mark.parametrize(
    "raw",
    [
        {},
        {"id": "old", "labelIds": []},
        {"id": "old", "internalDate": "bad", "labelIds": []},
        {"id": "old", "internalDate": "0"},
        {"id": "old", "internalDate": "0", "labelIds": "STARRED"},
        {"id": "old", "internalDate": "0", "labelIds": [None]},
        {"id": "old", "internalDate": "-1", "labelIds": []},
    ],
)
def test_incomplete_or_malformed_metadata_fails_closed(raw):
    with pytest.raises(ValueError):
        Message.from_api(raw)


def test_page_token_cycle_is_rejected(monkeypatch):
    mailbox = GmailMailbox("unused", timeout=1)
    monkeypatch.setattr(
        mailbox, "_request", lambda *args: {"nextPageToken": "repeated"}
    )
    with pytest.raises(CleanupError):
        list(mailbox.list_ids("query"))


def test_drafts_are_retained():
    assert not RetentionPolicy(DAYS, AS_OF).eligible(message(labels=("DRAFT",)))


def test_offline_cli_worked_example(capsys):
    """The table in the guide has old and spam eligible, four retained."""
    import json
    from pathlib import Path

    snapshot = (
        Path(__file__).resolve().parents[2] / "examples/email_cleanup/messages.json"
    )
    assert (
        main(
            [
                "--snapshot",
                str(snapshot),
                "--retention-days",
                str(DAYS),
                "--as-of",
                "2025-01-01T00:00:00+00:00",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["candidate_ids"] == ["old", "spam"]
    assert output["mode"] == "dry-run"
    assert output["cutoff"] == "2024-01-02T00:00:00+00:00"


def test_snapshot_cannot_be_applied(capsys):
    with pytest.raises(SystemExit):
        main(["--snapshot", "unused.json", "--apply", "--retention-days", str(DAYS)])
    assert "--snapshot" in capsys.readouterr().err


def test_cli_missing_credentials_is_sanitized(monkeypatch, capsys):
    monkeypatch.delenv("GMAIL_ACCESS_TOKEN", raising=False)
    assert main(["--retention-days", str(DAYS), "--timeout-seconds", "1"]) != 0
    assert "GMAIL_ACCESS_TOKEN" in capsys.readouterr().err


class Connection:
    """Synthetic HTTPS transport; no sockets or credentials are used."""

    def __init__(self, response):
        self.response = response
        self.requests = []
        self.closed = False

    def request(self, method, target, body=None, headers=None):
        self.requests.append((method, target, body))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


def test_transport_uses_https_metadata_requests_and_empty_trash_body(monkeypatch):
    """Request shapes follow Gmail API v1 list/get/trash references."""
    import io
    from http import HTTPStatus
    from urllib.parse import parse_qs, urlsplit

    connections = []

    def connect(host, timeout):
        assert host == "gmail.googleapis.com"
        assert timeout == 1
        response = io.BytesIO(b"{}")
        response.status = HTTPStatus.OK
        connection = Connection(response)
        connections.append(connection)
        return connection

    monkeypatch.setattr(email_cleanup, "HTTPSConnection", connect)
    mailbox = GmailMailbox("unused", timeout=1)
    assert list(mailbox.list_ids("before:0 -is:starred")) == []
    mailbox.trash("old")
    listing, trashing = [connection.requests[0] for connection in connections]
    assert parse_qs(urlsplit(listing[1]).query)["q"] == ["before:0 -is:starred"]
    assert listing[0] == "GET"
    assert listing[2] is None
    assert trashing[1].endswith("/users/me/messages/old/trash")
    assert trashing[0] == "POST"
    assert trashing[2] == b""
    assert all(connection.closed for connection in connections)


@pytest.mark.parametrize(
    "kind", ["http", "network", "invalid-json", "not-object", "redirect"]
)
def test_transport_errors_do_not_expose_response_details(monkeypatch, kind):
    import io
    from http import HTTPStatus
    from http.client import HTTPException

    response = io.BytesIO(b"[]" if kind == "not-object" else b"private-detail")
    response.status = (
        HTTPStatus.FORBIDDEN
        if kind == "http"
        else HTTPStatus.FOUND
        if kind == "redirect"
        else HTTPStatus.OK
    )
    connection = Connection(response)
    if kind == "network":

        def fail(*args, **kwargs):
            raise HTTPException("private-detail")

        connection.request = fail
    monkeypatch.setattr(
        email_cleanup, "HTTPSConnection", lambda *args, **kwargs: connection
    )
    with pytest.raises(CleanupError) as error:
        list(GmailMailbox("unused", timeout=1).list_ids("query"))
    assert "private-detail" not in str(error.value)
    assert connection.closed


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_live_timeout_requires_positive_finite_input(timeout):
    with pytest.raises(ValueError):
        GmailMailbox("unused", timeout=timeout)


def test_cli_apply_reports_completed_ids(monkeypatch, capsys):
    import json

    mailbox = Mailbox([message()])
    monkeypatch.setattr(email_cleanup, "GmailMailbox", lambda *args: mailbox)
    assert (
        main(
            [
                "--retention-days",
                str(DAYS),
                "--timeout-seconds",
                "1",
                "--apply",
                "--as-of",
                "2025-01-01T00:00:00Z",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "apply"
    assert output["trashed_ids"] == ["old"]
    assert output["failed_id"] is None
    assert mailbox.trashed == ["old"]


def test_cli_partial_failure_returns_nonzero_and_progress(monkeypatch, capsys):
    import json

    mailbox = Mailbox([message()])

    def fail(identifier):
        raise CleanupError("private-detail")

    mailbox.trash = fail
    monkeypatch.setattr(email_cleanup, "GmailMailbox", lambda *args: mailbox)
    assert (
        main(
            [
                "--retention-days",
                str(DAYS),
                "--timeout-seconds",
                "1",
                "--apply",
                "--as-of",
                "2025-01-01T00:00:00Z",
            ]
        )
        != 0
    )
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["trashed_ids"] == []
    assert output["failed_id"] == "old"
    assert "private-detail" not in captured.out + captured.err


def test_snapshot_invalid_json_is_rejected_without_content(tmp_path, capsys):
    path = tmp_path / "invalid.json"
    path.write_text("private-detail")
    assert main(["--snapshot", str(path), "--retention-days", str(DAYS)]) != 0
    captured = capsys.readouterr()
    assert "private-detail" not in captured.out + captured.err


def test_empty_mailbox_returns_empty_plan():
    plan = build_plan(Mailbox([]), RetentionPolicy(DAYS, AS_OF))
    assert not plan.candidate_ids
    assert not plan.scanned


def test_query_rounds_up_subsecond_cutoff_for_local_comparison():
    """Jan 2 midnight plus 1 ms lies before the next whole epoch second."""
    policy = RetentionPolicy(DAYS, AS_OF + timedelta(milliseconds=1))
    assert policy.query.startswith("before:1704153601 ")
    assert policy.eligible(message(received=datetime(2024, 1, 2, tzinfo=timezone.utc)))


def test_snapshot_rejects_duplicate_ids(tmp_path):
    import json

    from assetutilities.email_cleanup import SnapshotMailbox

    path = tmp_path / "duplicate.json"
    raw = {"id": "old", "internalDate": "0", "labelIds": []}
    path.write_text(json.dumps([raw, raw]))
    with pytest.raises(ValueError):
        SnapshotMailbox(path)


def test_discovery_failure_leaves_all_mail_untouched():
    mailbox = Mailbox([message(), message("fail")])
    original = mailbox.get_message

    def get(identifier):
        if identifier == "fail":
            raise CleanupError("unavailable")
        return original(identifier)

    mailbox.get_message = get
    with pytest.raises(CleanupError):
        build_plan(mailbox, RetentionPolicy(DAYS, AS_OF))
    assert mailbox.trashed == []


def test_newly_trashed_candidate_is_skipped_on_recheck():
    mailbox = Mailbox([message()])
    plan = build_plan(mailbox, RetentionPolicy(DAYS, AS_OF))
    mailbox.messages["old"] = message(labels=("TRASH",))
    result = apply_plan(mailbox, plan)
    assert result.skipped == ("old",)
    assert not mailbox.trashed
