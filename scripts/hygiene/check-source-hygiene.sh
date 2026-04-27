#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

failures=0

check_empty() {
  local description="$1"
  shift

  local output
  output="$("$@" || true)"
  if [[ -n "$output" ]]; then
    printf 'FAIL: %s\n%s\n' "$description" "$output" >&2
    failures=$((failures + 1))
  else
    printf 'PASS: %s\n' "$description"
  fi
}

check_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    printf 'FAIL: required routing surface missing: %s\n' "$path" >&2
    failures=$((failures + 1))
  else
    printf 'PASS: required routing surface exists: %s\n' "$path"
  fi
}

check_file "AGENTS.md"
check_file "README.md"
check_file "MODULE_STRUCTURE.md"
check_file "docs/README.md"
check_file "docs/maps/assetutilities-operator-map.md"
check_file "docs/registry/module-routing.yaml"

check_empty "no tracked backup artifacts" \
  git ls-files ':(glob)**/*.bak' ':(glob)**/*.orig'

check_empty "no root visualizations scratch BAT files" \
  git ls-files tests/visualizations_tests.bat tests/visualizations_tests_temp.bat

check_empty "no Python cache files tracked" \
  git ls-files ':(glob)**/__pycache__/**' ':(glob)**/*.pyc'

if ! grep -qxF "*.bak" .gitignore; then
  printf 'FAIL: .gitignore missing *.bak\n' >&2
  failures=$((failures + 1))
else
  printf 'PASS: .gitignore contains *.bak\n'
fi

if ! grep -qxF "*.orig" .gitignore; then
  printf 'FAIL: .gitignore missing *.orig\n' >&2
  failures=$((failures + 1))
else
  printf 'PASS: .gitignore contains *.orig\n'
fi

exit "$failures"
