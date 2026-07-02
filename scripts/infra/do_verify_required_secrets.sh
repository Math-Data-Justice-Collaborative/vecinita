#!/usr/bin/env bash
# Verify DigitalOcean backend apps have required secrets and Modal embed/LLM are reachable.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/infra/do_verify_required_secrets.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}"

if [[ -z "${DIGITALOCEAN_TOKEN:-}" ]]; then
  echo "ERROR: DIGITALOCEAN_TOKEN is required (export from prod.env)." >&2
  exit 1
fi

BACKEND_APPS=(
  "vecinita-chat-rag-backend"
  "vecinita-internal-write-api"
)
REQUIRED_KEYS=(
  DATABASE_URL
  VECINITA_MODAL_EMBED_URL
  VECINITA_MODAL_LLM_URL
  VECINITA_INTERNAL_API_KEY
)

echo "==> Live DO app secret keys"
export ROOT
uv run --with pydo --with pyyaml python3 - <<PY
import os
import sys

ROOT = os.environ.get("ROOT", ".")
sys.path.insert(0, os.path.join(ROOT, "scripts", "deploy"))

from do_apps import _client, _find_app, _iter_apps

required = [
    "DATABASE_URL",
    "VECINITA_MODAL_EMBED_URL",
    "VECINITA_MODAL_LLM_URL",
    "VECINITA_INTERNAL_API_KEY",
]
apps = ["vecinita-chat-rag-backend", "vecinita-internal-write-api"]
client = _client()
all_apps = _iter_apps(client)
failed = False
for name in apps:
    app = _find_app(all_apps, name)
    if not app:
        print(f"ERROR: missing DO app {name!r}", file=sys.stderr)
        failed = True
        continue
    spec = app.get("spec") or {}
    present: set[str] = set()
    for svc in spec.get("services") or []:
        for env in svc.get("envs") or []:
            key = env.get("key")
            val = (env.get("value") or "").strip()
            if key in required and val:
                present.add(key)
    missing = [k for k in required if k not in present]
    if missing:
        print(f"ERROR: {name} missing secret keys: {missing}", file=sys.stderr)
        failed = True
    else:
        print(f"OK: {name} has required secret keys")
if failed:
    sys.exit(1)
PY

if [[ -n "${VECINITA_MODAL_EMBED_URL:-}" ]]; then
  echo "==> Validate embed URL format (shell)"
  uv run python scripts/deploy/modal_url_validate.py \
    VECINITA_MODAL_EMBED_URL "${VECINITA_MODAL_EMBED_URL}"
fi
if [[ -n "${VECINITA_MODAL_LLM_URL:-}" ]]; then
  echo "==> Validate LLM URL format (shell)"
  uv run python scripts/deploy/modal_url_validate.py \
    VECINITA_MODAL_LLM_URL "${VECINITA_MODAL_LLM_URL}"
fi

chat_url="${VECINITA_STAGING_CHAT_URL:-}"
if [[ -n "$chat_url" ]]; then
  echo "==> ChatRAG /health dependency probe"
  python3 - <<'PY' "${chat_url%/}/health"
import json
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=15) as resp:
    body = json.load(resp)
assert body.get("status") == "ok", body
deps = body.get("dependencies") or {}
for key in ("postgres", "modal_embed", "modal_llm"):
    state = deps.get(key)
    assert state == "ok", f"dependency {key}={state!r} (full={deps})"
print("OK: ChatRAG dependencies postgres/modal_embed/modal_llm are ok")
PY
fi

embed_url="${VECINITA_MODAL_EMBED_URL:-}"
if [[ -n "$embed_url" ]]; then
  echo "==> Modal embed POST /embed smoke"
  code="$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST "${embed_url%/}/embed" \
    -H "Content-Type: application/json" \
    -d '{"text":"do verify embed"}')"
  if [[ "$code" != "200" ]]; then
    echo "ERROR: POST ${embed_url%/}/embed returned HTTP ${code}" >&2
    exit 1
  fi
  echo "OK: embed endpoint returned HTTP 200"
fi

echo "OK: DO required secrets and Modal embed probes passed."
