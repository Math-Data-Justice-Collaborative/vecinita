# Data Management System Deployment - Complete Implementation Guide

**Using:** GitHub CLI (gh) + Render CLI + Render API

---

## 📦 What's Been Prepared

We've created comprehensive deployment documentation:

| File | Purpose |
|------|---------|
| **DEPLOYMENT_QUICK_START.md** | ⚡ Fast reference for deployment commands |
| **CLI_DEPLOYMENT_GUIDE.md** | 📚 Complete guide with all CLI options |
| **DATA_MANAGEMENT_RENDER_DEPLOYMENT_GUIDE.md** | 🎯 Step-by-step Render dashboard setup |
| **scripts/deploy-data-management-render.sh** | 🔧 Automated deployment script |

---

## 🚀 Start Here - Deploy in 3 Commands

### Deploy Backend (API)
```bash
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --ref main
```

### Deploy Frontend (Static Site)
```bash
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --ref main
```

### Monitor Deployment
```bash
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml -L 1
```

**That's it!** The workflows will:
1. ✅ Build the services
2. ✅ Run tests/lint
3. ✅ Push to Render via deploy hook
4. ✅ Complete in 2-3 minutes

---

## 🔧 Prerequisites (One-Time Setup)

### 1. GitHub CLI Authentication
```bash
gh auth status
# Should show: ✓ Logged in to github.com
```

### 2. Set GitHub Actions Secrets
Get your Render deploy hook URLs (Render Dashboard → Service → Settings → Deploy Hook):

```bash
# Backend
gh secret set RENDER_DEPLOY_HOOK_URL \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  -b 'https://api.render.com/deploy/srv-XXXXX?key=YYYYY'

# Frontend
gh secret set RENDER_DEPLOY_HOOK_URL \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  -b 'https://api.render.com/deploy/srv-XXXXX?key=YYYYY'
```

### 3. Set Render Environment Variables
In Render Dashboard for each service, set:

**Backend (vecinita-modal-proxy):**
- `MODAL_TOKEN_ID=tok-xxxxx`
- `MODAL_TOKEN_SECRET=sk-xxxxx`
- `VECINITA_SCRAPER_API_URL=https://vecinita-scraper--latest.modal.run/`
- `CORS_ORIGINS=https://vecinita-data-management-frontend.onrender.com`

**Frontend (vecinita-data-management-frontend):**
- `VITE_VECINITA_SCRAPER_API_URL=https://vecinita-modal-proxy.onrender.com`

---

## 📊 Deployment Methods

### Method 1: Individual Service Deploy (Recommended)
Deploy each service independently for control:

```bash
# Backend only
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --ref main

# Frontend only  
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --ref main
```

**Pros:** Control, flexibility, easier debugging
**Cons:** Requires two commands
**Time:** 2-3 minutes per service

---

### Method 2: Orchestrator Deploy (All Services Together)
Deploy both services with root repo orchestrator:

```bash
gh workflow run multi-repo-release-orchestrator.yml \
  --repo acadiagit/vecinita \
  --ref main \
  -f deploy_data_management_api=true \
  -f deploy_data_management_frontend=true \
  -f wait_for_completion=true
```

**Pros:** Coordinated multi-repo deploy, transactional
**Cons:** More complex, slower
**Time:** 5-6 minutes total

---

### Method 3: Render API Direct
Use Render API for advanced control:

```bash
# Set API key
export RENDER_API_KEY="rk_live_xxxxxxxxxxxxx"

# Deploy service
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-xxxx/deploys

# Check status
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-xxxxx/deploys | jq '.[0].status'
```

**Pros:** Direct control, no GitHub Actions needed
**Cons:** Requires API key, more manual
**Time:** Immediate

---

## ✅ Verification Steps

### 1. Check Workflows Running
```bash
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml -L 1 --json status,conclusion

gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --workflow deploy.yml -L 1 --json status,conclusion
```

### 2. Health Check Backend
```bash
curl https://vecinita-modal-proxy.onrender.com/health
# Expected: 200 OK with health status
```

### 3. Health Check Frontend
```bash
curl https://vecinita-data-management-frontend.onrender.com
# Expected: 200 OK with HTML
```

### 4. View Logs
```bash
# Get run ID
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml -L 1 --json databaseId

# View logs
gh run view <RUN_ID> --repo Math-Data-Justice-Collaborative/vecinita-data-management --log | tail -50
```

---

## 🔄 Automatic CI/CD (Set It and Forget It)

Both repos have `deploy.yml` workflows configured to auto-deploy on push to main:

