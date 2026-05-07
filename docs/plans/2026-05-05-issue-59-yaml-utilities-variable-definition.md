# Plan: yaml_utilities — Variable Definition + placeholders (#59)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/59
- Tier: T2 (medium, in-scope, residual is small)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #59 explores how to define variables in YAML files for the team's
configs:
- Single variable + directive block (per geoserver YSLD docs).
- YAML placeholders (per StackOverflow ref).
- Adopt the chosen pattern across team repos.

State on `main`:
- `tests/modules/yaml_utlities/yml/variables/` contains
  `variable_example_1.yml` and `variable_example_2.yml`.
- All explore-pattern checkboxes are marked done.
- The only unchecked item is: "incorporate the logic in our repos
  (together)".

The remaining work is essentially **distribution** — make the chosen
pattern discoverable + adoptable across digitalmodel, energydata, etc.

In-scope: write a short usage doc citing the existing example files,
add a tiny `assetutilities.yaml_variables` helper if not present, and
mark adoption follow-ups for the consumer repos.

Out-of-scope: rewriting consumer repos' YAMLs to use placeholders.

## Plan

1. **Inspect the example YAMLs.** Read the two files to confirm the
   chosen pattern (single variable + block; placeholders).
2. **Verify the loader path.** Find the Python code that actually
   resolves variables / placeholders. Likely under
   `src/assetutilities/modules/yml_utilities/` or `common/yml_utilities.py`.
   If the resolver is missing or partial, add it (small).
3. **Document.** Write `docs/modules/yaml_utilities/variables.md`
   covering: the two patterns, when to pick each, links to the
   example YAMLs, the loader API.
4. **Add a unit test** that loads each example YAML and asserts the
   resolved values.
5. **File adoption follow-ups.** Per consumer repo (digitalmodel,
   energydata, acma-projects), file an issue: "Adopt assetutilities
   YAML variable patterns from #59".
6. **Close #59** referencing merge commit + the follow-up issues.

## Acceptance criteria

- [ ] `docs/modules/yaml_utilities/variables.md` exists with both
      patterns documented + linked examples.
- [ ] Unit test loads both example YAMLs and asserts resolved values.
- [ ] Loader API is named, exported, and listed in the doc.
- [ ] Per-consumer-repo adoption follow-ups filed (or maintainer
      explicitly waives them).
- [ ] #59 closed referencing merge commit.

## Open questions

- Did the team converge on one pattern or accept both? The doc should
  recommend a default — propose **placeholders** for cross-file
  reuse, **single-variable directive** for in-file local refs.
- Is there overlap with the `cfg_argv_dict` substitution that
  `engine.py` already does? If yes, the doc should call out the
  relationship to avoid two competing variable systems.
