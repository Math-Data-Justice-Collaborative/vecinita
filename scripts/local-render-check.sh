#!/usr/bin/env bash
# scripts/local-render-check.sh
#
# Pre-deploy health and smoke checks for the local Render-like environment.
# Validates proxy routing, agent service, embedding, and DB connectivity
# to catch configuration issues before deploying to Render.
#
# Usage:
#   ./scripts/local-render-check.sh [--fail-fast] [--skip-simulation]
#
# Options:
#   --fail-fast         Stop on the first failure instead of running all checks.
#   --skip-simulation   Skip the outage simulation tests.

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
PROXY_URL="${PROXY_URL:-http://localhost:10000}"
AGENT_URL="${AGENT_URL:-http://localhost:8000}"
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8004}"
ENV_FILE="${ENV_FILE:-.env.render-local}"
DOCUMENTS_EXPECTED_STATUS="${DOCUMENTS_EXPECTED_STATUS:-200}"
FAIL_FAST=false
SKIP_SIMULATION=false

for arg in "$@"; do
  case "$arg" in
    --fail-fast)        FAIL_FAST=true ;;
    --skip-simulation)  SKIP_SIMULATION=true ;;
  esac
done

# ─────────────────────────────────────────────────────────────────────────────
# Colour helpers
# ─────────────────────────────────────────────────────────────────────────────
PASS='\033[0;32m✅\033[0m'
FAIL='\033[0;31m❌\033[0m'
WARN='\033[0;33m⚠️ \033[0m'
INFO='\033[0;36mℹ️ \033[0m'
FAILURES=()

pass()  { echo -e "${PASS} $1"; }
fail()  {
  echo -e "${FAIL} $1"
  FAILURES+=("$1")
  if $FAIL_FAST; then exit 1; fi
}
warn()  { echo -e "${WARN} $1"; }
info()  { echo -e "${INFO} $1"; }

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
http_check() {
  local label="$1" url="$2" expected_status="${3:-200}"
  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
  if [[ "$status" == "$expected_status" ]]; then
    pass "$label ($url → $status)"
  else
    fail "$label: expected HTTP $expected_status, got $status ($url)"
  fi
}

json_check() {
  local label="$1" url="$2" key="$3"
  local body status
  body=$(curl -s --max-time 5 "$url" 2>/dev/null || echo "{}")
  if echo "$body" | grep -q "\"$key\""; then
    pass "$label ($url contains '$key')"
  else
    fail "$label: response does not contain '$key' — got: $body"
  fi
}

env_check() {
  local label="$1" key="$2"
  local val
  val=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' || true)
  if [[ -n "$val" ]]; then
    pass "Env: $label ($key is set)"
  else
    fail "Env: $label ($key missing or empty in $ENV_FILE)"
  fi
}

env_value() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' || true
}

db_host_from_url() {
  local url="$1"
  # Extract host from postgresql://user:pass@host:port/db
  echo "$url" | sed -E 's#^[A-Za-z0-9+.-]+://##' | sed -E 's#^[^@]*@##' | cut -d/ -f1 | cut -d: -f1
}

# ─────────────────────────────────────────────────────────────────────────────
# Phase 0: Env contract validation
# ─────────────────────────────────────────────────────────────────────────────
echo ""
info "Phase 0 — Env contract validation"
echo "──────────────────────────────────"

if [[ -f "$ENV_FILE" ]]; then
  if python3 scripts/github/validate_render_env.py "$ENV_FILE"; then
    pass "Env contract OK ($ENV_FILE)"
  else
    fail "Env contract FAILED ($ENV_FILE)"
  fi
else
  warn "$ENV_FILE not found; skipping env contract validation"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Modal proxy health
# ─────────────────────────────────────────────────────────────────────────────
echo ""
info "Phase 1 — Modal proxy health"
echo "──────────────────────────────"

http_check "Modal proxy /health" "${PROXY_URL}/health" "200"
http_check "Modal proxy /model/health (model upstream)" "${PROXY_URL}/model/health" "200"
http_check "Modal proxy /embedding/health (embedding upstream)" "${PROXY_URL}/embedding/health" "200"

# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Agent service health
# ─────────────────────────────────────────────────────────────────────────────
echo ""
info "Phase 2 — Agent service"
echo "──────────────────────────────"

