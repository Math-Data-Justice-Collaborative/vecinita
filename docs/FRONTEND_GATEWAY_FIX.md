# Frontend "Failed to fetch" Error - Fix Implementation Guide

## Problem Summary

**Error:** "Failed to fetch the Gateway is connected to the frontend and agent"

**Root Cause:** The frontend is trying to fetch from `/api` or `http://localhost:8004/api/v1` which don't exist in production.

**Why:** The environment variable `VITE_GATEWAY_URL` is not set to the actual deployed gateway URL (`https://vecinita-gateway-prod-v5.onrender.com/api/v1`) in the Render frontend service.

---

## Architecture & Data Flow

```
Browser (frontend.onrender.com)
    ↓ HTTP request to /api/v1/ask
    ↗ NOT WORKING: Falls back to localhost:8004 (doesn't exist)
    
✓ CORRECT FLOW:
Browser (frontend.onrender.com)
    ↓ HTTP request to https://gateway-prod-v5.onrender.com/api/v1/ask
    ↓ Gateway routes to Agent (langgraph service)
    ↓ Agent processes query and returns response
```

---

## Implementation Steps

### Step 1: Update Frontend Environment Variable in Render Dashboard

1. **Log into Render Dashboard** → https://dashboard.render.com
2. **Navigate to Frontend Service** → `vecinita-frontend`
3. **Go to Environment** section
4. **Add or Update** the following environment variable:
   - **Name:** `VITE_GATEWAY_URL`
   - **Value:** `https://vecinita-gateway-prod-v5.onrender.com/api/v1`
5. **Save** changes

**Why this matters:**
- Vite bakes environment variables into the JavaScript bundle at **build time**
- This ensures the compiled frontend knows how to reach the gateway
- Without this, the frontend falls back to a hardcoded `http://localhost:8004` which doesn't exist in production

### Step 2: Verify Gateway Configuration

1. **Log into Render Dashboard** → https://dashboard.render.com
2. **Navigate to Gateway Service** → `vecinita-gateway-prod-v5`
3. **Check Environment Variables:**
   - ✓ `AGENT_URL` should be set to `https://vecinita-agent.onrender.com`
   - ✓ `CORS_ORIGINS` should include `https://vecinita-frontend.onrender.com`
4. **If missing, add them** and save

**Gateway CORS Example:**
```
CORS_ORIGINS=https://vecinita-frontend.onrender.com,https://vecinita-data-management-frontend.onrender.com
```

### Step 3: Trigger Frontend Redeploy

The frontend must be **rebuilt** with the new environment variable. You have two options:

#### Option A: Using GitHub CLI (Recommended)
```bash
gh workflow run deploy.yml \
  --repo joseph-c-mcguire/Vecinitafrontend \
  --ref main
```

#### Option B: Manual Redeploy in Render
1. Open Render Dashboard
2. Navigate to `vecinita-frontend` service
3. Click the **Deploy** button (top right)
4. Select **Redeploy Latest Commit**

#### Option C: Push new commit
```bash
cd frontend
git add .env.production
git commit -m "fix: Configure production gateway URL for Render deployment"
git push origin main
```
This will automatically trigger the deploy workflow.

### Step 4: Wait for Deployment

- **Expected time:** 2-5 minutes
- **Check status:** 
  ```bash
  gh run list --repo joseph-c-mcguire/Vecinitafrontend --workflow deploy.yml -L 1
  ```
- **View logs:** Render Dashboard → `vecinita-frontend` → Logs tab

---

## Verification Checklist

### ✓ Check 1: Frontend Loads
```bash
curl -I https://vecinita-frontend.onrender.com
# Should return 200 OK
```

### ✓ Check 2: Gateway Health
```bash
curl https://vecinita-gateway-prod-v5.onrender.com/health
# Should return health check response
```

### ✓ Check 3: Agent Health
```bash
curl https://vecinita-agent.onrender.com/health
# Should return health check response
```

### ✓ Check 4: Browser Verification (Best Test)
1. Open https://vecinita-frontend.onrender.com in browser
2. **Press F12** to open Developer Console
3. Go to **Network** tab
4. Submit a question in the chat
5. Look for `POST /api/v1/ask` request
   - ✓ Status should be **200** or **201** (success)
   - ✗ Status **404** = Gateway URL not configured
   - ✗ Status **CORS error** = Check gateway CORS_ORIGINS

### ✓ Check 5: Console Check
In the same F12 console, check for errors:
- ✓ No "Failed to fetch" errors
- ✓ No "CORS policy" errors
- ✓ No network timeouts

---

