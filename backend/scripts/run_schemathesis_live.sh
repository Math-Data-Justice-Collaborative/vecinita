#!/usr/bin/env bash
# Live Schemathesis CLI against agent, gateway, and optional Modal microservices.
#
# Environment (agent / gateway):
#   AGENT_SCHEMA_URL     — e.g. https://vecinita-agent-lx27.onrender.com/openapi.json
#   GATEWAY_SCHEMA_URL   — e.g. https://vecinita-gateway-lx27.onrender.com/api/v1/docs/openapi.json
#   SCHEMA_URL           — backward compatible default when only one URL is used
#   GATEWAY_LIVE_BEARER  — optional Bearer token when ENABLE_AUTH=true on gateway
#   SCHEMATHESIS_CHECKS  — default: not_a_server_error
#   SCHEMATHESIS_REPORT_DIR — default: schemathesis-report (under cwd, usually backend/)
#   WAIT_FOR_SCHEMA_SECONDS — default: 30
#   SCHEMATHESIS_MAX_EXAMPLES — maps to --max-examples (default: 12)
#   SCHEMATHESIS_REQUEST_TIMEOUT — per-request HTTP timeout in seconds (default: 180)
#   SCHEMATHESIS_EXCLUDE_IGNORED_AUTH — set to 0 to keep Schemathesis "ignored_auth" checks
#       on the agent OpenAPI run (default: 1 — POST /model-selection returns 403 when locked,
#       which is policy, not missing Bearer credentials)
#   SCHEMATHESIS_EXCLUDE_AGENT_MODEL_SELECTION — set to 1 to skip POST /model-selection on the
#       agent run only (avoids auth-policy warnings when LOCK_MODEL_SELECTION locks the endpoint).
#       Uses OpenAPI operationId set_model_selection_model_selection_post (FastAPI default).
#   SCHEMATHESIS_SOURCE_URL — optional; known source_url for GET /api/v1/documents/preview and
#       /download-url (hooks default: https://example.org/community-resource-guide). Set to a URL
#       that exists in the target Postgres to avoid 404 warnings on live runs.
#   SCHEMATHESIS_SCRAPE_JOB_ID — optional; UUID for GET /api/v1/scrape/{job_id} and POST …/cancel
#       (hooks default: example UUID). Set to a real job id from POST /api/v1/scrape when testing.
#   SCHEMATHESIS_SCRAPE_URL — optional; first URL in POST /api/v1/scrape body (default: https://example.com/page).
#
# Modal microservices (on by default; set SCHEMATHESIS_MODAL_MICROSERVICES=0 to skip):
#   SCHEMATHESIS_MODAL_MICROSERVICES — default 1: run Schemathesis against Modal embedding, scraper, and model OpenAPI
#   MODAL_EMBEDDING_SCHEMA_URL — default: https://vecinita--vecinita-embedding-web-app.modal.run/openapi.json
#   MODAL_SCRAPER_SCHEMA_URL   — default: https://vecinita--vecinita-scraper-api-fastapi.modal.run/openapi.json
#   MODAL_MODEL_SCHEMA_URL     — default: https://vecinita--vecinita-model-api.modal.run/openapi.json
#   EMBEDDING_SERVICE_AUTH_TOKEN / MODAL_TOKEN_SECRET / MODAL_API_TOKEN_SECRET — sent to embedding Modal as Bearer + x-embedding-service-token
#   SCRAPER_SCHEMATHESIS_BEARER — optional explicit Bearer for scraper (else first comma-separated value from SCRAPER_API_KEYS is used)
#   SCRAPER_SCHEMATHESIS_ALLOW_MUTATIONS — set to 1 to allow POST on scraper (default: GET-only for production safety)
#   SCHEMATHESIS_MODAL_MODEL_MAX_EXAMPLES — default: 6 (LLM cost)
#   SCHEMATHESIS_MODAL_MODEL_REQUEST_TIMEOUT — default: 300 seconds
#
# Gateway deploy (Render) — reindex:
#   For POST /api/v1/scrape/reindex to succeed against a live gateway, set REINDEX_SERVICE_URL
#   to a publicly resolvable base URL (e.g. Modal scraper web URL) and REINDEX_TRIGGER_TOKEN
#   to match the scraper service. A 502 with "Name or service not known" means DNS cannot
#   resolve the configured host (fix in the Render dashboard / secrets, not in this script).
set -euo pipefail

