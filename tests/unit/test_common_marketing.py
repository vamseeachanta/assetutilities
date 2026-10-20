"""Calendar contract tests; all dates and text are synthetic inputs.

Expected counts are independent enumeration of the rows below, not benchmarks
or platform limits. RFC 3339 (2002), sections 4.3 and 5.6, supplies date syntax.
"""

from copy import deepcopy

import pytest

from assetutilities.common.marketing import calendar_report, validate_calendar


def post(**changes):
    item = {
        "id": "intro",
        "channel": "linkedin",
        "text": "Read the engineering guide.",
        "scheduled_at": "2026-10-20T12:00:00Z",
        "status": "approved",
        "url": "https://example.org/guide/",
    }
    return dict(item, **changes)


def test_calendar_normalizes_offsets_and_does_not_mutate_input():
    """Hand calculation: 14:00 at UTC+02:00 is 12:00 UTC."""
    payload = {"posts": [post(scheduled_at="2026-10-20T14:00:00+02:00")]}
    original = deepcopy(payload)
    rows = validate_calendar(payload)
    assert rows[0]["scheduled_at"] == "2026-10-20T12:00:00Z"
    assert payload == original


def test_report_orders_posts_and_only_marks_approved_rows_due():
    """At 12:00 UTC: one approved row is due, one is future.

    One earlier draft and one earlier published row remain in those states.
    Four enumerated rows give two LinkedIn and two X entries.
    """
    payload = {
        "posts": [
            post(id="future", channel="x", scheduled_at="2026-10-21T12:00:00Z"),
            post(id="draft", status="draft", scheduled_at="2026-10-19T12:00:00Z"),
            post(),
            post(id="done", channel="x", status="published"),
        ]
    }
    report = calendar_report(payload, as_of="2026-10-20T12:00:00Z")
    assert report["counts"] == {"draft": 1, "due": 1, "scheduled": 1, "published": 1}
    assert report["channels"] == {"linkedin": 2, "x": 2}
    assert [row["id"] for row in report["posts"]] == [
        "draft",
        "done",
        "intro",
        "future",
    ]
    assert report["posts"][1]["disposition"] == "published"


@pytest.mark.parametrize("status", ["draft", "approved", "published"])
def test_accepts_manual_workflow_states(status):
    assert validate_calendar({"posts": [post(status=status)]})[0]["status"] == status


def test_url_is_optional_and_text_is_preserved():
    item = post(text="Line one.\nLine two.")
    del item["url"]
    row = validate_calendar({"posts": [item]})[0]
    assert row["url"] == ""
    assert row["text"] == item["text"]


def test_empty_calendar_is_valid():
    report = calendar_report({"posts": []}, as_of="2026-10-20T12:00:00Z")
    assert report["posts"] == []
    assert report["counts"] == dict.fromkeys(
        ["draft", "due", "scheduled", "published"], 0
    )


@pytest.mark.parametrize(
    "payload", [None, [], {}, {"posts": {}}, {"posts": [], "typo": 1}]
)
def test_rejects_invalid_document_shape(payload):
    with pytest.raises(ValueError):
        validate_calendar(payload)


@pytest.mark.parametrize("field", ["id", "channel", "text", "scheduled_at", "status"])
def test_rejects_missing_required_fields(field):
    item = post()
    del item[field]
    with pytest.raises(ValueError, match=field):
        validate_calendar({"posts": [item]})


@pytest.mark.parametrize(
    "changes",
    [
        {"id": " "},
        {"text": "\n"},
        {"channel": "other"},
        {"status": "queued"},
        {"url": "relative.html"},
        {"url": "javascript:alert('test')"},
        {"url": "https://"},
        {"url": "https://example.org/a b"},
        {"url": "https://[invalid"},
        {"text": 12},
        {"id": False},
        {"extra": "typo"},
    ],
)
def test_rejects_invalid_post_values(changes):
    with pytest.raises(ValueError):
        validate_calendar({"posts": [post(**changes)]})


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org:bad/guide",
        "https://example.org:-1/guide",
        "https://example.org:65536/guide",
        "https://example.org:80:90/guide",
        "https://example.org:443suffix/guide",
        "https://[::1]:bad/guide",
        "https://example.org:+443/guide",
        "https://example.org:4_43/guide",
        "https://example.org:\u0664\u0664\u0663/guide",
    ],
)
def test_rejects_invalid_url_ports(url):
    with pytest.raises(ValueError, match="url"):
        validate_calendar({"posts": [post(url=url)]})


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/guide",
        "https://example.org:443/guide",
        "http://example.org:0/guide",
        "https://example.org:65535/guide",
        "https://example.org:/guide",
        "https://[::1]/guide",
        "https://[::1]:8443/guide",
    ],
)
def test_preserves_valid_url_authorities(url):
    assert validate_calendar({"posts": [post(url=url)]})[0]["url"] == url


@pytest.mark.parametrize("row", [None, [], "post"])
def test_rejects_non_object_rows(row):
    with pytest.raises(ValueError):
        validate_calendar({"posts": [row]})


def test_rejects_duplicate_ids_across_channels():
    with pytest.raises(ValueError, match="duplicate"):
        validate_calendar({"posts": [post(), post(channel="x")]})


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-10-20",
        "2026-10-20T12:00:00",
        "2026-10-20 12:00:00Z",
        "2026-02-30T12:00:00Z",
        "2026-10-20T12:00:00-00:00",
        "2026-10-20T12:00:00+01:60",
        "2026-10-20T24:00:00Z",
        "2026-10-20T12:00:60Z",
        "2026-10-20T12:00:00.123Z",
        "0001-01-01T00:00:00+01:00",
    ],
)
def test_rejects_unsupported_or_invalid_timestamps(timestamp):
    with pytest.raises(ValueError, match="scheduled_at"):
        validate_calendar({"posts": [post(scheduled_at=timestamp)]})


def test_as_of_uses_same_timestamp_contract():
    with pytest.raises(ValueError, match="as_of"):
        calendar_report({"posts": []}, as_of="yesterday")


def test_lowercase_timestamp_is_accepted():
    rows = validate_calendar({"posts": [post(scheduled_at="2026-10-20t12:00:00z")]})
    assert rows[0]["scheduled_at"] == "2026-10-20T12:00:00Z"
