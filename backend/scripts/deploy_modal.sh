#!/bin/bash
# Deploy Vecinita Modal apps from canonical service packages (Modal 1.x).
#
# Usage: ./backend/scripts/deploy_modal.sh [--embedding] [--model] [--scraper] [--all]
# Optional legacy cron-only app (monolith CLI, no HTTP):
#   ./backend/scripts/deploy_modal.sh --legacy-scraper-cron
#
# Requires: modal CLI (pip install modal) and authentication (modal token new).

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
    modal deploy services/embedding-modal/src/vecinita/app.py
    echo -e "${GREEN}✓ Embedding Modal app deployed${NC}\n"
fi

if [ "$DEPLOY_MODEL" = true ]; then
    echo -e "${BLUE}→ Deploying model Modal app...${NC}"
    modal deploy services/model-modal/src/vecinita/app.py
    echo -e "${GREEN}✓ Model Modal app deployed${NC}\n"
fi

if [ "$DEPLOY_SCRAPER" = true ]; then
    echo -e "${BLUE}→ Deploying scraper workers + HTTP API...${NC}"
    modal deploy services/scraper/src/vecinita_scraper/app.py
    modal deploy services/scraper/src/vecinita_scraper/api/app.py
    echo -e "${GREEN}✓ Scraper Modal apps deployed${NC}\n"
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
echo -e "${YELLOW}Teardown old HTTP apps:${NC} see backend/scripts/modal_teardown_legacy_web.sh"
echo -e "${YELLOW}Operations:${NC} modal app list --all | modal app logs <name>"
