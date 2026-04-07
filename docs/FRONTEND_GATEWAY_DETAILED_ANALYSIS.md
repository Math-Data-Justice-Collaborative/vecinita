# Vecinita Frontend-Gateway Connectivity Issue: Detailed Analysis

## Executive Summary

**Problem:** Frontend cannot fetch from gateway, resulting in "Failed to fetch" errors
**Error Message:** "Failed to load resources: Failed to fetch the Gateway is connected to the frontend and agent"
**Root Cause:** Frontend environment variable `VITE_GATEWAY_URL` not set to deployed gateway URL
**Solution:** Set `VITE_GATEWAY_URL=https://vecinita-gateway-prod-v5.onrender.com/api/v1` in Render dashboard
**Impact:** Blocks all chat functionality and API communication

---

## Architecture Overview

### Deployed Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser / User Client                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    HTTP/HTTPS Request
                           │
                           ▼
        ┌──────────────────────────────┐
        │  FRONTEND (Vite SPA)          │
        │  vecinita-frontend.onrender   │
        │  - React components           │
        │  - Static HTML/CSS/JS         │
        │  - API client library         │
        └────────────┬──────────────────┘
                     │
                     │ API Requests (fetch)
                     │ Should point to:
                     │ VITE_GATEWAY_URL
                     │
                     ▼
        ┌──────────────────────────────┐
        │  GATEWAY API (Express/FastAPI)│
        │  vecinita-gateway-prod-v5    │
        │  - Request routing            │
        │  - API aggregation            │
        │  - CORS handling              │
        │  - Auth verification          │
        └────────────┬──────────────────┘
                     │
                     │ Internal routing
                     │ Routes to AGENT_URL
                     │
                     ▼
        ┌──────────────────────────────┐
        │  AGENT (LangGraph)            │
        │  vecinita-agent.onrender      │
        │  - Vector embeddings          │
        │  - LLM queries                │
        │  - Vector database retrieval  │
        └────────────┬──────────────────┘
                     │
                     │ API call
                     │ GROQ LLM
                     │
                     ▼
        ┌──────────────────────────────┐
        │  GROQ API (External)          │
        │  Llama 3.1 8B LLM             │
        │  - Question answering         │
        │  - Response generation        │
        └──────────────────────────────┘
```

### Problem: Broken Frontend Configuration

```
CURRENT (Broken):

Frontend loads with hardcoded fallback:
  VITE_GATEWAY_URL = http://localhost:8004/api/v1  ❌

Browser tries to fetch:
  POST http://localhost:8004/api/v1/ask/config  ❌
  ✗ Localhost doesn't exist in production
  ✗ "Failed to fetch" error thrown
  ✗ Chat is blocked


FIXED:

Frontend loads with correct gateway URL:
  VITE_GATEWAY_URL = https://vecinita-gateway-prod-v5.onrender.com/api/v1  ✓

Browser tries to fetch:
  POST https://vecinita-gateway-prod-v5.onrender.com/api/v1/ask/config  ✓
  ✓ Reaches actual gateway service
  ✓ Gateway routes to agent
  ✓ Chat works end-to-end
```

---

## Why This Happened: Vite Build-Time Variables

### How Vite Environment Variables Work

Vite is a frontend build tool that processes environment variables at **build time**, not runtime.

```
Build Process:
┌─────────────┐
│  Source Code│  ← import.meta.env.VITE_GATEWAY_URL
│  (TypeScript)│
└──────┬──────┘
       │
       │ Vite Build (reads .env files and Render env vars)
       │
       ▼
┌──────────────────────────────────┐
│  Compiled JavaScript             │
│  (all env vars replaced)         │
│  window.location = "https://..." │  ← Fixed at build time!
└──────────────────────────────────┘
```

### The Problem in the Code

**File:** `frontend/src/app/services/agentService.ts` (lines 39-42)

```typescript
const GATEWAY_URL =
  import.meta.env.VITE_GATEWAY_URL ||           // Check 1: Custom env var
  import.meta.env.VITE_BACKEND_URL ||           // Check 2: Backup env var
  (import.meta.env.DEV ? '/api' : 'http://localhost:8004/api/v1'); // Check 3: Fallback (BAD!)
