#!/usr/bin/env bash

# Verify Frontend Gateway Fix
# This script checks if the frontend-gateway connectivity issue has been resolved

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service URLs
FRONTEND_URL="https://vecinita-frontend.onrender.com"
GATEWAY_URL="https://vecinita-gateway-prod-v5.onrender.com"
AGENT_URL="https://vecinita-agent.onrender.com"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

echo -e "${BLUE}"
cat << 'EOF'
╔═════════════════════════════════════════════════════════════════╗
║        Vecinita Frontend-Gateway Connectivity Verification      ║
║                                                                 ║
║  Checking if "Failed to fetch" issue has been resolved          ║
╚═════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Test 1: Frontend service is up
echo -e "\n${YELLOW}[1/5] Checking Frontend Service${NC}"
if curl -s -I "$FRONTEND_URL" | grep -q "200\|301\|302"; then
  echo -e "${GREEN}✓ Frontend is reachable${NC}"
  echo "    URL: $FRONTEND_URL"
  ((PASS_COUNT++))
else
  echo -e "${RED}✗ Frontend is not reachable${NC}"
  echo "    URL: $FRONTEND_URL"
  echo "    Action: Check Render Dashboard for service status"
  ((FAIL_COUNT++))
fi

# Test 2: Gateway service is up
echo -e "\n${YELLOW}[2/5] Checking Gateway Service${NC}"
if curl -s "$GATEWAY_URL/health" > /dev/null 2>&1 || curl -s -I "$GATEWAY_URL" | grep -q "200"; then
  echo -e "${GREEN}✓ Gateway is reachable${NC}"
  echo "    URL: $GATEWAY_URL"
  ((PASS_COUNT++))
else
  echo -e "${RED}✗ Gateway is not reachable${NC}"
  echo "    URL: $GATEWAY_URL"
  echo "    Action: Check Render Dashboard for service status"
  ((FAIL_COUNT++))
fi

# Test 3: Agent service is up
echo -e "\n${YELLOW}[3/5] Checking Agent Service${NC}"
if curl -s "$AGENT_URL/health" > /dev/null 2>&1 || curl -s -I "$AGENT_URL" | grep -q "200"; then
  echo -e "${GREEN}✓ Agent is reachable${NC}"
  echo "    URL: $AGENT_URL"
  ((PASS_COUNT++))
else
  echo -e "${RED}✗ Agent is not reachable${NC}"
  echo "    URL: $AGENT_URL"
  echo "    Action: Check Render Dashboard for service status"
  ((FAIL_COUNT++))
fi

# Test 4: Check .env.production exists locally
echo -e "\n${YELLOW}[4/5] Checking Local Environment Files${NC}"
if [ -f "./frontend/.env.production" ]; then
  echo -e "${GREEN}✓ .env.production file exists${NC}"
  if grep -q "VITE_GATEWAY_URL" ./frontend/.env.production; then
    GATEWAY_VALUE=$(grep "VITE_GATEWAY_URL" ./frontend/.env.production | cut -d= -f2)
    echo "    Value: $GATEWAY_VALUE"
    if [[ "$GATEWAY_VALUE" == *"onrender.com"* ]]; then
      echo -e "${GREEN}✓ VITE_GATEWAY_URL points to Render gateway${NC}"
      ((PASS_COUNT++))
    else
      echo -e "${YELLOW}⚠ VITE_GATEWAY_URL doesn't look like a Render URL${NC}"
      echo "    Expected pattern: https://vecinita-gateway-prod-v5.onrender.com/api/v1"
      ((WARN_COUNT++))
    fi
  else
    echo -e "${YELLOW}⚠ VITE_GATEWAY_URL not found in .env.production${NC}"
    ((WARN_COUNT++))
  fi
else
  echo -e "${YELLOW}⚠ .env.production file not found (this is OK if only using .env)${NC}"
  ((WARN_COUNT++))
fi

# Test 5: Check if frontend deployment is recent
echo -e "\n${YELLOW}[5/5] Checking Frontend Deployment Status${NC}"

# Try to get Render API info if gh CLI is available
if command -v gh &> /dev/null; then
  if gh auth status &>/dev/null; then
    echo -e "${BLUE}Using GitHub CLI to check deployment status...${NC}"
    
    FRONTEND_REPO="joseph-c-mcguire/Vecinitafrontend"
    if gh run list --repo "$FRONTEND_REPO" --workflow deploy.yml -L 1 --json conclusion,status --jq '.[0] | "\(.status) (\(.conclusion))"' 2>/dev/null > /dev/null; then
      DEPLOYMENT_STATUS=$(gh run list --repo "$FRONTEND_REPO" --workflow deploy.yml -L 1 --json conclusion,status --jq '.[0] | "\(.status) (\(.conclusion))"' 2>/dev/null)
      echo "    Latest deployment: $DEPLOYMENT_STATUS"
      
      if [[ "$DEPLOYMENT_STATUS" == *"completed"* ]] && [[ "$DEPLOYMENT_STATUS" == *"success"* ]]; then
        echo -e "${GREEN}✓ Latest deployment succeeded${NC}"
        ((PASS_COUNT++))
      elif [[ "$DEPLOYMENT_STATUS" == *"in_progress"* ]]; then
        echo -e "${YELLOW}⚠ Deployment is still in progress${NC}"
        echo "    Action: Wait 5 more minutes and rerun this test"
        ((WARN_COUNT++))
      else
        echo -e "${RED}✗ Latest deployment may have failed${NC}"
        echo "    Status: $DEPLOYMENT_STATUS"
        ((FAIL_COUNT++))
      fi
    fi
  else
    echo -e "${YELLOW}⚠ GitHub CLI not authenticated${NC}"
    echo "    Action: Run 'gh auth login' to authenticate"
    ((WARN_COUNT++))
  fi
else
  echo -e "${YELLOW}⚠ GitHub CLI not installed${NC}"
  echo "    Action: Manual check at https://github.com/joseph-c-mcguire/Vecinitafrontend/actions"
  ((WARN_COUNT++))
fi

# Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Tests Passed:  ${GREEN}${PASS_COUNT}${NC}"
echo -e "Tests Failed:  ${RED}${FAIL_COUNT}${NC}"
echo -e "Warnings:      ${YELLOW}${WARN_COUNT}${NC}"

if [ "$FAIL_COUNT" -eq 0 ] && [ "$WARN_COUNT" -le 1 ]; then
  echo -e "\n${GREEN}✓ Frontend-Gateway connectivity appears healthy!${NC}"
  echo ""
  echo "Next steps:"
  echo "1. Open https://vecinita-frontend.onrender.com in your browser"
  echo "2. Open DevTools (F12) → Network tab"
  echo "3. Try submitting a question"
  echo "4. Verify the POST request to /api/v1/ask returns 200 OK"
  echo ""
  exit 0
else
  echo -e "\n${RED}✗ Please address the issues above${NC}"
  echo ""
  echo "Common fixes:"
  echo "1. If deployment is in progress, wait 5 more minutes"
  echo "2. If VITE_GATEWAY_URL not set, update Render environment variables"
  echo "3. If services are down, check Render Dashboard for error messages"
  echo ""
  exit 1
fi
