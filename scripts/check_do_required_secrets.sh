#!/usr/bin/env bash
# CI guard: DO YAML specs and do_apps sync lists include Modal embed/LLM URLs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

for spec in \
  infra/do/chat-rag-backend.yaml \
  infra/do/internal-write-api.yaml \
  infra/do/staging/chat-rag-backend.yaml \
  infra/do/staging/internal-write-api.yaml; do
  if ! rg -q 'key: VECINITA_MODAL_EMBED_URL' "$spec"; then
    echo "ERROR: ${spec} must declare VECINITA_MODAL_EMBED_URL." >&2
    exit 1
  fi
  if ! rg -q 'key: VECINITA_MODAL_LLM_URL' "$spec"; then
    echo "ERROR: ${spec} must declare VECINITA_MODAL_LLM_URL." >&2
    exit 1
  fi
done

# ChatRAG must send X-Vecinita-Proxy-Key on LLM /generate (RD-165).
if ! rg -q 'key: VECINITA_MODAL_PROXY_KEY' infra/do/chat-rag-backend.yaml; then
  echo "ERROR: chat-rag-backend.yaml must declare VECINITA_MODAL_PROXY_KEY (RD-165)." >&2
  exit 1
fi
if ! rg -q 'key: VECINITA_MODAL_PROXY_KEY' infra/do/internal-write-api.yaml; then
  echo "ERROR: internal-write-api.yaml must declare VECINITA_MODAL_PROXY_KEY." >&2
  exit 1
fi
if ! rg -q 'key: VECINITA_MODAL_PROXY_KEY' infra/do/staging/chat-rag-backend.yaml; then
  echo "ERROR: staging/chat-rag-backend.yaml must declare VECINITA_MODAL_PROXY_KEY (F83)." >&2
  exit 1
fi
if ! rg -q 'key: VECINITA_MODAL_PROXY_KEY' infra/do/staging/internal-write-api.yaml; then
  echo "ERROR: staging/internal-write-api.yaml must declare VECINITA_MODAL_PROXY_KEY (F83)." >&2
  exit 1
fi

if ! rg -q 'VECINITA_MODAL_EMBED_URL' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must sync VECINITA_MODAL_EMBED_URL." >&2
  exit 1
fi

if ! rg -q 'validate_modal_service_url' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must validate Modal URLs before sync." >&2
  exit 1
fi

if ! rg -q 'key: VECINITA_MODAL_LLM_URL' infra/do/internal-write-api.yaml; then
  echo "ERROR: internal-write-api.yaml must declare VECINITA_MODAL_LLM_URL." >&2
  exit 1
fi

if ! rg -q 'key: VECINITA_MODAL_LLM_PLAYGROUND_URL' infra/do/internal-write-api.yaml; then
  echo "ERROR: internal-write-api.yaml must declare VECINITA_MODAL_LLM_PLAYGROUND_URL (TP-S010-27)." >&2
  exit 1
fi

if ! rg -q 'VECINITA_MODAL_LLM_URL' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must sync VECINITA_MODAL_LLM_URL." >&2
  exit 1
fi

if ! rg -q 'VECINITA_MODAL_LLM_PLAYGROUND_URL' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must sync VECINITA_MODAL_LLM_PLAYGROUND_URL." >&2
  exit 1
fi

# do_apps must sync PROXY_KEY onto chat backends (prod + staging short names).
if ! awk '
  /if name in _CHAT_BACKEND_NAMES/ { in_block=1 }
  in_block && /VECINITA_MODAL_PROXY_KEY/ { found=1; exit }
  in_block && /elif name in _WRITE_API_NAMES/ { exit }
  END { exit found ? 0 : 1 }
' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must sync VECINITA_MODAL_PROXY_KEY for chat backends." >&2
  exit 1
fi

if ! rg -q 'vecinita-staging-chat-api' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must know staging app names (F83 / ADR-054)." >&2
  exit 1
fi

# One-shot sync must materialize aliases and push both Modal secrets.
if ! rg -q 'ci_materialize_env.sh' scripts/deploy/sync_env.sh; then
  echo "ERROR: sync_env.sh must source ci_materialize_env.sh (staging URL aliases)." >&2
  exit 1
fi
if ! rg -q 'sync_llm_secret.sh' scripts/deploy/sync_env.sh; then
  echo "ERROR: sync_env.sh must call sync_llm_secret.sh (vecinita-llm proxy key)." >&2
  exit 1
fi
if ! rg -q 'sync_modal_secret.sh --merge' scripts/deploy/sync_env.sh; then
  echo "ERROR: sync_env.sh Modal path must use --merge (preserve live keys)." >&2
  exit 1
fi

echo "OK: DO specs and sync helper include Modal embed/LLM URL guards."