```

**What happens when Render builds the frontend:**

1. **Render starts build** with no `VITE_GATEWAY_URL` env var set
2. **Vite substitution occurs:**
   - `import.meta.env.VITE_GATEWAY_URL` → `undefined`
   - `import.meta.env.VITE_BACKEND_URL` → `undefined`
   - `import.meta.env.DEV` → `false` (production build)
3. **Compiled JavaScript becomes:**
   ```javascript
   const GATEWAY_URL = 'http://localhost:8004/api/v1';
   ```
4. **Browser tries to use it:**
   ```javascript
   fetch('http://localhost:8004/api/v1/ask')
   // ✗ Failed to fetch - localhost doesn't exist in browser environment!
   ```

### Why the Fallback is Dangerous

The fallback to `http://localhost:8004` was:
- ✓ Good for local development (port forward during `npm run dev`)
- ✗ Catastrophic for production (localhost is undefined)
- ✗ No error message - just silent failure with "Failed to fetch"

---

## The Fix: Setting VITE_GATEWAY_URL

### What Must Be Set

In **Render Dashboard** → **vecinita-frontend** → **Environment**:

```
VITE_GATEWAY_URL=https://vecinita-gateway-prod-v5.onrender.com/api/v1
```

### Why This Works

1. **Render reads** the environment variable
2. **Vite substitution** during build:
   ```typescript
   const GATEWAY_URL = 'https://vecinita-gateway-prod-v5.onrender.com/api/v1';
   ```
3. **Compiled JS** contains the correct URL
4. **Browser fetch** succeeds:
   ```javascript
   POST https://vecinita-gateway-prod-v5.onrender.com/api/v1/ask ✓ Works!
   ```

### Build-Time Verification

After deploying with the env var set, the compiled frontend includes:

```bash
# Check what URL is baked into the frontend
curl -s https://vecinita-frontend.onrender.com | grep -o "vecinita-gateway"

# Output should show references to vecinita-gateway.onrender.com
# NOT references to localhost, 127.0.0.1, or /api proxy
```

---

## Complete Data Flow After Fix

### Request Flow

```
① User opens https://vecinita-frontend.onrender.com
   │
   ├─ Browser loads HTML
   ├─ JavaScript loads with VITE_GATEWAY_URL baked in
   └─ Chat UI renders

② User types question and sends

③ Frontend makes API call:
   fetch('https://vecinita-gateway-prod-v5.onrender.com/api/v1/ask', {
     method: 'POST',
     body: { question: "..." },
     headers: { 'Content-Type': 'application/json' }
   })

④ Browser sends HTTPS request to gateway

⑤ Gateway receives request:
   POST /api/v1/ask
   ├─ Check CORS_ORIGINS (must include frontend URL)
   ├─ Extract Bearer token
   ├─ Route to Agent service (AGENT_URL env var)
   └─ Forward request

⑥ Agent processes request:
   ├─ Generate query embeddings
   ├─ Search vector database for similar docs
   ├─ Build prompt with context
   └─ Call GROQ LLM

⑦ LLM returns response

⑧ Agent streams response back to gateway

⑨ Gateway forwards to frontend

⑩ Frontend displays in chat UI
```

---

## Environment Variables Configuration

### Frontend (.env.production)

Must be set BEFORE Render builds the frontend:

```bash
# CRITICAL: Must point to deployed gateway
VITE_GATEWAY_URL=https://vecinita-gateway-prod-v5.onrender.com/api/v1

# Optional but recommended: Request timeouts
VITE_AGENT_REQUEST_TIMEOUT_MS=90000
VITE_AGENT_STREAM_TIMEOUT_MS=120000
VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS=15000

# Admin authentication
VITE_ADMIN_AUTH_ENABLED=true
```

### Gateway (.env or Render Environment)

Must configured to route properly:

```bash
# Critical: Where to find the agent
AGENT_URL=https://vecinita-agent.onrender.com

# Critical: Allow frontend to fetch from this service
CORS_ORIGINS=https://vecinita-frontend.onrender.com,https://vecinita-data-management-frontend.onrender.com

# Database connection
DATABASE_URL=postgresql://user:pass@host:5432/db

# API authentication
API_KEY_SECRET=your-secret-key
```

### Agent (.env or Render Environment)

Must be configured to process queries:

```bash
# LLM API key
GROQ_API_KEY=your-groq-api-key

# Database connection (same as gateway)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Modal service URL (if using Modal for embedding/scraping)
MODEL_URL=https://your-modal-endpoint
```

---

## Verification Process

### Step 1: Confirm Environment Variable Set

```bash
# Go to Render Dashboard
# vecinita-frontend → Environment
# Verify: VITE_GATEWAY_URL = https://vecinita-gateway-prod-v5.onrender.com/api/v1
```

### Step 2: Trigger Rebuild

The frontend MUST be rebuilt with the new env var. Options:

```bash
# Option A: GitHub CLI
gh workflow run deploy.yml --repo joseph-c-mcguire/Vecinitafrontend --ref main

# Option B: Direct push
git add frontend/.env.production
git commit -m "Configure gateway URL"
git push origin main

# Option C: Render dashboard click Redeploy button
```

