# AssetUtilities Repository Structure Contract

Issue #78 Phase 1 adds a conservative, enforceable structure contract for this repository. The goal is to prevent new CI/CD drift before any broad package, docs, or generated-artifact migration happens.

## Contract surfaces

- Machine-readable contract: `config/repo_structure.yml`
- Checker: `scripts/maintenance/verify_repo_structure.py`
- TDD coverage: `tests/repo_structure/test_repo_structure_contract.py`
- CI enforcement: `.github/workflows/tests.yml`
- Local enforcement: `.pre-commit-config.yaml`

## Current policy

The checker enforces two low-risk gates:

1. Every tracked root entry must be explicitly listed as an approved root file or directory.
2. Every tracked top-level generated-output root must have exception metadata before it can remain tracked.

Generated-looking files are **not** moved or deleted by this phase. Existing tracked `results/` evidence is retained as a temporary durable exception with owner, review date, follow-up issue, and reason metadata. Future work can migrate or classify those files under a separately approved issue.

## Reference-scan gate

Before any candidate path is moved, run the checker reference scan:

```bash
uv run python scripts/maintenance/verify_repo_structure.py \
  --reference-scan-root . \
  --candidate-move results/example.csv
```

A non-zero exit means live references still consume the candidate path; do not move it until references and rollback notes are handled.

## CI/local usage

```bash
uv run python scripts/maintenance/verify_repo_structure.py
bash scripts/hygiene/check-source-hygiene.sh
uv run python -m pytest tests
```

The repo-structure checker runs in the main test workflow and as a pre-commit local hook so newly introduced root/generated drift is caught before merge.