## Troubleshooting

### Problem: Still seeing "Failed to fetch"

**Solution 1: Check if Render deployment completed**
- Go to Render Dashboard → `vecinita-frontend` → Deploys
- Verify the latest deployment shows "Live" status
- If still building, wait and refresh

**Solution 2: Check environment variable was actually set**
- Go to Render Dashboard → `vecinita-frontend` → Environment
- Confirm `VITE_GATEWAY_URL=https://vecinita-gateway-prod-v5.onrender.com/api/v1` is present
- If not, add it and redeploy

**Solution 3: Clear browser cache**
```bash
# In DevTools Console, run:
localStorage.clear()
sessionStorage.clear()
```
Then reload the page.

**Solution 4: Check gateway is actually deployed**
```bash
curl https://vecinita-gateway-prod-v5.onrender.com/health
# If this fails, gateway service is down
```

**Solution 5: Check agent is reachable**
```bash
curl https://vecinita-agent.onrender.com/health
# If this fails, agent service is down
```

### Problem: CORS error in console

**Solution: Update Gateway CORS Configuration**
1. Go to Render Dashboard → `vecinita-gateway-prod-v5`
2. Go to Environment
3. Check `CORS_ORIGINS` includes:
   ```
   https://vecinita-frontend.onrender.com
   ```
4. Save and restart gateway service

### Problem: Gateway returns 404 for /api/v1 routes

**Solution: Check gateway routes are configured**
- Gateway should proxy `/api/v1/*` to agent service
- Verify `AGENT_URL` is set in gateway environment
- Restart gateway service if recently updated

---

## What the Fix Does

### Before (Broken):
```javascript
// agentService.ts line 39-42
const GATEWAY_URL =
  import.meta.env.VITE_GATEWAY_URL ||      // undefined if not set in Render
  import.meta.env.VITE_BACKEND_URL ||      // undefined if not set in Render
  (import.meta.env.DEV ? '/api' : 'http://localhost:8004/api/v1'); // ← Falls back to localhost!
// Result: fetch('http://localhost:8004/api/v1/ask') → Failed to fetch
```

### After (Fixed):
```javascript
// agentService.ts (same code, but with env var set)
const GATEWAY_URL =
  import.meta.env.VITE_GATEWAY_URL ||      // ✓ Set to https://vecinita-gateway-prod-v5.onrender.com/api/v1
  import.meta.env.VITE_BACKEND_URL ||
  (import.meta.env.DEV ? '/api' : 'http://localhost:8004/api/v1');
// Result: fetch('https://vecinita-gateway-prod-v5.onrender.com/api/v1/ask') → ✓ Works!
```

---

## Environment Variables Summary

### Frontend (.env.production)
```
VITE_GATEWAY_URL=https://vecinita-gateway-prod-v5.onrender.com/api/v1
VITE_AGENT_REQUEST_TIMEOUT_MS=90000
VITE_AGENT_STREAM_TIMEOUT_MS=120000
VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS=15000
VITE_ADMIN_AUTH_ENABLED=true
```

### Gateway Service (Render Environment)
```
AGENT_URL=https://vecinita-agent.onrender.com
CORS_ORIGINS=https://vecinita-frontend.onrender.com,https://vecinita-data-management-frontend.onrender.com
DATABASE_URL=postgresql://vecinita_postgres_user:...@dpg-d6or4g2a214c73f6hl20-a.virginia-postgres.render.com/vecinita_postgres
```

### Agent Service (Render Environment)
```
MODEL_URL=https://your-modal-endpoint
DATABASE_URL=postgresql://vecinita_postgres_user:...@dpg-d6or4g2a214c73f6hl20-a.virginia-postgres.render.com/vecinita_postgres
GROQ_API_KEY=your-groq-api-key
```

---

## Quick Reference

| Service | URL | Role |
|---------|-----|------|
| Frontend | https://vecinita-frontend.onrender.com | React/Vite UI |
| Gateway | https://vecinita-gateway-prod-v5.onrender.com | API aggregator, routing |
| Agent | https://vecinita-agent.onrender.com | LangGraph backend |
| Database | dpg-d6or4g2a214c73f6hl20-a.virginia-postgres.render.com | PostgreSQL |

---

## Summary

The fix addresses the broken frontend-to-gateway communication:

1. **Set `VITE_GATEWAY_URL`** in Render frontend environment
2. **Verify gateway configuration** and CORS settings
3. **Trigger redeploy** to rebuild frontend with new env var
4. **Test** by opening frontend and checking network requests

This restores the data flow: **Browser → Gateway → Agent → LLM**

