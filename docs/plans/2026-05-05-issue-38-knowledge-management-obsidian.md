# Plan: Knowledge management — Obsidian setup (#38)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/38
- Tier: T3 (productivity / out-of-scope; recommend re-route or close)
- Repo: assetutilities (proposed: close)
- Status: plan-review

## Context

Issue #38 is a stub asking to:
- Read Obsidian YouTube resources from Siva.
- Install Obsidian packages across machines.

There is no deliverable in assetutilities. Knowledge-management tooling
choices (Obsidian vs alternatives, vault layout) are workspace-level
or personal decisions, not assetutilities-internal.

The workspace-hub memory layer already serves as the team's knowledge
substrate (`.claude/memory/topics/`, `KNOWLEDGE.md`,
`docs/sessions/`). The question "do we also adopt Obsidian on top" is
a workflow decision separate from assetutilities.

**Re-routing recommendation:** close #38. If Obsidian adoption is still
desired, file a workspace-hub issue.

In-scope here: triage + close. No code.

## Plan

1. **Comment on #38.** Note that workspace-hub memory + `.claude/`
   ecosystem now handles team knowledge management; ask if Obsidian
   is still being considered as a complement.
2. **If yes:** file workspace-hub issue "Evaluate Obsidian as
   complement to .claude/ memory" with concrete sub-items (vault
   layout, sync mechanism, gitignore boundary).
3. **If no:** close #38 with `wontfix` and a comment.

## Acceptance criteria

- [ ] Comment on #38 with current state.
- [ ] Decision recorded (re-route vs close).
- [ ] #38 closed.

## Open questions

- Are the YouTube videos in the issue body still considered required
  watching, or is the team past that point?
- Does anyone on the team currently use Obsidian on top of .claude/,
  and if so do they want a shared vault?
