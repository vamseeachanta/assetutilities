# Plan: Simplify CI test environment to use declared test dependency path (#75)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/75
- Tier: T1 (tactical, in-scope, low risk)
- Repo: assetutilities
- Status: plan-review

## Context

`.github/workflows/tests.yml` currently installs test dependencies via two
mechanisms:

```
uv sync --group dev
uv pip install pytest-benchmark
```

The ad-hoc `uv pip install pytest-benchmark` step bypasses the declared
dependency contract in `pyproject.toml` and is a drift risk. Issue #75 asks
that CI use a single declared path: either move `pytest-benchmark` into the
`dev` group (or a dedicated `test` group) and drop the ad-hoc step, or
document the intentional divergence.

In-scope: edit `pyproject.toml` dependency groups + `.github/workflows/tests.yml`.

Out-of-scope: broader CI restructure (caching, matrix, parallelism).

## Plan

1. **Inspect current state.** Read `pyproject.toml` `[dependency-groups]`
   (or `[project.optional-dependencies]`, whichever the repo uses) and
   confirm `pytest-benchmark` is not already declared. Read
   `.github/workflows/tests.yml` to confirm the install steps.
2. **Pick the single declared path.** Default choice: add `pytest-benchmark`
   to the existing `dev` group in `pyproject.toml`. Rationale: minimal
   churn, matches what `uv sync --group dev` already pulls.
3. **Edit the declared dependency set.** Add `pytest-benchmark>=4.0` (or
   the version currently being installed transitively in CI) to the
   `dev` group entries.
4. **Edit the workflow.** Remove the `uv pip install pytest-benchmark` line
   from `.github/workflows/tests.yml`. Leave `uv sync --group dev` as the
   sole install command.
5. **Validate locally.** Run `uv sync --group dev` in a clean venv, then
   `uv run python -c "import pytest_benchmark; print(pytest_benchmark.__version__)"`.
   Then `uv run python -m pytest tests -q --tb=short --collect-only` to
   confirm pytest still discovers tests.
6. **Open PR.** Title: `ci: install pytest-benchmark via dev group, drop ad-hoc uv pip step`.
   Body cites #75 and shows before/after of `tests.yml`.

## Acceptance criteria

- [ ] `pytest-benchmark` declared in `pyproject.toml` dev (or test) group.
- [ ] `.github/workflows/tests.yml` contains exactly one install command
      for test deps (`uv sync --group dev`).
- [ ] Local `uv sync --group dev` followed by `uv run python -m pytest --collect-only`
      succeeds.
- [ ] CI green on the PR branch.
- [ ] Issue #75 closed referencing the merge commit.

## Open questions

- Should `pytest-benchmark` go in `dev` or in a dedicated `test` group?
  Default is `dev` to keep churn minimal; revisit only if the repo
  already has a separate `test` group.
