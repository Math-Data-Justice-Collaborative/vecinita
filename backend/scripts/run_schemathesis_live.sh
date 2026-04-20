#!/usr/bin/env bash
# Live Schemathesis CLI against gateway, data-management, and optional agent APIs.
#
# Environment:
#   GATEWAY_SCHEMA_URL   — e.g. https://vecinita-gateway-lx27.onrender.com/api/v1/openapi.json
#   DATA_MANAGEMENT_SCHEMA_URL — e.g. https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json
#   AGENT_SCHEMA_URL — optional; e.g. https://vecinita-agent-lx27.onrender.com/openapi.json (third Schemathesis pass)
#   GATEWAY_LIVE_BEARER  — optional Bearer token when ENABLE_AUTH=true on gateway
#   SCHEMATHESIS_CHECKS  — default: not_a_server_error
#   SCHEMATHESIS_REPORT_DIR — default: schemathesis-report (under cwd, usually backend/)
#   SCHEMATHESIS_REPORT_FORMATS — comma list for --report (default: junit). Include `allure` for HTML via Allure CLI.
#   WAIT_FOR_SCHEMA_SECONDS — default: 90 (Render cold starts may need 60–120s)
#   SCHEMATHESIS_REQUEST_RETRIES — default: 2 (transient network while schema HTTP wakes up)
#   SCHEMATHESIS_MAX_EXAMPLES — maps to --max-examples (default: 12)
#   SCHEMATHESIS_AGENT_MAX_EXAMPLES — overrides --max-examples for AGENT_SCHEMA_URL only (default: 6)
#   SCHEMATHESIS_REQUEST_TIMEOUT — per-request HTTP timeout in seconds (default: 180)
#   SCHEMATHESIS_SOURCE_URL — optional; default source_url for GET /api/v1/documents/preview and
#       /download-url (hooks default: https://example.org/community-resource-guide). Set to a URL
#       that exists in the target Postgres to avoid 404 warnings on live runs.
#   SCHEMATHESIS_DOCUMENTS_PREVIEW_SOURCE_URL — optional; overrides SCHEMATHESIS_SOURCE_URL for
#       GET /api/v1/documents/preview only (use when preview and download need different seeds).
#   SCHEMATHESIS_DOCUMENTS_DOWNLOAD_SOURCE_URL — optional; overrides SCHEMATHESIS_SOURCE_URL for
#       GET /api/v1/documents/download-url only.
#   SCHEMATHESIS_SCRAPE_JOB_ID — optional; UUID for GET /api/v1/scrape/{job_id} and POST …/cancel
#       (hooks default: example UUID). Set to a real job id from POST /api/v1/scrape when testing.
#   SCHEMATHESIS_MODAL_SCRAPER_JOB_ID — optional; UUID for GET/POST …/modal-jobs/scraper/{job_id} and …/cancel
#       (defaults to SCHEMATHESIS_SCRAPE_JOB_ID when unset). Use a real Modal-native scraping_jobs id on live DB.
#   SCHEMATHESIS_MODAL_GATEWAY_JOB_ID — optional; path param for GET/DELETE …/modal-jobs/registry/{id}
#       (hooks default: same example UUID). Set to a real gateway_job_id to reduce 404 warnings.
#   MODAL_SCRAPER_PERSIST_VIA_GATEWAY — when set to 1 on the **gateway**, scraping job rows are written on Render
#       and Modal ``modal_scrape_job_submit`` only enqueues (see docs/deployment/RENDER_SHARED_ENV_CONTRACT.md).
#   SCHEMATHESIS_SCRAPE_URL — optional; first URL in POST /api/v1/scrape body (default: https://example.com/page).
#   SCHEMATHESIS_INCLUDE_GATEWAY_REINDEX — set to 1 to include POST /api/v1/scrape/reindex in the gateway
#       run (default: excluded). Live fuzzing hits the gateway, which then calls REINDEX_SERVICE_URL on the
#       server; a bad or internal-only host yields 502 and fails not_a_server_error checks.
#   SCHEMATHESIS_EXCLUDE_ASK_STREAM — set to 1 to exclude GET /api/v1/ask/stream (and legacy paths) from the
#       gateway run (default: 0, stream is included; uses hooks for a short `question` and may need higher
#       SCHEMATHESIS_REQUEST_TIMEOUT for slow agents).
#   SCHEMATHESIS_STREAM_QUESTION — passed via hooks as `question` for GET /api/v1/ask/stream (default in hooks).
#   SCHEMATHESIS_ASK_QUESTION — passed via hooks as `question` for GET /api/v1/ask (default in hooks).
#   SCHEMATHESIS_BOOTSTRAP_IDS — default 1: before the gateway run, probe the live gateway to set
#       SCHEMATHESIS_MODAL_GATEWAY_JOB_ID (first entry from GET /modal-jobs/registry) and/or
#       SCHEMATHESIS_SCRAPE_JOB_ID (POST /api/v1/scrape) when those env vars are unset, reducing 404 / mismatch noise.
#       Set to 0 to skip (e.g. read-only environments).
#   SCHEMATHESIS_GATEWAY_MAX_EXAMPLES — overrides --max-examples for the gateway run only (default: SCHEMATHESIS_MAX_EXAMPLES).
#   SCHEMATHESIS_GATEWAY_INCLUDE_PATH_REGEX — optional; when set, passed as ``--include-path-regex`` on the gateway pass only
#       (e.g. ``/api/v1/ask$`` for **T034** ask-only runs without editing the script).
#   SCHEMATHESIS_GATEWAY_STATEFUL — set to 1 to append ``--phases examples,coverage,fuzzing,stateful`` on the
#       gateway pass (redundant when ``backend/schemathesis.toml`` already enables the stateful phase globally;
#       use for forcing an explicit phase list). Stateful job-queue tuning (scrape + modal-jobs, negative_data
#       relaxation) lives in ``schemathesis.toml`` [[operations]] blocks; pytest-only flows stay in
#       ``tests/integration/test_gateway_*_stateful.py`` (see TESTING_DOCUMENTATION.md).
#   SCHEMATHESIS_THOROUGH — set to 1 to append --generation-maximize response_time (optional; longer runs).
#   SCHEMATHESIS_SUPPRESS_HEALTH_CHECK — comma list for --suppress-health-check (default: filter_too_much,too_slow).
#       Modal-jobs path params can trip Schemathesis generation health checks without affecting runtime API quality.
#
# Data-management OpenAPI (pytest hooks share these with the CLI DM pass when applicable):
#   SCHEMATHESIS_DM_SUBMIT_URL — seed URL for POST /jobs body (default: https://example.org/community-resources).
#   SCHEMATHESIS_DM_USER_ID — user_id in POST /jobs (default: schemathesis).
#   SCHEMATHESIS_DM_JOB_ID — UUID for GET /jobs/{id} and POST …/cancel (default: OpenAPI example UUID).
#
# TraceCov / schema coverage (https://schemathesis.readthedocs.io/en/stable/guides/coverage/):
#   SCHEMATHESIS_COVERAGE — set to 0/false/no to skip tracecov.schemathesis.install() in hooks (no schema coverage map).
#   SCHEMATHESIS_COVERAGE_FORMAT — default for this script: html,text (HTML file + terminal summary). Comma-separated:
#       html, text, markdown (see TraceCov CLI / schemathesis --help Coverage options).
#   SCHEMATHESIS_COVERAGE_REPORT_HTML_PATH — if unset, each pass writes
#       SCHEMATHESIS_REPORT_DIR/schema-coverage-<slug>.html (slug from junit name, e.g. gateway, data-management, agent)
#       so multi-pass runs do not overwrite each other. Set explicitly to force one path (last pass wins).
#   SCHEMATHESIS_COVERAGE_REPORT_MARKDOWN_PATH — optional Markdown report path (same per-slug default if FORMAT includes markdown).
#   SCHEMATHESIS_COVERAGE_MARKDOWN_REPORT_URL — URL linked from the Markdown footer (defaults to file://… HTML when markdown is emitted).
#   SCHEMATHESIS_COVERAGE_NO_REPORT — set to 1/true to collect coverage but skip writing report files (TraceCov option).
#   SCHEMATHESIS_COVERAGE_FAIL_UNDER — TraceCov minimum % per dimension for ``schemathesis run`` (hooks enforce exit 1 if below).
#       When coverage is enabled and this var is unset, this script defaults it to 100. Set to 0 to disable the gate only.
#   SCHEMATHESIS_HOOKS_VERBOSE — set to 1/true to log schema load (before_load_schema / after_load_schema) and failed checks
#       (after_validate); see https://schemathesis.readthedocs.io/en/stable/reference/hooks/
#
# Reports:
#   - JUnit: SCHEMATHESIS_REPORT_DIR/junit-*.xml
#   - Allure raw results: SCHEMATHESIS_REPORT_DIR/allure-results (when SCHEMATHESIS_REPORT_FORMATS includes allure);
#     open in a browser with: allure serve SCHEMATHESIS_REPORT_DIR/allure-results
#   - Schema coverage: SCHEMATHESIS_REPORT_DIR/schema-coverage-*.html (and optional .md); cwd fallback copied if present.
#
# Gateway deploy (Render) — reindex:
#   For POST /api/v1/scrape/reindex to succeed when included, configure the gateway's REINDEX_SERVICE_URL
#   to a publicly resolvable base URL (e.g. Modal scraper web URL) and REINDEX_TRIGGER_TOKEN to match
#   the scraper service. A 502 with "Name or service not known" means DNS cannot resolve the host
#   from the gateway container (fix in Render env / secrets).
set -euo pipefail