http_check "Agent /health" "${AGENT_URL}/health" "200"
json_check "Agent /config (providers list)" "${AGENT_URL}/config" "providers"

# ─────────────────────────────────────────────────────────────────────────────
# Phase 3: Gateway health
# ─────────────────────────────────────────────────────────────────────────────
echo ""
info "Phase 3 — Gateway service"
echo "──────────────────────────────"

http_check "Gateway /health" "${GATEWAY_URL}/api/v1/health" "200"

echo ""
info "Phase 3b — Documents endpoint smoke"
echo "──────────────────────────────"

http_check \
  "Gateway /documents/overview" \
  "${GATEWAY_URL}/api/v1/documents/overview" \
  "${DOCUMENTS_EXPECTED_STATUS}"
http_check \
  "Gateway /documents/tags" \
  "${GATEWAY_URL}/api/v1/documents/tags?limit=20" \
  "${DOCUMENTS_EXPECTED_STATUS}"

echo ""
info "Phase 3c — DATABASE_URL host scope guard"
echo "──────────────────────────────"

if [[ -f "$ENV_FILE" ]]; then
  db_url=$(env_value "DATABASE_URL")
  db_host=$(db_host_from_url "$db_url")
  if [[ -n "$db_host" ]]; then
    if [[ "$db_host" == dpg-* && "$GATEWAY_URL" == http://localhost* ]]; then
      fail "DATABASE_URL host '$db_host' is Render-internal and will not resolve from local runs. Use Render external hostname or local Postgres."
    else
      pass "DATABASE_URL host scope check ($db_host)"
    fi
  else
    warn "DATABASE_URL not found in $ENV_FILE; host scope check skipped"
  fi
else
  warn "Skipping DATABASE_URL host scope guard — $ENV_FILE not found"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Phase 4: Proxy routing contract (URL path verification)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
info "Phase 4 — Proxy routing contract"
echo "──────────────────────────────"

# Verify that /model path correctly returns content (not nginx 404 or 502)
model_resp=$(curl -s --max-time 5 "${PROXY_URL}/model/health" 2>/dev/null || echo "")
if echo "$model_resp" | grep -qiE "ok|healthy|running"; then
  pass "Model path correctly routes to model service"
else
  fail "Model path response not as expected: $model_resp"
fi

embedding_resp=$(curl -s --max-time 5 "${PROXY_URL}/embedding/health" 2>/dev/null || echo "")
if echo "$embedding_resp" | grep -qiE "ok|healthy|running"; then
  pass "Embedding path correctly routes to embedding service"
else
  fail "Embedding path response not as expected: $embedding_resp"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Phase 5: Strict-mode flag verification
# ─────────────────────────────────────────────────────────────────────────────
echo ""
info "Phase 5 — Strict-mode flag check"
echo "──────────────────────────────"

if [[ -f "$ENV_FILE" ]]; then
  env_check "Agent enforce proxy" "AGENT_ENFORCE_PROXY"
  env_check "Render remote inference only" "RENDER_REMOTE_INFERENCE_ONLY"
  env_check "Proxy auth token" "PROXY_AUTH_TOKEN"
else
  warn "Skipping strict-mode flag check — $ENV_FILE not found"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Phase 6: Failure simulation (optional)
# ─────────────────────────────────────────────────────────────────────────────
if ! $SKIP_SIMULATION; then
echo ""
info "Phase 6 — Failure simulation"
echo "──────────────────────────────"
info "Testing that /ask returns a structured error (not a 500 crash) when agent is busy"

ask_resp_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  -G "${GATEWAY_URL}/api/v1/ask" \
  --data-urlencode "q=test" \
  2>/dev/null || echo "000")

if [[ "$ask_resp_code" =~ ^(200|422|400|503|502)$ ]]; then
  pass "Gateway /ask returns a structured HTTP response code ($ask_resp_code)"
else
  fail "Gateway /ask returned unexpected code $ask_resp_code"
fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════"
if [[ ${#FAILURES[@]} -eq 0 ]]; then
  echo -e "${PASS} All checks passed — environment ready for Render deploy"
  exit 0
else
  echo -e "${FAIL} ${#FAILURES[@]} check(s) failed:"
  for f in "${FAILURES[@]}"; do
    echo "   • $f"
  done
  echo ""
  echo "Fix the above issues before deploying to Render."
  exit 1
fi
