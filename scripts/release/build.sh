#!/usr/bin/env bash
# Build and check distributions; this helper never uploads them.
# Build basis: Astral uv, Building and publishing a package, online edition
# retrieved 2026-10-20; --no-sources verifies portable build dependencies.
set -euo pipefail

if [[ $# != 3 ]]; then
  printf 'Usage: bash build.sh PROJECT OUTPUT TAG\n' >&2
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project="$1"
output="$2"
tag="$3"
python_command="${PYTHON:-python3}"
uv_command="${UV:-uv}"

"$python_command" "$script_dir/validate_release.py" "$project" "$tag" "$output"
mkdir -p -- "$output"
"$uv_command" build --no-sources --out-dir "$output" "$project"
# PyPA Twine documentation, twine check --strict (online edition, 2026-10-20).
"$uv_command" run --no-project --with twine python -m twine check --strict \
  "$output"/*.whl "$output"/*.tar.gz
