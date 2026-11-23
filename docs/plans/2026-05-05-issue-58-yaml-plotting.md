# Plan: YAML plotting — placeholder triage (#58)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/58
- Tier: T3 (placeholder; recommend close in favor of #52)
- Repo: assetutilities (proposed: close as duplicate)
- Status: plan-review

## Context

Issue #58 has a one-line body: "placeholder for yml plots". It was
opened 2025-04-09 — after #52 (YAML file split) which covered the same
"plot from YAML arrays" capability.

`docs/modules/visualization/` contains plotly + matplotlib templates,
and `docs/modules/visualization/plotly/pycode.py` shows the plotting
side. The "yml + plot" wiring is what #52 already addresses.

**Re-routing recommendation:** close #58 as duplicate of #52, or as a
placeholder that never got fleshed out.

In-scope here: triage + close. No code.

## Plan

1. **Compare #58 against #52.** Confirm overlap. If #52's plot work is
   complete (it is, per the body checkboxes), #58 has no residual.
2. **Comment on #58.** Recommend close-as-duplicate-of-#52, or ask the
   filer to specify what's still wanted that isn't covered by #52.
3. **Close #58** with `duplicate` label after maintainer ack.
4. **(If #58 turns out to mean something concrete that #52 didn't cover):**
   replace this plan with a narrow scoped one — e.g., "ship a
   `yaml-plot` CLI in assetutilities that takes a YAML config and
   emits a Plotly HTML".

## Acceptance criteria

- [ ] Comment on #58 noting overlap with #52.
- [ ] #58 closed (duplicate) or scope clarified by filer.

## Open questions

- Does the filer (vamseeachanta) recall what specific YAML-plotting
  scenario this placeholder was meant to capture? The 1-line body
  isn't recoverable without that input.
