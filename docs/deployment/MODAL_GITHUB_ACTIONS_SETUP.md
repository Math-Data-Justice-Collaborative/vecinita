# GitHub Actions Modal Deployment Setup

This document explains how to configure GitHub Actions to deploy your Modal applications automatically.

## Prerequisites

- Modal account with valid credentials
- GitHub repository with Admin or Settings access
- Modal CLI installed locally for testing

## Step 1: Obtain Modal Credentials

### Option A: Create a new Modal token

1. Install Modal CLI locally:
```bash
pip install modal
```

2. Authenticate with Modal:
```bash
modal token new
```

3. Follow the web-based authentication flow

4. Find your credentials in `~/.modal/config.toml`:
```toml
[vecinita]  # or your profile name
token_id = "pznLGXAX90k..."
token_secret = "as-Vsu9AfbL..."
```

### Option B: Retrieve existing credentials

If you have Modal credentials already saved:
```bash
cat ~/.modal/config.toml | grep -A 2 vecinita
```

## Step 2: Add Credentials to GitHub

### Using GitHub Web UI:

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `MODAL_TOKEN_ID`:
   - Name: `MODAL_TOKEN_ID`
   - Value: Your token ID (e.g., `pznLGXAX90k...`)
   - Click "Add secret"

4. Repeat for `MODAL_TOKEN_SECRET`:
   - Name: `MODAL_TOKEN_SECRET`
   - Value: Your token secret (e.g., `as-Vsu9AfbL...`)
   - Click "Add secret"

### Using GitHub CLI:

```bash
# Set MODAL_TOKEN_ID
gh secret set MODAL_TOKEN_ID --body "YOUR_TOKEN_ID" --repo owner/repo

# Set MODAL_TOKEN_SECRET
gh secret set MODAL_TOKEN_SECRET --body "YOUR_TOKEN_SECRET" --repo owner/repo

# Verify secrets are set
gh secret list --repo owner/repo | grep MODAL
```

## Step 3: Verify Configuration

Run a manual workflow trigger to test:

```bash
gh workflow run modal-deploy.yml --repo owner/repo
```

Check the workflow results:
```bash
gh run list --workflow modal-deploy.yml --limit 1
```

View detailed logs:
```bash
gh run view RUN_ID --log
```

## Workflow Trigger Events

The `.github/workflows/modal-deploy.yml` workflow is triggered by:

1. **Auto-deploy on code changes** (push to main):
   - Changes to `backend/src/embedding_service/**`
   - Changes to `backend/src/scraper/**`
   - Changes to `backend/requirements.txt`
   - Changes to `.github/workflows/modal-deploy.yml`

2. **Manual trigger** (workflow_dispatch):
   ```bash
   gh workflow run modal-deploy.yml \
     --repo owner/repo \
     -f deploy_embedding=true \
     -f deploy_scraper=true
   ```

## Modal Apps Configuration

The workflow deploys two Modal applications:

### 1. Embedding Service (`backend/src/embedding_service/modal_app.py`)
- **App Name**: `vecinita-embedding` (configurable via `MODAL_EMBEDDING_APP_NAME`)
- **Endpoint**: https://vecinita--vecinita-embedding.modal.run
- **Resources**: 
  - CPU: 1.0
  - Memory: 2048 MB
  - Timeout: 3600s
- **Dependencies**: Retrieved from `modal.Secret.from_name("vecinita-secrets")`

### 2. Scraper Service (`backend/src/scraper/modal_app.py`)
- **App Name**: `vecinita-scraper` (configurable via `MODAL_SCRAPER_APP_NAME`)
- **Endpoint**: https://vecinita--vecinita-scraper.modal.run
- **Features**: Cron jobs for web content re-indexing
- **Dependencies**: Retrieved from `modal.Secret.from_name("vecinita-secrets")`

## Modal Secrets Configuration

Both applications expect a Modal secret named `vecinita-secrets` to be available in your Modal workspace.

### To create Modal secrets:

```bash
modal secret create vecinita-secrets
```

Then add environment variables via Modal dashboard:
- `EMBEDDING_MODEL`: HuggingFace model identifier
- `SUPABASE_URL`: Database connection URL
- `SUPABASE_KEY`: Database API key
- Other service credentials as needed

Or use CLI:
```bash
modal secret create vecinita-secrets \
  --env EMBEDDING_MODEL=BAAI/bge-small-en-v1.5 \
  --env SUPABASE_URL="https://your-db.supabase.co"
```

## Environment Variable Mapping

GitHub Secrets → Workflow Environment → Modal CLI:

```
GitHub Secret: MODAL_TOKEN_ID
  ↓
Workflow Env: MODAL_TOKEN_ID
  ↓
Modal CLI: modal token set --token-id $MODAL_TOKEN_ID
```

## Troubleshooting

### "Modal authentication failed"

**Issue**: `modal token info` returns authentication error

**Solutions**:
1. Verify token is not expired: `modal token new`
2. Check secret values don't have leading/trailing whitespace
3. Verify Modal workspace is active: `modal config`
4. Test locally first:
   ```bash
   modal token set --token-id YOUR_ID --token-secret YOUR_SECRET
   modal token info
   ```

### "Failed to find modal app"

**Issue**: Deployment fails because Modal app doesn't exist

**Solution**: This is expected on first deployment. Modal creates apps on first deployment.

### "Secret 'vecinita-secrets' not found in Modal account"

**Issue**: Modal deployment fails looking for `vecinita-secrets`

**Solution**: Create the secret:
```bash
modal secret create vecinita-secrets
```

Add required environment variables via Modal dashboard.

### Workflow not triggering on code changes

**Verify**:
1. File paths match the trigger configuration in `.github/workflows/modal-deploy.yml`
2. Push is to `main` branch (not a feature branch)
3. Changes include one of the monitored paths:
   - `backend/src/embedding_service/**`
   - `backend/src/scraper/**`
   - `backend/requirements.txt`
   - `.github/workflows/modal-deploy.yml`

## Manual Deployment

If you need to deploy without GitHub:

```bash
# Set credentials locally
modal token set --token-id YOUR_ID --token-secret YOUR_SECRET

# Deploy embedding service
modal deploy backend/src/embedding_service/modal_app.py

# Deploy scraper service
modal deploy backend/src/scraper/modal_app.py

# List deployed apps
modal app list
```

## References

- [Modal Documentation](https://modal.com/docs)
- [Modal Token Management](https://modal.com/docs/reference/modal.token)
- [Modal Python SDK](https://modal.com/docs/guide/deploy)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
