#!/bin/bash

# Data Management System Render Deployment Script
# Uses: GitHub CLI (gh), Render CLI (render), and environment variables
# Deploys: vecinita-modal-proxy (backend) and vecinita-data-management-frontend (frontend)

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Data Management System - Render Deployment                   ║${NC}"
echo -e "${BLUE}║  Using: GitHub CLI + Render CLI + Render MCP                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Check prerequisites
echo -e "\n${YELLOW}[1/8] Checking prerequisites...${NC}"

# Check gh CLI
if ! command -v gh &> /dev/null; then
  echo -e "${RED}✗ GitHub CLI (gh) is not installed${NC}"
  exit 1
fi
echo -e "${GREEN}✓ GitHub CLI found${NC}"

# Check render CLI
if ! command -v render &> /dev/null; then
  echo -e "${RED}✗ Render CLI is not installed${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Render CLI found${NC}"

# Check required environment variables
echo -e "\n${YELLOW}[2/8] Verifying authentication...${NC}"

if ! gh auth status &> /dev/null; then
  echo -e "${RED}✗ GitHub CLI not authenticated. Run: gh auth login${NC}"
  exit 1
fi
echo -e "${GREEN}✓ GitHub CLI authenticated${NC}"

# Check Render API token
if [ -z "${RENDER_API_KEY:-}" ]; then
  echo -e "${YELLOW}⚠ RENDER_API_KEY not set${NC}"
  echo -e "${YELLOW}   Set it with: export RENDER_API_KEY='your-api-key'${NC}"
  echo -e "${YELLOW}   Get it from: https://dashboard.render.com/account/api-tokens${NC}"
else
  echo -e "${GREEN}✓ RENDER_API_KEY is set${NC}"
fi

# Get repo information
BACKEND_REPO="Math-Data-Justice-Collaborative/vecinita-data-management"
FRONTEND_REPO="Math-Data-Justice-Collaborative/vecinita-data-management-frontend"
ROOT_REPO="acadiagit/vecinita"

echo -e "\n${YELLOW}[3/8] Repository Status${NC}"

# Check backend repo status
echo -e "\n${BLUE}Backend Repository: ${BACKEND_REPO}${NC}"
gh api repos/$BACKEND_REPO --jq '.name, .description, .default_branch' 2>/dev/null || \
  echo -e "${YELLOW}Could not fetch backend repo info${NC}"

# Check frontend repo status
echo -e "\n${BLUE}Frontend Repository: ${FRONTEND_REPO}${NC}"
gh api repos/$FRONTEND_REPO --jq '.name, .description, .default_branch' 2>/dev/null || \
  echo -e "${YELLOW}Could not fetch frontend repo info${NC}"

# Check for recent commits
echo -e "\n${YELLOW}[4/8] Recent Commits${NC}"

echo -e "\n${BLUE}Backend recent commit:${NC}"
gh api repos/$BACKEND_REPO/commits/main --jq '.commit.message, .commit.author.name, .commit.author.date' 2>/dev/null || \
  echo -e "${YELLOW}Could not fetch backend commits${NC}"

echo -e "\n${BLUE}Frontend recent commit:${NC}"
gh api repos/$FRONTEND_REPO/commits/main --jq '.commit.message, .commit.author.name, .commit.author.date' 2>/dev/null || \
  echo -e "${YELLOW}Could not fetch frontend commits${NC}"

# Get GitHub Actions secrets (check if deploy hook URLs are set)
echo -e "\n${YELLOW}[5/8] Checking GitHub Actions Secrets${NC}"

echo -e "\n${BLUE}Backend repo secrets:${NC}"
gh secret list --repo $BACKEND_REPO 2>/dev/null | grep -i render || \
  echo -e "${YELLOW}No RENDER_DEPLOY_HOOK_URL found in backend repo${NC}"

echo -e "\n${BLUE}Frontend repo secrets:${NC}"
gh secret list --repo $FRONTEND_REPO 2>/dev/null | grep -i render || \
  echo -e "${YELLOW}No RENDER_DEPLOY_HOOK_URL found in frontend repo${NC}"

# Deployment strategy - trigger GitHub Actions workflows
echo -e "\n${YELLOW}[6/8] Triggering GitHub Actions Workflows${NC}"

