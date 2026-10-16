#!/usr/bin/env bash
# Python/Node versions stay in sync across config files.
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONPATH=src

python -m pytest -q tests/environment
