# Releasing assetutilities

assetutilities is consumed from git by `digitalmodel` and `worldenergydata`
(PyPI still carries 0.1.0, which lacks `workflow_api`). Consumers pin a
**release tag**, never a branch, so a new commit on `main` cannot change a
consumer environment until that consumer moves its pin.

## Version and tag scheme

- The version lives in `pyproject.toml` (`[project].version`), mirrored in
  `src/assetutilities/__init__.py` (`__version__`) and the root entry of `uv.lock`.
- Semantic Versioning. While the version is `0.x`, a behavior or API change bumps
  the minor version and a fix-only release bumps the patch version.
- Release tags are annotated and named `v<version>`, for example `v0.2.0`.
  Older tags (`0.0.8`, `archive/*`, `backup/*`, `enhanced-agent-os-*`) predate this
  scheme and are not release pins.
- A tag is never moved or deleted once pushed. A bad release is fixed by a new
  patch release.

## First tagged release: `v0.2.0`

| Item | Value |
|------|-------|
| Version | `0.2.0` (bumped from the untagged `0.1.1`) |
| Tag | `v0.2.0` (annotated) |
| Commit | the head of `main` right after the PR that bumps the version to `0.2.0` merges |

The `0.1.1` string was carried by many different `main` commits, so it is not
tagged. The minor bump also covers the units template-matching change listed in
`CHANGELOG.md`.

## Release steps

1. **Release PR.** Open a PR that:
   - bumps `version` in `pyproject.toml`, `__version__` in
     `src/assetutilities/__init__.py`, and the root `assetutilities` entry in `uv.lock`;
   - moves the `CHANGELOG.md` entries under `[Unreleased]` into a new
     `## [<version>]` section.
2. **Merge** it with CI green.
3. **Tag the merge commit** (a maintainer with push rights does this):

   ```bash
   git fetch origin main
   git checkout --detach origin/main
   # Confirm HEAD is the release PR merge and the version matches the tag
   git log -1 --oneline
   grep '^version = ' pyproject.toml        # version = "0.2.0"
   git tag -a v0.2.0 -m "assetutilities 0.2.0"
   git push origin v0.2.0
   git ls-remote --tags origin v0.2.0        # record the commit for consumers
   ```

4. Optionally create a GitHub release from the tag:
   `gh release create v0.2.0 --title "assetutilities 0.2.0" --notes-from-tag`
   (or paste the CHANGELOG section as notes).
5. **Move the consumer pins** (see below).

## Consumer pins

Each consumer declares the source in `[tool.uv.sources]`:

```toml
assetutilities = { git = "https://github.com/vamseeachanta/assetutilities.git", tag = "v0.2.0" }
```

and refreshes only this package in its lock:

```bash
uv lock --upgrade-package assetutilities
```

Then it runs its assetutilities contract tests (`tests/contracts/`) and opens a PR.
`digitalmodel` CI also overlays assetutilities in `.claude/quality-gates.yaml`
(`--with 'assetutilities @ git+...@<ref>'`); that overlay must name the same tag.

Until `v0.2.0` exists, the consumer PRs for the first tagged release pin
`rev = "<sha>"` (the `main` commit they were tested against) and switch to
`tag = "v0.2.0"` once the tag is pushed.

## Proposal: weekly pin-bump PR (not installed)

This is a proposal only. No workflow file is added here; schedules are installed
by the desk.

A scheduled job (weekly, in each consumer repo, or one job in a hub repo that
loops over both consumers) would:

1. Find the newest release tag:
   `git ls-remote --tags --refs https://github.com/vamseeachanta/assetutilities.git 'v*'`,
   sorted by version (ignoring tags that are not `v<semver>`).
2. Compare it with the `tag =` in the consumer's `[tool.uv.sources]`. If equal, stop.
3. Otherwise, on a branch such as `bot/assetutilities-v<version>`, rewrite the tag,
   run `uv lock --upgrade-package assetutilities`, and run the consumer's
   assetutilities contract tests.
4. Open (or update) one PR titled `chore(deps): bump assetutilities to v<version>`
   whose body links the CHANGELOG section between the old and new tags and
   includes the test result. It never merges itself; a person reviews and merges.

The job needs a token that can push branches and open PRs in the consumer repos.
