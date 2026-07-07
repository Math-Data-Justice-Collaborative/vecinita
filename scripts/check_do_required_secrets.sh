#!/usr/bin/env bash
# CI guard: DO YAML specs and do_apps sync lists include Modal embed/LLM URLs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

for spec in infra/do/chat-rag-backend.yaml infra/do/internal-write-api.yaml; do
  if ! rg -q 'key: VECINITA_MODAL_EMBED_URL' "$spec"; then
    echo "ERROR: ${spec} must declare VECINITA_MODAL_EMBED_URL." >&2
    exit 1
  fi
  if ! rg -q 'key: VECINITA_MODAL_LLM_URL' "$spec"; then
    echo "ERROR: ${spec} must declare VECINITA_MODAL_LLM_URL." >&2
    exit 1
  fi
done

if ! rg -q 'VECINITA_MODAL_EMBED_URL' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must sync VECINITA_MODAL_EMBED_URL." >&2
  exit 1
fi

if ! rg -q 'validate_modal_service_url' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must validate Modal URLs before sync." >&2
  exit 1
fi

if ! rg -q 'key: VECINITA_MODAL_OLLAMA_URL' infra/do/internal-write-api.yaml; then
  echo "ERROR: internal-write-api.yaml must declare VECINITA_MODAL_OLLAMA_URL." >&2
  exit 1
fi

if ! rg -q 'VECINITA_MODAL_OLLAMA_URL' scripts/deploy/do_apps.py; then
  echo "ERROR: do_apps.py must sync VECINITA_MODAL_OLLAMA_URL." >&2
  exit 1
fi

echo "OK: DO specs and sync helper include Modal embed/LLM/Ollama URL guards."
