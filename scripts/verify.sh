#!/usr/bin/env bash
# Check the environment, then run everything CI runs (except the Docker
# build) and print a summary. Run it with `lando verify`.
set -uo pipefail

cd "$(dirname "$0")/.."

steps=()
failed=0

run_step() {
  local name="$1"
  shift
  printf '\n\033[1m==> %s\033[0m\n' "$name"
  if "$@"; then
    steps+=("  ✓ $name")
  else
    steps+=("  ✗ $name")
    failed=1
  fi
}

print_summary() {
  printf '\n\033[1mSummary\033[0m\n'
  printf '%s\n' "${steps[@]}"
}

run_step "Environment doctor" python scripts/check_env.py
if [ "$failed" -ne 0 ]; then
  print_summary
  printf '\nFix the environment problems above before running the other checks.\n'
  exit 1
fi

run_step "Python lint" ruff check .
run_step "Python formatting" ruff format --check .
run_step "Environment tests" python -m pytest -q tests/environment
run_step "Unit tests" python -m pytest -q tests/unit
run_step "Smoke tests" python -m pytest -q tests/smoke
run_step "Frontend lint" npm --prefix frontend run lint
run_step "Frontend tests" npm --prefix frontend run test
run_step "Frontend build" npm --prefix frontend run build

print_summary
if [ "$failed" -ne 0 ]; then
  printf '\nSome checks failed. CI will fail on the same checks.\n'
  exit 1
fi
printf '\nAll checks passed. Your environment matches CI.\n'
