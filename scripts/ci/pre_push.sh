#!/usr/bin/env bash
# Husky pre-push hook — medium tier for fast day-to-day pushes.
#
# Tier workflow (Option 1 — ci-local-parity.mdc):
#   While editing  → hooks + make check-fast / make test-fast
#   Before commit  → make check
#   git push       → make check + make test-fast (this hook)
#   Before PR      → make ci-push (full CI parity; GitHub CI is the merge gate)
#
# Opt-in full local parity on push: VECINITA_FULL_PRE_PUSH=1 git push
# Skip entirely: VECINITA_SKIP_PRE_PUSH=1 git push
set -euo pipefail

if [[ "${VECINITA_SKIP_PRE_PUSH:-}" == "1" ]]; then
	echo "pre-push: skipped (VECINITA_SKIP_PRE_PUSH=1)"
	exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ "${VECINITA_FULL_PRE_PUSH:-}" == "1" ]]; then
	echo "pre-push: running make ci-push (full CI parity; VECINITA_FULL_PRE_PUSH=1)"
	exec make ci-push
fi

echo "pre-push: make check + make test-fast (run make ci-push before opening a PR)"
make check
make test-fast