WAIT_FOR_SCHEMA_SECONDS="${WAIT_FOR_SCHEMA_SECONDS:-90}"
REPORT_DIR="${SCHEMATHESIS_REPORT_DIR:-schemathesis-report}"
CHECKS="${SCHEMATHESIS_CHECKS:-not_a_server_error}"
SUPPRESS_HC="${SCHEMATHESIS_SUPPRESS_HEALTH_CHECK:-filter_too_much,too_slow}"
MAX_EX="${SCHEMATHESIS_MAX_EXAMPLES:-12}"
GATEWAY_MAX_EX="${SCHEMATHESIS_GATEWAY_MAX_EXAMPLES:-$MAX_EX}"
AGENT_MAX_EX="${SCHEMATHESIS_AGENT_MAX_EXAMPLES:-6}"
REQ_TIMEOUT="${SCHEMATHESIS_REQUEST_TIMEOUT:-180}"
REQUEST_RETRIES="${SCHEMATHESIS_REQUEST_RETRIES:-2}"
REPORT_FORMATS="${SCHEMATHESIS_REPORT_FORMATS:-junit}"

# Use ${VAR-default} (not :-) so an explicitly empty value skips that run (cold-start / agent-only jobs).
GATEWAY_URL="${GATEWAY_SCHEMA_URL-https://vecinita-gateway-lx27.onrender.com/api/v1/openapi.json}"
DATA_MANAGEMENT_URL="${DATA_MANAGEMENT_SCHEMA_URL-https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json}"
AGENT_URL="${AGENT_SCHEMA_URL-}"

