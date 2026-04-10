# Data Management API - Environment Variables Reference

## Canonical Template Files

- Local development shared template: `.env.local.example`
- Render production shared template: `.env.prod.render.example`
- Render staging shared template: `.env.staging.render.example`

Copy templates into real environment files/secrets and never commit populated credentials.

## Exact Variables Required

Set these 3 environment variables on Render for `vecinita-data-management-api-v1`:

| Render Env Var | Value from `.env` | Value |
|---|---|---|
| `MODAL_TOKEN_ID` | `MODAL_API_TOKEN_ID` | `ak-1YjGmfYdtX7etaGwRqxkTa` |
| `MODAL_TOKEN_SECRET` | `MODAL_API_TOKEN_SECRET` | `as-tELxaoFAqbkNeOKSNY1sVu` |
| `MODAL_WORKSPACE` | (optional) | Leave blank or set to `vecinita` |

## Optional Variables (for advanced features)

| Render Env Var | Source | Purpose |
|---|---|---|
| `VECINITA_EMBEDDING_API_URL` | `.env` line 149 | Custom embedding service URL |
| `VECINITA_MODEL_API_URL` | `.env` line 148 | Custom model service URL |
| `DATABASE_URL` | `.env` | Postgres for data persistence |
| `SCRAPER_API_KEYS` | Render env group/secret | Comma-separated Bearer API keys accepted by scraper API |
| `SCRAPER_DEBUG_BYPASS_AUTH` | local/dev only | `true` bypasses auth in local/dev/test only; must remain `false` in staging/prod |

## Copy-Paste Ready

**For Render Dashboard Environment Tab:**
```
MODAL_TOKEN_ID=ak-1YjGmfYdtX7etaGwRqxkTa
MODAL_TOKEN_SECRET=as-tELxaoFAqbkNeOKSNY1sVu
```

## What the Code Expects

The data-management API reads these exact environment variable names from `config.py`:

```python
# From vecinita_scraper.core.config.py (line 112-116)
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
- **Config File**: `/root/GitHub/VECINA/vecinita/services/data-management-api/apps/backend/scraper-service/src/vecinita_scraper/core/config.py`
