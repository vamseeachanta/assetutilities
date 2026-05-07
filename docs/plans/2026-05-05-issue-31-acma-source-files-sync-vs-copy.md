# Plan: ACMA source files — sync vs copy (#31)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/31
- Tier: T3 (cross-repo / project-specific; flag for re-routing)
- Repo: assetutilities (proposed home for the boilerplate gitignore + helper)
- Status: plan-review

## Context

Issue #31 is about how an ACMA (WLNG) project organizes source files: run
in `run_location`, sync in `sync_location`, with the proposal of three
methods:

- M1: explicit `.gitignore` at folder level so run+sync share location.
- M2: separate locations + a copy script.
- M3: alternative.

This is fundamentally **a project setup decision for the ACMA repo**, not
an assetutilities feature. assetutilities's contribution should be a
generic helper: a folder-level gitignore template + (optionally) a
`scripts/sync-folder.sh` utility.

**Re-routing recommendation:** narrow this issue to "ship boilerplate
folder-level gitignore + sync helper in assetutilities", and file the
ACMA-specific decision as a separate issue in the ACMA project repo.

In-scope: the boilerplate + helper, with smoke tests.

Out-of-scope: choosing M1/M2/M3 for ACMA — that's a project decision.

## Plan

1. **Comment on #31 to narrow scope.** Propose: assetutilities ships the
   boilerplate; ACMA chooses M1/M2/M3 in its own repo. Wait for ack.
2. **Design folder-level gitignore boilerplate.** Create
   `docs/sub_shell/folder_gitignore_boilerplate.md` with:
   - Recipe for ignoring everything in a folder except a tracked allow-list.
   - Recipe for the inverse (track everything, ignore a few).
   - Worked example: a `runs/` folder where `.yml` is tracked but
     `.h5` outputs are ignored.
3. **Implement `scripts/sync-folder.sh`.** Minimal rsync wrapper:
   `sync-folder.sh <run_location> <sync_location> [--include glob]`,
   `--dry-run` default, `--apply` to actually copy. Filters out
   common large output extensions (`.h5`, `.sim`, `.dat`) unless
   explicitly included.
4. **Add smoke test.** `tests/scripts/test_sync_folder.sh` against a
   temp directory pair.
5. **Open PR.**
6. **Coordinate ACMA-side adoption.** File a separate issue in the ACMA
   repo: "Choose sync model (M1/M2/M3) and adopt assetutilities boilerplate".

## Acceptance criteria

- [ ] `docs/sub_shell/folder_gitignore_boilerplate.md` covers folder-level
      ignore + allow-list patterns with worked examples.
- [ ] `scripts/sync-folder.sh` exists, dry-run by default, with smoke test.
- [ ] Issue #31 narrowed (or closed) with the ACMA-side decision tracked
      separately in the ACMA repo.

## Open questions

- Does the ACMA repo already exist as a tracked GitHub repo, or is it a
  local-only directory? If local-only, the "file an issue there" step
  may need to land somewhere else (acma-projects?).
- Should the sync helper use `rsync` (Linux/Mac) or be Windows-friendly
  (`robocopy` fallback)? Default: rsync only; document Windows users
  should use WSL.