mkdir -p "$REPORT_DIR"

export SCHEMATHESIS_HOOKS="${SCHEMATHESIS_HOOKS:-tests.schemathesis_hooks}"

HEADER_ARGS=()
if [[ -n "${GATEWAY_LIVE_BEARER:-}" ]]; then
  HEADER_ARGS+=( -H "Authorization: Bearer ${GATEWAY_LIVE_BEARER}" )
fi

_gateway_base_from_schema_url() {
  local u="$1"
  echo "$u" | sed -E 's#/api/v1/.*$##'
}

_schemathesis_bootstrap_gateway_ids() {
  [[ "${SCHEMATHESIS_BOOTSTRAP_IDS:-1}" == "1" ]] || return 0
  [[ -n "${GATEWAY_URL:-}" ]] || return 0
  local base
  base="$(_gateway_base_from_schema_url "${GATEWAY_URL}")"
  [[ -n "$base" ]] || return 0
  local PYBIN
  PYBIN="$(command -v python3 || command -v python || true)"
  [[ -n "${PYBIN}" ]] || return 0

  if [[ -z "${SCHEMATHESIS_MODAL_GATEWAY_JOB_ID:-}" ]]; then
    local gid=""
    gid="$(curl -sS -m 45 "${base}/api/v1/modal-jobs/registry?limit=1" \
      ${HEADER_ARGS[@]+"${HEADER_ARGS[@]}"} \
      -H "Accept: application/json" 2>/dev/null | "${PYBIN}" -c "import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit(0)
jobs=d.get(\"jobs\") or []
if jobs and isinstance(jobs[0], dict):
    print(jobs[0].get(\"gateway_job_id\") or \"\", end=\"\")" )" || true
    if [[ -n "${gid}" ]]; then
      export SCHEMATHESIS_MODAL_GATEWAY_JOB_ID="${gid}"
      echo "Schemathesis bootstrap: SCHEMATHESIS_MODAL_GATEWAY_JOB_ID from GET /modal-jobs/registry"
    fi
  fi

  if [[ -z "${SCHEMATHESIS_SCRAPE_JOB_ID:-}" ]]; then
    local surl="${SCHEMATHESIS_SCRAPE_URL:-https://example.com/one}"
    export _SCHEMATHESIS_BOOTSTRAP_URL="${surl}"
    local body=""
    body="$("${PYBIN}" -c "import json,os; u=os.environ['_SCHEMATHESIS_BOOTSTRAP_URL']; print(json.dumps({'urls':[u],'force_loader':'auto','stream':False}))")" || true
    unset _SCHEMATHESIS_BOOTSTRAP_URL || true
    local jid=""
    jid="$(curl -sS -m 120 -X POST "${base}/api/v1/scrape" \
      -H "Content-Type: application/json" \
      ${HEADER_ARGS[@]+"${HEADER_ARGS[@]}"} \
      -d "${body}" 2>/dev/null | "${PYBIN}" -c "import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(d.get(\"job_id\") or \"\", end=\"\")" )" || true
    if [[ -n "${jid}" ]]; then
      export SCHEMATHESIS_SCRAPE_JOB_ID="${jid}"
      echo "Schemathesis bootstrap: SCHEMATHESIS_SCRAPE_JOB_ID from POST /api/v1/scrape"
    fi
  fi
}

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

  # TraceCov: per-pass report paths + terminal text summary (guide: html + dimensions in log).
  local slug="${junit_name%.xml}"
  slug="${slug#junit-}"
  local cov_on=1
  case "${SCHEMATHESIS_COVERAGE:-on}" in 0|false|no|False|NO) cov_on=0 ;; esac
  local no_rep=0
  case "${SCHEMATHESIS_COVERAGE_NO_REPORT:-}" in 1|true|yes|on|TRUE|YES|ON) no_rep=1 ;; esac
  local had_html=0 had_fmt=0 had_md=0 had_md_url=0
  [[ -n "${SCHEMATHESIS_COVERAGE_REPORT_HTML_PATH+x}" ]] && had_html=1
  [[ -n "${SCHEMATHESIS_COVERAGE_FORMAT+x}" ]] && had_fmt=1
  [[ -n "${SCHEMATHESIS_COVERAGE_REPORT_MARKDOWN_PATH+x}" ]] && had_md=1
  [[ -n "${SCHEMATHESIS_COVERAGE_MARKDOWN_REPORT_URL+x}" ]] && had_md_url=1
  local we_set_fmt=0 we_set_html=0 we_set_md=0 we_set_md_url=0 we_set_cov_fail_under=0
  if [[ "${cov_on}" -eq 1 ]] && [[ "${no_rep}" -eq 0 ]]; then
    if [[ -z "${SCHEMATHESIS_COVERAGE_FAIL_UNDER+x}" ]]; then
      export SCHEMATHESIS_COVERAGE_FAIL_UNDER="100"
      we_set_cov_fail_under=1
    fi
    if [[ "${had_fmt}" -eq 0 ]]; then
      export SCHEMATHESIS_COVERAGE_FORMAT="${SCHEMATHESIS_COVERAGE_FORMAT_DEFAULT:-html,text}"
      we_set_fmt=1
    fi
    if [[ "${had_html}" -eq 0 ]]; then
      export SCHEMATHESIS_COVERAGE_REPORT_HTML_PATH="${REPORT_DIR}/schema-coverage-${slug}.html"
      we_set_html=1
    fi
    local eff_fmt="${SCHEMATHESIS_COVERAGE_FORMAT:-}"
    if [[ "${eff_fmt}" == *markdown* ]]; then
      if [[ "${had_md}" -eq 0 ]]; then
        export SCHEMATHESIS_COVERAGE_REPORT_MARKDOWN_PATH="${REPORT_DIR}/schema-coverage-${slug}.md"
        we_set_md=1
      fi
      if [[ "${had_md_url}" -eq 0 ]]; then
        local html_ref="${SCHEMATHESIS_COVERAGE_REPORT_HTML_PATH:-${REPORT_DIR}/schema-coverage-${slug}.html}"
        export SCHEMATHESIS_COVERAGE_MARKDOWN_REPORT_URL="file://${html_ref}"
        we_set_md_url=1
      fi
    fi
  fi

  echo "Schemathesis run → ${location}"
  local auth_args=()
  if [[ "${use_gateway_auth}" == "1" ]] && [[ "${#HEADER_ARGS[@]}" -gt 0 ]]; then
    auth_args=( "${HEADER_ARGS[@]}" )
  fi
  local suppress_args=()
  if [[ -n "${SUPPRESS_HC}" ]]; then
    suppress_args=( --suppress-health-check "${SUPPRESS_HC}" )
  fi

  local report_args=(
    --report "${REPORT_FORMATS}"
    --report-dir "${REPORT_DIR}"
    --report-junit-path "${REPORT_DIR}/${junit_name}"
  )
  if [[ "${REPORT_FORMATS}" == *"allure"* ]]; then
    report_args+=( --report-allure-path "${REPORT_DIR}/allure-results" )
  fi

  local retry_args=()
  if [[ -n "${REQUEST_RETRIES}" ]] && [[ "${REQUEST_RETRIES}" != "0" ]]; then
    retry_args=( --request-retries "${REQUEST_RETRIES}" )
  fi

  uv run schemathesis run "${location}" \
    --request-timeout "${timeout_sec}" \
    "${retry_args[@]+"${retry_args[@]}"}" \
    --wait-for-schema "${WAIT_FOR_SCHEMA_SECONDS}" \
    "${suppress_args[@]+"${suppress_args[@]}"}" \
    "${report_args[@]}" \
    --checks "${CHECKS}" \
    --max-examples "${max_ex}" \
    --continue-on-failure \
    "${@}" \
    ${auth_args[@]+"${auth_args[@]}"}

  if [[ "${we_set_fmt}" -eq 1 ]]; then
    unset SCHEMATHESIS_COVERAGE_FORMAT || true
  fi
  if [[ "${we_set_html}" -eq 1 ]]; then
    unset SCHEMATHESIS_COVERAGE_REPORT_HTML_PATH || true
  fi
  if [[ "${we_set_md}" -eq 1 ]]; then
    unset SCHEMATHESIS_COVERAGE_REPORT_MARKDOWN_PATH || true
  fi
  if [[ "${we_set_md_url}" -eq 1 ]]; then
    unset SCHEMATHESIS_COVERAGE_MARKDOWN_REPORT_URL || true
  fi
  if [[ "${we_set_cov_fail_under}" -eq 1 ]]; then
    unset SCHEMATHESIS_COVERAGE_FAIL_UNDER || true
  fi
}

