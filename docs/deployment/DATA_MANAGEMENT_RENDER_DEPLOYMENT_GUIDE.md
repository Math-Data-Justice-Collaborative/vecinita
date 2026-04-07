# Data Management System Render Deployment Guide

## Quick Summary

This guide provides step-by-step instructions for deploying the data management frontend and backend (proxy) to Render. The deployment follows the canonical multi-repo architecture with the proxy service (vecinita-modal-proxy) handling API routing and the frontend static site consuming the proxy URL.

---

## Architecture

```
User Browser
    ↓
vecinita-data-management-frontend (Render Static Site)
    ↓ HTTP Calls with VITE_VECINITA_SCRAPER_API_URL
vecinita-modal-proxy (Render Web Service)
    ↓ Routes to Modal endpoints
├─ vecinita-scraper (Modal)
├─ vecinita-embedding (Modal)
└─ vecinita-model (Modal)
```

---

## Deployment Steps

### Phase 1: Backend Deployment (vecinita-modal-proxy)

**Why first?** The frontend needs the proxy URL at build time.

#### 1. Create Render Web Service

1. Log into [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect GitHub: Select `Math-Data-Justice-Collaborative/vecinita-data-management`
4. Configure:
   - **Service name:** `vecinita-modal-proxy`
   - **Environment:** Production
   - **Region:** Virginia (US-VA)
   - **Build command:** Auto-detected or `pip install -r requirements.txt`
   - **Start command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service** (initial deploy will start automatically)

#### 2. Set Environment Variables

After creation, navigate to **Service → Environment** and add:

| Variable | Value | Notes |
|----------|-------|-------|
| `MODAL_TOKEN_ID` | `<your-token-id>` | From Modal workspace settings |
| `MODAL_TOKEN_SECRET` | `<your-token-secret>` | From Modal workspace settings |
| `VECINITA_SCRAPER_API_URL` | `https://vecinita-scraper--latest.modal.run/` | Modal scraper endpoint |
| `VECINITA_MODEL_API_URL` | `https://vecinita-model--latest.modal.run/` | Optional; Modal model endpoint |
| `VECINITA_EMBEDDING_API_URL` | `https://vecinita-embedding--latest.modal.run/` | Optional; Modal embedding endpoint |
| `CORS_ORIGINS` | `https://localhost:5173` | Temporary; will update after frontend deploy |
| `ENVIRONMENT` | `production` | |
| `LOG_LEVEL` | `INFO` | |

#### 3. Capture the Proxy URL

Once deployed (check **Live** status), copy the proxy service URL from the dashboard:
```
https://vecinita-modal-proxy.onrender.com
```

Save this for frontend configuration.

---

### Phase 2: Frontend Deployment (vecinita-data-management-frontend)

#### 1. Create Render Static Site

1. In Render Dashboard, click **New +** → **Static Site**
2. Connect GitHub: Select `Math-Data-Justice-Collaborative/vecinita-data-management-frontend`
3. Configure:
   - **Service name:** `vecinita-data-management-frontend`
   - **Build command:** `npm ci && npm run build`
   - **Publish directory:** `./dist`
   - **Environment:** Production
   - **Region:** Virginia (US-VA)
4. Click **Create Static Site**

#### 2. Set Environment Variables

Navigate to **Service → Environment** and add:

| Variable | Value | Notes |
|----------|-------|-------|
| `VITE_VECINITA_SCRAPER_API_URL` | `https://vecinita-modal-proxy.onrender.com` | The proxy URL from Phase 1 |
| `VITE_DEFAULT_SCRAPER_USER_ID` | `frontend-user` | Optional; default user ID for jobs |

#### 3. Capture the Frontend URL

Once deployed (check **Live** status), copy the frontend service URL:
```
https://vecinita-data-management-frontend.onrender.com
```

Save this for proxy CORS configuration.

---

### Phase 3: Cross-Service Configuration

#### 1. Update Proxy CORS Settings

Go back to **vecinita-modal-proxy** → **Environment** and update:

```
CORS_ORIGINS=https://vecinita-data-management-frontend.onrender.com
```

This allows the frontend to make browser requests to the proxy without CORS errors.

#### 2. Verify Health Checks

From your terminal:
```bash
# Check proxy health
curl https://vecinita-modal-proxy.onrender.com/health

# Check frontend loads
curl https://vecinita-data-management-frontend.onrender.com
```

---

## Continuous Deployment Setup

### GitHub Actions Deploy Hooks

To automate future deployments:

#### 1. Get Deploy Hook URLs from Render

For each Render service:
- Navigate to **Settings → Deploy Hook**
- Copy the hook URL (format: `https://api.render.com/deploy/srv-xxxxx?key=yyyyy`)

#### 2. Set GitHub Actions Secrets

**In `Math-Data-Justice-Collaborative/vecinita-data-management`:**
- Go to **Settings → Secrets and variables → Actions**
- Click **New repository secret**
- Name: `RENDER_DEPLOY_HOOK_URL`
- Value: Paste the proxy deploy hook URL

**In `Math-Data-Justice-Collaborative/vecinita-data-management-frontend`:**
- Go to **Settings → Secrets and variables → Actions**
- Click **New repository secret**
- Name: `RENDER_DEPLOY_HOOK_URL`
- Value: Paste the frontend deploy hook URL

#### 3. Workflow Behavior

Both repos have `deploy.yml` workflows that:
- Trigger on push to `main` branch
- Run linting, type checks, and tests
- Call the Render deploy hook if all checks pass
- Deployment completes in ~2-3 minutes per service

---

## Orchestrated Deployment (Multi-Repo)

For coordinated deploys of both services:

1. In root repo (`acadiagit/vecinita`), go to **Actions → Multi-Repo Release Orchestrator**
2. Click **Run workflow**
3. Configure:
   ```
   deploy_data_management_frontend: true
   deploy_data_management_api: true
   target_ref: main
   wait_for_completion: true
   ```
4. Click **Run workflow**

The orchestrator dispatches workflows to both repos and waits for completion.

---

## Environment Variables Summary

### Frontend (Build-Time — Baked into JavaScript)

| Variable | Purpose | Example |
|----------|---------|---------|
| `VITE_VECINITA_SCRAPER_API_URL` | **Required.** Proxy service URL for API calls | `https://vecinita-modal-proxy.onrender.com` |
| `VITE_DEFAULT_SCRAPER_USER_ID` | Optional user ID prefix for job tracking | `frontend-user` |

### Proxy (Runtime — Configurable Anytime)

| Variable | Purpose | Example |
|----------|---------|---------|
| `MODAL_TOKEN_ID` | **Required.** Modal workspace authentication | `tok-xxxxx` |
| `MODAL_TOKEN_SECRET` | **Required.** Modal workspace secret | `sk-xxxxx` |
| `VECINITA_SCRAPER_API_URL` | **Required.** Scraper Modal endpoint | `https://vecinita-scraper--latest.modal.run/` |
| `CORS_ORIGINS` | **Required.** Allowed browser origins (CORS) | `https://vecinita-data-management-frontend.onrender.com` |
| `VECINITA_MODEL_API_URL` | Optional. Model Modal endpoint | `https://vecinita-model--latest.modal.run/` |
| `VECINITA_EMBEDDING_API_URL` | Optional. Embedding Modal endpoint | `https://vecinita-embedding--latest.modal.run/` |
| `ENVIRONMENT` | Runtime environment label | `production` |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARN, ERROR) | `INFO` |
| `UPSTREAM_TIMEOUT_SECONDS` | Timeout for Modal calls | `55` |

