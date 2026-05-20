#!/usr/bin/env bash
# Stop Vecinita Modal apps that were mistakenly deployed on the fontface workspace.
# Does not remove fontface-tools / fontface-job-queue (unrelated apps).
set -euo pipefail

echo "==> Switching to fontface profile..."
modal profile activate fontface

for app in vecinita-embedding vecinita-llm vecinita-data-management; do
  echo "==> Stopping ${app} (if deployed)..."
  modal app stop "$app" 2>/dev/null || echo "    (not deployed — skipped)"
done

echo "==> Restoring vecinita profile for Vecinita work..."
modal profile activate vecinita
modal profile current

echo "Done. Deploy Vecinita apps with: bash scripts/deploy/modal.sh"
