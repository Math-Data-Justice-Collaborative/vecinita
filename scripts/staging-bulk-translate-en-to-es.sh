#!/usr/bin/env bash
# EV-031 staging bulk translate: queue F75 ingest jobs for EN-only published docs.
# [Corpus: staging] [Corpus: product §F76] [Issue #245]

set -euo pipefail

LIMIT=10
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="${2:?}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

DM_URL="${VECINITA_STAGING_ADMIN_API_URL:-${VECINITA_MODAL_DATA_MGMT_URL:-https://vecinita--vecinita-data-management-fastapi-app.modal.run}}"
WRITE_URL="${VECINITA_STAGING_WRITE_URL:-}"
ADMIN_FE_ORIGIN="${VECINITA_STAGING_ADMIN_FRONTEND_URL:-https://vecinita-admin-frontend-ef4ob.ondigitalocean.app}"
SUPABASE_URL="${SUPABASE_URL:-https://cfuvghdsuwactfeamtym.supabase.co}"
PROXY_HEADER="X-Vecinita-Proxy-Key"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT_DIR="${VECINITA_BULK_TRANSLATE_REPORT_DIR:-${SCRIPT_DIR}/../docs/sessions/EV-031-corpus-language-parity/reports}"
mkdir -p "$REPORT_DIR"

[[ -n "${VECINITA_MODAL_PROXY_KEY:-}" ]] || { echo "ERROR: VECINITA_MODAL_PROXY_KEY not set." >&2; exit 1; }
[[ -n "$WRITE_URL" && -n "${VECINITA_INTERNAL_API_KEY:-}" ]] || {
  echo "ERROR: VECINITA_STAGING_WRITE_URL + VECINITA_INTERNAL_API_KEY required." >&2
  exit 1
}

if [[ "${DATABASE_URL:-}" == *ondigitalocean.com* && "${VECINITA_BULK_TRANSLATE_ACK:-}" != "staging-only" ]]; then
  echo "ERROR: Refusing without VECINITA_BULK_TRANSLATE_ACK=staging-only on DO host." >&2
  exit 1
fi

resolve_operator_token() {
  if [[ -n "${VECINITA_OPERATOR_ACCESS_TOKEN:-}" ]]; then return 0; fi
  local resp
  resp=$(curl -sS -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
    -H "apikey: ${SUPABASE_PUBLISHABLE_KEY:?}" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg e "$SUPABASE_ADMIN_EMAIL" --arg p "$SUPABASE_ADMIN_PASSWORD" '{email:$e,password:$p}')")
  VECINITA_OPERATOR_ACCESS_TOKEN=$(echo "$resp" | jq -r '.access_token // empty')
  [[ -n "$VECINITA_OPERATOR_ACCESS_TOKEN" ]] || { echo "Login failed" >&2; exit 1; }
}

dm_curl() {
  curl -sf "$@" \
    -H "${PROXY_HEADER}: $VECINITA_MODAL_PROXY_KEY" \
    -H "Authorization: Bearer $VECINITA_OPERATOR_ACCESS_TOKEN" \
    -H "Origin: $ADMIN_FE_ORIGIN"
}

resolve_operator_token

INVENTORY="${REPORT_DIR}/en-only-inventory.json"
TMP="${REPORT_DIR}/.en-only-pages.jsonl"
: > "$TMP"
PAGE=1
while true; do
  BATCH=$(curl -sf "${WRITE_URL}/internal/v1/documents?page=${PAGE}&page_size=100" \
    -H "Authorization: Bearer ${VECINITA_INTERNAL_API_KEY}")
  echo "$BATCH" | jq -c '[.items[] | select(.language == "en" and .publish_status == "published" and (.paired_document_id == null))][]' >> "$TMP"
  TOTAL=$(echo "$BATCH" | jq .total)
  if (( PAGE * 100 >= TOTAL )); then break; fi
  PAGE=$((PAGE + 1))
done

jq -s --argjson limit "$LIMIT" 'if length > $limit then .[:$limit] else . end' "$TMP" > "$INVENTORY"
SELECTED=$(jq 'length' "$INVENTORY")
echo "Selected ${SELECTED} EN-only URLs (limit=${LIMIT})"

if [[ "$DRY_RUN" -eq 1 ]]; then
  jq . "$INVENTORY"
  exit 0
fi

JOB_IDS=()
while IFS= read -r url; do
  [[ -z "$url" ]] && continue
  echo "==> translate_locales=[es] ${url}"
  JOB=$(dm_curl -X POST "${DM_URL}/jobs" -H "Content-Type: application/json" \
    -d "{\"urls\":[\"${url}\"],\"options\":{\"force\":true,\"translate_locales\":[\"es\"]}}")
  JOB_IDS+=("$(echo "$JOB" | jq -r .job_id)")
done < <(jq -r '.[].url' "$INVENTORY")

printf '%s\n' "${JOB_IDS[@]}" | jq -R . | jq -s --arg inv "$INVENTORY" '{inventory:$inv, job_ids:.}' > "${REPORT_DIR}/bulk-translate-jobs.json"
echo "Wrote ${REPORT_DIR}/bulk-translate-jobs.json — promote drafts before ChatRAG check."
