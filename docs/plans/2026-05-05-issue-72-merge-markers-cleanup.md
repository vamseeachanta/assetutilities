# Plan: Cleanup merge markers blocking editable install (#72)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/72
- Tier: T1 (tactical, in-scope, high downstream impact)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #72 reports unresolved merge markers in `pyproject.toml` and
`src/assetutilities/common/update_deep.py`, which broke `uv` editable
resolution and downstream `digitalmodel` pytest startup.

Local verification on `main` (SHA at plan time) shows
`grep -c "<<<<<<< " pyproject.toml src/assetutilities/common/update_deep.py`
returns `0` for both files — i.e., the markers have already been removed in a
later commit. This plan therefore covers **verification + closure**, not a
fresh edit. The downstream consumer (`digitalmodel`) must still confirm that
its `uv sync` and pytest startup pass once it points at the current
`assetutilities` HEAD.

In-scope: confirm clean state, run editable install + smoke import locally,
post evidence to issue, close.

Out-of-scope: any larger refactor of `update_deep.py` or `pyproject.toml`.

## Plan

1. **Re-verify cleanliness on current `main`.** Run
   `grep -nE "^(<<<<<<< |======= |>>>>>>> )" pyproject.toml src/assetutilities/common/update_deep.py`
   and `git log --oneline -- pyproject.toml src/assetutilities/common/update_deep.py | head`
   to identify the resolving commit. Capture the commit SHA.
2. **Smoke-test editable install.** From a scratch venv:
   `uv pip install -e .` then `python -c "import assetutilities.common.update_deep as m; print(m.__file__)"`.
   Capture stdout/stderr.
3. **Smoke-test downstream consumer.** In `../digitalmodel`, run
   `PYTHONPATH=src uv run python -m pytest tests/solvers/calculix/test_fem_chain.py --collect-only -q`
   and confirm collection passes the import phase. (Test pass/fail beyond
   import is out of scope for this issue.)
4. **Document evidence on the issue.** Post a comment with: resolving
   commit SHA, `grep` output (zero markers), editable-install transcript,
   downstream collect-only transcript.
5. **Close #72** referencing the resolving commit. If the local check
   surprises us and markers are still present, escalate to a real fix
   plan (re-resolve conflict, add a CI gate that greps for marker
   patterns to prevent regression).

## Acceptance criteria

- [ ] `grep -E "^(<<<<<<< |======= |>>>>>>> )" pyproject.toml src/assetutilities/common/update_deep.py`
      returns no matches.
- [ ] `uv pip install -e .` succeeds from a clean venv.
- [ ] `import assetutilities.common.update_deep` succeeds without
      `SyntaxError`.
- [ ] Downstream `digitalmodel` pytest collection passes the import phase.
- [ ] Issue comment with verification evidence posted; issue closed
      referencing resolving commit.

## Open questions

- None. If verification fails, a follow-up plan is filed.
