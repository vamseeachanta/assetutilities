# Plan: Consolidate data on Linux machine (#33)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/33
- Tier: T3 (infrastructure / out-of-scope; recommend re-route)
- Repo: assetutilities (proposed: re-route to workspace-hub or close)
- Status: plan-review

## Context

Issue #33 is a one-line stub: "setup linux machine — ?". It's an
infrastructure / data-consolidation work item with no concrete acceptance
criteria, no referenced files in assetutilities, and no clear
relationship to a Python utility library.

**Re-routing recommendation:** this issue does not belong in
assetutilities. Recent workspace-hub work has tracked Linux machine
setup, drive ingest (Elements drive), and data consolidation under
workspace-hub-level governance (per global memory:
`project_elements_drive_identity.md`,
`project_ace_linux_2_vnc.md`, `project_consolidate_*` if any).

Two options:

- **(a)** Close #33 in assetutilities, file a fresh issue in
  `vamseeachanta/workspace-hub` titled "Consolidate data on ace-linux-1
  / ace-linux-2" with concrete scope.
- **(b)** Convert #33 in place into a concrete narrow task: e.g., "ship
  a `scripts/data-inventory.sh` that reports disk usage by repo across
  all workspace-hub repos".

Default: path (a).

In-scope here: stocktake + close/reroute decision. No code.

## Plan

1. **Inventory candidate work.** Read recent workspace-hub memory entries
   for Linux machine setup (Elements drive, VNC, NTFS dirty-volume,
   etc.) and identify which subitems #33 plausibly meant.
2. **Decide re-route vs narrow.** Default (a). Confirm with maintainer
   via issue comment.
3. **(If a)** File issue in workspace-hub repo titled "Consolidate data
   on Linux machines (was assetutilities #33)" with concrete subitems:
   - Inventory of repos + sizes per machine.
   - Migration plan for any data living off-repo (Elements drive ingest).
   - Decision on canonical machine for each data class.
   Then close #33 referencing the new issue.
4. **(If b)** Replace this plan with a narrow scoped one for the
   `scripts/data-inventory.sh` deliverable.

## Acceptance criteria

- [ ] Decision recorded as a comment on #33 (re-route vs narrow).
- [ ] If re-routed: workspace-hub issue filed; #33 closed with a link.
- [ ] If narrowed: this plan superseded with a scoped follow-up plan.

## Open questions

- Is there a current canonical "data consolidation" tracking issue in
  workspace-hub already? If yes, link to it instead of filing a new one.
- Does the maintainer want assetutilities to ship any helper scripts
  (e.g., disk-usage-by-repo) regardless? If yes, that's a separate
  narrow plan.
