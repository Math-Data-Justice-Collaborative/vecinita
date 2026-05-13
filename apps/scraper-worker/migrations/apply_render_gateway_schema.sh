#!/usr/bin/env bash
# Apply render_gateway_scraper_schema.sql to the database in DATABASE_URL.
# Run from repo root or any cwd (script resolves SQL path relative to this file).
#
# Connection notes (Render Postgres):
# - "Internal Database URL" hostnames like dpg-xxxxx-a only resolve inside Render's network.
# - From your laptop or a non-Render VM, use the External Connection String from the
#   database dashboard (host ends with REGION-postgres.render.com, requires SSL).
# - IP allowlisting (if enabled) only authorizes your address; it does not make internal
#   dpg-* hostnames resolve off Render—you still need the External URL in DATABASE_URL.
# - Or open Render Shell on vecinita-gateway (or any service in the same env) and run
#   this script there with DATABASE_URL from the dashboard.
# - From the repo checkout, you can put DATABASE_URL in .env at the repo root; this script
#   loads it when DATABASE_URL is not already set in the environment.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
SQL="${HERE}/render_gateway_scraper_schema.sql"

# Load repo-root .env if DATABASE_URL is not already exported (shell env wins).
if [[ -z "${DATABASE_URL:-}" && -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required: export it, or set it in ${REPO_ROOT}/.env (e.g. from Render dashboard)." >&2
  exit 1
fi

_render_gateway_check_db_url() {
  DATABASE_URL="$DATABASE_URL" python3 <<'PY'
import os
import sys
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
parsed = urlparse(url)
host = parsed.hostname or ""
if not host:
    sys.exit(0)
# Internal-only Render host: does not resolve outside Render's network.
if host.startswith("dpg-") and "render.com" not in host:
    print(
        "apply_render_gateway_schema.sh: DATABASE_URL uses host %r, which does not resolve "
        "outside Render's private network (Temporary failure in name resolution).\n"
        "\n"
        "Fix one of:\n"
        "  1) Render Dashboard → your Postgres → Connect → copy the **External** connection "
        "string (hostname like …REGION-postgres.render.com) and set it as DATABASE_URL "
        "(IP allowlisting does not fix DNS for internal hostnames).\n"
        "  2) Render Dashboard → vecinita-gateway-lx27 → Shell → clone or paste this repo → "
        "export DATABASE_URL from **Internal Database URL** → run this script again.\n"
        % (host,),
        file=sys.stderr,
    )
    sys.exit(2)
sys.exit(0)
PY
}

_render_gateway_check_db_url
check_status=$?
if [[ "$check_status" -eq 2 ]]; then
  exit 2
fi

# Ensure SSL when using Render public hostname (harmless if already in URL).
export PGSSLMODE="${PGSSLMODE:-require}"

exec psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$SQL"
