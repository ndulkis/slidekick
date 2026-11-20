#!/usr/bin/env bash
# Check the dev environment and print fixes.
set -euo pipefail
cd "$(dirname "$0")/../.."

python scripts/check_env.py
