# Archived: claude-flow-era boilerplate (2026-06-11)

This directory holds the 2025-generation agent scaffolding that shipped with the
claude-flow/ruv-swarm template: `agents/` (54 fictional agent definitions),
`commands/` (swarm/hive-mind/flow-nexus/sparc slash commands), `docs/`
(CONTEXT_LIMITS.md and friends written for "Claude 3.5/4, 200K context"), and the
600-line `CLAUDE.md` orchestration narrative.

Archived because instructions written for prior models anchor current models to
stale patterns: the MCP swarm tools never existed in this harness, the
`npx claude-flow@alpha` hooks failed on every tool call, and the PreCompact hooks
re-injected the fiction into every compacted session.

Kept (outside this archive): `.claude/skills/` (repo-specific), `.claude/hooks/`
(workspace-hub signal capture), `settings.json` (cleaned), statusline.

History is preserved via git mv — nothing was deleted.