---

## Troubleshooting

### Frontend Shows "API Not Configured" Banner

**Cause:** `VITE_VECINITA_SCRAPER_API_URL` is not set or incorrect.

**Fix:**
1. Go to frontend service → **Environment**
2. Verify `VITE_VECINITA_SCRAPER_API_URL` is set to the proxy URL
3. Trigger a new deploy (frontend must rebuild with the correct value)

### Proxy Returns 401 on Requests

**Cause:** Modal authentication tokens expired or invalid.

**Fix:**
1. Go to proxy service → **Environment**
2. Update `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` from Modal workspace
3. Restart the service or wait for automatic redeploy

### CORS Errors in Browser Console

**Cause:** `CORS_ORIGINS` on proxy doesn't match frontend URL.

**Fix:**
1. Go to proxy service → **Environment**
2. Update `CORS_ORIGINS` to the exact frontend URL from Render
3. Restart the service

### Deployment Fails with Build Error

**Solution:**
1. Check **Logs** tab in Render dashboard for the specific error
2. For build errors, verify:
   - `requirements.txt` (backend) or `package.json` (frontend) are present
   - Python/Node.js versions are compatible
   - All environment variables marked **Required** are set
3. Fix the error in the repo and push to trigger a redeploy

### Rollback to Previous Version

1. In Render dashboard, go to Service → **Deployments**
2. Find the last successful deployment
3. Click the three-dot menu → **Redeploy**

---

## Health Checks & Monitoring

### Endpoint Health

```bash
# Proxy health/status endpoint
curl https://vecinita-modal-proxy.onrender.com/health

# Modal scraper health (direct)
curl https://vecinita-scraper--latest.modal.run/health
```

### View Logs

- **Proxy logs:** Render dashboard → vecinita-modal-proxy → **Logs**
- **Frontend logs:** Render dashboard → vecinita-data-management-frontend → **Logs**
- **Build logs:** Render dashboard → Service → **Build & Deploy** (oldest entries first)

### Monitoring Checklist

- [ ] Frontend loads without banner
- [ ] Proxy health endpoint returns 200
- [ ] CORS headers allow frontend origin
- [ ] Modal endpoints are reachable from proxy
- [ ] E2E test: Submit a scraping job from frontend UI

---

## Security Notes

- **CORS_ORIGINS:** Never set to `*` in production. Always use explicit frontend URL.
- **PROXY_AUTH_TOKEN:** Optional shared secret. If set, frontend must send `X-Proxy-Token` header.
- **Modal Tokens:** Treat `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` as secrets. Never commit them. Rotate periodically.
- **Environment Variables:** All are encrypted at rest in Render and in GitHub Actions secrets.

---

## Next Steps

1. ✅ Deploy backend (vecinita-modal-proxy)
2. ✅ Deploy frontend (vecinita-data-management-frontend)
3. ✅ Configure CORS
4. ✅ Set up GitHub Actions deploy hooks
5. ✅ Test end-to-end flow
6. Test submitting a scraping job from the frontend UI
7. Monitor logs and health endpoints

For questions or issues, check the multi-repo orchestrator docs in `MULTI_REPO_CICD_ORCHESTRATION.md`.