run_core_openapi() {
  local location="$1"
  local junit_name="$2"
  local use_auth="${3:-0}"
  shift 3 || true
  local extra=("$@")
  local reindex_exclude=()
  if [[ "${SCHEMATHESIS_INCLUDE_GATEWAY_REINDEX:-0}" != "1" ]]; then
    reindex_exclude=( --exclude-path '/api/v1/scrape/reindex' )
  fi
  local stream_exclude=()
  if [[ "${SCHEMATHESIS_EXCLUDE_ASK_STREAM:-0}" == "1" ]]; then
    stream_exclude=(
      --exclude-path-regex '/ask/stream$'
      --exclude-path '/ask/stream'
      --exclude-path '/ask-stream'
    )
  fi
  local thorough_args=()
  if [[ "${SCHEMATHESIS_THOROUGH:-0}" == "1" ]]; then
    thorough_args=( --generation-maximize response_time )
  fi
  local stateful_args=()
  if [[ "${SCHEMATHESIS_GATEWAY_STATEFUL:-0}" == "1" ]]; then
    stateful_args=( --phases examples,coverage,fuzzing,stateful )
  fi
  local gateway_scope_args=()
  if [[ -n "${SCHEMATHESIS_GATEWAY_INCLUDE_PATH_REGEX:-}" ]]; then
    gateway_scope_args=( --include-path-regex "${SCHEMATHESIS_GATEWAY_INCLUDE_PATH_REGEX}" )
  fi
  run_st "${location}" "${junit_name}" "${use_auth}" "${REQ_TIMEOUT}" "${GATEWAY_MAX_EX}" \
    "${stream_exclude[@]+"${stream_exclude[@]}"}" \
    "${reindex_exclude[@]+"${reindex_exclude[@]}"}" \
    "${stateful_args[@]+"${stateful_args[@]}"}" \
    "${thorough_args[@]+"${thorough_args[@]}"}" \
    "${gateway_scope_args[@]+"${gateway_scope_args[@]}"}" \
    "${extra[@]+"${extra[@]}"}"
}

