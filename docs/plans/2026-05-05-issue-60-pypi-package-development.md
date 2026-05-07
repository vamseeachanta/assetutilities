# Plan: PyPI package development + GitHub Actions release flow (#60)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/60
- Tier: T2 (medium, in-scope, infra)
- Repo: assetutilities
- Status: plan-review

## Context

Issue #60 wants:
- gitbash scripts to manage PyPI uploads across repos.
- Migrate to GitHub Actions (Twine under the hood) over time.
- Learn how to manage PyPI secrets.
- Create PyPI tokens per repo.

assetutilities is already on PyPI (per `pyproject.toml`). The cross-repo
"all repos" framing is too broad for one issue; this plan narrows to:
**ship a release Action for assetutilities itself + a reusable workflow
template that other repos can copy.**

In-scope:
- `.github/workflows/release.yml` triggered on git tag `v*`.
- Trusted-publishing via OIDC (PyPI's recommended modern path) — no
  long-lived API tokens stored in GitHub secrets.
- Doc: `docs/sub_release/pypi.md` covering tag → release flow.

Out-of-scope: rolling the same action into digitalmodel / energydata /
etc. (file follow-ups).

## Plan

1. **Confirm PyPI project ownership.** `pip index versions assetutilities`
   to confirm current published version. Note the PyPI project owner
   (vamseeachanta) — needed to configure trusted-publishing.
2. **Configure PyPI trusted-publishing.**
   - On pypi.org: add a "trusted publisher" for the
     `vamseeachanta/assetutilities` GitHub repo, workflow
     `release.yml`, environment `pypi`.
   - This avoids the need to manage `PYPI_API_TOKEN` secrets.
3. **Add `.github/workflows/release.yml`.** Triggered on `push` to
   tags matching `v*`. Steps: checkout → setup-uv → `uv build` →
   `pypa/gh-action-pypi-publish@release/v1` (uses OIDC).
4. **Add `docs/sub_release/pypi.md`.** Cover: how to bump version in
   `pyproject.toml`, `git tag vX.Y.Z`, `git push --tags`, what the
   action does, how to roll back a bad release.
5. **(Optional)** Add a manual `workflow_dispatch` test path that
   builds + uploads to TestPyPI for dry-runs.
6. **File follow-up issues** for digitalmodel, energydata, etc., to
   adopt the same workflow template.
7. **Open PR.** Tag the first release after merge to validate end-to-end.

## Acceptance criteria

- [ ] `.github/workflows/release.yml` exists; uses OIDC (no
      `PYPI_API_TOKEN` secret).
- [ ] PyPI trusted-publisher configured for the workflow.
- [ ] `docs/sub_release/pypi.md` documents the tag-driven flow.
- [ ] First post-merge tag (`v<next>`) successfully publishes to PyPI.
- [ ] Per-repo adoption follow-ups filed.
- [ ] #60 closed referencing merge commit.

## Open questions

- Does the PyPI account already have 2FA + trusted-publishing
  available? If 2FA isn't set up, that has to land first.
- Should the action also produce a GitHub Release with auto-generated
  changelog? Default: yes — `softprops/action-gh-release` after the
  publish step.
