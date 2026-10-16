#!/usr/bin/env bash
# Check the dev environment and print fixes.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src

python scripts/check_env.py