if [[ -z "${GATEWAY_URL}" && -z "${DATA_MANAGEMENT_URL}" && -z "${AGENT_URL}" ]]; then
  echo "Set GATEWAY_SCHEMA_URL, DATA_MANAGEMENT_SCHEMA_URL, and/or AGENT_SCHEMA_URL." >&2
  exit 1
fi

if [[ -n "${GATEWAY_URL}" ]]; then
  _schemathesis_bootstrap_gateway_ids || true
  run_core_openapi "${GATEWAY_URL}" "junit-gateway.xml" 1
fi

if [[ -n "${DATA_MANAGEMENT_URL}" ]]; then
  DM_TOKEN="$(_scraper_bearer_token)"
  DM_HEADERS=()
  if [[ -n "${DM_TOKEN}" ]]; then
    DM_HEADERS=( -H "Authorization: Bearer ${DM_TOKEN}" )
  fi
  run_st "${DATA_MANAGEMENT_URL}" "junit-data-management.xml" 0 "${REQ_TIMEOUT}" "${MAX_EX}" ${DM_HEADERS[@]+"${DM_HEADERS[@]}"}
fi

if [[ -n "${AGENT_URL}" ]]; then
  # Match backend/tests/live/test_live_schemathesis.py: positive generation only; skip expensive chat routes.
  run_st "${AGENT_URL}" "junit-agent-live.xml" 0 "${REQ_TIMEOUT}" "${AGENT_MAX_EX}" \
    --mode positive \
    --exclude-path '/ask' \
    --exclude-path '/ask/stream' \
    --exclude-path '/ask-stream'
fi

if [[ -f schema-coverage.html ]]; then
  cp -f schema-coverage.html "${REPORT_DIR}/schema-coverage-cwd-fallback.html" || true
fi

echo "Reports under: ${REPORT_DIR}"
if [[ "${REPORT_FORMATS}" == *"allure"* ]]; then
  echo "Allure (browser): allure serve ${REPORT_DIR}/allure-results"
fi
shopt -s nullglob
for f in "${REPORT_DIR}"/schema-coverage-*.html; do
  [[ -f "$f" ]] || continue
  echo "Schema coverage (browser): file://${f}"
done
shopt -u nullglob
