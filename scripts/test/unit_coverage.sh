#!/usr/bin/env bash
# Run unit tests with coverage for Python packages/apps and TS frontends.
# Prints a per-component summary via print_unit_coverage_summary.py.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

UV="${UV:-uv}"
FRONTENDS=(chat-rag-frontend data-management-frontend)

mkdir -p coverage

echo "==> Python unit tests (tests/unit)"
"$UV" run pytest tests/unit \
	-q \
	--cov \
	--cov-report=json:coverage/python.json \
	--cov-report=html:htmlcov

echo "==> TypeScript unit tests (Vitest + coverage)"
bash scripts/npm_with_lock.sh bash scripts/npm_workspaces.sh run test:coverage \
	vecinita-chat-rag-frontend vecinita-data-management-frontend

echo ""
"$UV" run python scripts/test/print_unit_coverage_summary.py --enforce
