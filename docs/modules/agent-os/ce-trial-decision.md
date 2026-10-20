# Compound Engineering trial decision

**Recommendation: drop for now; no ecosystem rollout.** At the 2026-10-20
review, issues #82–#85 are open and contain no result comments. Installation,
isolation, advisory value and the compounding loop are `NOT_EVALUATED`, not
failed measurements. No skill has earned adoption on that evidence. This is a
provisional recommendation for maintainer ratification in #86, not a finding
that the plugin is ineffective or an authorization to begin rollout.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| Initial | 2026-10-20 | Record the evidence gap and block rollout pending the trial results. |

## Scope and sources

The source requirements are this repository's issues, read on 2026-10-20:

| Source | Requirement used | Observed evidence |
|---|---|---|
| #81, goal, guardrails and success criteria | Evaluate before ecosystem integration; choose artifact policies; protect mains. | Defines the trial; supplies no completed evaluations. |
| #82, acceptance criteria | User-scoped installation, ignored local config and dependency health. | Open; no result comments. |
| #83, acceptance criteria and cleanup | Isolated trial, clean primary checkout, artifact policy and branch disposition. | Open; no result comments. |
| #84, skills and acceptance criteria | Report-only code review, debug, simplification and documentation review; written value assessments. | Open; no result comments. |
| #85, steps and acceptance criteria | Plan, tested implementation, review and reusable solution on a feature branch. | Open; no result comments. |
| #86, task and deliverable | Decide before rollout; persist skill selection and repository guardrails. | Decision proposed here; ratification remains pending. |

Issue references identify source records within this repository. The checked
acceptance criteria describe desired evidence; unchecked boxes and issue state
alone do not prove a trial ran or failed. The example input records this dated
observation, not a live GitHub query. No plugin installation or skill execution
is claimed. The package contains existing agent tooling but no CE trial result
was found in the package search. The security-remediation issue #80 linked by
#84 supplies a possible trial subject, not a CE evaluation.

## Slice 1: evidence and recommendation

The [read-only gate](../../../src/assetutilities/devtools/ce_trial.py) accepts
reviewed assessments for installation, isolation and the named trial skills.
Each record has `status`, a list of `evidence` references, and a substantive
`reason`. Status is exactly `PASS`, `FAIL` or `NOT_EVALUATED`. An observed result
requires a nonempty evidence list. Unknown or missing assessment names and
invalid records are errors. `PASS` means the cited trial outcome has been
reviewed against the corresponding issue criteria; merely running a command
is insufficient.

The following conservative decision rule is proposed for #86. It is an authored
policy derived from #81's success criteria and #86's evidence gate, rather than
a numerical performance threshold:

