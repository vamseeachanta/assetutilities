# Compound Engineering adoption note

Current recommendation: **drop for now; no ecosystem rollout**. The dated
[evidence and decision](ce-trial-decision.md) records missing trial results,
not plugin failures. The earned keep-list is empty. Maintainer ratification in
#86 is pending; a generated recommendation or merged documentation is not
permission to roll out the plugin.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| Initial | 2026-10-20 | Persist the missing-evidence gate and repository restrictions. |

Before any adoption work, read #81–#86 and the decision record. Complete and
review the actual trial evidence, reassess the dated recommendation and record
a maintainer decision in #86. Until that happens, no CE skill is adopted by this
note. Installing a plugin and opening a feature branch do not establish value.

After a ratified decision, retain these restrictions:

- Partial adoption permits only the passing advisory keep-list; the incomplete
  compounding loop permits no implementation or publishing skills.
- `digitalmodel` and `worldenergydata` use separate repository directories,
  protected mains, feature branches and reviewed PRs. Verify the destination
  before every operation. Maintainers merge; no automatic merge or force-push.
- The private application repository can use the full loop only after full
  adoption and local authorization; reviewed CE documentation may stay private.
- `workspace-hub` remains advisory/plan-only. Never direct CE commit, push or PR
  skills there, including `ce-work`, `ce-commit-push-pr` or `lfg`. Its existing
  synchronization service controls publication. Do not write sensitive plans
  into public Git.
- Review artifact policy before generating `docs/plans/`, `docs/brainstorms/`,
  `docs/solutions/`, `CONCEPTS.md` or `STRATEGY.md`. Public repositories admit
  reviewed public-only content. The hub uses local exclusion after verifying
  existing tracked documentation remains intact. Private visibility does not
  waive data-rights or credential restrictions.
- Installation stays user-scoped; `.compound-engineering/*.local.yaml` remains
  local and ignored. Verify ignored status in each destination repository.
- Keep the trial worktree until its evidence is promoted to a reviewed PR or
  its disposition is explicitly agreed. This note deletes no worktree or data.

These are authored guardrails sourced from #81 and #86, not installed access
controls. The [assessment tool](../../../src/assetutilities/devtools/ce_trial.py)
only reads an evidence file and prints a recommendation. It does not authorize
writes, change repository configuration or inspect a plugin installation.
