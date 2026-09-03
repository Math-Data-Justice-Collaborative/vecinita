#!/usr/bin/env bash
# Fail closed when staging Deploy would sync a Modal Environment staging embed URL
# onto DO apps that serve a prod→staging mirrored corpus (EV-338 / BUG-2026-09-03).
#
# Usage (CI / local):
#   export VECINITA_MODAL_EMBED_URL=...
#   bash scripts/deploy/check_staging_embed_mirror_align.sh
#
# Waiver (staging-rebuilt corpus under staging pin only):
#   VECINITA_ALLOW_STAGING_EMBED=1 bash scripts/deploy/check_staging_embed_mirror_align.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

url="${VECINITA_MODAL_EMBED_URL:-}"
if [[ -z "$url" ]]; then
  echo "VECINITA_MODAL_EMBED_URL unset — skip mirror-align check" >&2
  exit 0
fi

uv run python scripts/deploy/modal_url_validate.py --mirrored-staging-embed "$url"
echo "OK: staging mirror embed URL uses prod vecinita-- host (or waiver set)"
