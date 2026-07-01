#!/usr/bin/env bash
# Apply Alembic migrations against the staging/prod Postgres (EV-008 redeploy order).
#
# Requires DATABASE_URL in the environment (GitHub Actions secret or prod.env).
# Usage:
#   bash scripts/deploy/ci_materialize_env.sh
#   bash scripts/deploy/ci_alembic_upgrade.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

bash scripts/deploy/ci_materialize_env.sh --check alembic

: "${DATABASE_URL:?DATABASE_URL required — add to GitHub Actions secrets via sync_github_secrets.sh}"

echo "==> Alembic upgrade head (apps/database)"
export DATABASE_URL
cd apps/database
uv run alembic upgrade head
cd "$ROOT"
echo "==> Alembic at head"
