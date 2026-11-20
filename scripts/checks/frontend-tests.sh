#!/usr/bin/env bash
# Frontend tests (Vitest).
set -euo pipefail
cd "$(dirname "$0")/../.."

npm --prefix frontend run test
