# Repository consolidation audit

The offline audit supports the repository, issue-routing and stale-branch review
in issue #35. It reads a normalized JSON snapshot and prints a report with
reasons. A review candidate requires a maintainer decision about dependencies,
retention, ownership and the destination before any change is made.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add reproducible review of repository inactivity, issue placement and merged branches. |

## Run

From a source checkout:

```bash
PYTHONPATH=src python -m assetutilities.devtools.repo_audit \
  examples/devtools/repo-audit.json \
  --stale-before 2026-04-01T00:00:00Z --issue-repo tools
```

For a Markdown table, add `--format markdown`. Repeat `--issue-repo` for each
permitted destination. Repeat `--keep-repo` to retain specific repositories
regardless of inactivity. Installed packages do not need `PYTHONPATH`.

The command writes to standard output only. It does not call Git, GitHub, a
shell or a solver, and does not modify its input. A successful report exits
with zero even when reviews or unknown evidence are reported; invalid inputs
use argparse's error exit status. A report is a snapshot, not live assurance.

## Input and collection

The top-level object requires `observed_at` and `repositories`. All timestamps
must be timezone-aware ISO strings; comparisons use UTC. The cutoff must precede
the observation time. Evidence timestamps after observation are rejected.
Repository names are unique labels within a snapshot; use unambiguous aliases
when collecting from multiple organizations. Policy names must match those
labels, and an issue destination must be confirmed unarchived.

Optional evidence may be omitted or null. Missing evidence produces
`NOT_EVALUATED` when needed for a decision. A malformed supplied value is an
input error, including negative counts, string booleans, duplicate names or
naive timestamps. Unknown fields are ignored. Raw API JSON must be normalized
to the following schema; it is not accepted as a complete snapshot by itself.

| Repository field | Meaning and collection basis |
|---|---|
| `name` | Required nonempty printable label, unique within the snapshot. |
| `archived` | Boolean repository archival status from the repository endpoint [1]. |
| `pushed_at` | Most recent push timestamp from the repository endpoint [1]; it does not measure discussion, release or usage activity. |
| `open_issues` | Count of open issues after excluding entries with a `pull_request` key [2]. Do not substitute `open_issues_count`, which can include pull requests. |
| `open_pull_requests` | Separate count of open pull requests; counts represent complete paginated results [5]. |
| `default_branch` | Default branch name from the repository endpoint [1]. |
| `branches_complete` | Explicit assertion that the branch listing covers every page [3]. Missing or false means branch coverage is `NOT_EVALUATED`. |
| `branches` | List of branch objects, with unique `name` values within the repository. An explicitly complete empty list represents a repository with no branches. |

| Branch field | Meaning and collection basis |
|---|---|
| `name` | Required branch name. |
| `protected` | Boolean protection status [3]; collection must account for applicable rulesets as well as branch protection. Unknown effective protection remains null. |
| `merged` | Boolean assertion that the branch tip is reachable from the observed default branch tip. For a local snapshot, `git branch --merged <default>` supplies this definition [4]. Merely having a merged pull request is insufficient after new commits. |
| `committed_at` | Branch-tip commit timestamp, collected from `commit.committer.date` for the observed tip [6]. |
| `open_pull_requests` | Count of open pull requests using this branch as their head; collect every page, including requests targeting other branches [5]. |

The collector is responsible for consistent branch tips, pagination and
permissions. If that evidence cannot be obtained, leave it unknown. Collectors
and live fetching are outside this command. Keep private inventories and reports
outside public source control. The shipped example uses invented labels only.

## Method and statuses

There are no engineering equations or empirical coefficients in this audit.
The following Boolean rules implement review policy. The cutoff is a required
input, not an inferred retention limit. All example dates and counts below are
synthetic inputs. Empty issue and pull-request sets have count zero by definition.

- Repository review: an unarchived repository is `REVIEW_CONSOLIDATION` when
  `pushed_at < stale_before` and both open-work counts are zero. Explicitly kept
  repositories, pending work and pushes on or after the cutoff yield `KEEP`.
  Already archived repositories yield `ARCHIVED`. Missing evidence yields
  `NOT_EVALUATED`. Push age alone does not establish that a repository is unused.
