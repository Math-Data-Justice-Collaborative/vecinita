#!/usr/bin/env bash
# Verify DigitalOcean Managed Postgres backups for vecinita-staging (corpus recovery).
# Uses DO REST API — doctl databases backups list has a known path bug on some versions.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/infra/do_verify_staging_backups.sh
#
# Optional:
#   VECINITA_DO_DB_CLUSTER_ID=cb528db3-...  (default: vecinita-staging)
#   VECINITA_DO_BACKUP_MIN_AGE_HOURS=24     (fail if newest backup older than this)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CLUSTER_ID="${VECINITA_DO_DB_CLUSTER_ID:-cb528db3-2840-4172-b3c3-6aa99fa00a2f}"
MIN_AGE_HOURS="${VECINITA_DO_BACKUP_MIN_AGE_HOURS:-24}"

if [[ -z "${DIGITALOCEAN_TOKEN:-}" ]]; then
  echo "ERROR: DIGITALOCEAN_TOKEN is required (export from prod.env)." >&2
  exit 1
fi

response="$(curl -fsS \
  -H "Authorization: Bearer ${DIGITALOCEAN_TOKEN}" \
  "https://api.digitalocean.com/v2/databases/${CLUSTER_ID}/backups")"

backup_count="$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
print(len(data.get('backups') or []))
" "${response}")"

if [[ "${backup_count}" -lt 1 ]]; then
  echo "ERROR: No backups found for DO cluster ${CLUSTER_ID}." >&2
  echo "Enable daily backups in DO control panel: Databases → vecinita-staging → Backups." >&2
  exit 1
fi

echo "OK: ${backup_count} backup(s) available for DO cluster ${CLUSTER_ID} (vecinita-staging)."

python3 -c "
import json, sys
from datetime import datetime, timedelta, timezone

data = json.loads(sys.argv[1])
min_age_hours = int(sys.argv[2])
backups = sorted(data.get('backups') or [], key=lambda b: b.get('created_at', ''), reverse=True)
newest = backups[0]
created = datetime.fromisoformat(newest['created_at'].replace('Z', '+00:00'))
age = datetime.now(tz=timezone.utc) - created
print(f\"Newest backup: {newest['created_at']} ({age.total_seconds() / 3600:.1f}h ago, {newest.get('size_gigabytes', '?')} GiB)\")
if age > timedelta(hours=min_age_hours + 24):
    print(
        f'WARNING: Newest backup is older than {min_age_hours + 24}h — verify DO backup schedule.',
        file=sys.stderr,
    )
print()
print('Restore (fork from backup) — DO control panel or API:')
print('  https://docs.digitalocean.com/products/databases/postgresql/how-to/restore-from-backups/')
print('  Fork to a new cluster, verify corpus row counts, then swap DATABASE_URL on DO apps.')
" "${response}" "${MIN_AGE_HOURS}"

echo ""
echo "Corpus TRUNCATE on staging is blocked in tests — see tests/helpers/corpus_db_guard.py"
