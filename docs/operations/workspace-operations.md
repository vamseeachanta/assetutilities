# Workspace operations assessment

## Summary

The operations script provides a read-only repository inventory, an evidence
checklist for the ten child issues of #122, and a report of outstanding actions.
It is separate from the installed library API. A `PASS` means the input records
current completion evidence; a maintainer must independently review that evidence
before accepting an operational outcome.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| Initial | 2026-10-20 | Add an inventory and evidence workflow to make outstanding operations work explicit. |

## Scope and sources

The source is the definition of done and Children list in issue #122, with its
linked issues as retrieved on 2026-10-20. The criteria below turn those outcomes
into review questions; they do not establish that any setup has been performed.
The source numbers are issue identifiers, not engineering constants. No physical
equations, engineering coefficients or numerical acceptance limits apply.

| Record identifier | Source | Evidence to review |
|---|---|---|
| `repositories` | #35, #122 | Repository and branch inventory, chosen issue destinations, consolidation decisions and preservation checks. |
| `data` | #33, #122 | Existing authoritative catalog and storage references, authorized access and a restore or integrity check. |
| `hardware` | #36 | Reproducible setup, network, shared peripherals, display/audio and authorized remote access checks. |
| `agents` | #30, #122 | Versioned configuration and evidence of use in a normal workflow. |
| `meetings` | #56, #122 | Authorized capture, transcription and reviewed summary, with consent and retention recorded. |
| `knowledge` | #38, #122 | Selected tool, installation checks and a capture/retrieval routine. |
| `email` | #39, #122 | Scheduled retention, reviewed dry run and protection of starred and important messages. |
| `onboarding` | #42 | Tools, repository access, environment and hardware checks by a new team member. |
| `process` | #37, #122 | Repeatable onboarding checklist, responsibilities and an independently completed handoff. |
| `marketing` | #40, #122 | Responsibility and cadence for public channels and website maintenance. |

The older plans under `docs/plans/` for issues #30, #33, #36 and #42 already
identify cross-workspace or infrastructure work. Keep authoritative catalogs,
agent configuration and operational evidence in their existing systems; the
input here holds references and a review snapshot, rather than a replacement
registry. Existing repository utilities under `src/assetutilities/devtools/`
modify dependencies, structure or commands; this script only reports.

## Slice 1: inventory repository candidates

Run from the repository root with Python; only the standard library is needed:

```sh
python scripts/operations/workspace_ops.py inventory WORKSPACE_ROOT
```

Supply a checkout root, a directory containing checkouts, or several such roots.
The script examines each supplied root and its immediate children. A `.git`
directory or regular marker file is reported, which includes ordinary checkouts,
worktrees and submodules. Overlapping roots are deduplicated. Child and marker
symlinks are excluded; an explicitly supplied symlink root is resolved.

Each result contains a zero-based `root_index`, a path relative to that root, and
`marker` set to `directory` or `file`. Root paths and marker contents are omitted.
A marker identifies a candidate, not a healthy Git repository. No recursive
search, branch inspection, remote request, data hashing or modification occurs.
An unavailable root is an input error; the script does not return partial output.

Review candidates against the existing repository inventory. Record branch and
issue destinations there. Preserve original data and history, identify consumers
and obtain a reviewed disposition before carrying out consolidation. Inventory
output alone cannot satisfy the `repositories` requirement.

## Slice 2: record operational evidence

Use `examples/operations/workspace-operations.json` as a synthetic format example.
It is deliberately incomplete and makes no claim about the actual workspace.

The top-level object accepts `as_of` and `records`. `as_of` is required, using an
ISO calendar date. The records object may omit requirements; every omitted
requirement is still included in the assessment. Unknown keys, invalid types,
duplicate JSON keys and non-finite JSON values are rejected.

Each requirement accepts only these string fields:

| Field | Meaning |
|---|---|
| `state` | `complete`, `pending` or `blocked`; absent or empty means no observation. |
| `responsible_role` | Role responsible for the operational outcome; use a generic role in a public example. |
| `evidence_ref` | Opaque reference to the existing acceptance record, not credentials or private content. |
| `observed_on` | Calendar date when the completion evidence was checked. |
| `valid_until` | Exclusive calendar date selected by the maintainer for the next review. |
| `next_action` | Action for incomplete work; if absent, the requirement's review criterion is used. |

