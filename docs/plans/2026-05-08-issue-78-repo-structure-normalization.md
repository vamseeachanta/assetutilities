# Plan for #78: chore(repo-structure): normalize assetutilities folder/file structure

> **Status:** ready for `status:plan-review` / user approval; implementation blocked
> **Complexity:** T3
> **Date:** 2026-05-08
> **Issue:** https://github.com/vamseeachanta/assetutilities/issues/78
> **Review artifact:** `scripts/review/results/2026-05-08-plan-78-repo-structure-review-synthesis.md`
> **Parent anchors:** workspace-hub#1962, workspace-hub#2397

---

## Decision Summary

This plan is a **repo-specific planning gate** for `assetutilities` folder/file structure normalization. It authorizes only a bounded Phase 1 after approval: inventory-backed structure contract, machine-readable exception policy, checker/test harness, and minimal documentation/index updates required to stop new drift.

No broad file moves, generated artifact deletion, package-source reshuffle, docs migration, or runtime behavior change is authorized until this plan is explicitly approved and Phase 1 tests/checkers exist.



## Resource Intelligence Summary

### Existing assets

- Repository: `vamseeachanta/assetutilities`
- Current issue: https://github.com/vamseeachanta/assetutilities/issues/78
- Root directories observed: .agent-os/, .agent-runtime/, .ai/, .benchmarks/, .claude/, .codex/, .command-backups/, .common-commands/, .common/, .drcode/, .gemini/, .git-commands/, .github/, .hive-mind/, .mypy_cache/, .planning/, .pytest_cache/, .ruff_cache/, .slash-commands/, .swarm/, .sync-reports/, .venv/, .vscode/, agents/, build/, config/, data/, dist/, docs/, examples/, htmlcov/, logs/, modules/, reports/, results/, scripts/, site/, slash_commands/, src/, tests/
- Root files observed: .command-registry.json, .coverage, .gitignore, .pre-commit-config.yaml, .python-version, .radon.cfg, .uvrc, AGENTS.md, CHANGELOG.md, CLAUDE.md, DEPLOYMENT_SUMMARY.md, ENHANCED_AGENT_OS_RELEASE.md, LICENSE, MANDATORY_SLASH_COMMAND_ECOSYSTEM.md, MANIFEST.in, MODULE_STRUCTURE.md, Makefile, README.md, REQUIREMENTS_MIGRATION.md, TEST_PATH_RESOLUTION_FIX.md, coverage.json, coverage.xml, create-module-agent.py, distribution_summary.md, global-uv-env.toml, hub-config.yaml, mkdocs.yml, poetry.lock, pyproject.toml, pyproject.toml.backup, pytest.ini, requirements.txt, uv.lock, vulture_whitelist.py
- Standard directory counts:
- `src/`: 513 files in working-tree scan
- `tests/`: 963 files in working-tree scan
- `docs/`: 2017 files in working-tree scan
- `scripts/`: 66 files in working-tree scan
- `config/`: 3 files in working-tree scan
- `.github/`: 3 files in working-tree scan
- `reports/`: 0 files in working-tree scan
- `results/`: 27 files in working-tree scan
- `data/`: 0 files in working-tree scan
- `modules/`: 7 files in working-tree scan
- `site/`: 49 files in working-tree scan
- `dist/`: 2 files in working-tree scan
- `build/`: 224 files in working-tree scan
- `htmlcov/`: 226 files in working-tree scan

### Tracked root files observed

- `AGENTS.md`
- `CHANGELOG.md`
- `CLAUDE.md`
- `.command-registry.json`
- `coverage.json`
- `create-module-agent.py`
- `DEPLOYMENT_SUMMARY.md`
- `distribution_summary.md`
- `ENHANCED_AGENT_OS_RELEASE.md`
- `.gitignore`
- `global-uv-env.toml`
- `hub-config.yaml`
- `LICENSE`
- `Makefile`
- `MANDATORY_SLASH_COMMAND_ECOSYSTEM.md`
- `MANIFEST.in`
- `mkdocs.yml`
- `MODULE_STRUCTURE.md`
- `poetry.lock`
- `.pre-commit-config.yaml`
- `pyproject.toml`
- `pyproject.toml.backup`
- `pytest.ini`
- `.radon.cfg`
- `README.md`
- `REQUIREMENTS_MIGRATION.md`
- `requirements.txt`
- `TEST_PATH_RESOLUTION_FIX.md`
- `uv.lock`
- `.uvrc`
- `vulture_whitelist.py`

### Tracked generated-output candidates observed

- `results/data_exploration.yml`
- `results/data_exploration_column.csv`
- `results/data_exploration_column_T.csv`
- `results/data_exploration_data_type.csv`
- `results/data_exploration_data_type_T.csv`
- `results/data_exploration_end_value.csv`
- `results/data_exploration_end_value_T.csv`
- `results/data_exploration_max.csv`
- `results/data_exploration_max_T.csv`
- `results/data_exploration_mean.csv`
- `results/data_exploration_mean_T.csv`
- `results/data_exploration_min.csv`
- `results/data_exploration_min_T.csv`
- `results/data_exploration_no_of_unique_values.csv`
- `results/data_exploration_no_of_unique_values_T.csv`
- `results/data_exploration_row_count.csv`
- `results/data_exploration_row_count_T.csv`
- `results/data_exploration_row_count_per_unique_values.csv`
- `results/data_exploration_row_count_per_unique_values_T.csv`
- `results/data_exploration_start_value.csv`
- `results/data_exploration_start_value_T.csv`
- `results/data_exploration_stdev.csv`
- `results/data_exploration_stdev_T.csv`
- `results/data_exploration_unique_values.csv`
- `results/data_exploration_unique_values_T.csv`
- `results/file_edit.yml`
- `results/file_management.yml`

