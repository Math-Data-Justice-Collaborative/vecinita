#!/bin/bash

# Vecinita Service Connectivity Diagnostic
# Diagnoses and fixes "Failed to fetch" errors between services

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Vecinita Service Connectivity Diagnostic                       ║${NC}"
echo -e "${BLUE}║  Diagnosing: Gateway ↔ Frontend ↔ Agent                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Service URLs
GATEWAY_URL="https://vecinita-gateway-prod-v5.onrender.com"
FRONTEND_URL="https://vecinita-frontend.onrender.com"
AGENT_URL="https://vecinita-agent.onrender.com"

# Colors based on status
check_service() {
  local name=$1
  local url=$2
  
  echo -e "\n${BLUE}Checking: ${name}${NC}"
  echo "URL: ${url}"
  
  # Try to reach the service
  if timeout 10 curl -s -o /dev/null -w "%{http_code}" "$url" > /tmp/http_code 2>/dev/null; then
    http_code=$(cat /tmp/http_code)
    case $http_code in
      200|301|302)
        echo -e "${GREEN}✓ Service responding (HTTP ${http_code})${NC}"
        return 0
        ;;
      500|502|503|504)
        echo -e "${RED}✗ Service error (HTTP ${http_code})${NC}"
        return 1
        ;;
      000)
        echo -e "${RED}✗ Connection failed (timeout or unreachable)${NC}"
        return 1
        ;;
      *)
        echo -e "${YELLOW}⚠ Unexpected response (HTTP ${http_code})${NC}"
        return 1
        ;;
    esac
  else
    echo -e "${RED}✗ Cannot reach service${NC}"
    return 1
  fi
}

# Step 1: Check service health
echo -e "\n${YELLOW}[1/5] Testing Service Health${NC}"

check_service "Frontend" "$FRONTEND_URL" || FRONTEND_DOWN=1
check_service "Gateway" "$GATEWAY_URL" || GATEWAY_DOWN=1
check_service "Agent" "$AGENT_URL" || AGENT_DOWN=1

# Step 2: Check CORS configuration
echo -e "\n${YELLOW}[2/5] Checking CORS Headers${NC}"

echo -e "\n${BLUE}Gateway CORS headers:${NC}"
curl -s -i "$GATEWAY_URL" \
  | grep -i "access-control\|content-type" \
  | head -10 || echo "Could not fetch headers"

echo -e "\n${BLUE}Agent CORS headers:${NC}"
curl -s -i "$AGENT_URL" \
  | grep -i "access-control\|content-type" \
  | head -10 || echo "Could not fetch headers"

# Step 3: Check environment variables
echo -e "\n${YELLOW}[3/5] Environment Variables Check${NC}"

echo -e "\n${BLUE}Frontend should have:${NC}"
echo "- VITE_GATEWAY_URL pointing to gateway"
echo "- Check: Backend URL config in frontend .env"

echo -e "\n${BLUE}Gateway should have:${NC}"
echo "- AGENT_URL pointing to agent service"
echo "- ALLOWED_ORIGINS including frontend URL"
echo "- CORS configured for frontend origin"

echo -e "\n${BLUE}Agent should have:${NC}"
echo "- Database connection string set"
echo "- CORS_ORIGINS set to gateway/frontend URLs"

# Step 4: Check specific error patterns
echo -e "\n${YELLOW}[4/5] Checking Network Path${NC}"

# Test if frontend can reach gateway (simulated)
echo -e "\n${BLUE}Frontend → Gateway path:${NC}"
if curl -s "$GATEWAY_URL/api" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Gateway API endpoint reachable${NC}"
else
  echo -e "${RED}✗ Gateway API endpoint not reachable${NC}"
fi

# Test if gateway can reach agent (simulated)
echo -e "\n${BLUE}Gateway → Agent path:${NC}"
if curl -s "$AGENT_URL/health" > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Agent health endpoint reachable${NC}"
else
  echo -e "${RED}✗ Agent health endpoint not reachable${NC}"
fi

# Step 5: Common issues and solutions
echo -e "\n${YELLOW}[5/5] Common Issues & Solutions${NC}"

echo -e "\n${BLUE}Issue: "Failed to fetch" error in frontend${NC}"
echo "Causes:"
echo "  1. VITE_GATEWAY_URL not set or incorrect"
echo "  2. Gateway CORS not allowing frontend origin"
echo "  3. Gateway service is down or restarting"
echo ""
echo "Solutions:"
echo "  1. Verify VITE_GATEWAY_URL in frontend .env"
echo "  2. Check ALLOWED_ORIGINS in gateway"
echo "  3. Trigger frontend redeploy"

echo -e "\n${BLUE}Issue: Gateway cannot reach Agent${NC}"
echo "Causes:"
echo "  1. AGENT_URL not configured in gateway"
echo "  2. Agent service is down"
echo "  3. Network connectivity issue"
echo ""
echo "Solutions:"
echo "  1. Set AGENT_URL in gateway environment"
echo "  2. Check agent service status"
echo "  3. Verify agent is responding to requests"

# Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. ${BLUE}Check Frontend Logs:${NC}"
echo "   You'll need access to Render dashboard or:"
echo "   gh run logs --repo joseph-c-mcguire/Vecinitafrontend"
echo ""
echo "2. ${BLUE}Check Gateway Logs:${NC}"
echo "   View recent deployments and errors"
echo ""
echo "3. ${BLUE}Check Agent Logs:${NC}"
echo "   Verify agent is running and connectable"
echo ""
echo "4. ${BLUE}Common Fix - Redeploy Services${NC}"
echo "   Sometimes services get stuck:"
echo "   gh workflow run deploy.yml --repo joseph-c-mcguire/Vecinitafrontend --ref main"
echo ""
echo "5. ${BLUE}Environment Variables Check${NC}"
echo "   Make sure all URLs are correct:"
echo "   - Frontend VITE_GATEWAY_URL: $GATEWAY_URL"
echo "   - Gateway AGENT_URL: $AGENT_URL"
echo "   - Gateway ALLOWED_ORIGINS: $FRONTEND_URL"
echo ""
