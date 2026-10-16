#!/usr/bin/env bash
# Integration and recognition tests.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src

python -m pytest -q tests/integration tests/recognition
