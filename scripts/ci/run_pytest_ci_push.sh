#!/usr/bin/env bash
# Full Python pytest paths plus unit coverage (ci-push tier) inside one Postgres session.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTEST_PATHS=(
	tests/unit
	tests/integration
	tests/privacy
	tests/e2e
	tests/smoke
	tests/eval
	tests/bugs
)

"$UV" run pytest "${PYTEST_PATHS[@]}"
bash scripts/test/unit_coverage.sh
