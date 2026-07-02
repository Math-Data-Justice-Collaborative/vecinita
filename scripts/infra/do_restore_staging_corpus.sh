#!/usr/bin/env bash
# Fork vecinita-staging from a DO daily backup and swap DATABASE_URL on backend apps.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/infra/do_restore_staging_corpus.sh
#
# Optional:
#   VECINITA_DO_BACKUP_AT=2026-07-01T16:41:12Z
#   VECINITA_DO_FORK_NAME=vecinita-staging-restored-20260701
#   VECINITA_DO_SKIP_DEPLOY=1   # only fork + verify counts
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}"

SOURCE_CLUSTER_ID="${VECINITA_DO_DB_CLUSTER_ID:-cb528db3-2840-4172-b3c3-6aa99fa00a2f}"
SOURCE_NAME="${VECINITA_DO_DB_SOURCE_NAME:-vecinita-staging}"
BACKUP_AT="${VECINITA_DO_BACKUP_AT:-2026-07-01T16:41:12Z}"
FORK_NAME="${VECINITA_DO_FORK_NAME:-vecinita-staging-restored-20260701}"

if [[ -z "${DIGITALOCEAN_TOKEN:-}" ]]; then
  echo "ERROR: DIGITALOCEAN_TOKEN required (source prod.env)." >&2
  exit 1
fi

echo "==> Source cluster: ${SOURCE_NAME} (${SOURCE_CLUSTER_ID})"
echo "==> Backup timestamp: ${BACKUP_AT}"
echo "==> Fork name: ${FORK_NAME}"

meta="$(curl -fsS \
  -H "Authorization: Bearer ${DIGITALOCEAN_TOKEN}" \
  "https://api.digitalocean.com/v2/databases/${SOURCE_CLUSTER_ID}")"

read -r REGION ENGINE VERSION SIZE NUM_NODES <<<"$(python3 -c "
import json, sys
db = json.loads(sys.argv[1])['database']
print(db['region'], db['engine'], db['version'], db['size'], db['num_nodes'])
" "${meta}")"

echo "==> Fork spec: region=${REGION} engine=${ENGINE} version=${VERSION} size=${SIZE} nodes=${NUM_NODES}"

create_body="$(python3 -c "
import json
print(json.dumps({
    'name': '${FORK_NAME}',
    'engine': '${ENGINE}',
    'version': '${VERSION}',
    'region': '${REGION}',
    'size': '${SIZE}',
    'num_nodes': int('${NUM_NODES}'),
    'backup_restore': {
        'database_name': '${SOURCE_NAME}',
        'backup_created_at': '${BACKUP_AT}',
    },
}))
")"

echo "==> Creating forked cluster (this may take several minutes)..."
create_resp="$(curl -fsS -X POST \
  -H "Authorization: Bearer ${DIGITALOCEAN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${create_body}" \
  "https://api.digitalocean.com/v2/databases")"

FORK_ID="$(python3 -c "import json,sys; print(json.load(sys.stdin)['database']['id'])" <<<"${create_resp}")"
echo "==> Fork cluster id: ${FORK_ID}"

echo "==> Waiting for fork to become online..."
for _ in $(seq 1 60); do
  status="$(curl -fsS \
    -H "Authorization: Bearer ${DIGITALOCEAN_TOKEN}" \
    "https://api.digitalocean.com/v2/databases/${FORK_ID}" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['database']['status'])")"
  echo "    status=${status}"
  if [[ "${status}" == "online" ]]; then
    break
  fi
  if [[ "${status}" != "creating" && "${status}" != "forking" && "${status}" != "migrating" ]]; then
    echo "ERROR: unexpected cluster status: ${status}" >&2
    exit 1
  fi
  sleep 30
done

if [[ "${status}" != "online" ]]; then
  echo "ERROR: fork did not reach online within timeout." >&2
  exit 1
fi

fork_meta="$(curl -fsS \
  -H "Authorization: Bearer ${DIGITALOCEAN_TOKEN}" \
  "https://api.digitalocean.com/v2/databases/${FORK_ID}")"

NEW_DATABASE_URL="$(python3 -c "
import json, sys
db = json.loads(sys.argv[1])['database']
print(db['connection']['uri'])
" "${fork_meta}")"

echo "==> Verifying corpus row counts on fork..."
DOC_COUNT="$(DATABASE_URL="${NEW_DATABASE_URL}" uv run python -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    total = conn.execute(text('SELECT count(*) FROM documents')).scalar()
    fixtures = conn.execute(text(\"SELECT count(*) FROM documents WHERE url LIKE 'fixture://%'\")).scalar()
    real = conn.execute(text(\"SELECT count(*) FROM documents WHERE url NOT LIKE 'fixture://%'\")).scalar()
print(f'{total}|{fixtures}|{real}')
")"

IFS='|' read -r TOTAL FIXTURES REAL <<<"${DOC_COUNT}"
echo "    documents total=${TOTAL} fixtures=${FIXTURES} real=${REAL}"

if [[ "${REAL}" -lt 1 ]]; then
  echo "ERROR: fork has no non-fixture documents — aborting DATABASE_URL swap." >&2
  exit 1
fi

if [[ -f prod.env ]]; then
  python3 -c "
import pathlib, re, sys
path = pathlib.Path('prod.env')
text = path.read_text()
new_url = sys.argv[1]
if re.search(r'^DATABASE_URL=', text, flags=re.M):
    text = re.sub(r'^DATABASE_URL=.*$', f'DATABASE_URL={new_url}', text, flags=re.M)
else:
    text = text.rstrip() + f'\nDATABASE_URL={new_url}\n'
path.write_text(text)
" "${NEW_DATABASE_URL}"
  echo "==> Updated prod.env DATABASE_URL (gitignored)"
else
  export DATABASE_URL="${NEW_DATABASE_URL}"
  echo "WARN: prod.env missing — export DATABASE_URL manually before sync-secrets." >&2
fi

set -a
# shellcheck disable=SC1091
source prod.env
set +a

if [[ "${VECINITA_DO_SKIP_DEPLOY:-}" == "1" ]]; then
  echo "==> VECINITA_DO_SKIP_DEPLOY=1 — skipping DO app secret sync/deploy"
  echo "OK: fork ${FORK_NAME} (${FORK_ID}) ready with ${REAL} real documents."
  exit 0
fi

echo "==> Syncing DATABASE_URL to backend DO apps..."
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-secrets --name vecinita-internal-write-api
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-secrets --name vecinita-chat-rag-backend

echo "==> Redeploying backends..."
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-internal-write-api
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-chat-rag-backend

echo "==> Post-restore verification (live DATABASE_URL)..."
uv run python /tmp/check_corpus.py 2>/dev/null || uv run python -c "
import os
from sqlalchemy import create_engine, text
e = create_engine(os.environ['DATABASE_URL'])
with e.connect() as c:
    t = c.execute(text('SELECT count(*) FROM documents')).scalar()
    r = c.execute(text(\"SELECT count(*) FROM documents WHERE url NOT LIKE 'fixture://%'\")).scalar()
print('documents total:', t, 'real:', r)
"

echo ""
echo "OK: restored corpus from backup ${BACKUP_AT}"
echo "    New cluster: ${FORK_NAME} (${FORK_ID})"
echo "    Old cluster ${SOURCE_NAME} is unchanged — destroy it after smoke tests pass."
echo "    Run: bash scripts/deploy/staging_smoke.sh"