```bash
# Just push to main
cd vecinita-data-management
git add .
git commit -m "Update feature"
git push origin main

# Workflow automatically runs → deploys to Render
# It's that simple!
```

---

## 🎯 Recommended Workflow

### For Development / Testing
1. Push to `dev` branch (doesn't deploy)
2. Create PR to main
3. Merge PR to main (auto-triggers deploy)
4. Monitor with: `gh run watch --repo ...`

### For Production Hotfixes
1. Push to main (auto-triggers deploy)
2. 2-3 minutes later, live

### For Scheduled Deployments
```bash
# Edit .github/workflows/deploy.yml and add:
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

---

## 🚨 Emergency Rollback

### Quick Rollback
```bash
# Find last successful deployment
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --workflow deploy.yml --status success -L 1 --json databaseId

# Rerun it (go back to that version)
gh run rerun <RUN_ID> \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management
```

### Nuclear Option
Redeploy from Render dashboard manually:
1. Dashboard → Service → Deployments
2. Find last working deployment
3. Click "Redeploy"

---

## 📚 Documentation Structure

```
vecinita/
├── DEPLOYMENT_QUICK_START.md                    (← Start here)
├── docs/deployment/
│   ├── CLI_DEPLOYMENT_GUIDE.md                  (← All CLI commands)
│   ├── DATA_MANAGEMENT_RENDER_DEPLOYMENT_GUIDE.md (← UI setup)
│   └── MULTI_REPO_CICD_ORCHESTRATION.md         (← Architecture)
└── scripts/
    └── deploy-data-management-render.sh         (← Automated script)
```

---

## 🎓 Learning Path

### Quick Deploy (5 minutes)
1. Read: `DEPLOYMENT_QUICK_START.md`
2. Run: `gh workflow run deploy.yml ...`
3. Monitor: `gh run list ...`

### Full Understanding (30 minutes)
1. Read: `CLI_DEPLOYMENT_GUIDE.md`
2. Read: `DATA_MANAGEMENT_RENDER_DEPLOYMENT_GUIDE.md`
3. Practice: Try each deployment method

### Deep Dive (1 hour+)
1. Read: `MULTI_REPO_CICD_ORCHESTRATION.md`
2. Study: `.github/workflows/*.yml`
3. Explore: Render API docs

---

## 🔑 CLI Tools Reference

| Tool | Status | Install |
|------|--------|---------|
| **GitHub CLI (gh)** | ✅ Installed | `brew install gh` |
| **Render CLI** | ✅ Installed | `npm install -g @render-as-code/cli` |
| **Render MCP** | ⚙️ Available | Activate via Copilot |

---

## 📞 Support & Troubleshooting

### Problem: Workflow Not Found
**Solution:** Repo must have `.github/workflows/deploy.yml`
```bash
gh api repos/OWNER/REPO/contents/.github/workflows/deploy.yml
```

### Problem: RENDER_DEPLOY_HOOK_URL Not Set
**Solution:** Get from Render Dashboard and set secret
```bash
gh secret set RENDER_DEPLOY_HOOK_URL --repo OWNER/REPO -b 'url'
```

### Problem: Deployment Fails
**Solution:** Check logs
```bash
gh run view <RUN_ID> --repo OWNER/REPO --log
```

### Problem: CORS Errors
**Solution:** Update proxy CORS_ORIGINS to frontend URL
```
CORS_ORIGINS=https://vecinita-data-management-frontend.onrender.com
```

---

## ✨ Key Features of This Setup

✅ **Automated CI/CD** - Push to main → Auto-deploy  
✅ **Multi-repo coordination** - Orchestrator deploys both services  
✅ **CLI-based** - No dashboard clicking needed  
✅ **Health checks** - Automatic verification after deploy  
✅ **Rollback support** - Quick rollback to previous versions  
✅ **Environment variables** - Secure secret management  
✅ **Monitoring** - Real-time logs via GitHub CLI  

---

## 🎉 You're Ready to Deploy!

**Next Step:** Run this command and watch your services deploy:

```bash
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management \
  --ref main
```

Then:

```bash
gh workflow run deploy.yml \
  --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend \
  --ref main
```

**That's it!** Monitor with:

```bash
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management --workflow deploy.yml -L 1
gh run list --repo Math-Data-Justice-Collaborative/vecinita-data-management-frontend --workflow deploy.yml -L 1
```

---

**For detailed commands, see:** `DEPLOYMENT_QUICK_START.md`  
**For full guide, see:** `docs/deployment/CLI_DEPLOYMENT_GUIDE.md`
