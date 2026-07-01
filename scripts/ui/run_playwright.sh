#!/usr/bin/env bash
# CI-parity Playwright UI tests (T0-ui tier — preview + route mocks).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

bash scripts/npm_with_lock.sh bash -eu -o pipefail -c '
  npm ci
  bash scripts/ui/build_for_playwright.sh
  npx playwright install chromium
  npx playwright test "$@"
' -- "$@"
