#!/usr/bin/env bash
# =============================================================================
# run_migrations.sh — Apply Vecinita DB migrations to Render Postgres
#
# Usage:
#   DATABASE_URL=postgresql://user:pass@host:5432/db ./run_migrations.sh
#   ./run_migrations.sh --dry-run     (print SQL file list, no execution)
#
# Requirements: psql CLI must be available in PATH
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/migrations" && pwd)"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [ -z "${DATABASE_URL:-}" ]; then
  echo "[error] DATABASE_URL is not set." >&2
  echo "        Export it before running:" >&2
  echo "        export DATABASE_URL=postgresql://user:pass@host:5432/dbname" >&2
  exit 1
fi

# Enumerate migration files in lexicographic order
mapfile -t MIGRATIONS < <(find "$SCRIPT_DIR" -maxdepth 1 -name '*.sql' | sort)

if [ "${#MIGRATIONS[@]}" -eq 0 ]; then
  echo "[warn] No .sql migration files found in $SCRIPT_DIR"
  exit 0
fi

echo "[info] Running migrations against: $(echo "$DATABASE_URL" | sed 's|://[^@]*@|://***@|')"
echo "[info] Found ${#MIGRATIONS[@]} migration file(s):"
for f in "${MIGRATIONS[@]}"; do
  echo "       $(basename "$f")"
done

if [ "$DRY_RUN" = true ]; then
  echo "[info] Dry-run mode — no SQL was executed."
  exit 0
fi

for migration in "${MIGRATIONS[@]}"; do
  name="$(basename "$migration")"
  echo "[run]  $name ..."
  psql "$DATABASE_URL" \
    --single-transaction \
    --set ON_ERROR_STOP=1 \
    --file "$migration" \
    --quiet
  echo "[ok]   $name"
done

echo ""
echo "[done] All migrations applied successfully."