WAIT_FOR_SCHEMA_SECONDS="${WAIT_FOR_SCHEMA_SECONDS:-30}"
REPORT_DIR="${SCHEMATHESIS_REPORT_DIR:-schemathesis-report}"
CHECKS="${SCHEMATHESIS_CHECKS:-not_a_server_error}"
MAX_EX="${SCHEMATHESIS_MAX_EXAMPLES:-12}"
REQ_TIMEOUT="${SCHEMATHESIS_REQUEST_TIMEOUT:-180}"
MODEL_REQ_TIMEOUT="${SCHEMATHESIS_MODAL_MODEL_REQUEST_TIMEOUT:-300}"
MODEL_MAX_EX="${SCHEMATHESIS_MODAL_MODEL_MAX_EXAMPLES:-6}"
EXCLUDE_IGNORED_AUTH="${SCHEMATHESIS_EXCLUDE_IGNORED_AUTH:-1}"
EXCLUDE_AGENT_MODEL_SELECTION="${SCHEMATHESIS_EXCLUDE_AGENT_MODEL_SELECTION:-0}"

AGENT_URL="${AGENT_SCHEMA_URL:-}"
GATEWAY_URL="${GATEWAY_SCHEMA_URL:-}"
LEGACY="${SCHEMA_URL:-}"
MODAL_FLAG="${SCHEMATHESIS_MODAL_MICROSERVICES:-1}"

MODAL_EMBEDDING_SCHEMA_URL="${MODAL_EMBEDDING_SCHEMA_URL:-https://vecinita--vecinita-embedding-web-app.modal.run/openapi.json}"
MODAL_SCRAPER_SCHEMA_URL="${MODAL_SCRAPER_SCHEMA_URL:-https://vecinita--vecinita-scraper-api-fastapi.modal.run/openapi.json}"
MODAL_MODEL_SCHEMA_URL="${MODAL_MODEL_SCHEMA_URL:-https://vecinita--vecinita-model-api.modal.run/openapi.json}"

mkdir -p "$REPORT_DIR"

export SCHEMATHESIS_HOOKS="${SCHEMATHESIS_HOOKS:-tests.schemathesis_hooks}"

HEADER_ARGS=()
if [[ -n "${GATEWAY_LIVE_BEARER:-}" ]]; then
  HEADER_ARGS+=( -H "Authorization: Bearer ${GATEWAY_LIVE_BEARER}" )
fi