### Related prior work

- Workspace-hub ecosystem anchors: `workspace-hub#1962` and `workspace-hub#2397`.
- `digitalmodel#596` is the template-quality first repo plan and discipline model: contract first, checker second, bounded moves only after approval.
- This plan does not assume previous repo-specific cleanup issues are complete; implementation must re-check live git state before editing.

### Constraints

- Follow workspace-hub hard gates: Issue → Plan → Adversarial Review → `status:plan-review` → explicit user approval → implementation.
- TDD is mandatory before checker or migration code.
- Preserve evidence and rollback ability for every moved/removed tracked path.
- Do not delete or relocate generated-looking tracked files until classified as unauthorized artifact, durable evidence, or temporary durable exception.
- Do not move package/source/runtime/static entrypoints without import/build/deploy proof specific to this repo.

### Gaps

- No approved local structure contract for this normalization tranche.
- Generated-output and root-clutter classification needs a machine-readable allow/deny/exception inventory before cleanup.
- CI/pre-commit enforcement may be absent or insufficient for new root artifacts.

### Risks / unknowns

- Hidden consumers may reference current paths from docs, CI, packaging, static hosting, notebooks, or external scripts.
- Some generated-looking files may be durable evidence or deploy artifacts; deleting them blindly would lose traceability.
- Root-level clutter can include user/session artifacts; implementation must not reset unrelated dirty files.

## Scope Boundaries

### In scope after approval

1. Add/update repo-local structure standard under `docs/standards/repo-structure.md` or closest existing standards surface.
2. Add machine-readable contract such as `config/repo_structure.yml` listing allowed roots, denied generated roots, and temporary durable exceptions.
3. Add checker under `scripts/maintenance/verify_repo_structure.py` or equivalent repo-appropriate maintenance path.
4. Add TDD tests under `tests/repo_structure/` or equivalent test surface.
5. Wire checker into pre-commit/CI if those surfaces exist.
6. Move only low-risk root utility/docs artifacts that have no source/runtime consumers and are covered by tests/checker evidence.
7. Create follow-up issues for broad package/docs/generated-evidence migrations discovered during implementation.

### Out of scope

- Bulk source package reorganization.
- Broad docs tree migration.
- Deletion of generated-looking tracked files without classification and follow-up linkage.
- Notebook/data/report/static deploy relocation unless explicitly classified and tested.
- Any execution before explicit user approval.

## Artifact Map

| Artifact | Path | Purpose |
|---|---|---|
| Canonical plan | `docs/plans/2026-05-08-issue-78-repo-structure-normalization.md` | Approval gate for this repo |
| Review synthesis | `scripts/review/results/2026-05-08-plan-78-repo-structure-review-synthesis.md` | Adversarial/readiness findings |
| Structure standard | `docs/standards/repo-structure.md` or existing standard path | Human-readable contract |
| Machine contract | `config/repo_structure.yml` | Checker source of truth |
| Checker | `scripts/maintenance/verify_repo_structure.py` | Enforce root/generated/exception rules |
| Tests | `tests/repo_structure/test_repo_structure_contract.py` | TDD for checker and contract |
| Approval marker after approval only | `.planning/plan-approved/78.md` | Execution authorization evidence |

## Pseudocode

```text
load config/repo_structure.yml
collect git-tracked paths and working-tree root entries
for each root entry:
    classify as allowed, denied-generated, temporary-exception, or unknown
    if unknown or denied without exception:
        emit deterministic violation with remediation hint
for each temporary exception:
    require owner/category/review-date/follow-up URL/non-placeholder justification
scan moved-file candidates:
    require no references outside approved update set before moving
return nonzero if violations exist
```

## TDD Test List

- RED: checker fails on an unapproved root file/dir fixture.
- RED: checker fails on tracked generated-output root without exception metadata.
- RED: checker fails on exception metadata with placeholder owner/review-date/follow-up URL.
- GREEN: checker accepts current approved roots and explicitly listed exceptions.
- GREEN: reference scan blocks candidate moves with live consumers.
- GREEN: CI/pre-commit invocation path is covered by a smoke test or workflow grep assertion.

## Acceptance Criteria

1. Plan remains planning-only until explicit user approval.
2. Implementation has TDD coverage before checker/migration code lands.
3. Human-readable and machine-readable structure contracts exist.
4. Generated-output candidates are classified, not blindly deleted.
5. CI/pre-commit prevents newly introduced root/generated drift.
6. Any moved paths have reference-scan proof and rollback notes.
7. Follow-up issues are created for broad migrations rather than silently absorbed.

## Follow-up Issue Candidates

- Package/domain module reorganization if inventory shows large package-layout drift.
- Generated evidence relocation/classification for tracked reports/results/build outputs.
- Docs/navigation restructuring if docs references require broader moves.
- Static deploy artifact policy, if applicable, for generated `dist/`, site, sitemap, or public assets.

## Review Readiness Notes

This plan is intentionally conservative and reusable across the tier-1 repo ecosystem. Reviewers should reject implementation attempts that start moving/deleting files before the contract/checker/test layer is approved and green.

## Approval Gate

Execution is not authorized until the user approves this exact plan and implementation records `.planning/plan-approved/78.md` with the reviewed commit/blob SHA.
