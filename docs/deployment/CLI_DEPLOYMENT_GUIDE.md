# CLI-Based Deployment Guide for Data Management System

## Quick Start with GitHub CLI + Render CLI

### Prerequisites

```bash
# Verify CLIs are installed
which gh        # Should output: /usr/bin/gh
which render    # Should output: /usr/local/bin/render

# Authenticate with GitHub
gh auth login
gh auth status  # Verify authentication

# Set Render API key (get from https://dashboard.render.com/account/api-tokens)
export RENDER_API_KEY="rk_live_xxxxxxxxxxxxx"
```

---

## Deployment Strategies

### Strategy 1: Automatic GitHub Actions (Recommended for CI/CD)

The repos have `deploy.yml` workflows that auto-deploy on push to main.

**Trigger workflow manually via CLI:**

```bash
# Deploy backend (vecinita-modal-proxy)
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --ref main

# Deploy frontend (vecinita-data-management-frontend)
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --ref main
```

**Check workflow status:**

```bash
# List recent runs
gh run list \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml \
  -L 5

# Watch a specific run
gh run watch <RUN_ID> \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management
```

---

### Strategy 2: Root Repo Orchestrator (Coordinated Multi-Repo Deploy)

Deploy both services together with the orchestrator workflow.

**Trigger orchestrator:**

```bash
gh workflow run multi-repo-release-orchestrator.yml \
  --repo acadiagit/vecinita \
  --ref main \
  -f deploy_data_management_frontend=true \
  -f deploy_data_management_api=true \
  -f target_ref=main \
  -f wait_for_completion=true
```

**Monitor orchestrator:**

```bash
gh run list \
  --repo acadiagit/vecinita \
  --workflow multi-repo-release-orchestrator.yml \
  -L 1

gh run watch <RUN_ID> --repo acadiagit/vecinita
```

---

### Strategy 3: Direct Render CLI (For Simple Redeploys)

Use Render CLI to trigger deploys directly without GitHub Actions.

**Prerequisites:**
- Know your Render service IDs (from dashboard)
- Have RENDER_API_KEY set

**List Render services:**

```bash
# Note: Exact commands depend on Render CLI version
# This is a typical pattern:
render services list

# Or via Render API directly (if render CLI doesn't support list):
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services | jq '.[]'
```

**Trigger a deploy (example):**

```bash
# Using Render API directly (more reliable than CLI)
SERVICE_ID="srv_xxxxxxxxxxxxx"  # vecinita-modal-proxy

curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$SERVICE_ID/deploys

# Or if using deploy hooks (simpler):
curl -X POST https://api.render.com/deploy/srv-xxxxx?key=yyyyy
```

---

## Complete Deployment Workflow

### Step 1: Prepare Repos

```bash
# Ensure repos are on main and up to date
cd ~/GitHub/VECINA/vecinita
git fetch origin
git status

# Check backend repo
cd apps/data-management-backend/  # Or wherever the backend is
git fetch origin main
git status
```

### Step 2: Set Up GitHub Actions Secrets

**Add Render deploy hook URLs (if using auto-deploy):**

```bash
# Get hook URLs from Render dashboard:
# Settings → Deploy Hook for each service

# Set secrets in backend repo
gh secret set RENDER_DEPLOY_HOOK_URL \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  -b 'https://api.render.com/deploy/srv-xxxxx?key=yyyyy'

# Set secrets in frontend repo
gh secret set RENDER_DEPLOY_HOOK_URL \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  -b 'https://api.render.com/deploy/srv-xxxxx?key=yyyyy'

# Verify secrets are set
gh secret list --repo Math-Data-Justice-Collaborative/vecinita-data-management
gh secret list --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend
```

### Step 3: Set Up Render Environment Variables

**View current env vars:**

```bash
# Using Render API to get service details
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv_xxxxx" | jq '.envVars'
```

**Set env vars via API:**

```bash
# For backend (vecinita-modal-proxy)
BACKEND_SERVICE_ID="srv_xxxxxxxxxxxxx"

curl -X PATCH \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.render.com/v1/services/$BACKEND_SERVICE_ID \
  -d '{
    "envVars": [
      {
        "key": "MODAL_TOKEN_ID",
        "value": "tok-xxxxx"
      },
      {
        "key": "MODAL_TOKEN_SECRET",
        "value": "sk-xxxxx"
      },
      {
        "key": "VECINITA_SCRAPER_API_URL",
        "value": "https://vecinita-scraper--latest.modal.run/"
      },
      {
        "key": "CORS_ORIGINS",
        "value": "https://vecinita-data-management-frontend.onrender.com"
      }
    ]
  }'

# For frontend (vecinita-data-management-frontend)
FRONTEND_SERVICE_ID="srv_xxxxxxxxxxxxx"

curl -X PATCH \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.render.com/v1/services/$FRONTEND_SERVICE_ID \
  -d '{
    "envVars": [
      {
        "key": "VITE_VECINITA_SCRAPER_API_URL",
        "value": "https://vecinita-modal-proxy.onrender.com"
      }
    ]
  }'
```

