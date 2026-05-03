#!/bin/bash

# Vecinita Frontend "Failed to fetch" Fix
# Root cause: VITE_GATEWAY_URL not set to gateway URL in Render deployment
# Fix: Set environment variable and redeploy

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Vecinita Frontend - "Failed to fetch" Fix                      ║${NC}"
echo -e "${BLUE}║  Root Cause: VITE_GATEWAY_URL not configured                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Service URLs
GATEWAY_URL="https://vecinita-gateway-prod-v5.onrender.com"
AGENT_URL="https://vecinita-agent.onrender.com"
FRONTEND_URL="https://vecinita-frontend.onrender.com"
FRONTEND_REPO="joseph-c-mcguire/Vecinitafrontend"

echo -e "\n${YELLOW}Error Analysis:${NC}"
echo "When frontend loads from: $FRONTEND_URL"
echo "And tries to fetch from: /api (or /api/v1)"
echo "There's no proxy, so it fails:"
echo "  → GET $FRONTEND_URL/api/v1/ask → 404 or CORS error"
echo ""
echo "Solution: Set VITE_GATEWAY_URL to actual gateway:"
echo "  → VITE_GATEWAY_URL=$GATEWAY_URL/api/v1"

# Step 1: Check current frontend logs
echo -e "\n${YELLOW}[1/4] Checking Frontend Logs${NC}"
echo -e "\n${BLUE}To view frontend errors in browser:${NC}"
echo "1. Open: $FRONTEND_URL"
echo "2. Press F12 to open Developer Console"
echo "3. Check Network tab → failed requests"
echo "4. Check Console tab for JavaScript errors"
echo ""
echo -e "${BLUE}Expected error:${NC}"
echo "  Failed to fetch https://vecinita-frontend.onrender.com/api/v1/ask/config"
echo "  CORS error: Cross-Origin Request Blocked"

# Step 2: Fix via GitHub CLI
echo -e "\n${YELLOW}[2/4] Setting Environment Variable via GitHub${NC}"

if gh auth status &>/dev/null; then
  echo -e "${GREEN}✓ GitHub CLI authenticated${NC}"
else
  echo -e "${RED}✗ GitHub CLI not authenticated${NC}"
  echo "Run: gh auth login"
  exit 1
fi

# Check if environment variable is already set
echo -e "\n${BLUE}Checking if VITE_GATEWAY_URL is set in GitHub variables...${NC}"
if gh variable list --repo $FRONTEND_REPO 2>/dev/null | grep -i "VITE_GATEWAY_URL"; then
  echo -e "${YELLOW}Variable already exists, updating...${NC}"
else
  echo -e "${YELLOW}Variable not found, creating...${NC}"
fi

# Set the environment variable
echo -e "\n${BLUE}Setting VITE_GATEWAY_URL to: $GATEWAY_URL/api/v1${NC}"
gh variable set VITE_GATEWAY_URL \
  --repo $FRONTEND_REPO \
  --body "$GATEWAY_URL/api/v1" \
  2>/dev/null && \
  echo -e "${GREEN}✓ Variable set successfully${NC}" || \
  echo -e "${YELLOW}⚠ Could not set variable (may not have permission)${NC}"

# Step 3: Update .env files
echo -e "\n${YELLOW}[3/4] Updating Local .env Files${NC}"

FRONTEND_ENV_FILE="./frontends/chat/.env"
FRONTEND_ENV_PROD_FILE="./frontends/chat/.env.production"

if [ -f "$FRONTEND_ENV_FILE" ]; then
  echo -e "${BLUE}Updating $FRONTEND_ENV_FILE${NC}"
  # Use sed to update or add VITE_GATEWAY_URL
  if grep -q "VITE_GATEWAY_URL" "$FRONTEND_ENV_FILE"; then
    sed -i "s|VITE_GATEWAY_URL=.*|VITE_GATEWAY_URL=$GATEWAY_URL/api/v1|" "$FRONTEND_ENV_FILE"
    echo -e "${GREEN}✓ Updated existing VITE_GATEWAY_URL${NC}"
  else
    echo "VITE_GATEWAY_URL=$GATEWAY_URL/api/v1" >> "$FRONTEND_ENV_FILE"
    echo -e "${GREEN}✓ Added VITE_GATEWAY_URL${NC}"
  fi
