# Plan: Consolidate hardware (#36)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/36
- Tier: T3 (infrastructure; out-of-scope; recommend re-route or close)
- Repo: assetutilities (proposed: re-route)
- Status: plan-review

## Context

Issue #36 is a hardware-setup checklist for a Linux machine: graphics
card, sound card, SMB for an 8 TB drive, dual monitor, remote login for
India employees, KVM, USB-C sound card for ACMA meetings, wired
internet. None of these items have any code or doc deliverable in
assetutilities.

**Re-routing recommendation:** this work belongs in workspace-hub
(or a private ops/IT tracker). assetutilities should not host hardware
checklists.

Recent workspace-hub memory entries cover similar territory
(`project_ace_linux_2_vnc.md`, `project_elements_drive_identity.md`)
which suggests workspace-hub is the right home.

In-scope here: re-route + close. No assetutilities deliverable.

## Plan

1. **Audit unchecked items.** From the issue body, list which checkboxes
   are still open (sound card, SMB, dual monitor, X-server remote login,
   ACMA remote login, USB-C sound, wired internet).
2. **Cross-check workspace-hub memory.** For each item, look up whether
   workspace-hub already has a project-memory entry covering it
   (e.g., VNC for remote login, Elements drive for SMB-equivalent).
   Mark: covered / not covered.
3. **File workspace-hub umbrella issue.** Title: "Hardware setup
   consolidation (continuation of assetutilities #36)". Body lists the
   remaining items + links to existing workspace-hub memory entries
   that already cover some of them.
4. **Close #36** in assetutilities with a link to the new workspace-hub
   issue.

## Acceptance criteria

- [ ] Comment on #36 with the audit (covered vs not covered) table.
- [ ] Workspace-hub umbrella issue filed.
- [ ] #36 closed with link to the workspace-hub issue.

## Open questions

- Some items (e.g., "remote login for India employees") may have
  privacy / security considerations and may belong in a private repo
  rather than workspace-hub. Confirm with maintainer.
- Does workspace-hub already have a hardware/ops issue tracker we
  should append to instead of creating a new umbrella?
