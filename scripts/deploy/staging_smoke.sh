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
  python3 -c "
import json
body = json.load(open('/tmp/vecinita-health.json'))
assert body.get('status') == 'ok', body
deps = body.get('dependencies') or {}
for key in ('postgres', 'modal_embed', 'modal_llm'):
    assert deps.get(key) == 'ok', f'dependency {key}={deps.get(key)!r} (full={deps})'
"

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

run_t3_ev002() {
  local write_url="${VECINITA_STAGING_WRITE_URL:-}"
  local api_key="${VECINITA_STAGING_INTERNAL_API_KEY:-}"
  if [[ -z "$api_key" && -f "$REPO_ROOT/chat-rag-spec.yaml" ]]; then
    api_key="$(python3 -c "
import re, pathlib
text = pathlib.Path('$REPO_ROOT/chat-rag-spec.yaml').read_text()
m = re.search(r'VECINITA_INTERNAL_API_KEY[\\s\\S]*?value:\\s*\"([^\"]+)\"', text)
print(m.group(1) if m else '', end='')
" 2>/dev/null || true)"
  fi
  if [[ -z "$write_url" || -z "$api_key" ]]; then
    echo "T3 EV-002: skipped (set VECINITA_STAGING_WRITE_URL and VECINITA_STAGING_INTERNAL_API_KEY, or add chat-rag-spec.yaml)"
    return 0
  fi

  RAN=$((RAN + 1))
  echo "T3 EV-002: Admin API smokes (stats, health, audit)"
  export VECINITA_STAGING_WRITE_URL="$write_url"
  export VECINITA_STAGING_INTERNAL_API_KEY="$api_key"
  uv run pytest tests/smoke/test_staging_ev002_admin.py -m live -q
}

run_h1
run_h2
run_h3
run_h3b_browse
run_t3_ev002

if [[ "$RAN" -eq 0 ]]; then
  echo "No staging checks ran; set VECINITA_STAGING_CHAT_URL and/or DATABASE_URL."
  exit 0
fi

echo "Staging smoke passed ($RAN tier(s))."
