#!/usr/bin/env bash
# Frontend tests (Vitest).
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src

npm --prefix frontend run test