`complete` requires a nonblank role and evidence reference, plus both dates.
An observation cannot be later than `as_of`, and expiry cannot precede the
observation. Invalid dates or inconsistent chronology reject the input. The
script does not infer a freshness interval or a retention period. Select review
dates according to the applicable policy and keep its basis with the referenced
evidence. The `as_of` date is caller supplied, so an old snapshot says nothing
about present readiness.

| Input condition | Assessment |
|---|---|
| No record or no state | `NOT_EVALUATED` |
| `pending` or `blocked` | `FAIL` |
| `complete` with missing required evidence fields | `NOT_EVALUATED` |
| `complete` with `valid_until` on or before `as_of` | `NOT_EVALUATED` |
| `complete` with all required evidence fields and current dates | `PASS` |

The overall result is `FAIL` if any requirement fails, otherwise `NOT_EVALUATED`
if any requirement remains unevaluated, otherwise `PASS`. The counts are the
number of requirements in each status. Every nonpassing requirement produces an
action with its responsible role, or `unassigned` if no role was supplied.

## Slice 3: review the report and use the onboarding handoff

```sh
python scripts/operations/workspace_ops.py assess examples/operations/workspace-operations.json
python scripts/operations/workspace_ops.py assess examples/operations/workspace-operations.json --format markdown
```

JSON is the default. Exit status is zero for all `PASS`, one for a valid but
incomplete assessment, and two for invalid or unreadable input. Reports go to
standard output; redirect to an authorized destination outside the source tree.
The example commands intentionally return one. The Markdown report includes a
summary, revision history, per-requirement evidence and dates, outstanding actions
and limits. Each generated snapshot is a new document. Retain prior snapshots;
append a row to their revision history if a retained report is reissued.

For an onboarding handoff, the maintainer and new team member can follow this
sequence without relying on an undocumented setup:

1. Locate the authoritative repository inventory, data catalog, setup instructions,
   agent configuration and knowledge store. Check access under the intended role.
2. Follow the recorded environment and hardware setup. Run the repository's normal
   checks, exercise remote access if required, and record the outcome.
3. Complete a normal workflow using the versioned agent configuration and retrieve
   a saved knowledge item. Review a permitted meeting summary if that is in scope.
4. Review scheduled email retention in a dry run with protected messages. Record
   the applicable policy; never use this assessment to authorize message deletion.
5. Complete the onboarding checklist independently. Record difficulties, follow-up
   actions, evidence and review dates in the existing operational records.
6. Reassess and assign every outstanding action. Review the public-channel cadence
   and handoff responsibilities with the maintainer.

## Worked example: inputs, method and answer

The committed JSON supplies an assessment date of 2026-10-20. Repository evidence
was observed on 2026-10-19 and agent evidence on 2026-10-20; both expire on
2026-10-21. These are synthetic dates chosen to exercise the date comparisons,
not recommended review intervals. Email retention is explicitly pending. The
other seven requirements are omitted.

By hand, the two complete records have roles, references and current dates, so
there are two `PASS` results. Email contributes one `FAIL`. Data, hardware,
meetings, knowledge, onboarding, process and marketing contribute seven
`NOT_EVALUATED` results. The answer is overall `FAIL`, with eight actions. The
worked-example test independently enumerates those records and asserts those
counts. Separate tests cover all ten passing, expiry boundaries, missing fields,
input errors, inventory coverage and CLI behavior.

## Later slices and limits

Actual repository retirement, data migration, restore validation, machine setup,
access changes, account configuration, meeting capture, knowledge-tool deployment,
retention automation and marketing publication require work in their authoritative
systems. These remain unevaluated until evidence is supplied and reviewed. This
change does not complete the epic or close its child issues. It does not install
software, provision services, operate an assistant or execute a licensed solver.
Evidence references and completion states are caller assertions; the script does
not resolve references, verify access or authenticate the evidence.
