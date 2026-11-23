# Plan: Email cleanup automation (#39)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/39
- Tier: T3 (out-of-scope; recommend close)
- Repo: assetutilities (proposed: close)
- Status: plan-review

## Context

Issue #39 asks for a script to:
- Treat email as transient (not storage).
- Delete unstarred / unimportant emails older than 365 days.
- Reduce / eliminate spam over time.

All three checkboxes in the body are already marked. The body lists no
referenced files or scripts in assetutilities, and there is no email
automation code in `src/`. Email mutation work has substantially shifted
to the workspace-hub Gmail MCP work (see global memory:
`project_gmail_mcp_scope_bump_decision.md`, `feedback_gmail_*` entries),
which uses OAuth `gmail.modify` scope on the `claude_ai_Gmail` MCP.

**Re-routing recommendation:** close #39. The actual capability now
lives in workspace-hub Gmail MCP; if there's still desire for an
assetutilities-hosted script, it's redundant with that work.

In-scope here: triage + close. No code.

## Plan

1. **Comment on #39.** Note that:
   - Email cleanup is now handled via workspace-hub Gmail MCP filter +
     archive flow (per global memory feedback entries).
   - assetutilities is not the right home for email automation
     (no IMAP/MAPI deps, no OAuth handling).
2. **Close #39** with `wontfix` or `superseded`.
3. **(Optional)** If the maintainer wants a documentation pointer in
   assetutilities, add a one-paragraph note in `docs/sub_email/README.md`
   pointing at the workspace-hub Gmail MCP project memory entries.

## Acceptance criteria

- [ ] Comment on #39 referencing the workspace-hub Gmail MCP work.
- [ ] #39 closed.
- [ ] (Optional) doc pointer added if maintainer requests it.

## Open questions

- Is there any cross-repo email automation that genuinely belongs in
  assetutilities (e.g., a parser for vendor emails into structured YAML)?
  If yes, that's a separate fresh issue, not a continuation of #39.
