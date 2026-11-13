#!/usr/bin/env bash
# Unit tests.
set -euo pipefail
cd "$(dirname "$0")/../.."

python -m pytest -q tests/unit
