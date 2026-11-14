#!/usr/bin/env bash
# Latency benchmark and command safety tests (end-to-end test skips itself).
set -euo pipefail
cd "$(dirname "$0")/../.."

python -m pytest -q tests/performance
