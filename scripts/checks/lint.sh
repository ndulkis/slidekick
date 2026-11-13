#!/usr/bin/env bash
# Lint Python with Ruff.
set -euo pipefail
cd "$(dirname "$0")/../.."

ruff check .
