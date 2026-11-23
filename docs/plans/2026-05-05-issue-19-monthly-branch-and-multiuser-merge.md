# Plan: Monthly branch hygiene + multi-user merge guardrails (#19)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/19
- Tier: T3 (cross-repo coordination; flag for re-routing)
- Repo: assetutilities (proposed home for shared script)
- Status: plan-review

## Context

Issue #19 asks for a daily/weekly gitbash automation to:
(a) enforce a `YYYYMM` monthly branch convention across ~10 repos,
(b) detect and report stale branches,
(c) run unit/integration tests at merge time and notify contributors,
(d) end-of-month merges back to main.

The issue body enumerates 10+ repos (digitalmodel, teamresumes, energydata,
assethold, energy, acma-projects, achantas-data, achantas-media,
aceengineer-admin, etc.). This is fundamentally **cross-repo workflow**,
not assetutilities-internal logic.

**Re-routing recommendation:** the *script* belongs in assetutilities
(consistent with assetutilities's role as the shared utility repo), but
the *enforcement decisions per repo* (monthly branch creation, end-of-month
merge windows) are governance work that should live in workspace-hub
governance docs or per-repo issues. Suggest splitting:

- This issue → narrow scope: ship a reusable `scripts/branch-hygiene.sh`
  in assetutilities + `docs/sub_shell/gitbash.md` runbook.
- New issues per repo → "adopt monthly-branch convention" with explicit
  `YYYYMM` first-of-month creation and end-of-month merge.

Out-of-scope here: repo-by-repo adoption (file follow-ups).

## Plan

1. **Reduce scope on issue.** Comment on #19 proposing the split above:
   assetutilities ships the script + runbook; per-repo adoption tracked
   elsewhere. Wait for maintainer ack before coding.
2. **Design the script contract.** `scripts/branch-hygiene.sh <repo-path>` should:
   - Print local + remote branches.
   - Flag any branch not matching `^YYYYMM$` (where YYYY is current year,
     MM is current or previous month) as stale.
   - Suggest deletion commands for stale local + remote branches (do not
     execute deletes by default; require `--apply`).
   - Detect if a `YYYYMM`-current branch exists; if not, suggest
     `git switch -c $(date +%Y%m) && git push -u origin HEAD`.
   - Exit 0 if clean, 1 if any stale branch found.
3. **Implement `scripts/branch-hygiene.sh`.** Pure bash, no external
   deps beyond `git`. Add unit-style smoke test under `tests/scripts/`
   that runs the script against a temp repo with seeded branches.
4. **Document.** Update `docs/sub_shell/gitbash.md` (or create
   `docs/sub_shell/branch_hygiene.md`) with: usage, exit codes, sample
   output, opt-in cron snippet (`0 9 * * MON`).
5. **Sketch the test-at-merge piece.** Out of scope for v1. File a
   follow-up issue: "branch-hygiene: add pre-merge test runner that
   blocks merge on red CI and emails contributors". Reference
   GitHub-native branch protections + `gh pr checks` as the lower-cost
   alternative.
6. **Adoption tracker.** File one tracking issue per repo listed in #19
   (digitalmodel, teamresumes, energydata, etc.) titled "Adopt
   YYYYMM monthly-branch convention" with a checklist linking back to
   this script + runbook.

## Acceptance criteria

- [ ] `scripts/branch-hygiene.sh` exists, executable, exit-code contract
      documented.
- [ ] Smoke test passes against a temp git repo with seeded branches.
- [ ] `docs/sub_shell/branch_hygiene.md` (or equivalent) describes
      usage + exit codes.
- [ ] Per-repo adoption follow-ups filed (one issue per listed repo).
- [ ] Issue #19 reduced in scope or closed in favor of the follow-ups,
      with maintainer's explicit OK.

## Open questions

- Should `--apply` actually push deletions, or just print `git push origin --delete`
  commands? Default: print only. Destructive path requires `--apply --force`.
- Does GitHub-native branch protection + Actions cover the "test at
  merge / notify contributors" requirement well enough that the script
  doesn't need to? Likely yes — confirm with maintainer.
