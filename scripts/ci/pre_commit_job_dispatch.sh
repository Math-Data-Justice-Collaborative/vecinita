#!/usr/bin/env bash
# Husky pre-commit gate: Modal/DM job_type dispatch must stay fail-closed.
# Evidence: BUG-2026-07-31 — unknown/eval types must not fall through to ingest.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ "${VECINITA_SKIP_PRE_COMMIT:-}" == "1" ]]; then
	echo "pre-commit job-dispatch: skipped (VECINITA_SKIP_PRE_COMMIT=1)"
	exit 0
fi

echo "pre-commit: job_type dispatch gate (BUG-2026-07-31)"
uv run pytest tests/bugs/test_bug_2026_07_31_eval_job_dispatch.py -q --tb=line
