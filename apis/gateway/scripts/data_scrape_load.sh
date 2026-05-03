#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[DEPRECATED] scripts/data_scrape_load.sh now delegates to scripts/run_scraper.sh"
exec "${SCRIPT_DIR}/run_scraper.sh" "$@"
