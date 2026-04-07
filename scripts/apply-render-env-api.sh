#!/bin/bash
# Direct Render API script to set environment variables for data-management-api
# This script calls the Render API directly without needing Render CLI authentication
#
# Prerequisites:
#   - RENDER_API_KEY environment variable set
#   - curl installed
#
# Usage:
#   RENDER_API_KEY="your-api-key" ./scripts/apply-render-env-api.sh

set -e

SERVICE_ID="srv-d7a6477kijhs7395eneg"
SERVICE_NAME="vecinita-data-management-api-v1"
API_BASE="https://api.render.com/v1"
ENV_FILE=".env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Render API - Set Environment Variables                 ║${NC}"
echo -e "${BLUE}║         Service: ${SERVICE_NAME}${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

# Check prerequisites
if [ -z "$RENDER_API_KEY" ]; then
    echo -e "${RED}✗ RENDER_API_KEY environment variable not set${NC}"
    echo -e "${YELLOW}Usage: RENDER_API_KEY='your-key' $0${NC}"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}✗ curl not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}\n"

# Extract values from .env
echo -e "${YELLOW}Extracting environment variables...${NC}"

MODAL_TOKEN_ID=$(grep "^MODAL_API_TOKEN_ID=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')
MODAL_TOKEN_SECRET=$(grep "^MODAL_API_TOKEN_SECRET=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')
SCRAPER_URL=$(grep "^VECINITA_SCRAPER_API_URL=" "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')

if [ -z "$SCRAPER_URL" ]; then
    SCRAPER_URL="https://vecinita--vecinita-scraper-web-app.modal.run"
fi

if [ -z "$MODAL_TOKEN_ID" ] || [ -z "$MODAL_TOKEN_SECRET" ]; then
    echo -e "${RED}✗ Could not extract Modal credentials from .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Extracted credentials${NC}\n"

# Show what will be set
echo -e "${YELLOW}Variables to set:${NC}"
echo "  • MODAL_TOKEN_ID=${MODAL_TOKEN_ID:0:10}...${MODAL_TOKEN_ID: -4}"
echo "  • MODAL_TOKEN_SECRET=${MODAL_TOKEN_SECRET:0:10}...${MODAL_TOKEN_SECRET: -4}"
echo "  • VECINITA_SCRAPER_API_URL=${SCRAPER_URL}"
echo ""

read -p "Continue with API request? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Build JSON payload
PAYLOAD=$(cat <<EOF
{
  "envVars": [
    {
      "key": "MODAL_TOKEN_ID",
      "value": "$MODAL_TOKEN_ID"
    },
    {
      "key": "MODAL_TOKEN_SECRET",
      "value": "$MODAL_TOKEN_SECRET"
    },
    {
      "key": "VECINITA_SCRAPER_API_URL",
      "value": "$SCRAPER_URL"
    }
  ]
}
EOF
)

echo -e "${YELLOW}Calling Render API...${NC}"
echo ""

# Make the API call
HTTP_CODE=$(curl -s -w "%{http_code}" -X PATCH \
    "${API_BASE}/services/${SERVICE_ID}" \
    -H "authorization: Bearer ${RENDER_API_KEY}" \
    -H "content-type: application/json" \
    -d "$PAYLOAD" \
    -o /tmp/render_response.json)

echo "HTTP Status: $HTTP_CODE"

# Check response
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Successfully set environment variables${NC}"
    echo ""
    echo -e "${YELLOW}Response:${NC}"
    cat /tmp/render_response.json | jq . 2>/dev/null || cat /tmp/render_response.json
    echo ""
    echo -e "${YELLOW}The service will redeploy automatically in a few seconds.${NC}"
elif [ "$HTTP_CODE" = "401" ]; then
    echo -e "${RED}✗ Authentication failed (401)${NC}"
    echo -e "${RED}Check that RENDER_API_KEY is valid${NC}"
    cat /tmp/render_response.json
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${RED}✗ Service not found (404)${NC}"
    echo -e "${RED}Check SERVICE_ID: ${SERVICE_ID}${NC}"
    cat /tmp/render_response.json
else
    echo -e "${RED}✗ API call failed (HTTP $HTTP_CODE)${NC}"
    cat /tmp/render_response.json
fi

echo ""
echo -e "${YELLOW}Verification:${NC}"
echo "Once service is live, test with:"
echo "  curl https://${SERVICE_NAME}.onrender.com/health"
echo ""
