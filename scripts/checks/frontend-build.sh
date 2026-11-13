#!/usr/bin/env bash
# Production build of the frontend.
set -euo pipefail
cd "$(dirname "$0")/../.."

npm --prefix frontend run build
