# Gmail retention cleanup

The cleanup command identifies old, unprotected messages and, with explicit
application, moves them to Trash. Starred and important messages are excluded
from this command regardless of age. The retention period is required input.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add retention planning, explicit cleanup and a reproducible example for issue #39. |

## Method and scope

The reference time is converted to UTC. The cutoff equals that reference time
minus the supplied number of elapsed days. A message is eligible only when its
`internalDate` is strictly before the cutoff and its labels contain none of
`STARRED`, `IMPORTANT`, `TRASH` or `DRAFT`. Drafts are additionally excluded to
preserve unfinished work. These system label identifiers are defined in [Manage
labels, Gmail API v1](https://developers.google.com/workspace/gmail/api/guides/labels).

The [Message resource](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages)
defines `internalDate` as Unix epoch milliseconds. For ordinary received mail it
records Google's acceptance time; imported messages can use a supplied date.
Search uses epoch seconds because Gmail interprets date strings in PST; see
[Filtering](https://developers.google.com/workspace/gmail/api/guides/filtering).
The search cutoff rounds upward, then exact metadata comparison handles the
boundary. Mail exactly at the cutoff is retained.

[messages.list](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list)
is paginated until no continuation token remains. Spam is included, existing
Trash is excluded, and duplicate message identifiers are evaluated once.
[messages.get](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get)
requests the full resource with a partial response restricted to identifiers,
labels and timestamps, without message bodies or headers. The
[Format reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/Format)
states that minimal format provides only identifiers and labels, which is
insufficient for age checks.
Incomplete metadata, repeated continuation tokens or discovery failures stop the
operation before any message is changed. Missing labels are treated as incomplete
metadata rather than assumed unprotected.

With `--apply`, discovery completes before changes begin. Each candidate is read
again to check its current age and labels, then
[messages.trash](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/trash)
moves only that message. The command never calls permanent deletion or changes
a whole conversation. An application error stops further operations and reports
the completed, skipped and failed identifiers. Re-running discovery excludes mail
already in Trash. A failed request may have reached Gmail before the response was
lost, so its identifier requires inspection before retrying.

## Worked example without credentials

The synthetic metadata is in `examples/email_cleanup/messages.json`.
The example uses the **365 days** requested in issue #39 as an input, with a
reference time of **2025-01-01 at midnight UTC**. The expected cutoff is
**2024-01-02 at midnight UTC**: the intervening calendar year is a leap year, so
subtracting the specified retention interval leaves one day after January 1.

| Identifier | Received (UTC) | Labels | Expected result |
|---|---|---|---|
| old | 2024-01-01 | INBOX | Candidate |
| spam | 2024-01-01 | SPAM | Candidate |
| starred | 2024-01-01 | STARRED | Retained |
| important | 2024-01-01 | IMPORTANT | Retained |
| boundary | 2024-01-02 | INBOX | Retained: equals cutoff |
| recent | 2024-12-31 | INBOX | Retained: newer than cutoff |

Independent timestamp calculation for the fixture: from the Unix epoch to
2024-01-01 are `54 * 365 + 13 = 19723` days, including leap days. Multiplying by
`24 * 60 * 60 * 1000` gives `1704067200000` milliseconds. Adding one elapsed day
gives the boundary `1704153600000`. Adding `365` elapsed days to the January 1
timestamp gives the recent timestamp `1735603200000`. These are synthetic fixture
values, not measured mail. The corresponding hand calculations are recorded in
the tests.

From a source checkout:

```bash
PYTHONPATH=src python -m assetutilities.email_cleanup \
  --snapshot examples/email_cleanup/messages.json \
  --retention-days 365 --as-of 2025-01-01T00:00:00+00:00
```

The answer is `candidate_ids: ["old", "spam"]`, `scanned: 6`, with cutoff
`2024-01-02T00:00:00+00:00` and mode `dry-run`. Snapshot mode rejects `--apply`.

## Live Gmail use

Acquire an OAuth access token externally and provide it through the
`GMAIL_ACCESS_TOKEN` environment variable. Token acquisition, refresh and storage
are outside this utility. For preview, `gmail.readonly` supports the required
reads; application requires `gmail.modify`, as specified by the API references
above. The narrower `gmail.metadata` scope cannot use the search query.

Run the same command without `--snapshot`, supplying `--timeout-seconds` as an
explicit positive input suitable for the connection. With no `--as-of`, the
reference time is current UTC. Review the JSON candidate identifiers against
Gmail, then repeat with `--apply` only when moving those messages to Trash is
intended. Each invocation discovers candidates again; a preview is not a frozen
approval list. Successful commands return zero; invalid arguments, discovery
errors and incomplete application return nonzero. Keep identifier output private.

Gmail [deletes mail from Trash after 30 days](https://support.google.com/mail/answer/7401?hl=en).
Restore an unintended move before that provider retention period expires. This
utility cannot guarantee permanent retention against Gmail's own Spam or Trash
policies, existing filters, other software or manual actions. There is also no
atomic Gmail operation combining the last protection check and the move: a label
changed during that interval can race with application. Avoid concurrent mailbox
changes while applying and inspect Trash afterward.

## Reduce incoming clutter and spam

Use the [filter and spam guide](filters.md) to distinguish unwanted bulk mail
from mail that should be reported as spam. Filters act on matching incoming mail;
they are not an elapsed-age scheduler. Repeat the cleanup command at a chosen
interval with a fresh token and a reviewed retention policy. No scheduler, filter
creation or spam classification is installed by this command. Spam reduction is
**NOT_EVALUATED**: no delivery history or acceptance target is supplied.

## Sources and validation

The Google Gmail API v1 and Gmail Help pages linked above were opened on
2026-10-20. They define API fields and operations; issue #39 defines the retention
requirement. There are no engineering coefficients or default retention limits.
The reference clock, retention days and live timeout are inputs.

`tests/unit/test_email_cleanup.py` tests the hand-calculated example, time
boundaries, protective labels, malformed metadata, pagination, partial progress,
HTTP behavior and CLI preview/application. Remote calls are simulated. Live
mailbox behavior requires separate acceptance with authorized credentials.
