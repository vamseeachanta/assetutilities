# Plan: Environment management — converge on uv, retire poetry scripts (#32)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/32
- Tier: T2 (medium, in-scope, decision + cleanup)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #32 asked whether to use poetry vs uv for environment management.
The repo state has answered the question already: `pyproject.toml` is uv-flavored,
CI uses `uv sync --group dev` (per #75), and ecosystem-wide convention
(per global memory and other workspace-hub repos) is `uv run`.

However, the repo still ships:

- `poetry.lock` at the root (contradicts the uv lockfile workflow)
- legacy "Utilize poetry for environment management" gitbash snippets
  referenced from the issue

This plan locks in uv as the sole supported path and retires the poetry
artifacts.

In-scope: delete `poetry.lock`, audit any `pyproject.toml` `[tool.poetry]`
sections, replace doc references to poetry with uv equivalents, ensure
`uv.lock` is committed and authoritative.

Out-of-scope: introducing new dependency groups (covered by #75); changing
Python version pins.

## Plan

1. **Audit poetry artifacts.**
   - `git ls-files | grep -i poetry` to enumerate.
   - Inspect `pyproject.toml` for `[tool.poetry]`, `[tool.poetry.dependencies]`,
     etc.
   - Inspect `Makefile` and `scripts/` for `poetry install` / `poetry run`
     invocations.
2. **Decide the canonical lockfile.**
   - Confirm `uv.lock` exists and is up-to-date (`uv lock --check` or
     `uv lock --dry-run`).
   - If absent, run `uv lock` and commit.
3. **Delete poetry artifacts.**
   - `git rm poetry.lock` (and `pyproject.toml.backup` if it's stale poetry-era).
   - Remove `[tool.poetry*]` sections from `pyproject.toml`, leaving only
     PEP-621 `[project]` and uv-native `[tool.uv]`/`[dependency-groups]`.
4. **Update docs and scripts.** Replace any "poetry install" /
   "poetry run" examples with `uv sync` / `uv run`. Specifically check:
   `README.md`, `docs/sub_python/`, `Makefile`, `scripts/`.
5. **Validate locally.** From a clean clone:
   `uv sync --group dev && uv run python -m pytest tests -q --collect-only`.
6. **Open PR.** Title:
   `chore(env): drop poetry, converge on uv as sole environment manager`.

## Acceptance criteria

- [ ] No `poetry.lock` in the repo.
- [ ] No `[tool.poetry*]` sections in `pyproject.toml`.
- [ ] `uv.lock` present and current.
- [ ] No poetry references in `README.md` / docs / `Makefile`.
- [ ] `uv sync --group dev && uv run python -m pytest --collect-only` green.
- [ ] Issue #32 closed referencing merge commit.

## Open questions

- Are there any internal contributors still running `poetry install`?
  If so, add a one-liner migration note to `README.md`.
- Should `pyproject.toml.backup` be deleted too, or kept as historical?
  Default: delete; the backup pre-dates the uv migration.
