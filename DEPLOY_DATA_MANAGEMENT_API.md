# Data Management API Deployment Instructions

## Current Status

**Frontend**: ✅ LIVE at `https://vecinita-data-management-frontend-v1.onrender.com`  
**API**: ⏳ DEPLOYED but NOT RUNNING (awaiting environment variable configuration)

## API Service Configuration

**Service**: `vecinita-data-management-api-v1`  
**Service ID**: `srv-d7a6477kijhs7395eneg`  
**Dashboard URL**: `https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg`

## Required Environment Variables

The API service requires these environment variables (extracted from `.env`):

```
MODAL_TOKEN_ID=ak-1YjGmfYdtX7etaGwRqxkTa
MODAL_TOKEN_SECRET=as-tELxaoFAqbkNeOKSNY1sVu
VECINITA_SCRAPER_API_URL=https://vecinita--vecinita-scraper-web-app.modal.run
```

## Setup Steps

### Option 1: Via Render Dashboard (Easiest)

1. Go to: `https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg`
2. Click **Environment** tab
3. Click **Add Environment Variable** and add:
   - `MODAL_TOKEN_ID` = `ak-1YjGmfYdtX7etaGwRqxkTa`
   - `MODAL_TOKEN_SECRET` = `as-tELxaoFAqbkNeOKSNY1sVu`
   - `VECINITA_SCRAPER_API_URL` = `https://vecinita--vecinita-scraper-web-app.modal.run`
4. Click **Save**
5. Service will auto-redeploy

### Option 2: Via Render CLI (Recommended for CI/CD)

```bash
# 1. Authenticate with Render CLI
render login

# 2. Run the setup script (extracts values from .env)
./scripts/setup-render-env.sh
```

The script will:
- Load credentials from your `.env` file
- Apply them to the service via Render API
- Display verification instructions

### Option 3: Via Render API (Automated - Requires API Key)

If you have a `RENDER_API_KEY` environment variable:

```bash
# Automatically extracts credentials from .env and applies them
RENDER_API_KEY="<your-key>" ./scripts/apply-render-env-api.sh
```

This script:
- Reads Modal credentials from `.env`
- Calls Render API to set environment variables
- Shows real-time status and verification steps

### Option 4: Manual Curl Command

```bash
export RENDER_API_KEY="<your-api-key>"

curl -X PATCH \
  "https://api.render.com/v1/services/srv-d7a6477kijhs7395eneg" \
  -H "authorization: Bearer ${RENDER_API_KEY}" \
  -H "content-type: application/json" \
  -d '{
    "envVars": [
      {"key": "MODAL_TOKEN_ID", "value": "ak-1YjGmfYdtX7etaGwRqxkTa"},
      {"key": "MODAL_TOKEN_SECRET", "value": "as-tELxaoFAqbkNeOKSNY1sVu"},
      {"key": "VECINITA_SCRAPER_API_URL", "value": "https://vecinita--vecinita-scraper-web-app.modal.run"}
    ]
  }'
```

## Verification

Once variables are set and service restarts:

```bash
curl https://vecinita-data-management-api-v1.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "modal_reachable": true,
  "upstream_reachable": {
    "scraper": true
  },
  "environment": "production"
}
```

## Frontend Wiring

The frontend is already configured to use:
```
VITE_VECINITA_SCRAPER_API_URL=https://vecinita-data-management-api-v1.onrender.com
```

No additional frontend configuration is needed.

## Source Code

- **API**: `https://github.com/Math-Data-Justice-Collaborative/vecinita-modal-proxy`
- **Frontend**: `https://github.com/Math-Data-Justice-Collaborative/vecinita-data-management-frontend`
