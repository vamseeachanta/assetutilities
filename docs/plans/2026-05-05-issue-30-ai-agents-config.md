# Plan: AI agents config + cross-repo distribution (#30)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/30
- Tier: T3 (cross-repo coordination; partially superseded; flag for re-routing)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #30 was filed in 2024-12 to set up YAML configs for AI agents
(python programmer, devops ci-cd, engineer physics/finance, etc.) and
distribute them across `digitalmodel`, `energydata`, etc.

State on `main` (2026-05):

- `agents/` and `src/assetutilities/agent_os/` already exist.
- `.agent-runtime/agents/registry/sub-agents.yaml` is in place.
- `docs/modules/ai/_agents/agent_devops_engineer.yaml` exists.
- The broader workspace-hub ecosystem now uses `.claude/skills/` and
  `.claude/agents/` conventions, which were not yet established when #30
  was filed.

**Re-routing recommendation:** issue #30 is largely overtaken by the
workspace-hub `.claude/` ecosystem and Agent OS work. This plan therefore
**closes the loop on what's still meaningful in assetutilities** rather
than building the full multi-agent universe described in the issue body.

In-scope: stocktake of the agent YAMLs that exist, document them in
`docs/modules/ai/`, and either close #30 or narrow it to a concrete
"cross-repo agent template distribution" follow-up.

Out-of-scope: building new agent personas (visionaries, engineer-physics,
engineer-finance); copilot integration; multi-agent orchestration.

## Plan

1. **Inventory existing agent assets.** List every YAML/MD under
   `agents/`, `.agent-runtime/`, `docs/modules/ai/_agents/`,
   `src/assetutilities/agent_os/`, and `.claude/agents/`. Produce a
   one-page index.
2. **Map to issue #30 checkboxes.** For each unchecked checkbox in #30,
   mark: `done in repo X`, `superseded by .claude/agents/`, or
   `still-todo`. Post the mapping as an issue comment.
3. **Decide the residual scope.** Two paths:
   - **(a) Close #30** as superseded; file 1-2 narrow follow-ups for the
     genuinely-still-todo items (e.g., "ship a `gitbash` distribution
     script that copies `.claude/agents/` from assetutilities to N
     downstream repos").
   - **(b) Reduce #30** to just that distribution script.
   Default: path (a). Awaiting maintainer ack.
4. **Document the agent index.** Write `docs/modules/ai/agents-index.md`
   listing every agent YAML with: name, purpose, source-of-truth path,
   downstream consumers. This is the artifact whether we pick (a) or (b).
5. **(If path b)** Implement `scripts/sync-agents.sh <target-repo>` that
   rsyncs `.claude/agents/` and `docs/modules/ai/_agents/` to a target
   repo with a `--dry-run` default. Add smoke test.

## Acceptance criteria

- [ ] `docs/modules/ai/agents-index.md` enumerates every agent asset
      with path + purpose.
- [ ] Comment on #30 maps each checkbox to current state (done /
      superseded / still-todo).
- [ ] Either #30 closed with follow-up issues filed, or #30 retitled
      to the residual scope.
- [ ] No new agent YAMLs or persona files added by this plan (kept
      conservative).

## Open questions

- Is `.claude/agents/` the canonical agent home in workspace-hub now?
  If yes, the answer to "where do agent YAMLs live" is upstream of
  assetutilities and #30 should close.
- Does the maintainer want a literal cross-repo distribution script, or
  is per-repo `.claude/` already syncing via workspace-hub tooling?
