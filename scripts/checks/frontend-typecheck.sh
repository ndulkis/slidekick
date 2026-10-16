#!/usr/bin/env bash
# Type-check the frontend.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src

npm --prefix frontend run typecheck
