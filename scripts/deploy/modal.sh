#!/usr/bin/env bash
# Deploy all Modal apps (embedding, data-management, LLM). Requires: modal CLI, authenticated.
# Uses the vecinita Modal workspace (not fontface). See scripts/modal_ensure_workspace.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck source=../modal_ensure_workspace.sh
source "${ROOT}/scripts/modal_ensure_workspace.sh"

echo "Deploying vecinita-embedding..."
modal deploy infra/modal/embedding_app.py

echo "Deploying vecinita-data-management..."
modal deploy infra/modal/data_management_app.py

echo "Deploying vecinita-llm..."
modal deploy infra/modal/llm_app.py

echo "Done. Record embed/LLM URLs in DO ChatRAG secrets (see docs/staging-secrets-matrix.md)."
