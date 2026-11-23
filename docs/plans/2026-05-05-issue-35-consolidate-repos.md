# Plan: Consolidate / retire stale repos (#35)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/35
- Tier: T3 (cross-repo governance; flag for re-route)
- Repo: assetutilities (proposed: re-route to workspace-hub)
- Status: plan-review

## Context

Issue #35 enumerates ~30 GitHub repos owned by `vamseeachanta` and asks
which to keep / consolidate / archive. The body has many checkboxes
already marked (saipem, investments, rock-oil-field, py_package, etc.
have been actioned), but ~13 still need a decision (energydata,
teamresumes, acma-projects, assetutilities itself, achantas-data,
digitalmodel, doris, aceengineer-admin, client_projects, achantas-media,
hobbies, sd-work, achantas).

This is a **portfolio-management decision**, not an assetutilities feature.

**Re-routing recommendation:** transfer to workspace-hub as a governance
issue. Or, if workspace-hub already tracks ecosystem-wide repo decisions
(see global memory: ecosystem-terminology, repo-capability-map skill),
fold this into that work.

In-scope here: triage and re-route. No code.

## Plan

1. **Audit the unchecked rows.** For each unchecked repo, check `gh repo view`
   to confirm: last commit date, open issues, recent activity, size,
   visibility. Build a one-line per-repo summary.
2. **Apply lightweight decision rule.**
   - Last commit > 12 months AND no open issues → propose archive.
   - Active digitalmodel-adjacent (assetutilities, digitalmodel,
     energydata, achantas-data) → keep.
   - Personal/private (achantas, hobbies, sd-work) → defer; not a
     consolidation candidate.
3. **Comment on #35 with the table.** Each row: repo, last-activity,
   recommendation (keep / archive / merge into X).
4. **File workspace-hub coordination issue.** Title: "Repo portfolio
   consolidation (continuation of assetutilities #35)". Move all
   unchecked rows there. Close #35.
5. **Stop.** Actual archives / transfers / merges happen as separate
   per-repo issues, not in this plan.

## Acceptance criteria

- [ ] Comment on #35 with per-repo recommendation table.
- [ ] Workspace-hub issue filed with the residual scope.
- [ ] Issue #35 closed with link to the workspace-hub issue.

## Open questions

- Does the maintainer want this work paused until the workspace-hub
  `repo-capability-map` skill output is reviewed? That skill already
  classifies repos by domain and maturity — its output may directly
  answer #35.
- Are any of the listed repos owned by other GitHub orgs/users that
  would require explicit ownership transfer (cf. assethold transfer
  per global memory)?
