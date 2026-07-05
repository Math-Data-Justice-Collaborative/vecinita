#!/usr/bin/env bash
# Start local Postgres when needed, migrate, run a command, tear down only if we started it.
#
# Used by make test-py, make ci, and scripts/run_tests.sh so docker compose is not left
# running after CI-style runs. If compose Postgres is already up, it is left running.
#
# Env:
#   VECINITA_KEEP_POSTGRES=1  — never run docker compose down (debug)
#   COMPOSE_FILE              — defaults to infra/docker-compose.yml
#   DATABASE_URL              — exported for Alembic/pytest
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose.yml}"
DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita}"
export DATABASE_URL

VECINITA_STARTED_POSTGRES=0

compose_postgres_running() {
	docker compose -f "$COMPOSE_FILE" ps --services --filter status=running 2>/dev/null | grep -qx postgres
}

postgres_accepts_connections() {
	if compose_postgres_running; then
		docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U vecinita -d vecinita >/dev/null 2>&1
		return $?
	fi
	if command -v pg_isready >/dev/null 2>&1; then
		pg_isready -h localhost -p 5432 -U vecinita -d vecinita >/dev/null 2>&1
		return $?
	fi
	uv run python - <<'PY'
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

url = os.environ["DATABASE_URL"]
try:
    with create_engine(url).connect() as conn:
        conn.execute(text("SELECT 1"))
except SQLAlchemyError:
    sys.exit(1)
PY
}

start_postgres() {
	echo "==> Starting local Postgres (docker compose)"
	docker compose -f "$COMPOSE_FILE" up -d postgres
	echo "Waiting for Postgres..."
	until postgres_accepts_connections; do sleep 1; done
	VECINITA_STARTED_POSTGRES=1
}

stop_postgres() {
	if [[ "${VECINITA_KEEP_POSTGRES:-0}" == "1" ]]; then
		echo "==> Keeping local Postgres running (VECINITA_KEEP_POSTGRES=1)"
		return 0
	fi
	if [[ "$VECINITA_STARTED_POSTGRES" == "1" ]]; then
		echo "==> Stopping local Postgres (docker compose down)"
		docker compose -f "$COMPOSE_FILE" down
	fi
}

teardown() {
	local status=$?
	stop_postgres
	exit "$status"
}

trap teardown EXIT INT TERM

if postgres_accepts_connections; then
	echo "==> Postgres already reachable; leaving compose stack unchanged on exit"
else
	start_postgres
fi

echo "==> Applying Alembic migrations"
(cd apps/database && uv run alembic upgrade head)

if (($# == 0)); then
	echo "with_local_postgres.sh: expected command" >&2
	exit 2
fi

"$@"
