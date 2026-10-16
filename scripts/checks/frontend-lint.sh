#!/usr/bin/env bash
# Lint the frontend with oxlint.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src

npm --prefix frontend run lint
