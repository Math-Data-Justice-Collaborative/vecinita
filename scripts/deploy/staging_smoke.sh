#!/usr/bin/env bash
# H1–H3 staging smoke (15-service-health). Requires deployed staging URLs.
set -euo pipefail

CHAT_URL="${VECINITA_STAGING_CHAT_URL:?Set VECINITA_STAGING_CHAT_URL}"
WRITE_URL="${VECINITA_STAGING_WRITE_URL:-}"

echo "H1: ChatRAG liveness"
curl -fsS "${CHAT_URL%/}/health" | tee /tmp/vecinita-health.json
python3 -c "import json,sys; d=json.load(open('/tmp/vecinita-health.json')); assert d.get('status')=='ok', d"

if [[ -n "$WRITE_URL" ]]; then
  echo "H1: Internal write API liveness"
  curl -fsS "${WRITE_URL%/}/health"
fi

echo "H3: Sample ask"
curl -fsS -X POST "${CHAT_URL%/}/api/v1/ask" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What are the food pantry hours?"}' \
  | tee /tmp/vecinita-ask.json
python3 -c "
import json
p=json.load(open('/tmp/vecinita-ask.json'))
assert p.get('answer'), 'missing answer'
assert p.get('language') in ('en','es'), p
print('OK: ask returned answer in', p['language'])
"

echo "Staging smoke passed (H1 + H3)."
