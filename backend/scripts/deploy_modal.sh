#!/bin/bash
# Deploy Vecinita Modal apps from canonical service packages (Modal 1.x).
#
# Usage:
#   ./backend/scripts/deploy_modal.sh [--embedding] [--model] [--scraper] [--all]
#   ./backend/scripts/deploy_modal.sh --no-web [--embedding] [--model] [--scraper] [--all]
#
# ``--no-web`` sets ``VECINITA_MODAL_INCLUDE_WEB_ENDPOINTS=0`` so ``modal deploy`` only
# registers function endpoints (embedding ``embed_*``, model ``chat_completion`` / downloads,
# scraper workers). Scraper FastAPI (``vecinita_scraper/api/app.py``) is skipped.
#
# Optional legacy cron-only app:
#   ./backend/scripts/deploy_modal.sh --legacy-scraper-cron
#
# Requires: modal CLI and authentication (``modal token new``).
# See: https://modal.com/docs/guide/managing-deployments

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "Vecinita Modal Deployment (service packages)"
echo -e "======================================${NC}\n"

if ! command -v modal &> /dev/null; then
    echo -e "${RED}Modal CLI not found. Install with: pip install modal${NC}"
    exit 1
fi

if ! modal token info &> /dev/null 2>&1; then
    echo -e "${RED}Not authenticated with Modal. Run: modal token new${NC}"
    exit 1
fi

INCLUDE_WEB=1
FILTERED_ARGS=()
for arg in "$@"; do
    case $arg in
        --no-web) INCLUDE_WEB=0 ;;
        *) FILTERED_ARGS+=("$arg") ;;
    esac
done
set -- "${FILTERED_ARGS[@]}"

if [ "$INCLUDE_WEB" = 0 ]; then
    export VECINITA_MODAL_INCLUDE_WEB_ENDPOINTS=0
    echo -e "${YELLOW}Web / ASGI endpoints omitted (function-only deploy).${NC}\n"
else
    export VECINITA_MODAL_INCLUDE_WEB_ENDPOINTS=1
fi

DEPLOY_EMBEDDING=false
DEPLOY_MODEL=false
DEPLOY_SCRAPER=false
DEPLOY_LEGACY_SCRAPER_CRON=false

if [ $# -eq 0 ]; then
    DEPLOY_EMBEDDING=true
    DEPLOY_MODEL=true
    DEPLOY_SCRAPER=true
else
    for arg in "$@"; do
        case $arg in
            --embedding) DEPLOY_EMBEDDING=true ;;
            --model) DEPLOY_MODEL=true ;;
            --scraper) DEPLOY_SCRAPER=true ;;
            --legacy-scraper-cron) DEPLOY_LEGACY_SCRAPER_CRON=true ;;
            --all)
                DEPLOY_EMBEDDING=true
                DEPLOY_MODEL=true
                DEPLOY_SCRAPER=true
                ;;
            *)
                echo "Unknown option: $arg"
                exit 1
                ;;
        esac
    done
fi

cd "$(dirname "$0")/../.."

# Run ``modal deploy`` from the service directory so ``uv run`` resolves import-time deps.
_modal_deploy_in_service() {
    local svc_dir="$1"
    local entry_file="$2"
    if command -v uv >/dev/null 2>&1 && [ -f "$svc_dir/uv.lock" ]; then
        ( cd "$svc_dir" && uv run modal deploy "$entry_file" )
    else
        ( cd "$svc_dir" && modal deploy "$entry_file" )
    fi
}

init_submodules() {
    echo -e "${BLUE}→ Ensuring service submodules are present...${NC}"
    git submodule update --init --depth 1 \
        services/embedding-modal \
        services/model-modal \
        services/scraper
}

if [ "$DEPLOY_EMBEDDING" = true ] || [ "$DEPLOY_MODEL" = true ] || [ "$DEPLOY_SCRAPER" = true ]; then
    init_submodules
fi

if [ "$DEPLOY_EMBEDDING" = true ]; then
    echo -e "${BLUE}→ Deploying embedding Modal app...${NC}"
    _modal_deploy_in_service services/embedding-modal main.py
    echo -e "${GREEN}✓ Embedding Modal app deployed${NC}\n"
fi

if [ "$DEPLOY_MODEL" = true ]; then
    echo -e "${BLUE}→ Deploying model Modal app...${NC}"
    _modal_deploy_in_service services/model-modal main.py
    echo -e "${GREEN}✓ Model Modal app deployed${NC}\n"
fi

if [ "$DEPLOY_SCRAPER" = true ]; then
    echo -e "${BLUE}→ Deploying scraper workers...${NC}"
    _modal_deploy_in_service services/scraper modal_workers_entry.py
    if [ "$INCLUDE_WEB" = 1 ]; then
        echo -e "${BLUE}→ Deploying scraper HTTP API...${NC}"
        _modal_deploy_in_service services/scraper modal_api_entry.py
    else
        echo -e "${YELLOW}  Skipped vecinita_scraper/api (HTTP) — use without --no-web to deploy.${NC}"
    fi
    echo -e "${GREEN}✓ Scraper Modal deploy step(s) complete${NC}\n"
fi

if [ "$DEPLOY_LEGACY_SCRAPER_CRON" = true ]; then
    echo -e "${YELLOW}→ Deploying legacy scraper cron (backend/src/scraper/modal_app.py)...${NC}"
    modal deploy backend/src/scraper/modal_app.py
    echo -e "${YELLOW}⚠ This overwrites the Modal app named in MODAL_SCRAPER_APP_NAME if it matches${NC}"
    echo -e "${YELLOW}  the workers app; prefer migrating cron to services/scraper.${NC}\n"
fi

echo -e "${GREEN}======================================"
echo "Done"
echo -e "======================================${NC}"
echo -e "${YELLOW}Operations:${NC} modal app list --all | modal app logs <name>"
