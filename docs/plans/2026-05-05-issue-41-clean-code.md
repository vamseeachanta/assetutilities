# Plan: Clean code conventions doc (#41)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/41
- Tier: T2 (in-scope; modest doc + light enforcement)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #41 says:
> Assumption that consistent code will help AI add new code/documentation
> faster, seamless. Reference: docs/clean_code.md (on the 202502 branch).

The referenced file `docs/clean_code.md` exists today on `main` (4 KB,
short style guide). The issue is essentially "make this doc real /
enforced".

In-scope: refresh `docs/clean_code.md` to current state, add a short
checklist that the AI agents can read at PR time, and wire one or two
of the rules into existing `scripts/hygiene/check-source-hygiene.sh`
(referenced in `.github/workflows/tests.yml`) so the CI gate enforces
them.

Out-of-scope: full lint/format ruleset (ruff config, mypy adoption);
those are larger separate efforts.

## Plan

1. **Read current `docs/clean_code.md`.** Identify which rules are
   (a) opinion-only (keep as prose), (b) mechanically checkable
   (promote to script-level enforcement per the workspace-hub
   enforcement gradient).
2. **Refresh the doc.** Sections to add or harden:
   - Naming: snake_case for funcs/vars; PascalCase for classes;
     `SCREAMING_SNAKE` for constants.
   - File layout: `src/assetutilities/<area>/<module>.py`; tests
     mirror under `tests/unit/` or `tests/modules/`.
   - Imports: stdlib / third-party / first-party blocks separated;
     no relative imports beyond one level.
   - Docstrings: Google-style or NumPy-style (pick one) on public
     callables.
   - Logging: use loguru `logger` (cf. #28).
   - Errors: raise typed exceptions, not bare `Exception`.
3. **Audit `scripts/hygiene/check-source-hygiene.sh`.** Add or confirm
   checks for: no merge markers (cf. #72), no `print()` in `src/`
   (use logger), no bare `except:` clauses.
4. **Add `tests/test_clean_code_hygiene.py`** (tiny test that runs the
   hygiene script and asserts exit 0). This makes the rule visible to
   `pytest` runs, not just CI.
5. **Open PR.** Title:
   `docs(clean-code): refresh conventions and wire two rules into hygiene gate`.

## Acceptance criteria

- [ ] `docs/clean_code.md` refreshed with the sections above.
- [ ] `scripts/hygiene/check-source-hygiene.sh` enforces at minimum:
      no merge markers, no `print()` in `src/`, no bare `except:`.
- [ ] `tests/test_clean_code_hygiene.py` runs the script as a
      pytest-callable check.
- [ ] CI green; pre-existing hygiene step still passes.
- [ ] Issue #41 closed referencing merge commit.

## Open questions

- Google-style vs NumPy-style docstrings? Default Google (shorter).
- Should ruff be adopted in the same PR? Default: no — file follow-up;
  this PR is doc + hygiene only.
