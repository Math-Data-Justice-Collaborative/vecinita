#!/usr/bin/env bash
# H1–H3 staging smoke (15-service-health). Skips tiers when env vars are unset.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RAN=0

run_h1() {
  local chat_url="${VECINITA_STAGING_CHAT_URL:-}"
  if [[ -z "$chat_url" ]]; then
    echo "H1: skipped (set VECINITA_STAGING_CHAT_URL)"
    return 0
  fi

  RAN=$((RAN + 1))
  echo "H1: ChatRAG liveness"
  curl -fsS "${chat_url%/}/health" | tee /tmp/vecinita-health.json
  python3 -c "import json; d=json.load(open('/tmp/vecinita-health.json')); assert d.get('status')=='ok', d"

  local write_url="${VECINITA_STAGING_WRITE_URL:-}"
  if [[ -n "$write_url" ]]; then
    echo "H1: Internal write API liveness"
    curl -fsS "${write_url%/}/health"
  fi
}

run_h2() {
  local db_url="${VECINITA_STAGING_DATABASE_URL:-${DATABASE_URL:-}}"
  if [[ -z "$db_url" ]]; then
    echo "H2: skipped (set VECINITA_STAGING_DATABASE_URL or DATABASE_URL)"
    return 0
  fi

  RAN=$((RAN + 1))
  echo "H2: Database ready"
  export DATABASE_URL="$db_url"
  uv run python tests/smoke/staging_h2.py
}

run_h3() {
  local chat_url="${VECINITA_STAGING_CHAT_URL:-}"
  if [[ -z "$chat_url" ]]; then
    echo "H3: skipped (set VECINITA_STAGING_CHAT_URL)"
    return 0
  fi

  RAN=$((RAN + 1))
  echo "H3: Sample ask (+ AC-C6 latency sample)"
  start_ms="$(date +%s%3N)"
  curl -fsS -X POST "${chat_url%/}/api/v1/ask" \
    -H 'Content-Type: application/json' \
    -d '{"question":"What are the food pantry hours?"}' \
    | tee /tmp/vecinita-ask.json
  end_ms="$(date +%s%3N)"
  elapsed_ms=$((end_ms - start_ms))
  python3 -c "
import json
p=json.load(open('/tmp/vecinita-ask.json'))
assert p.get('answer'), 'missing answer'
assert p.get('language') in ('en','es'), p
print('OK: ask returned answer in', p['language'])
"
  echo "H3: sample ask latency ${elapsed_ms}ms (informative; p95 gate: uv run pytest tests/smoke/test_staging_latency.py -m live)"
}

run_h3b_browse() {
  local chat_url="${VECINITA_STAGING_CHAT_URL:-}"
  if [[ -z "$chat_url" ]]; then
    echo "H3b: skipped (set VECINITA_STAGING_CHAT_URL)"
    return 0
  fi

  RAN=$((RAN + 1))
  echo "H3b: EV-001 browse GET smoke (/api/v1/documents, /api/v1/tags)"
  curl -fsS "${chat_url%/}/api/v1/documents?page=1&page_size=5" | tee /tmp/vecinita-browse-docs.json
  python3 -c "
import json
p=json.load(open('/tmp/vecinita-browse-docs.json'))
assert 'items' in p and 'total' in p, p
print('OK: browse documents returned', len(p['items']), 'items (total', p['total'], ')')
"
  curl -fsS "${chat_url%/}/api/v1/tags" | tee /tmp/vecinita-browse-tags.json
  python3 -c "
import json
p=json.load(open('/tmp/vecinita-browse-tags.json'))
assert 'tags' in p, p
print('OK: browse tags returned', len(p['tags']), 'facets')
"
}

run_h1
run_h2
run_h3
run_h3b_browse

if [[ "$RAN" -eq 0 ]]; then
  echo "No staging checks ran; set VECINITA_STAGING_CHAT_URL and/or DATABASE_URL."
  exit 0
fi

echo "Staging smoke passed ($RAN tier(s))."
