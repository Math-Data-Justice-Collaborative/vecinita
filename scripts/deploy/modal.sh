#!/usr/bin/env bash
# Deploy all Modal apps (embedding, data-management, LLM). Requires: modal CLI, authenticated.
# Uses the vecinita Modal workspace (not fontface). See scripts/modal_ensure_workspace.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=../modal_ensure_workspace.sh
source "${ROOT}/scripts/modal_ensure_workspace.sh"

# Prefer uv-run Modal so workspace packages (shared-schemas) resolve on import.
# Bare ``modal`` on PATH often lacks vecinita_shared_schemas (T80.7 operator).
if command -v uv >/dev/null 2>&1; then
  MODAL_CMD=(uv run modal)
else
  MODAL_CMD=(modal)
fi

echo "Deploying vecinita-embedding..."
"${MODAL_CMD[@]}" deploy infra/modal/embedding_app.py

echo "Deploying vecinita-data-management..."
"${MODAL_CMD[@]}" deploy infra/modal/data_management_app.py

echo "Deploying vecinita-llm (prod pin; ADR-037 / RD-169)..."
"${MODAL_CMD[@]}" deploy infra/modal/llm_app.py

echo "Deploying vecinita-llm-playground (shared llm-models; TP-S010-25)..."
"${MODAL_CMD[@]}" deploy infra/modal/llm_playground_app.py

echo "Done. vecinita-ollama is deprecated — do not deploy (ADR-037)."
echo "Record VECINITA_MODAL_LLM_URL (prod) and VECINITA_MODAL_LLM_PLAYGROUND_URL in DO secrets"
echo "(see docs/staging-secrets-matrix.md)."
