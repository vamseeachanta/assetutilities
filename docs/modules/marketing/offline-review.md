# Offline marketing review

The utilities prepare a manual content calendar for LinkedIn and X and inventory
a static website export before editorial simplification. They produce JSON for
review; publishing, account management and deployed website changes remain manual.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add calendar and local HTML review to prepare editorial work. |

## Worked example

All inputs in `examples/workflows/marketing/` are synthetic. The website deliberately
contains omissions so that the example demonstrates findings rather than approval.
Run from the repository root with the package dependencies available:

```sh
PYTHONPATH=src python -m assetutilities.cli.marketing review \
  examples/workflows/marketing/calendar.json \
  examples/workflows/marketing/html-export \
  --as-of 2026-10-20T12:00:00Z
```

The command prints a combined report to standard output. The method and expected
answer can be checked without executing the implementation:

| Input | Method | Expected answer |
|---|---|---|
| Approved LinkedIn row at `14:00:00+02:00` | Subtract the supplied offset: `14:00 - 02:00 = 12:00 UTC`; compare with the supplied cutoff | `due` |
| X row with `draft` status | Draft status requires review regardless of its date | `draft` |
| The two calendar rows | Count each supplied channel and disposition once | LinkedIn: 1; X: 1; due: 1; draft: 1; scheduled: 0; published: 0 |
| `index.html` and `guide.html` | Enumerate the supplied files | 2 pages |
| Both pages have title `Engineering guide` | Group identical stripped title text | 1 duplicate-title group containing both paths |
| `guide.html` has no description meta element | Record absent description text | `missing_description` |
| `guide.html` links to absent `contact.html` | Resolve against the page directory, then check file existence | `broken_local_link` |

The independent enumeration and UTC subtraction are also written into the test
docstrings. No platform limits or engineering coefficients are used.

Individual reports are available with the `calendar` and `site` subcommands:

```sh
PYTHONPATH=src python -m assetutilities.cli.marketing calendar \
  examples/workflows/marketing/calendar.json --as-of 2026-10-20T12:00:00Z
PYTHONPATH=src python -m assetutilities.cli.marketing site \
  examples/workflows/marketing/html-export
```

A completed inventory exits successfully even when it contains findings. Invalid
input returns a nonzero exit status, a concise diagnostic on standard error and
no partial JSON report. No output files are created by the utility.

## Calendar contract and workflow

The input document contains only a `posts` array. Each row requires:

| Field | Input contract |
|---|---|
| `id` | Unique, nonempty string without surrounding whitespace |
| `channel` | `linkedin` or `x` |
| `text` | Nonempty string, preserved verbatim |
| `scheduled_at` | Whole-second RFC 3339 timestamp with a known UTC offset |
| `status` | `draft`, `approved` or `published`, supplied by the editor |
| `url` | Optional absolute HTTP or HTTPS URL; an empty string is also allowed |

Unknown fields, duplicate identifiers, duplicate JSON keys and invalid dates are
rejected. The timestamp profile excludes fractional seconds, leap seconds and
`-00:00` (unknown local offset). Lowercase `t` and `z` are accepted. UTC conversion
must fit the supported calendar date range. All rows require a schedule, including
drafts, so that the calendar exposes intended timing for review.

The editor records proposed content as `draft`, reviews the wording and link,
and explicitly changes the status to `approved`. At the supplied `as_of` instant,
an approved row is `due` if its timestamp is earlier than or equal to that instant;
otherwise it is `scheduled`. Draft and published rows retain their disposition.
After manual publication, the editor may record `published`. This state is an
input assertion; the utility does not obtain confirmation from a platform.

The API functions are `validate_calendar(payload)` and
`calendar_report(payload, as_of=timestamp)` in
`src/assetutilities/common/marketing.py`. Validation returns new rows sorted by
UTC timestamp then id; it does not mutate the input. The `as_of` input is explicit
so results are reproducible. Text is retained as data and is never executed.

## Website inventory and simplification workflow

`audit_site(directory)` in `src/assetutilities/common/website_audit.py` reads local
UTF-8 `.html` and `.htm` files. It lists title text, description text, heading and
link counts, missing metadata, missing first-level headings and duplicate titles.
These are editorial prompts, not HTML conformance or search ranking verdicts.
Multiple first-level headings are counted without imposing a threshold.

Local anchor targets resolve relative to the page directory or the supplied site
root. Percent-encoded path characters are decoded. Query strings and fragments do
not name local files. Directory URLs map to `index.html`; this is an explicit
static-export convention. Symlinked HTML files are rejected; symlinked directories
are not scanned. Resolved targets outside the supplied root are reported without
reading them. The report contains site-relative page names.

Use the inventory to identify pages that may be consolidated, review their content
and navigation, and plan redirects before removing any page. Duplicate titles alone
do not establish duplicate content. Broken links require a corrected destination
or restored content. Rerun the inventory on the revised export to check that local
navigation still resolves. The utility changes no content and chooses no pages
for deletion.

## Sources and limits

- [RFC 3339, Date and Time on the Internet: Timestamps (2002), sections 4.2, 4.3 and 5.6](https://www.rfc-editor.org/rfc/rfc3339): known offsets, timestamp grammar and UTC conversion basis.
- [RFC 3986, Uniform Resource Identifier: Generic Syntax (2005), sections 3 and 5.2](https://www.rfc-editor.org/rfc/rfc3986): URI components and relative-reference resolution. The filesystem mapping is the local convention described above.
- [HTML Living Standard, sections 4.2.2, 4.2.3 and 4.2.5 (retrieved 2026-10-20)](https://html.spec.whatwg.org/multipage/semantics.html): title, base and description metadata elements.
- [HTML Living Standard, section 4.3.6 (retrieved 2026-10-20)](https://html.spec.whatwg.org/multipage/sections.html#the-h1,-h2,-h3,-h4,-h5,-and-h6-elements): heading elements.

There are no quantitative marketing acceptance limits. Platform length rules,
publication and search performance are `NOT_EVALUATED`: platform documentation,
account-specific access and measured outcomes are not inputs to this utility.
External links, fragment targets and rendered content are also `NOT_EVALUATED`.
A `base` element with `href` makes that page's link resolution `NOT_EVALUATED`.

This is a static source inventory, not a browser DOM or HTML validator. Script
content is not executed. Server routing, redirects, extensionless routes and
non-UTF-8 exports need separate handling. Input is a local trusted export; no
network resources are fetched. The package's existing common-module imports still
require its declared data and visualization dependencies.

Later work covers editorial approval criteria, platform-specific limits backed by
current documentation, manual or separately authorized publishing, and actual
website copy, layout and deployment changes. The two original ongoing marketing
activities are not completed by an offline utility.
