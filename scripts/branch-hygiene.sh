#!/usr/bin/env bash
# Read-only daily report; PYTHON can select an existing Python interpreter.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON:-python}" "$script_dir/git/branch_hygiene.py" "$@"
