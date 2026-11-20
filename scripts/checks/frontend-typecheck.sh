#!/usr/bin/env bash
# Type-check the frontend.
set -euo pipefail
cd "$(dirname "$0")/../.."

npm --prefix frontend run typecheck
