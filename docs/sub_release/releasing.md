# Releasing assetutilities

Tag releases build and validate a wheel and a source distribution before a
separate, protected publishing job sends those same artifacts to PyPI.
Offline tests gate normal contributions; the identified live-service tests
require an explicit selection. No release is created by running the local examples.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add tag release safeguards, offline test guidance and source reuse examples. |
| Update | 2026-10-22 | Pin release actions and tools, run CI contracts once per matrix, and clarify live-test and branch-policy limits. |

## What is implemented

- Slice 1: live-service tests carry `live_data` and are excluded by default
  alongside `pdf_integration`. Offline scraper dispatch, defaults overlays,
  URL-shape validation and ZIP processing replace the node-ID quarantine.
- Slice 2: `.github/workflows/release.yml` builds on `v*` tag pushes. Source,
  tag and distribution versions must agree; the wheel must contain packaged
  defaults; `twine check --strict` must accept both artifacts. Publishing uses
  PyPI Trusted Publishing in a separate `pypi` environment.
- Slice 3: contribution checks reject outdated monthly branches while keeping
  topic branches supported. A daily audit reports stale monthly refs; local
  audits also report unpublished work. Folder ignore boilerplate documents a
  single authoritative source tree.

## Maintainer setup and release method

Configure a PyPI Trusted Publisher for this repository, workflow `release.yml`,
environment `pypi`. Protect the GitHub environment with required reviewers and
restrict deployment refs to release tags. Require the existing `Gates` and
domain aggregate checks in branch protection. These are external settings and
are not established by committing the workflow.

Trusted Publishing exchanges an OIDC identity for a short-lived credential;
it requires no stored PyPI API token. Only the publish job receives
`id-token: write`. It downloads the artifacts from the validated build job and
does not execute repository code. See the [Python Packaging User Guide's
publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

For a release, update `project.version` in `pyproject.toml` and `__version__`
in `src/assetutilities/__init__.py` together. Merge the reviewed change after
CI passes. Create and push just the corresponding `v<version>` tag on that
commit. The workflow rejects a commit outside `origin/main` history and a tag
that disagrees with the metadata. A manual workflow run validates and builds
without publishing, including when manually run on a tag.

Review the built artifacts and environment approval before publication.
Publication has not been exercised by this change. A published version cannot
be silently replaced: correct the source and issue a new version. Keep the
failed run's evidence when diagnosing a rejected upload.

## Offline tests and configuration compatibility

```bash
uv run python -m pytest tests/ci tests/modules/web_scraping tests/modules/download_data
uv run python examples/release/offline_config.py
```

The checked-in pytest configuration preserves the PDF exclusion and adds the
live-data exclusion. To select live tests intentionally, use
`uv run python -m pytest -m live_data tests/modules/web_scraping tests/modules/download_data`.
That command contacts external services and is not a release gate. Do not use
its result as evidence that other domains are broken. The Scrapy router still
does not launch a crawler; passing configuration tests establish no live-data
capability.

The three quarantined live-service tests were re-gated, not repaired: they
still contact external services. The offline replacements exercise synthetic
inputs only. Any explicit `-m` expression replaces the default expression in
`addopts`, including the PDF exclusion. For example, `-m "not pdf_integration"`
can run live-service tests again. Keep both exclusions when selecting another
offline subset: `-m "not pdf_integration and not live_data"`.

The scraper input method overlays `settings_master`, then `input_settings`,
then each `input` item, at the top-level key boundary. This repairs the key
mismatch between the packaged defaults and consumers without changing the
engine's general merge contract. Returned items are independent copies.
Download URLs accept the packaged list of `{url: ...}` entries, a list of URL
strings, or the existing named mapping of URL strings. Every entry is validated
before any request. The download default's basename is `download_data`.

Worked example inputs:

```yaml
settings_master:
  url: https://example.invalid/default
  save_csv: true
input_settings:
  output_dir: results
input:
  - label: sample
    url: https://example.invalid/sample
```

Method: copy the defaults, overlay explicit settings, then overlay the item.
The item URL replaces the default; the save flag and output directory survive.
The executable example returns:

```json
[
  {
    "url": "https://example.invalid/sample",
    "save_csv": true,
    "output_dir": "results",
    "label": "sample"
  }
]
```

The ZIP regression independently constructs a CSV with header `label,value`
and row `sample,ok`. Downloading the synthetic `archive.zip` produces
`archive_sample.csv` with that exact header and row. Both examples are synthetic
configuration exercises; no engineering constants or acceptance limits apply.

## Branch policy and source reuse

Use a topic branch for an individual contribution. If a monthly branch is
used, its entire name must be the current UTC `YYYYMM`; older monthly names
fail the pull-request contribution check. Existing topic branch workflows
remain supported. No automation in this change creates, merges, pushes or
deletes a branch.

The source-branch check applies equally to forks: a pull request opened from a
fork branch named `main` is rejected intentionally. Outside contributors must
create a topic branch in their fork before opening a pull request. This is a
contribution naming rule; it does not restrict the pull request's target branch.

Run `uv run python scripts/ci/branch_policy.py --audit` in a contributor checkout
to report stale monthly refs and local branches without an upstream, ahead of
their upstream, or tracking a missing remote ref. The audit reads available
local refs only: refresh them through the usual review process before making
decisions. The daily hosted audit produces a `branch-audit` artifact; it cannot
see unpublished work in another checkout. Maintainers review the report, push
work that must be retained, and prune only after confirming it is merged and
no contributor still needs it. Scheduled reports do not enforce cleanup.
On a fresh hosted checkout, the audit therefore covers remote monthly refs;
`unpublished_local` is normally empty. The fixed daily time, 09:00 UTC, provides
a predictable reporting cadence and carries no age or service-level guarantee.

Keep source inputs in one version-controlled tree and execute beside them.
Ignore generated outputs explicitly at folder level; avoid an unmanaged second
copy of source files. Install shared Python utilities as a versioned dependency
rather than copying their source. When execution needs a separate directory,
record the source revision and input digests with results so the copy has a
defined provenance.

Copy `examples/source-layout/runs/.gitignore` into a run folder. It tracks the
ignore file and direct YAML files under `inputs/`; it ignores output folders,
logs and other input-folder file types. For example, `inputs/case.yml` is
eligible for tracking while `outputs/result.csv` is ignored. The regression
test uses Git itself to verify this distinction. Parent ignore rules must
also permit the run folder. See [gitignore, Pattern format](https://git-scm.com/docs/gitignore).

## Sources and limits

Consulted public documentation, online editions accessed 2026-10-20:

- [Python Packaging User Guide, GitHub Actions publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/): isolated build and Trusted Publishing.
- [Core Metadata, Name and Version](https://packaging.python.org/en/latest/specifications/core-metadata/): distribution identity checks.
- [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows): tag pushes, manual runs and scheduled audits.
- [git-for-each-ref, Field names](https://git-scm.com/docs/git-for-each-ref): upstream tracking reports.
- [gitignore, Pattern format](https://git-scm.com/docs/gitignore): folder allow-list rules.

Later work requires maintainer action: configure publishing and branch
protection, approve a first release, review stale refs, and choose adoption
settings in consuming repositories. Live-service operation remains unverified.
Issues #99 and #153 already describe overlapping offline-test and config work;
coordinate their pending changes before merging. No external settings or
repositories are changed here.
