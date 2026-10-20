# Package releases to PyPI

Version tags build a source distribution and wheel, validate their metadata,
and pass those artifacts to a separate Trusted Publishing job. Local builds
use the same helper and do not upload anything. This implements the reusable
release path for this repository; it does not configure a PyPI account.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add a checked build helper and tag-based Trusted Publishing to replace manual token handling. |

## Maintainer setup

Before pushing a release tag:

- In the repository settings, create the GitHub environment named `pypi`.
  Require approval by a maintainer and restrict deployment tags to the release
  pattern `v*`. Protect release tags against unauthorized creation or changes.
- In the existing PyPI project's Publishing settings, add a GitHub Trusted
  Publisher. Use the repository's actual organization or user and repository
  name, workflow filename `release.yml` (filename only), and environment `pypi`.
  For a new package, use a pending publisher instead. Registration requires
  appropriate access to the PyPI project; it has not been performed by this change.
- Confirm the environment protection is effective before approving publishing.
  No repository PyPI password or long-lived API token is needed for this flow.
  Older manual upload aliases are separate from this workflow; review any
  existing credentials before retiring them, following the PyPA guide.

The required identity fields and optional environment binding are specified in
[PyPI: Adding a Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
The [PyPA publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
recommends requiring approval on the production environment and keeping build
and publish jobs separate. Both online editions were checked on 2026-10-20.

## Local build and validation

The helper requires Bash (including Git Bash), Python with `tomllib` (Python
3.11 or newer), and uv. This tooling requirement does not change the library's
supported Python versions. Run from the repository root:

```bash
bash scripts/release/build.sh . ../release-artifacts v0.1.1
python3 scripts/maintenance/check_wheel_package_data.py ../release-artifacts
```

Use the version actually recorded in `pyproject.toml`; the example version
comes from this repository's current `[project].version`. The output must be
new or empty. Previously built artifacts are retained, never cleaned by the
helper. Set `UV` or `PYTHON` to an executable if it has a different name or
location; each variable takes one executable, not shell arguments.

The helper first requires the exact tag `v` followed by the static project
version. This prefix is a repository convention, not a PyPI requirement.
Dynamic versions are rejected by this helper. Then `uv build --no-sources`
builds a source distribution and a wheel, and
`uv run --no-project --with twine python -m twine check --strict` checks both.
The existing wheel guard separately ensures runtime base configurations ship.
No application dependencies are installed by the build helper.

The build follows [uv: Building and publishing a package](https://docs.astral.sh/uv/guides/package/),
which recommends `--no-sources` for portable build dependencies.
Static version metadata follows the
[PyPA pyproject.toml specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/#name).
Strict README and distribution metadata checking follows
[Twine: twine check](https://twine.readthedocs.io/en/stable/#twine-check).
These online editions were checked on 2026-10-20. This tooling performs no
engineering calculations, so engineering coefficients and equations do not apply.

## Worked example: inputs, method, answer

Inputs: a clean package source tree containing `[project].version = "0.1.1"`,
requested tag `v0.1.1`, and an empty output directory. The version is read from
`pyproject.toml`, not inferred from Git history.

Method:

1. Concatenate the literal prefix `v` with `0.1.1`: the expected tag is
   `v0.1.1`, which equals the input tag.
2. Build using the declared build backend and public build dependencies.
3. Run strict Twine metadata validation against the resulting wheel and source
   archive; run the package-data guard against the wheel.

Expected answer: both `assetutilities-0.1.1-py3-none-any.whl` and
`assetutilities-0.1.1.tar.gz` exist, Twine reports `PASSED` for each, and the
wheel guard reports packaged configuration files. A tag `v0.1.2` with the same
metadata fails before building. A directory containing an older wheel also
fails before building, leaving the old wheel intact. Synthetic tests repeat
these cases with version `1.2.3`; that number is fixture input, not a limit.

This validates the distribution build, metadata and configuration inclusion.
It does not establish that the package installs with all dependencies on every
platform or that PyPI will accept a new upload.

## Publishing a version

Update the static version in `pyproject.toml`, run the relevant package tests
and local build, and merge the reviewed change before tagging the release
commit. For an illustrative new version `X.Y.Z`:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Push only the intended tag. `.github/workflows/release.yml` responds to tags
matching `v*`; a branch push or pull request does not publish. The build job
checks the exact metadata/tag match, checks distribution metadata and packaged
configurations, then stores an artifact. Only after it succeeds can the
protected `pypi` job download and upload that artifact. Only the publishing
job receives `id-token: write`. The publishing job neither checks out source
nor runs the build backend. Default PyPA action attestations remain enabled.

After approving the protected job, confirm the workflow succeeded and that
PyPI lists the intended version. Test installation of that version in a clean
consumer environment. These live acceptance steps have not been run here.

## Failure recovery and reuse

- Tag mismatch: correct the metadata in a new reviewed commit and choose the
  matching release tag. Do not move an existing published tag.
- Build or strict metadata check failure: correct the reported packaging error
  and build into a fresh directory; the helper preserves earlier output.
- Identity or environment failure: check the registered repository identity,
  exact workflow filename and environment name against the PyPI instructions.
- An interrupted upload may have published some files. Inspect PyPI before
  retrying; the action deliberately does not skip existing distributions.
  PyPI does not allow reuse of an uploaded filename. If needed, publish a
  corrected new version. For a harmful release, consider yanking it using
  PyPI's project management controls; do not treat deletion as a rollback.

The filename restriction is documented in
[PyPI Help: file name reuse](https://pypi.org/help/#file-name-reuse), online
edition checked on 2026-10-20.

For another repository, copy `scripts/release/` and the release workflow,
register that repository's own publisher, and update the environment URL and
package-specific wheel guard. Keep the tag convention, static metadata check,
strict distribution validation and separation of privileges. Repositories
using dynamic versions or platform-specific wheels require a different build
strategy. TestPyPI is an optional later addition requiring its own publisher
and environment; this workflow publishes only to production PyPI.

## Verification commands

```bash
uv run --no-project --with 'pytest<9' --with pyyaml --with pytest-asyncio python -m pytest tests/release -q -p no:cacheprovider
uv run --no-project --with ruff ruff check scripts/release/validate_release.py tests/release
shellcheck scripts/release/build.sh
bash -n scripts/release/build.sh
```

Pytest 8 is used because the existing repository collection hook uses the
legacy `path` argument removed in pytest 9. This command does not alter or
skip that hook. Production publishing is verified only after maintainer setup
and the first real release; local tests use a fake uv executable to test
failure paths without uploading.