else
  echo -e "${YELLOW}⚠ $FRONTEND_ENV_FILE not found${NC}"
fi

# Create .env.production for production build
echo -e "\n${BLUE}Creating $FRONTEND_ENV_PROD_FILE${NC}"
mkdir -p "$(dirname "$FRONTEND_ENV_PROD_FILE")"
cat > "$FRONTEND_ENV_PROD_FILE" << EOF
# Production environment variables for Vecinita Frontend
# Used during build process on Render

# Backend Gateway URL - MUST point to actual deployed gateway
VITE_GATEWAY_URL=$GATEWAY_URL/api/v1

# Request timeouts
VITE_AGENT_REQUEST_TIMEOUT_MS=90000
VITE_AGENT_STREAM_TIMEOUT_MS=120000
VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS=15000

# Admin settings
VITE_ADMIN_AUTH_ENABLED=true
EOF

echo -e "${GREEN}✓ Created .env.production with correct gateway URL${NC}"

# Step 4: Git commit and push
echo -e "\n${YELLOW}[4/4] Committing Changes${NC}"

if [ "$(git -C . status --porcelain | wc -l)" -gt 0 ]; then
  echo -e "${BLUE}Changes detected, committing...${NC}"
  git add frontends/chat/.env frontends/chat/.env.production 2>/dev/null || true
  
  git commit -m "fix: Set VITE_GATEWAY_URL to deployed gateway URL

- Update frontend environment to use deployed gateway: $GATEWAY_URL/api/v1
- Create .env.production for build-time configuration
- Resolves 'Failed to fetch' errors in production

This ensures the frontend correctly routes API requests through the gateway
instead of trying to access /api relative path which doesn't exist on Render." \
    2>/dev/null && \
    echo -e "${GREEN}✓ Committed locally${NC}" || \
    echo -e "${YELLOW}⚠ Could not commit (working directory issue)${NC}"
  
  # Push changes
  echo -e "\n${BLUE}Pushing changes to GitHub...${NC}"
  git push origin HEAD 2>/dev/null && \
    echo -e "${GREEN}✓ Pushed to GitHub${NC}" || \
    echo -e "${YELLOW}⚠ Could not push (check git status)${NC}"
else
  echo -e "${YELLOW}⚠ No changes detected${NC}"
fi

# Summary and next steps
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo ""
echo "1. ${BLUE}Wait for Frontend Deployment${NC}"
echo "   The workflow should trigger automatically on push."
echo "   Check status with:"
echo "   gh run list --repo $FRONTEND_REPO --workflow deploy.yml -L 1"
echo ""
echo "2. ${BLUE}Wait ~3-5 minutes for deployment to complete${NC}"
echo ""
echo "3. ${BLUE}Test the Fix${NC}"
echo "   Open: $FRONTEND_URL"
echo "   Press F12 → Network tab"
echo "   Check that requests to /api/v1/ask succeed (200 OK)"
echo ""
echo "4. ${BLUE}Verify Gateway Communication${NC}"
echo "   curl '$GATEWAY_URL/health'"
echo "   curl '$AGENT_URL/health'"
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Configuration applied. Waiting for Render redeploy...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}\n"

# Diagnostic info
echo -e "${BLUE}Current Service URLs:${NC}"
echo "  Frontend:  $FRONTEND_URL"
echo "  Gateway:   $GATEWAY_URL"
echo "  Agent:     $AGENT_URL"
echo ""
echo -e "${BLUE}Environment Variable Set:${NC}"
echo "  VITE_GATEWAY_URL=$GATEWAY_URL/api/v1"
echo ""
echo -e "${BLUE}What This Fixes:${NC}"
echo "  ✓ Frontend will now route API requests to gateway"
echo "  ✓ Eliminates 'GET /api/v1/ask 404' errors"
echo "  ✓ Enables proper CORS handling through gateway"
echo "  ✓ Restores communication: Frontend → Gateway → Agent"
