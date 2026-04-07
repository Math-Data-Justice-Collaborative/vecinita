# Render Environment Scripts

This directory contains helper scripts for managing Render service deployments.

## Scripts

### `setup-render-env.sh`

**Purpose**: Interactive setup of environment variables using Render CLI

**Requirements**:
- `render` CLI installed and authenticated (`render login`)
- `.env` file with Modal credentials
- Bash shell

**Usage**:
```bash
./scripts/setup-render-env.sh
```

**What it does**:
1. Verifies Render CLI is installed and authenticated
2. Reads Modal credentials from `.env` file
3. Shows what will be set and asks for confirmation
4. Attempts to set variables via Render API (requires RENDER_API_KEY)
5. Falls back to manual dashboard instructions if API key not available
6. Provides verification command

**Best for**: Local development and manual deployments

---

### `apply-render-env-api.sh`

**Purpose**: Automated environment variable setup via Render API

**Requirements**:
- `RENDER_API_KEY` environment variable set
- `.env` file with Modal credentials
- `curl` command available
- Bash shell

**Usage**:
```bash
RENDER_API_KEY="your-api-key" ./scripts/apply-render-env-api.sh
```

**What it does**:
1. Validates API key and .env file exist
2. Extracts Modal credentials from `.env`
3. Shows what will be set and prompts for confirmation
4. Calls Render API to set environment variables
5. Reports success/failure with HTTP status code
6. Provides verification command

**Best for**: CI/CD pipelines and automated deployments

---

## Environment Variables Used

Both scripts extract these variables from `.env`:

| Variable | Source | Purpose |
|----------|--------|---------|
| `MODAL_API_TOKEN_ID` | `.env` | Modal API authentication |
| `MODAL_API_TOKEN_SECRET` | `.env` | Modal API secret key |
| `VECINITA_SCRAPER_API_URL` | `.env` or inferred | Scraper backend URL |

## Render API Key

To get a RENDER_API_KEY:
1. Go to https://dashboard.render.com/api-keys
2. Create a new API key
3. Copy and store securely
4. Set as environment variable: `export RENDER_API_KEY="your-key"`

## Service IDs

- **vecinita-data-management-api-v1**: `srv-d7a6477kijhs7395eneg`

## Troubleshooting

### "Render CLI not authorized"
```bash
render login
```

### "RENDER_API_KEY not set"
```bash
export RENDER_API_KEY="<your-key>"
```

### "Service not found (404)"
Check that the SERVICE_ID is correct:
```bash
render services --output json
```

### API returns 401
Your RENDER_API_KEY may be expired or invalid. Generate a new one at https://dashboard.render.com/api-keys

## Manual Dashboard Method

If neither script works, set variables manually:
1. Go to https://dashboard.render.com/web/srv-d7a6477kijhs7395eneg
2. Click **Environment** tab
3. Add variables from `.env` file
4. Click **Save**

Service will auto-redeploy with new variables.