_scraper_bearer_token() {
  if [[ -n "${SCRAPER_SCHEMATHESIS_BEARER:-}" ]]; then
    echo "${SCRAPER_SCHEMATHESIS_BEARER}"
    return
  fi
  if [[ -z "${SCRAPER_API_KEYS:-}" ]]; then
    echo ""
    return
  fi
  # First key in comma-separated SCRAPER_API_KEYS
  local raw first
  raw="${SCRAPER_API_KEYS%%,*}"
  first="${raw#"${raw%%[![:space:]]*}"}"
  first="${first%"${first##*[![:space:]]}"}"
  echo "${first}"
}

# Args: location, junit_name, use_gateway_bearer(0|1), request_timeout, max_examples, extra schemathesis args...
run_st() {
  local location="$1"
  local junit_name="$2"
  local use_gateway_auth="${3:-0}"
  local timeout_sec="${4:-$REQ_TIMEOUT}"
  local max_ex="${5:-$MAX_EX}"
  shift 5 || true

  echo "Schemathesis run → ${location}"
  local auth_args=()
  if [[ "${use_gateway_auth}" == "1" ]] && [[ "${#HEADER_ARGS[@]}" -gt 0 ]]; then
    auth_args=( "${HEADER_ARGS[@]}" )
  fi

  uv run schemathesis run "${location}" \
    --request-timeout "${timeout_sec}" \
    --wait-for-schema "${WAIT_FOR_SCHEMA_SECONDS}" \
    --report junit \
    --report-dir "${REPORT_DIR}" \
    --report-junit-path "${REPORT_DIR}/${junit_name}" \
    --checks "${CHECKS}" \
    --max-examples "${max_ex}" \
    --continue-on-failure \
    "${@}" \
    ${auth_args[@]+"${auth_args[@]}"}
}

run_agent_or_gateway() {
  local location="$1"
  local junit_name="$2"
  local use_auth="${3:-0}"
  shift 3 || true
  local extra=("$@")
  run_st "${location}" "${junit_name}" "${use_auth}" "${REQ_TIMEOUT}" "${MAX_EX}" \
    --exclude-path-regex '/ask/stream$' \
    --exclude-path '/ask/stream' \
    --exclude-path '/ask-stream' \
    "${extra[@]+"${extra[@]}"}"
}

any_core_schema_set() {
  [[ -n "${AGENT_URL}" || -n "${GATEWAY_URL}" || -n "${LEGACY}" ]]
}

if ! any_core_schema_set && [[ "${MODAL_FLAG}" != "1" ]]; then
  echo "Set AGENT_SCHEMA_URL and/or GATEWAY_SCHEMA_URL (or SCHEMA_URL), or set SCHEMATHESIS_MODAL_MICROSERVICES=1 (default) for Modal-only OpenAPI runs." >&2
  exit 1
fi

if [[ -n "${AGENT_URL}" ]]; then
  agent_extra=()
  if [[ "${EXCLUDE_IGNORED_AUTH}" == "1" ]]; then
    agent_extra+=( --exclude-checks ignored_auth )
  fi
  if [[ "${EXCLUDE_AGENT_MODEL_SELECTION}" == "1" ]]; then
    agent_extra+=( --exclude-operation-id set_model_selection_model_selection_post )
  fi
  run_agent_or_gateway "${AGENT_URL}" "junit-agent.xml" 0 "${agent_extra[@]+"${agent_extra[@]}"}"
fi

if [[ -n "${GATEWAY_URL}" ]]; then
  run_agent_or_gateway "${GATEWAY_URL}" "junit-gateway.xml" 1
fi

if [[ -z "${AGENT_URL}" && -z "${GATEWAY_URL}" && -n "${LEGACY}" ]]; then
  legacy_auth=0
  if [[ -n "${GATEWAY_LIVE_BEARER:-}" ]]; then
    legacy_auth=1
  fi
  echo "Using legacy SCHEMA_URL (Bearer header only when GATEWAY_LIVE_BEARER is set)."
  run_agent_or_gateway "${LEGACY}" "junit.xml" "${legacy_auth}"
fi

if [[ "${MODAL_FLAG}" == "1" ]]; then
  echo "Modal microservices Schemathesis (embedding, scraper, model OpenAPI)"

  # --- Embedding Modal ---
  emb_hdrs=()
  _tok="${EMBEDDING_SERVICE_AUTH_TOKEN:-}"
  [[ -z "$_tok" ]] && _tok="${MODAL_TOKEN_SECRET:-}"
  [[ -z "$_tok" ]] && _tok="${MODAL_API_TOKEN_SECRET:-}"
  if [[ -n "$_tok" ]]; then
    emb_hdrs+=( -H "x-embedding-service-token: ${_tok}" -H "Authorization: Bearer ${_tok}" )
  fi
  run_st "${MODAL_EMBEDDING_SCHEMA_URL}" "junit-modal-embedding.xml" 0 "${REQ_TIMEOUT}" "${MAX_EX}" \
    "${emb_hdrs[@]+"${emb_hdrs[@]}"}"

  # --- Scraper Modal (GET-only unless SCRAPER_SCHEMATHESIS_ALLOW_MUTATIONS=1) ---
  scr_extra=()
  if [[ "${SCRAPER_SCHEMATHESIS_ALLOW_MUTATIONS:-0}" != "1" ]]; then
    scr_extra+=( --include-method GET )
  fi
  scr_hdrs=()
  _sb="$(_scraper_bearer_token)"
  if [[ -n "$_sb" ]]; then
    scr_hdrs+=( -H "Authorization: Bearer ${_sb}" )
  fi
  run_st "${MODAL_SCRAPER_SCHEMA_URL}" "junit-modal-scraper.xml" 0 "${REQ_TIMEOUT}" "${MAX_EX}" \
    "${scr_extra[@]+"${scr_extra[@]}"}" \
    "${scr_hdrs[@]+"${scr_hdrs[@]}"}"

  # --- Model Modal (exclude SSE; higher timeout; fewer examples) ---
  run_st "${MODAL_MODEL_SCHEMA_URL}" "junit-modal-model.xml" 0 "${MODEL_REQ_TIMEOUT}" "${MODEL_MAX_EX}" \
    --exclude-path-regex '/stream$' \
    --exclude-path-regex '/api/stream$'
fi

echo "Reports under: ${REPORT_DIR}"
