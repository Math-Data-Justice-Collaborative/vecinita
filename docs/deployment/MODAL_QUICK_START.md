# Modal CI/CD Quick Start

Deploy Vecinita services to Modal with one click or command.

## Prerequisites

1. **Modal Account**: https://modal.com (free tier available)
2. **Generate Token**: https://modal.com/settings/tokens
3. **Store in GitHub Secrets**

## GitHub Secrets Setup

1. Go to: **Settings → Secrets and variables → Actions**
2. Add two secrets:
   - `MODAL_TOKEN_ID`: Your Modal token ID (from https://modal.com/settings/tokens)
   - `MODAL_TOKEN_SECRET`: Your Modal token secret

## Deploy via GitHub

### Option 1: Automatic (on push)
Just push changes to `main` in these directories:
```
backend/src/embedding_service/**
backend/src/services/scraper/**
```

The workflow `.github/workflows/modal-deploy.yml` automatically deploys.

### Option 2: Manual Trigger
Go to: **Actions → Modal Deployment → Run workflow**

Select what to deploy:
- ☑ Deploy embedding service
- ☑ Deploy scraper service

Click **Run workflow**

## Deploy Locally

```bash
# Install Modal CLI
pip install modal

# Authenticate
modal token new

# Deploy everything
./backend/scripts/deploy_modal.sh --all   # embedding + model + scraper (from services/*)

# Or specific service
./backend/scripts/deploy_modal.sh --embedding
./backend/scripts/deploy_modal.sh --model
./backend/scripts/deploy_modal.sh --scraper
```

## After Deployment

Modal prints `*.modal.run` URLs after deploy (copy from the CLI output or dashboard). The scraper **HTTP** app is typically named ``vecinita-scraper-api`` (ASGI function ``fastapi``).

Update `.env`:
```bash
MODAL_EMBEDDING_ENDPOINT=https://<embedding-asgi-host>
REINDEX_SERVICE_URL=https://<scraper-api-host>/jobs
REINDEX_TRIGGER_TOKEN=<secure-random-token>  # Set in Modal secrets
```

## Monitoring

```bash
# View logs
modal app logs vecinita-embedding --stream
modal app logs vecinita-scraper-api --stream

# Check status
modal app list --all

# List functions
modal function list vecinita-embedding
modal function list vecinita-scraper-api
```

## Troubleshooting

### "Not authenticated with Modal"
```bash
modal token new  # Generate new token
modal token info  # Verify
```

### Deployment fails
```bash
# Check full logs
modal app logs vecinita-embedding
modal app logs vecinita-scraper

# Redeploy
./backend/scripts/deploy_modal.sh --all   # embedding + model + scraper (from services/*)
```

### 401 Unauthorized from embedding service
The service requires auth. Set token in `.env`:
```bash
EMBEDDING_SERVICE_AUTH_TOKEN=<your-token>
```

Or use Modal routing credential:
```bash
modal secret get vecinita-secrets
```

## Full Documentation

See [Modal Deployment Guide](./MODAL_DEPLOYMENT.md) for:
- Detailed setup instructions
- Configuration reference
- Security best practices
- Scaling & performance tuning
- Advanced configuration
