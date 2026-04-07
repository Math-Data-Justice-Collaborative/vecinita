# Data Management API - Complete Setup Guide

## Current Status

| Component | Status | Details |
|-----------|--------|---------|
| **Frontend** | ✅ Live | https://vecinita-data-management-frontend-v1.onrender.com |
| **API Service** | ⏳ Deployed (awaiting config) | https://vecinita-data-management-api-v1.onrender.com |
| **Environment Variables** | ❌ Not Set | Blocking API startup |

## What's Needed

The data-management API service needs 3 environment variables to start responding:

```
MODAL_TOKEN_ID=ak-1YjGmfYdtX7etaGwRqxkTa
MODAL_TOKEN_SECRET=as-tELxaoFAqbkNeOKSNY1sVu
VECINITA_SCRAPER_API_URL=https://vecinita--vecinita-scraper-web-app.modal.run
```

**All values are in your `.env` file** — the scripts will extract them automatically.

---

## Setup Methods (Choose One)

### Method 1: Render Dashboard (Manual, No Code)
**Best for**: One-time setup, no automation needed

1. Go to: https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg
2. Click **Environment** tab
3. Click **Add Environment Variable** three times:
   - `MODAL_TOKEN_ID` = `ak-1YjGmfYdtX7etaGwRqxkTa`
   - `MODAL_TOKEN_SECRET` = `as-tELxaoFAqbkNeOKSNY1sVu`
   - `VECINITA_SCRAPER_API_URL` = `https://vecinita--vecinita-scraper-web-app.modal.run`
4. Click **Save**
5. Service auto-redeploys

---

### Method 2: Render CLI (Recommended for Future Use)
**Best for**: Automation, CI/CD integration

**Step 1: Authorize CLI**
```bash
render login
```
- Browser will prompt for authorization
- If no browser available, manually visit:
  - https://dashboard.render.com/device-authorization/[CODE]
  - And authorize there

**Step 2: Apply Variables**
```bash
./scripts/setup-render-env.sh
```

The script will:
- Verify CLI is authenticated
- Load credentials from `.env`
- Ask for confirmation
- Apply to service
- Provide verification command

---

### Method 3: Render API (Automated, Most Flexible)
**Best for**: CI/CD pipelines, no CLI needed

**Step 1: Get API Key**
- Go to: https://dashboard.render.com/api-keys
- Create new API key
- Copy it

**Step 2: Apply Variables**
```bash
RENDER_API_KEY="your-api-key" ./scripts/apply-render-env-api.sh
```

The script will:
- Take your API key from environment
- Extract credentials from `.env`
- Call Render API directly
- Show success/failure status
- Provide verification command

---

## Verification (All Methods)

After applying variables, test the API:

```bash
curl https://vecinita-data-management-api-v1.onrender.com/health
```

**Expected response** (service healthy):
```json
{
  "status": "ok",
  "modal_reachable": true,
  "upstream_reachable": {
    "scraper": true
  }
}
```

**If you get connection timeout**: Service is still redeploying (wait 30-60 seconds, try again)

**If you get 500 error**: Variables didn't apply or are incorrect (double-check via dashboard)

---

## Reference

| Component | Location |
|-----------|----------|
| Setup Scripts | `./scripts/setup-render-env.sh` and `./scripts/apply-render-env-api.sh` |
| Dashboard | https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg |
| API Key Generator | https://dashboard.render.com/api-keys |
| Device Authorization | https://dashboard.render.com/device-authorization/H31Z-FL12-1YOP-GI0U |
| Credentials Source | `.env` file (local) |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "exec: xdg-open not found" | Run `render login` and manually visit device auth URL |
| "RENDER_API_KEY not set" | Get key from https://dashboard.render.com/api-keys |
| "Service not found (404)" | Verify Service ID: `srv-d7a6477kijhs7395eneg` |
| "Connection timeout" | Service is redeploying, wait 60 seconds |
| "401 Unauthorized" | API key is invalid or expired |
| Script won't run | `chmod +x scripts/*.sh` |

---

## Architecture Overview

```
User Browser
    ↓
Frontend (Render) ── VITE_VECINITA_SCRAPER_API_URL ──→ API (Render)
                                                          ↓
                                                    VECINITA_SCRAPER_API_URL
                                                          ↓
                                                    Scraper (Modal)
```

**Frontend** calls **API** → **API** calls **Scraper** → All using Modal credentials

---

## Next Steps After Setup

1. **Verify API is responding** → `curl /health`
2. **Test scraper endpoint** → `curl /scrape`
3. **Test data sync** → Check API logs in dashboard
4. **Wire frontend if needed** → Already configured to use API URL
5. **Monitor in production** → https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg/logs

---

## Files Created

- `./scripts/setup-render-env.sh` — CLI-based setup
- `./scripts/apply-render-env-api.sh` — API-based setup
- `./scripts/RENDER_SCRIPTS_README.md` — Script documentation
- `./RENDER_LOGIN_INSTRUCTIONS.md` — CLI login help
- `./DEPLOY_DATA_MANAGEMENT_API.md` — Original deployment guide