### Step 4: Deploy Backend First

```bash
# Option A: Via GitHub Actions
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --ref main

# Option B: Via Render API
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_backend_id/deploys

# Monitor progress
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management --workflow deploy.yml -L 1
gh run watch <RUN_ID> --repo Math-Data-Justice-Collaborative/vecinita-data-management
```

### Step 5: Deploy Frontend

```bash
# Option A: Via GitHub Actions
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --ref main

# Option B: Via Render API
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv_frontend_id/deploys

# Monitor progress
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend --workflow deploy.yml -L 1
gh run watch <RUN_ID> --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend
```

### Step 6: Verify Deployment

```bash
# Check service status via Render API
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv_backend_id" | jq '.status'

curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  "https://api.render.com/v1/services/srv_frontend_id" | jq '.status'

# Health checks
curl https://vecinita-modal-proxy.onrender.com/health
curl https://vecinita-data-management-frontend.onrender.com
```

---

## Using Render MCP (Model Context Protocol)

If Render MCP tools are available, you can use them for advanced management:

```bash
# Example: Query services via MCP
# (Exact commands depend on MCP implementation)

# Deploy a service
mcp_render_deploy_service --service-id srv_xxxxx --ref main

# Get service details
mcp_render_get_service --service-id srv_xxxxx

# Update environment variables
mcp_render_set_env_vars --service-id srv_xxxxx --vars CORS_ORIGINS=...
```

---

## Useful CLI Commands Reference

### GitHub CLI

```bash
# List workflows in a repo
gh workflow list --repo OWNER/REPO

# Trigger a workflow
gh workflow run WORKFLOW_FILE.yml --repo OWNER/REPO --ref BRANCH -f KEY=VALUE

# List recent runs
gh run list --repo OWNER/REPO --workflow WORKFLOW_FILE.yml -L 10

# Watch a run in real-time
gh run watch RUN_ID --repo OWNER/REPO

# View run logs
gh run view RUN_ID --repo OWNER/REPO --log

# Get run status
gh run view RUN_ID --repo OWNER/REPO --json status

# View available secrets
gh secret list --repo OWNER/REPO

# Set a secret
gh secret set SECRET_NAME --repo OWNER/REPO -b 'secret-value'

# Delete a secret
gh secret delete SECRET_NAME --repo OWNER/REPO
```

### Render API via curl

```bash
# List all services
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services

# Get service details
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/SERVICE_ID

# Trigger a deploy
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/SERVICE_ID/deploys

# Get deployment status
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/SERVICE_ID/deploys

# Update environment variables
curl -X PATCH \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.render.com/v1/services/SERVICE_ID \
  -d '{"envVars": [{"key": "KEY", "value": "VALUE"}]}'
```

---

## Troubleshooting

### GitHub Actions Workflow Not Found

```bash
# List available workflows
gh workflow list --repo OWNER/REPO

# Check if deploy.yml exists in the right repo
gh api repos/OWNER/REPO/contents/.github/workflows/deploy.yml
```

### RENDER_API_KEY Not Working

```bash
# Verify token format (should start with rk_live_)
echo $RENDER_API_KEY | head -c 20

# Test API connection
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services \
  -w "\nHTTP Status: %{http_code}\n"
```

### Service Not Deploying

```bash
# Check service status
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/SERVICE_ID | jq '.status, .notificationEmail'

# View recent deployments
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/SERVICE_ID/deploys | jq '.[]' | head -20
```

---

## Summary

| Task | Command |
|------|---------|
| **Deploy via GitHub Actions** | `gh workflow run deploy.yml --repo OWNER/REPO --ref main` |
| **Deploy via Orchestrator** | `gh workflow run multi-repo-release-orchestrator.yml --repo acadiagit/vecinita --ref main -f deploy_data_management_api=true -f deploy_data_management_frontend=true` |
| **Check deployment status** | `gh run list --repo OWNER/REPO --workflow deploy.yml -L 5` |
| **Set Render secret** | `gh secret set RENDER_DEPLOY_HOOK_URL --repo OWNER/REPO -b 'url'` |
| **Get Render services** | `curl -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services` |
| **Trigger Render deploy** | `curl -X POST -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services/ID/deploys` |

