# Data Management API - Environment Variables Reference

## Canonical Template Files

- Local development shared template: `.env.local.example`
- Render production shared template: `.env.prod.render.example`
- Render staging shared template: `.env.staging.render.example`

Copy templates into real environment files/secrets and never commit populated credentials.

## Exact Variables Required

On Render, `vecinita-data-management-api-v1` runs the [`services/scraper`](services/scraper) image. Besides Modal tokens, **`SCRAPER_API_KEYS` is required** in production or the process raises `ConfigError` on startup.

| Render Env Var | Notes |
|---|---|
| `DATABASE_URL` | Usually injected by root `render.yaml` `fromDatabase` |
| `SCRAPER_API_KEYS` | **Required** — comma-separated Bearer secrets; same values callers send as `Authorization: Bearer …` |
| `VECINITA_EMBEDDING_API_URL` | **Required** by scraper config validation |
| `CORS_ORIGINS` | **Required** for browser clients |
| `ENVIRONMENT` | Set to `production` on Render (see `render.yaml`) |
| `MODAL_TOKEN_ID` | Map from local `MODAL_API_TOKEN_ID` if you use that name locally |
| `MODAL_TOKEN_SECRET` | Map from local `MODAL_API_TOKEN_SECRET` |
| `MODAL_WORKSPACE` | Optional; e.g. `vecinita` |

## Optional / compatibility

| Render Env Var | Purpose |
|---|---|
| `VECINITA_MODEL_API_URL` | Model service URL when used |
| `DB_URL` | Optional fallback if `DATABASE_URL` is unset (same DSN) |
| `DEV_ADMIN_BEARER_TOKEN` | Optional extra accepted Bearer (see scraper `AuthConfig`) |
| `SCRAPER_DEBUG_BYPASS_AUTH` | Must stay `false` in prod |

## Copy-Paste Ready (placeholders only)

**For Render Dashboard Environment Tab** (replace with your real secrets):

```
MODAL_TOKEN_ID=ak-your-token-id
MODAL_TOKEN_SECRET=as-your-token-secret
SCRAPER_API_KEYS=your-first-key,your-second-key-optional
```

## What the Code Expects

The data-management API reads these exact environment variable names from `config.py`:

```python
# From services/scraper/src/vecinita_scraper/core/config.py — ModalConfig / AuthConfig
ModalConfig(
    token_id=os.getenv("MODAL_TOKEN_ID", ""),
    token_secret=os.getenv("MODAL_TOKEN_SECRET", ""),
    workspace=os.getenv("MODAL_WORKSPACE", ""),
)
```

**Note:** The API looks for `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`, not the longer `MODAL_API_TOKEN_ID` format from your `.env`.

## How Scripts Transform Variables

Both automated scripts (`setup-render-env.sh` and `apply-render-env-api.sh`) do this transformation:

1. Read from `.env`: `MODAL_API_TOKEN_ID` and `MODAL_API_TOKEN_SECRET`
2. Transform to: `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`
3. Apply to Render service

## Verification

Once set, the service will:
1. Load these variables on startup
2. Use them to authenticate with Modal services
3. Respond to health checks: `curl https://vecinita-data-management-api-v1.onrender.com/health`

Expected response:
```json
{
  "status": "ok",
  "modal_authenticated": true
}
```

## Service Details

- **Service ID**: `srv-d7a6477kijhs7395eneg`
- **Service Name**: `vecinita-data-management-api-v1`
- **Dashboard**: https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg
- **Config File**: `services/scraper/src/vecinita_scraper/core/config.py`
