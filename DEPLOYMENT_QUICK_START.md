# Data Management Deployment - Quick Reference

## 🚀 Fastest Path to Deploy

### 1. Deploy Backend API (vecinita-modal-proxy)

```bash
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --ref main
```

**Expected output:**
```
✓ Workflow dispatch for deploy.yml created (ID: 12345)
```

### 2. Deploy Frontend (vecinita-data-management-frontend)

```bash
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --ref main
```

### 3. Monitor Progress

```bash
# Backend workflow
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml --limit 1

# Frontend workflow  
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --workflow deploy.yml --limit 1
```

### 4. Watch a Deployment

```bash
# Get the RUN_ID from step 3, then:
gh run watch RUN_ID --repo Math-Data-Justice-Collaborative/vecinita-data-management
```

---

## 🎛️ Alternative: Use Orchestrator (Deploy Both Services Together)

```bash
gh workflow run multi-repo-release-orchestrator.yml \
  --repo acadiagit/vecinita \
  --ref main \
  -f deploy_data_management_api=true \
  -f deploy_data_management_frontend=true
```

**Monitor:**

```bash
gh run watch --repo acadiagit/vecinita \
  --workflow multi-repo-release-orchestrator
```

---

## 🔑 One-Time Setup (If Not Done)

### Set GitHub Actions Secrets

You need your Render deploy hook URLs (from Render dashboard → Service → Settings → Deploy Hook).

```bash
# Backend repo
gh secret set RENDER_DEPLOY_HOOK_URL \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  -b 'https://api.render.com/deploy/srv-xxxxx?key=yyyyy'

# Frontend repo
gh secret set RENDER_DEPLOY_HOOK_URL \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  -b 'https://api.render.com/deploy/srv-xxxxx?key=yyyyy'
```

**Verify:**

```bash
gh secret list --repo Math-Data-Justice-Collaborative/vecinita-data-management
gh secret list --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend
```

---

## 📊 Using Render API Directly (Advanced)

### Prerequisites

```bash
export RENDER_API_KEY="rk_live_xxxxxxxxxxxxx"  # Get from https://dashboard.render.com/account/api-tokens
```

### List Your Services

```bash
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services | jq '.[].name, .[].id'
```

### Deploy a Service

```bash
SERVICE_ID="srv_xxxxxxxxxxxxx"  # Get from list above

curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$SERVICE_ID/deploys
```

### Check Deployment Status

```bash
SERVICE_ID="srv_xxxxxxxxxxxxx"

# Get latest deployment
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$SERVICE_ID/deploys | jq '.[0] | {status, createdAt}'
```

### Set Environment Variables

```bash
SERVICE_ID="srv_xxxxxxxxxxxxx"

curl -X PATCH \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  https://api.render.com/v1/services/$SERVICE_ID \
  -d '{
    "envVars": [
      {"key": "MODAL_TOKEN_ID", "value": "tok-xxxxx"},
      {"key": "MODAL_TOKEN_SECRET", "value": "sk-xxxxx"},
      {"key": "CORS_ORIGINS", "value": "https://vecinita-data-management-frontend.onrender.com"}
    ]
  }'
```

---

## ✅ Verification Steps

### 1. Check GitHub Workflows Ran

```bash
# List last 3 backend deployments
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml --limit 3 --json status,conclusion,updatedAt

# List last 3 frontend deployments
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --workflow deploy.yml --limit 3 --json status,conclusion,updatedAt
```

### 2. Test Backend API

```bash
curl https://vecinita-modal-proxy.onrender.com/health
# Should return: {"status": "ok"} or similar
```

### 3. Test Frontend

```bash
curl https://vecinita-data-management-frontend.onrender.com | head -20
# Should return HTML
```

### 4. Check Logs

```bash
# View last 50 lines of backend logs
gh run view --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  RUN_ID --log | tail -50

# View last 50 lines of frontend logs
gh run view --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  RUN_ID --log | tail -50
```

---

## 🔄 Automating Future Deployments

### Option 1: Auto-Deploy on Main Branch Push

Both repos already have this configured. Just push to main:

```bash
cd vecinita-data-management
git add .
git commit -m "feat: update feature"
git push origin main

# This automatically triggers the deploy.yml workflow
# which calls RENDER_DEPLOY_HOOK_URL
```

### Option 2: Scheduled Deployments

Add this to `.github/workflows/deploy.yml` to auto-deploy daily at 2 AM UTC:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Every day at 2 AM UTC
  push:
    branches: [main]
  workflow_dispatch:
```

### Option 3: Pull Request Previews

Deploy to staging on every PR:

```bash
gh workflow run deploy-staging.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --ref PR_BRANCH
```

---

## 🚨 Rollback / Emergency Redeploy

### Rollback to Previous Version

```bash
# Find the last successful deployment
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml --status success --limit 1 --json databaseId,updatedAt,conclusion

# Rerun that exact commit
gh run rerun RUN_ID \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management
```

### Manual Rollback via Render API

```bash
SERVICE_ID="srv_xxxxxxxxxxxxx"

# Get previous deployment ID
curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$SERVICE_ID/deploys | jq '.[1]'

# Redeploy from previous version
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$SERVICE_ID/deploys \
  -d '{"clearCache": false}'
```

---

## 📋 Deployment Checklist

- [ ] GitHub CLI authenticated: `gh auth status`
- [ ] Render API key set: `echo $RENDER_API_KEY`
- [ ] GitHub Actions secrets configured
- [ ] Render environment variables set (MODAL_TOKEN_ID, etc.)
- [ ] Backend deploy hook URL in GitHub secret
- [ ] Frontend deploy hook URL in GitHub secret
- [ ] Ready to deploy backend
- [ ] Ready to deploy frontend
- [ ] Health checks passing
- [ ] E2E test: submit a job from frontend

---

## 🎯 Next Steps

### Immediate
```bash
# Deploy both services now
gh workflow run deploy.yml --repo Math-Data-Justice-Collaborative/vecinita-data-management --ref main
gh workflow run deploy.yml --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend --ref main

# Monitor
gh run list --limit 1 --repo Math-Data-Justice-Collaborative/vecinita-data-management --workflow deploy.yml
gh run list --limit 1 --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend --workflow deploy.yml
```

### Then
1. Verify health checks pass
2. Test end-to-end workflow from frontend UI
3. Monitor logs for errors

### Documentation
- Full guide: `docs/deployment/CLI_DEPLOYMENT_GUIDE.md`
- Render setup: `docs/deployment/DATA_MANAGEMENT_RENDER_DEPLOYMENT_GUIDE.md`
- Multi-repo orchestration: `docs/deployment/MULTI_REPO_CICD_ORCHESTRATION.md`

