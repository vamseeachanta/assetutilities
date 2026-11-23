# Plan: YAML file split + OrcaFlex automation (#52)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/52
- Tier: T2 (medium, in-scope, narrow residual)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #52 originally covered:
- Create individual ruamel YAML function as a module.
- Refactor save-yml flow.
- Plot X-Y from two arrays in a YAML file using the visualization template.
- Install OrcaFlex demo and automate the YAML test there.

State on `main`:
- `src/assetutilities/modules/yml_utilities/ruamel_yaml.py` exists.
- The visualization template path lives under `src/assetutilities/common/visualization*`
  (re-verify on PR).
- The first three items are all checked in the body. The remaining
  unchecked item is **OrcaFlex automation**: "automate the opening or
  otherwise of the OrcaFlex .yml test".

OrcaFlex is a commercial proprietary solver from Orcina. assetutilities
should not own an OrcaFlex driver (that lives in `digitalmodel/orcaflex/`
per the digitalmodel repo). The remaining acceptance criterion belongs
in digitalmodel, not assetutilities.

**Re-routing recommendation:** narrow #52 to "verify ruamel module +
plot helper are stable and documented", and re-route the OrcaFlex piece
to a digitalmodel issue.

In-scope: doc + smoke-test pass on existing modules; close.

## Plan

1. **Verify ruamel module surface.** Read
   `src/assetutilities/modules/yml_utilities/ruamel_yaml.py` and confirm:
   public functions documented; a roundtrip test exists under
   `tests/`. If missing, add a small unit test.
2. **Verify plot helper.** Confirm a YAML→X-Y plot example exists
   (look under `docs/sub_python/` or `examples/`). If missing, add a
   minimal example YAML + a 20-line script in `examples/yaml_xy_plot/`.
3. **File OrcaFlex follow-up in digitalmodel.** Title: "OrcaFlex YAML
   test automation (continuation of assetutilities #52)". Body links
   back here.
4. **Close #52** with a comment noting (a) ruamel + plot done, (b)
   OrcaFlex piece moved to digitalmodel.

## Acceptance criteria

- [ ] `ruamel_yaml.py` has at least one roundtrip unit test green.
- [ ] A YAML→X-Y plot example exists under `examples/` (or doc
      pointer to one).
- [ ] Digitalmodel follow-up issue filed for the OrcaFlex piece.
- [ ] #52 closed with comment.

## Open questions

- Is there already a YAML-driven plot example somewhere we missed?
  Default: search `examples/` and `docs/modules/visualization/` first
  before adding.
