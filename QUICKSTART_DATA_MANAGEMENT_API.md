# Quick Start: Data Management API Setup

**TL;DR** — Apply environment variables to the Render service in 2 minutes.

## Your Device Authorization Code
```
H31Z-FL12-1YOP-GI0U
```

---

## Option A: Dashboard (Fastest)

1. Open: https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg
2. Go to **Environment** tab
3. Add these 3 variables (values from your `.env`):
   ```
   MODAL_TOKEN_ID=ak-1YjGmfYdtX7etaGwRqxkTa
   MODAL_TOKEN_SECRET=as-tELxaoFAqbkNeOKSNY1sVu
   VECINITA_SCRAPER_API_URL=https://vecinita--vecinita-scraper-web-app.modal.run
   ```
4. Click **Save** → Done!

---

## Option B: Render CLI

```bash
# 1. Authorize CLI (complete device auth code in browser)
render login

# 2. Apply variables from .env automatically
./scripts/setup-render-env.sh
```

---

## Option C: Render API

```bash
# Get your API key from https://dashboard.render.com/api-keys
# Then run:
RENDER_API_KEY="your-key" ./scripts/apply-render-env-api.sh
```

---

## Verify It Works

After any method above, run:
```bash
curl https://vecinita-data-management-api-v1.onrender.com/health
```

Should return `{"status":"ok",...}`

---

## Environment Variables

See [ENV_VARIABLES_REFERENCE.md](./ENV_VARIABLES_REFERENCE.md) for exact variable names and transformations.

## Full Documentation

- [Complete Setup Guide](./DATA_MANAGEMENT_SETUP_COMPLETE.md)
- [Environment Variables Reference](./ENV_VARIABLES_REFERENCE.md)
- [Script Details](./scripts/RENDER_SCRIPTS_README.md)
- [CLI Login Help](./RENDER_LOGIN_INSTRUCTIONS.md)
