#!/bin/bash
# Deploy Vecinita services to Modal
# Usage: ./backend/scripts/deploy_modal.sh [--embedding] [--scraper] [--all]
# Requires: modal CLI installed (pip install modal) and authenticated (modal token new)

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "Vecinita Modal Deployment Script"
echo -e "======================================${NC}\n"

# Check prerequisites
if ! command -v modal &> /dev/null; then
    echo -e "${RED}❌ Modal CLI not found. Install with: pip install modal${NC}"
    exit 1
fi

if ! modal token info &> /dev/null 2>&1; then
    echo -e "${RED}❌ Not authenticated with Modal. Run: modal token new${NC}"
    exit 1
fi

# Parse arguments
DEPLOY_EMBEDDING=false
DEPLOY_SCRAPER=false

if [ $# -eq 0 ]; then
    DEPLOY_EMBEDDING=true
    DEPLOY_SCRAPER=true
else
    for arg in "$@"; do
        case $arg in
            --embedding) DEPLOY_EMBEDDING=true ;;
            --scraper) DEPLOY_SCRAPER=true ;;
            --all) DEPLOY_EMBEDDING=true; DEPLOY_SCRAPER=true ;;
            *) echo "Unknown option: $arg"; exit 1 ;;
        esac
    done
fi

# Navigate to repo root
cd "$(dirname "$0")/../.."

# ============================================================================
# Deploy Embedding Service
# ============================================================================
if [ "$DEPLOY_EMBEDDING" = true ]; then
    echo -e "${BLUE}→ Deploying Embedding Service to Modal...${NC}"
    
    if [ ! -f "backend/src/embedding_service/modal_app.py" ]; then
        echo -e "${RED}❌ Embedding service not found${NC}"
        echo "   Expected: backend/src/embedding_service/modal_app.py"
        exit 1
    fi
    
    echo "  Deploying backend/src/embedding_service/modal_app.py..."
    set +e
    modal deploy backend/src/embedding_service/modal_app.py 2>&1 | tee /tmp/modal_embedding.log
    EMBED_EXIT=${PIPESTATUS[0]}
    set -e
    if [ "$EMBED_EXIT" -ne 0 ]; then
        echo -e "${RED}❌ Embedding deployment failed${NC}"
        exit "$EMBED_EXIT"
    fi
    
    # Extract URL
    EMBEDDING_URL=$(grep -oP '(?<=Available at ).*' /tmp/modal_embedding.log || echo "https://vecinita-embedding--latest.modal.run")
    
    echo -e "${GREEN}✓ Embedding Service Deployed${NC}"
    echo -e "  URL: ${BLUE}$EMBEDDING_URL${NC}\n"
    
    # Save URL for next service
    export EMBEDDING_SERVICE_URL="$EMBEDDING_URL"
fi

# ============================================================================
# Deploy Scraper Service (Cron Job)
# ============================================================================
if [ "$DEPLOY_SCRAPER" = true ]; then
    echo -e "${BLUE}→ Deploying Scraper to Modal...${NC}"
    
    if [ ! -f "backend/src/scraper/modal_app.py" ]; then
        echo -e "${RED}❌ Scraper Modal app not found at backend/src/scraper/modal_app.py${NC}"
        exit 1
    fi
    
    echo "  Deploying backend/src/scraper/modal_app.py..."
    set +e
    modal deploy backend/src/scraper/modal_app.py 2>&1 | tee /tmp/modal_scraper.log
    SCRAPER_EXIT=${PIPESTATUS[0]}
    set -e
    if [ "$SCRAPER_EXIT" -ne 0 ]; then
        echo -e "${RED}❌ Scraper deployment failed${NC}"
        exit "$SCRAPER_EXIT"
    fi

    SCRAPER_URL=$(grep -oP '(?<=Available at ).*' /tmp/modal_scraper.log || echo "https://vecinita-scraper--latest.modal.run")
    
    echo -e "${GREEN}✓ Scraper Deployed${NC}"
    echo -e "  URL: ${BLUE}$SCRAPER_URL${NC}"
    echo -e "  Schedule: Weekly cron reindex (REINDEX_CRON_SCHEDULE)\n"

    export REINDEX_SERVICE_URL="$SCRAPER_URL"
fi

# ============================================================================
# Summary
# ============================================================================
echo -e "${GREEN}======================================"
echo "✓ Modal Deployment Complete"
echo -e "======================================${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Create Modal secrets (one-time):"
echo -e "   ${BLUE}modal secret create vecinita-secrets${NC}"
echo "   Add environment variables:"
echo "     SUPABASE_URL=https://..."
echo "     SUPABASE_KEY=eyJ..."
echo "     GROQ_API_KEY=gsk_..."
echo ""
echo "2. Update agent environment:"
if [ -n "$EMBEDDING_SERVICE_URL" ]; then
    echo -e "   ${BLUE}export EMBEDDING_SERVICE_URL=$EMBEDDING_SERVICE_URL${NC}"
fi
if [ -n "$REINDEX_SERVICE_URL" ]; then
    echo -e "   ${BLUE}export REINDEX_SERVICE_URL=$REINDEX_SERVICE_URL${NC}"
fi
echo ""
echo "3. Monitor deployments:"
echo -e "   ${BLUE}modal app logs vecinita-embedding${NC}"
echo -e "   ${BLUE}modal app logs vecinita-scraper${NC}"
echo ""
echo "4. Test services:"
echo -e "   ${BLUE}curl $EMBEDDING_SERVICE_URL/health${NC}"
if [ -n "$REINDEX_SERVICE_URL" ]; then
    echo -e "   ${BLUE}curl $REINDEX_SERVICE_URL/health${NC}"
fi
echo ""
echo "5. To undeploy:"
echo -e "   ${BLUE}modal app delete vecinita-embedding${NC}"
echo -e "   ${BLUE}modal app delete vecinita-scraper${NC}"
echo ""
echo "More info: modal app logs, modal app info <name>"