- Issue routing: permitted repositories yield `OK`; other repositories with a
  known issue count yield `REVIEW_ROUTING`, including empty backlogs so future
  intake can be reviewed. An unknown count yields `NOT_EVALUATED`. Destination
  selection is supplied policy; the audit proposes no automatic transfer target.
- Branch review: `REVIEW_DELETE` requires a confirmed unarchived repository,
  a known default branch, a different branch name, `protected = false`,
  `merged = true`, `committed_at < stale_before` and no open pull requests.
  Default, protected, unmerged, recently committed or active-PR branches yield
  `KEEP`. Otherwise missing evidence yields `NOT_EVALUATED`. Incomplete listing
  coverage is reported separately and never implies that unseen branches passed.

Repository and branch results are sorted by name. The summary counts the
repositories and each kind of review; inspect the detailed rows for unknowns.
An archived repository can still have unresolved issue-routing evidence.

## Worked example: inputs, method and answer

Use `examples/devtools/repo-audit.json`, observed at June 1, 2026, with an April 1
cutoff and `tools` as the only permitted issue destination. The input is a
synthetic truth-table example; it makes no claim about an existing repository.

| Input | Independent evaluation | Answer |
|---|---|---|
| `idle`: March push, no open work | March is before April; both work sets are empty. | `REVIEW_CONSOLIDATION` |
| `idle`: outside the permitted issue destinations | Existing issue count is known, even though empty. | `REVIEW_ROUTING` |
| `idle/main`: default branch | Default branch is retained regardless of age. | `KEEP` |
| `idle/topic`: March commit, merged, unprotected, no open pull requests | Every branch-review condition is satisfied. | `REVIEW_DELETE` |
| `tools`: May push, two issues and one pull request | May is after April; pending work also prevents consolidation review. It is a permitted issue destination. | `KEEP`, `OK` |
| `retired`: archived, issue count and branch listing unknown | Archival is known; the other checks lack evidence. | `ARCHIVED`, `NOT_EVALUATED` |

Hand counting gives **3 repositories, 1 consolidation review, 1 issue-routing
review and 1 branch review**. The tests write out these independent expectations
and also check cutoff equality, timezone equivalence, missing evidence, active
pull requests, protection, invalid input and unchanged input bytes. No expected
result is calculated by calling the implementation under test.

The next step for the example is to investigate dependencies and retention for
`idle`, select where its future issues belong, and reconfirm the tip and
protection evidence before considering removal of `topic`.

## Limits and later work

Actual repository consolidations, archives, issue transfers and branch deletion
remain separate maintainer decisions. The original issue and its operations
parent include that broader work; this command supplies repeatable review
evidence for all three categories without executing those actions. Consumers,
secrets, data retention, forks, deployments and non-GitHub issue systems are not
inventoried. A recent push does not prove current use, and an old push does not
prove disuse. Every action requires fresh evidence from the authoritative system.

## Sources

The following public documentation was opened successfully on 2026-10-20.
These are field and reachability definitions, not sources for a retention limit.

1. [GitHub REST: Get a repository, online edition (2026)](https://docs.github.com/en/rest/repos/repos#get-a-repository).
2. [GitHub REST: List repository issues, online edition (2026)](https://docs.github.com/en/rest/issues/issues#list-repository-issues), including the issue/pull-request distinction.
3. [GitHub REST: List branches, online edition (2026)](https://docs.github.com/en/rest/branches/branches#list-branches), including protection and branch-tip evidence.
4. [Git branch manual, online edition (2026)](https://git-scm.com/docs/git-branch), `--merged` reachability semantics.
5. [GitHub REST: List pull requests, online edition (2026)](https://docs.github.com/en/rest/pulls/pulls#list-pull-requests).
6. [GitHub REST: Get a commit, online edition (2026)](https://docs.github.com/en/rest/commits/commits#get-a-commit).