echo -e "\n${BLUE}Backend Deployment (vecinita-modal-proxy):${NC}"
gh workflow run deploy.yml \
  --repo $BACKEND_REPO \
  --ref main \
  2>&1 | head -5 || \
  echo -e "${YELLOW}Could not trigger backend workflow (may not exist)${NC}"

echo -e "\n${BLUE}Frontend Deployment (vecinita-data-management-frontend):${NC}"
gh workflow run deploy.yml \
  --repo $FRONTEND_REPO \
  --ref main \
  2>&1 | head -5 || \
  echo -e "${YELLOW}Could not trigger frontend workflow (may not exist)${NC}"

# Alternative: Use Render CLI to trigger deploys directly
echo -e "\n${YELLOW}[7/8] Render Service Status (if RENDER_API_KEY is set)${NC}"

if [ -n "${RENDER_API_KEY:-}" ]; then
  echo -e "\n${BLUE}Attempting to query Render services...${NC}"
  
  # Note: render CLI usage depends on Render's specific CLI commands
  # This is an example - adjust based on actual Render CLI API
  echo -e "${YELLOW}Render CLI connection test (non-interactive):${NC}"
  render --version 2>&1 || echo -e "${YELLOW}Render CLI version check incomplete${NC}"
  
  echo -e "\n${BLUE}Services to deploy:${NC}"
  echo "  • vecinita-modal-proxy (backend API on Render)"
  echo "  • vecinita-data-management-frontend (static site on Render)"
else
  echo -e "${YELLOW}Skipping Render service check (RENDER_API_KEY not set)${NC}"
fi

# Summary and next steps
echo -e "\n${YELLOW}[8/8] Deployment Summary${NC}"

echo -e "\n${GREEN}✓ Checks complete${NC}"

echo -e "\n${BLUE}Deployment Methods Available:${NC}"
echo ""
echo "1. ${YELLOW}Automatic GitHub Actions (Recommended)${NC}"
echo "   Each repo has a deploy.yml workflow that:"
echo "   • Runs on push to main branch"
echo "   • Executes linting, type checks, tests"
echo "   • Calls RENDER_DEPLOY_HOOK_URL if configured"
echo "   • Rollout: ~2-3 minutes per service"
echo ""
echo "2. ${YELLOW}Root Repo Orchestrator${NC}"
echo "   Coordinated multi-repo deployment:"
echo "   gh workflow run multi-repo-release-orchestrator.yml \\"
echo "     --repo $ROOT_REPO \\"
echo "     --ref main"
echo ""
echo "3. ${YELLOW}Manual Render Dashboard${NC}"
echo "   https://dashboard.render.com"
echo "   • Manual redeploy from dashboard"
echo "   • Real-time log monitoring"
echo "   • Environment variable management"
echo ""

echo -e "\n${BLUE}Required Setup Steps (if not done):${NC}"
echo ""
echo "1. Set GitHub Actions Secrets:"
echo "   gh secret set RENDER_DEPLOY_HOOK_URL \\"
echo "     --repo $BACKEND_REPO \\"
echo "     -b '<proxy-deploy-hook-url>'"
echo ""
echo "   gh secret set RENDER_DEPLOY_HOOK_URL \\"
echo "     --repo $FRONTEND_REPO \\"
echo "     -b '<frontend-deploy-hook-url>'"
echo ""
echo "2. Set Render Environment Variables (in dashboard):"
echo "   Backend (vecinita-modal-proxy):"
echo "     • MODAL_TOKEN_ID"
echo "     • MODAL_TOKEN_SECRET"
echo "     • VECINITA_SCRAPER_API_URL"
echo "     • CORS_ORIGINS (after frontend deploy)"
echo ""
echo "   Frontend (vecinita-data-management-frontend):"
echo "     • VITE_VECINITA_SCRAPER_API_URL (set to proxy URL)"
echo ""

echo -e "\n${BLUE}Status Check Commands:${NC}"
echo ""
echo "# Check backend workflow status:"
echo "gh run list --repo $BACKEND_REPO --workflow deploy.yml -L 5"
echo ""
echo "# Check frontend workflow status:"
echo "gh run list --repo $FRONTEND_REPO --workflow deploy.yml -L 5"
echo ""
echo "# Trigger orchestrator (root repo):"
echo "gh workflow run multi-repo-release-orchestrator.yml --repo $ROOT_REPO"
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Deployment script complete. Ready to proceed with deployment.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}\n"