### Step 3: Monitor Build

```bash
# Check deployment status
gh run list --repo joseph-c-mcguire/Vecinitafrontend --workflow deploy.yml -L 1

# Expected: Status "completed" with conclusion "success"
```

### Step 4: Test Connectivity

```bash
# Service health checks
curl -I https://vecinita-frontend.onrender.com        # 200 OK
curl https://vecinita-gateway-prod-v5.onrender.com/health  # health response
curl https://vecinita-agent.onrender.com/health       # health response

# Browser test (best way)
# 1. Open https://vecinita-frontend.onrender.com
# 2. F12 → Network tab
# 3. Submit a question
# 4. Look for POST /api/v1/ask request
# 5. Should return 200 OK (not 404, CORS error, or "Failed to fetch")
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Forgetting to Trigger Rebuild

**Problem:** Set VITE_GATEWAY_URL but didn't trigger a new build
**Result:** Frontend still has old hardcoded localhost value
**Solution:** After setting env var, click Redeploy in Render dashboard

### ❌ Mistake 2: Using Relative Path

**Problem:** Setting `VITE_GATEWAY_URL=/api` in production
**Result:** Browser interprets as relative to frontend domain: `https://frontend.onrender.com/api`
**Solution:** Use absolute URL: `https://gateway.onrender.com/api/v1`

### ❌ Mistake 3: Wrong Gateway URL

**Problem:** Setting to wrong gateway address (e.g., staging instead of production)
**Result:** Frontend connects to wrong backend services
**Solution:** Verify gateway URL: `https://vecinita-gateway-prod-v5.onrender.com/api/v1`

### ❌ Mistake 4: Missing CORS Configuration

**Problem:** Set VITE_GATEWAY_URL correctly, but gateway CORS_ORIGINS doesn't include frontend
**Result:** Browser blocks request with CORS error
**Solution:** Set `CORS_ORIGINS=https://vecinita-frontend.onrender.com` in gateway

### ❌ Mistake 5: Clearing Browser Cache Forgot

**Problem:** Deployed new frontend, but browser still serving cached old version
**Result:** Still see "Failed to fetch" with old URL
**Solution:** Hard refresh (Ctrl+Shift+R) or clear cache completely

---

## Technical Deep Dive: Why Relative Paths Don't Work

### Development vs. Production

```
DEVELOPMENT:
├─ Frontend runs on http://localhost:5173 (Vite dev server)
├─ Backend runs on http://localhost:8004 (FastAPI)
├─ Vite proxy translates /api → http://localhost:8004
└─ Works because both are local

PRODUCTION:
├─ Frontend on https://vecinita-frontend.onrender.com (static site)
├─ Gateway on https://vecinita-gateway-prod-v5.onrender.com (separate service)
├─ /api → ??? (no proxy, different domain!)
├─ Browser blocks cross-origin fetch unless CORS headers present
└─ Must use absolute URL with CORS configuration
```

### CORS (Cross-Origin Resource Sharing)

When frontend and backend are on **different domains**, browser enforces CORS:

```
Browser safety mechanism:
┌─────────────────────────┐
│ Request to different    │
│ origin not allowed!     │
│                         │
│ Origin: frontend.com    │
│ Target: gateway.com     │
│ → BLOCKED               │
└─────────────────────────┘

Unless gateway returns:
Access-Control-Allow-Origin: https://frontend.onrender.com
```

This is why the gateway must have `CORS_ORIGINS` configured correctly.

---

## Summary

| Aspect | Details |
|--------|---------|
| **Error** | "Failed to fetch" when frontend tries to reach /api |
| **Root Cause** | `VITE_GATEWAY_URL` not set, falls back to `localhost:8004` |
| **Fix** | Set `VITE_GATEWAY_URL=https://vecinita-gateway-prod-v5.onrender.com/api/v1` |
| **When Set** | In Render Dashboard environment variables |
| **When Compiled** | Into JavaScript during `npm run build` |
| **Requirements** | Rebuild frontend after setting env var |
| **Verification** | After deployment, check browser Network tab for 200 status |

---

## References

- **Vite Documentation:** https://vitejs.dev/guide/env-and-mode.html
- **CORS Documentation:** https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- **Render Documentation:** https://render.com/docs
- **Frontend Service Code:** [frontend/src/app/services/agentService.ts](frontend/src/app/services/agentService.ts)
- **Local Fix Guide:** [docs/FRONTEND_GATEWAY_FIX.md](docs/FRONTEND_GATEWAY_FIX.md)

