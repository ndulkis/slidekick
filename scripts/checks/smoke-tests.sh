#!/usr/bin/env bash
# Gesture smoke tests.
set -euo pipefail
cd "$(dirname "$0")/../.."

python -m pytest -q tests/smoke
