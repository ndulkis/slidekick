#!/usr/bin/env bash
# Check Python formatting with Ruff (run `ruff format .` to fix).
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src

ruff format --check .