- Let **P** mean installation AND isolation assessments pass (#82 and #83).
- Let **A** be the passing advisory skills from #84.
- Let **T** mean every advisory and loop assessment passes (#84 and #85).
- If P AND T, recommend `adopt`, keep all assessed skills, mode `full`.
- Otherwise, if P AND A is nonempty, recommend `adopt-partial`, keep A only,
  mode `advisory`. An incomplete loop earns no implementation skills.
- Otherwise, recommend `drop`, keep nothing, mode `none`.

The shared `ce-code-review` assessment covers both report-only value and loop
review behavior. Passing it requires evidence for both contexts to recommend
full adoption. The gate never authenticates evidence, approves a decision,
installs skills, changes ignore rules, invokes CE, commits, pushes or opens PRs.
A computed `adopt` result remains a recommendation for a maintainer to review.

## Slice 2: skill selection and conditional rollout

**Current keep-list: empty.** Every candidate below is `NOT_EVALUATED`.

| Candidate | Evidence required before keeping | Proposed scope after acceptance |
|---|---|---|
| `ce-code-review` | #84 report-only findings and value assessment; #85 review and autofix assessment for full adoption. | Report-only initially; reviewed fixes only in the accepted loop. |
| `ce-debug` | #84 debugging result, value assessment and clean-tree evidence. | Advisory diagnosis. |
| `ce-simplify-code` | #84 soundness assessment and clean-tree evidence. | Suggestions only. |
| `ce-doc-review` | #84 documentation findings, value assessment and clean-tree evidence. | Advisory review. |
| `ce-plan` | #85 usable plan and written assessment. | Planning with the repository's artifact policy. |
| `ce-work` | #85 tested implementation and observed feature-branch protection. | Feature branch only, after full adoption. |
| `ce-compound` | #85 reusable solution and written reuse assessment. | Reviewed knowledge capture, after full adoption. |

`ce-setup` and `ce-worktree` are setup mechanisms, not evidence of skill value.
`ce-commit-push-pr` and `lfg` are excluded from the earned keep-list: the former
is optional in #85 and neither has an observed evaluation. Any later use needs
separate reviewed evidence and repository authorization.

All entries below are **conditional plans**, currently blocked by the no-go
recommendation. This change configures no other repository.

| Repository | Maximum scope after a ratified go decision | Guardrails | Artifact policy proposed for local review |
|---|---|---|---|
| `assetutilities` | Full loop after full acceptance; accepted advisory skills only after partial acceptance. | Separate trial worktree; feature branch; PR only; maintainer merges. | Commit reviewed public-only plans and solutions and relevant glossary/strategy changes on the feature branch. |
| `digitalmodel` | Plan → work → review → PR after full acceptance; advisory only after partial acceptance. | Change directory into this separate repository first; verify repository and branch; protect main; no direct push, force-push or automatic merge. | Commit reviewed public-only artifacts; keep sensitive planning outside public Git. |
| `worldenergydata` | Plan → work → review → PR after full acceptance; advisory only after partial acceptance. | Change directory into this separate repository first; verify repository and branch; protect main; no direct push, force-push or automatic merge. | Commit reviewed public-only artifacts; keep sensitive planning outside public Git. |
| Private application repository | Full loop after full acceptance; advisory only after partial acceptance. | Verify the intended private repository locally; feature branch; PR and maintainer review. Its identity is deliberately omitted from this public record. | Commit reviewed plans and solutions in the private repository, subject to its data and rights rules. |
| `workspace-hub` | Advisory and planning only, under either adoption outcome. | Never target it with commit, push or PR skills, including `ce-work`, `ce-commit-push-pr` and `lfg`; the existing synchronization service retains control. No sensitive planning in public Git. | Gitignore CE-generated plans, brainstorms, solutions, glossary and strategy artifacts locally; retain only reviewed general guidance through the existing synchronization workflow. |

Per #81, the artifact set is `docs/plans/`, `docs/brainstorms/`,
`docs/solutions/`, `CONCEPTS.md` and `STRATEGY.md`. Apply a reviewed policy in
each target before producing artifacts. Do not blanket-ignore or remove
already tracked documentation: an ignore rule cannot untrack it. In the hub,
use advisory work that does not write those paths until a local exclusion
strategy protecting existing content is verified. Local configuration
`.compound-engineering/*.local.yaml` remains ignored in every repository;
the trial repository now records that narrow ignore rule. It covers setup
configuration only, not generated documentation or sensitive content generally.

Rollout order after ratification: retain the contained trial as the reference,
then review a separate PR for each public engineering repository, then the
private application repository. Assess the hub independently in advisory mode.
At each step, inspect the destination repository, public-content policy, branch
protection, diff, tests and reusable solution; stop that step on missing evidence,
unauthorized writes or artifact leakage. Revert an integration through a reviewed
PR if it violates those criteria. Never infer one repository's readiness from
another repository's successful trial.

## Slice 3: adoption note and worked example

The persistent [adoption note](ce-adoption-note.md) is linked from the canonical
documentation entry point. It preserves the no-go state and the hub restriction
for future work without editing agent instructions or private configuration.

Input: [ce-trial-evidence.json](../../../examples/devtools/ce-trial-evidence.json).
From the repository root, run the standard-library-only assessment:

```sh
PYTHONPATH=src uv run --no-project python -m assetutilities.devtools.ce_trial examples/devtools/ce-trial-evidence.json
```

Method: installation and isolation are both unknown, hence P is false. Every
candidate is unknown, hence A is empty and T is false. The rule therefore gives:

```json
{
  "verdict": "drop",
  "mode": "none",
  "keep": [],
  "failed": [],
  "not_evaluated": [
    "ce-code-review", "ce-compound", "ce-debug", "ce-doc-review", "ce-plan",
    "ce-simplify-code", "ce-work", "install", "worktree"
  ]
}
```

The gate sorts the lists and object keys; JSON key order does not affect the
answer. A valid no-go assessment exits successfully; invalid input returns an
error and no recommendation. To reassess, supply a separate reviewed input with
result references and reasons; do not overwrite this dated observation with
invented successes.

The regression cases derive expected recommendations by hand from the Boolean
rule in their docstrings. Successful trial fixtures are synthetic; they do not
supply real evidence for adoption. Tests cover the missing-results example,
accepted and partial trials, broken prerequisites and loop members, malformed
records and read-only CLI behavior. There are no engineering constants or
unsourced performance limits in this decision.

## Baseline

The repository collection hook still uses the removed `path` argument in
`tests/conftest.py:65`. Unbounded pytest resolution selected an incompatible
release; focused validation uses pytest 8.4.2 without changing that hook.
The routing contract also fails because the unchanged `standard_report` entry
in `docs/registry/module-routing.yaml` is not a top-level package directory.
Both entries are present on `origin/main`; neither is changed by this decision.

## Hooks that could not run

The hook framework is not installed in the validation environment and is not
run here. The direct Gitleaks check could not start: `gitleaks version` returned
`gitleaks: command not found`. Its hook entry is unchanged on `origin/main`.
Ruff, formatting, Bandit and the repository structure check run directly;
repository hooks remain required at commit time.

## Follow-up

Run and record #82–#85 through an authorized CE trial before reconsidering #86.
Capture installation health and ignored-config evidence, isolation and artifact
policy, advisory findings and time/value assessments, the plan, tested diff,
review and reusable solution. Include the evidence for protected-main behavior
and the trial worktree/branch disposition. No trial branch is deleted or claimed
to be cleaned here. The separate decision change is prepared for draft-PR
promotion; publication does not establish cleanup of the original trial.

Maintainers still need to ratify the verdict and copy or link the decision in
#86 before closing its gate. Actual CE execution, cross-repository integration,
optional publishing-skill evaluation and trial cleanup are later work; they are
not represented as completed slices by this change.
