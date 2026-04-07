#!/bin/bash
# Setup script to configure Render environment variables for data-management-api
# This script extracts values from .env and applies them to the Render service
# 
# Prerequisites:
#   1. Run: render login (requires browser authentication)
#   2. Ensure .env file exists in this repo with Modal credentials
#
# Usage:
#   ./scripts/setup-render-env.sh

set -e

SERVICE_ID="srv-d7a6477kijhs7395eneg"
SERVICE_NAME="vecinita-data-management-api-v1"
ENV_FILE=".env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${RED}Error: Render CLI not found. Install from https://render.com/docs/cli${NC}"
    exit 1
fi

# Check if authenticated
if ! render whoami &> /dev/null; then
    echo -e "${RED}Render CLI not authenticated. Please run: render login${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}\n"

# Extract values from .env
echo -e "${YELLOW}Extracting environment variables from .env...${NC}"

MODAL_TOKEN_ID=$(grep "^MODAL_API_TOKEN_ID=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')
MODAL_TOKEN_SECRET=$(grep "^MODAL_API_TOKEN_SECRET=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')

# For scraper URL, check if VECINITA_SCRAPER_API_URL exists, otherwise construct from Modal endpoint pattern
SCRAPER_URL=$(grep "^VECINITA_SCRAPER_API_URL=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')
if [ -z "$SCRAPER_URL" ]; then
    # Fallback: use Modal app endpoint for scraper
    SCRAPER_URL="https://vecinita--vecinita-scraper-web-app.modal.run"
    echo -e "${YELLOW}VECINITA_SCRAPER_API_URL not found, using inferred: $SCRAPER_URL${NC}"
fi

echo -e "${GREEN}✓ Extracted credentials${NC}\n"

# Display what will be set
echo -e "${YELLOW}Environment variables that will be set:${NC}"
echo "  MODAL_TOKEN_ID: ${MODAL_TOKEN_ID:0:10}...${MODAL_TOKEN_ID: -4}"
echo "  MODAL_TOKEN_SECRET: ${MODAL_TOKEN_SECRET:0:10}...${MODAL_TOKEN_SECRET: -4}"
echo "  VECINITA_SCRAPER_API_URL: $SCRAPER_URL"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# NOTE: Render CLI v1.1.0 does not have a direct 'env set' command
# The interactive mode in services command does not support env var editing
# The workaround is to use the Render API directly with curl

echo -e "${YELLOW}Setting environment variables...${NC}\n"

# Method 1: Try using Render API with stored credentials
echo -e "${YELLOW}Method 1: Attempting via Render API (requires RENDER_API_KEY)${NC}"
if [ -z "$RENDER_API_KEY" ]; then
    echo -e "${YELLOW}  ⚠ RENDER_API_KEY not set. Skipping API method.${NC}"
else
    echo -e "${YELLOW}  Using API key from RENDER_API_KEY env var${NC}"
    
    RESPONSE=$(curl -s -X PATCH \
        "https://api.render.com/v1/services/${SERVICE_ID}" \
        -H "authorization: Bearer ${RENDER_API_KEY}" \
        -H "content-type: application/json" \
        -d "{
            \"envVars\": [
                {
                    \"key\": \"MODAL_TOKEN_ID\",
                    \"value\": \"${MODAL_TOKEN_ID}\"
                },
                {
                    \"key\": \"MODAL_TOKEN_SECRET\",
                    \"value\": \"${MODAL_TOKEN_SECRET}\"
                },
                {
                    \"key\": \"VECINITA_SCRAPER_API_URL\",
                    \"value\": \"${SCRAPER_URL}\"
                }
            ]
        }" 2>&1)
    
    if echo "$RESPONSE" | grep -q "\"id\":"; then
        echo -e "${GREEN}✓ Environment variables set via API${NC}"
    else
        echo -e "${RED}✗ API method failed${NC}"
        echo "Response: $RESPONSE"
    fi
fi

echo ""
echo -e "${YELLOW}Method 2: Manual setup via Render Dashboard${NC}"
echo ""
echo "1. Go to: https://dashboard.render.com/web/${SERVICE_ID}"
echo "2. Click on 'Environment' tab"
echo "3. Add these variables:"
echo "   Key: MODAL_TOKEN_ID"
echo "   Value: ${MODAL_TOKEN_ID}"
echo ""
echo "   Key: MODAL_TOKEN_SECRET"
echo "   Value: ${MODAL_TOKEN_SECRET}"
echo ""
echo "   Key: VECINITA_SCRAPER_API_URL"
echo "   Value: ${SCRAPER_URL}"
echo "4. Click 'Save'"
echo ""
echo -e "${YELLOW}The service will automatically redeploy with these variables.${NC}\n"

# Verify (optional)
echo -e "${YELLOW}Verification command (after variables are set):${NC}"
echo "curl https://vecinita-data-management-api-v1.onrender.com/health"
echo ""
