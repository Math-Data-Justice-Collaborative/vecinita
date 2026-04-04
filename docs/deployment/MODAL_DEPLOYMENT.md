# Modal Deployment Guide

## Overview

Vecinita has two key services deployed on Modal:
- **Embedding Service**: Generates text embeddings using sentence-transformers
- **Scraper Service**: Periodically scrapes and re-indexes content via scheduled cron jobs

## Architecture

```
Frontend (React)
    ↓
API Gateway (FastAPI @ :8004)
    ├── Q&A Router → Agent Service (LangGraph @ :8000)
    ├── Embed Router → Modal Embedding Service
    ├── Scrape Router → Backend + Modal Scraper Service
    └── Ask Router → Question answering

Modal Services:
├── vecinita-embedding (ASGI app)
│   └── Runs FastAPI embedding service
│   └── Endpoint: /embed, /batch, /config, /health
│   └── Auth: Modal routing secret or custom token
│
└── vecinita-scraper (ASGI app + Cron jobs)
    ├── HTTP endpoint: /health, /reindex
    ├── Cron job: weekly_reindex() - scheduled scraping
    └── Auth: REINDEX_TRIGGER_TOKEN header
```

## Prerequisites

1. **Modal Account**: Create at https://modal.com
2. **Modal CLI**: `pip install modal`
3. **Modal Token**: Generate at https://modal.com/settings/tokens
4. **GitHub Secrets** (for CI/CD): `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`

## Local Development

For local development, use the local embedding service (no Modal required):

```bash
# Terminal 1: Embedding service (FastAPI)
cd backend
python -m uvicorn src.embedding_service.main:app --reload --port 8001

# Terminal 2: API gateway
python -m uvicorn src.api.main:app --reload --port 8004

# Terminal 3: Agent service (if needed)
python -m src.agent.main  # Starts on :8000
```

Set in `.env`:
```env
EMBEDDING_SERVICE_URL=http://localhost:8001
REINDEX_SERVICE_URL=  # Optional for local testing
```

## Manual Modal Deployment

### Step 1: Authenticate with Modal

```bash
# Generate and authenticate with Modal
modal token new

# Verify authentication
modal token info
```

### Step 2: Deploy Services

```bash
# Deploy both services
./backend/scripts/deploy_modal.sh --all

# Or deploy individually:
./backend/scripts/deploy_modal.sh --embedding  # Just embedding service
./backend/scripts/deploy_modal.sh --scraper    # Just scraper service
```

### Step 3: Configure Environment

After deployment, Modal returns URLs like:
- `https://vecinita--vecinita-embedding-web-app.modal.run`
- `https://vecinita--vecinita-scraper-web-app-api.modal.run`

Update `.env`:
```env
MODAL_EMBEDDING_ENDPOINT=https://vecinita--vecinita-embedding-web-app.modal.run
REINDEX_SERVICE_URL=https://vecinita--vecinita-scraper-web-app-api.modal.run
REINDEX_TRIGGER_TOKEN=<your-secure-token>  # Set in Modal secret
```

### Step 4: Test Deployments

```bash
# Test embedding service
curl https://vecinita--vecinita-embedding.modal.run/health

# Test scraper service
curl https://vecinita--vecinita-scraper.modal.run/health

# Verify from Modal CLI
modal app list --all
```

## GitHub Actions CI/CD

The `.github/workflows/modal-deploy.yml` workflow automatically deploys to Modal on:
- **Push to main** with changes to Modal app files
- **Manual workflow dispatch** (Actions → Modal Deployment → Run)

### Setup GitHub Secrets

1. Go to **Settings → Secrets and variables → Actions**
2. Add:
   - `MODAL_TOKEN_ID`: Your Modal token ID
   - `MODAL_TOKEN_SECRET`: Your Modal token secret

### Workflow Triggers

The workflow deploys when:
```yaml
paths:
  - backend/src/embedding_service/**
  - backend/src/scraper/**
  - backend/requirements.txt
  - .github/workflows/modal-deploy.yml
```

Manual trigger:
```bash
gh workflow run modal-deploy.yml \
  -f deploy_embedding=true \
  -f deploy_scraper=true
```

## Environment Variables

### Development (Local Services)

```env
EMBEDDING_SERVICE_URL=http://localhost:8001
EMBEDDING_SERVICE_AUTH_TOKEN=  # Optional, empty for local
REINDEX_SERVICE_URL=  # Optional for local testing
```

### Production (Modal Services)

```env
# Modal credentials (for deployment only, not runtime)
MODAL_API_TOKEN_ID=<your-token-id>
MODAL_API_TOKEN_SECRET=<your-token-secret>

# Runtime endpoints
MODAL_EMBEDDING_ENDPOINT=https://vecinita--vecinita-embedding.modal.run
REINDEX_SERVICE_URL=https://vecinita--vecinita-scraper.modal.run
REINDEX_TRIGGER_TOKEN=<your-secret-token>

# Optional: Override defaults
EMBEDDING_SERVICE_AUTH_TOKEN=${MODAL_TOKEN_SECRET}  # For secured endpoints
```

### Variable Resolution Order

The API gateway resolves URLs with this precedence:

For embedding service:
1. `MODAL_EMBEDDING_ENDPOINT` (Modal-hosted)
2. `EMBEDDING_SERVICE_URL` (fallback)
3. `http://localhost:8001` (default)

For auth tokens:
1. `EMBEDDING_SERVICE_AUTH_TOKEN` (explicit)
2. `MODAL_TOKEN_SECRET` (Modal routing token)
3. `MODAL_API_KEY` (Modal API key)
4. `MODAL_API_TOKEN_SECRET` (fallback)

## Troubleshooting

### Modal Authentication Error

```
Error: Not authenticated with Modal. Run: modal token new
```

**Solution**: Generate a new token at https://modal.com/settings/tokens

### Deployment Failed

Check logs with:
```bash
modal app list --all  # List all apps
modal app logs vecinita-embedding  # Stream logs
modal app logs vecinita-scraper
```

### 401 Unauthorized on Embedding Endpoint

**Cause**: Missing or incorrect auth token when `EMBEDDING_SERVICE_AUTH_TOKEN` is configured.

**Solution**: 
```bash
# Get routing secret from Modal app
modal secret get vecinita-secrets

# Or use explicit token
export EMBEDDING_SERVICE_AUTH_TOKEN=<token>
export MODAL_TOKEN_SECRET=<token>
```

### Endpoint Returns 404

**Cause**: App not deployed or wrong URL.

**Solution**:
```bash
# Check deployment status
modal app list --all

# Redeploy if needed
./backend/scripts/deploy_modal.sh --all
```

## Monitoring & Logs

### View Live Logs

```bash
# Embedding service
modal app logs vecinita-embedding --stream

# Scraper service  
modal app logs vecinita-scraper --stream
```

### Check Function Status

```bash
# List all functions in an app
modal function list vecinita-embedding

# Get function details
modal function show vecinita-embedding.web_app
modal function show vecinita-scraper.run_reindex
```

### Scheduled Jobs

The scraper runs on cron schedule (default: `0 2 * * 0` = Sunday 2 AM UTC):

```bash
# View scheduled runs
modal function logs vecinita-scraper.weekly_reindex --stream

# Manually trigger reindex
curl -X POST https://vecinita--vecinita-scraper.modal.run/reindex \
  -H "x-reindex-token: <REINDEX_TRIGGER_TOKEN>"
```

## Security

### Secrets Management

Modal secrets are configured per-app and referenced in `modal_app.py`:

```python
@modal.asgi_app()
def web_app():
    # Access secrets via env vars inside Modal function
    token = os.getenv("REINDEX_TRIGGER_TOKEN")
    # ...
```

**To set secrets:**
```bash
# Create modal-secrets
echo "REINDEX_TRIGGER_TOKEN=<your-secure-random-token>" | modal secret create vecinita-secrets

# Update existing secrets
echo "REINDEX_TRIGGER_TOKEN=<new-token>" | modal secret update vecinita-secrets
```

### Token Security

1. Never commit Modal tokens to git
2. Store in `.env.local` (not `.env`)
3. Use GitHub Secrets for CI/CD only
4. Rotate tokens regularly
5. Use `REINDEX_TRIGGER_TOKEN` for public endpoints

## Scaling & Performance

### Embedding Service

Current config:
```python
@modal.function(
    cpu=1.0,
    memory=2048,
    timeout=3600,
)
```

To scale:
- Increase `cpu` for faster embeddings
- Increase `memory` for larger models
- Add `concurrency_limit` for request batching

### Scraper Service

Current config:
```python
@modal.function(
    cpu=2.0,
    memory=4096,
    timeout=3 * 60 * 60,
)
```

For larger scrapes:
- Increase `memory` for parallel scraping
- Adjust `REINDEX_CRON_SCHEDULE` for frequency
- Set `SCRAPER_REINDEX_CLEAN=true` for full re-index

## Advanced Configuration

### Custom Embedding Models

```bash
# Update model in .env
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_PROVIDER=sentence-transformers  # or 'fastembed'

# Redeploy
./backend/scripts/deploy_modal.sh --embedding
```

### Custom Cron Schedule

```bash
# 2 AM UTC, every Sunday
REINDEX_CRON_SCHEDULE=0 2 * * 0

# 6 AM UTC, every day
REINDEX_CRON_SCHEDULE=0 6 * * *

# Disable scheduled runs (manual only)
REINDEX_CRON_SCHEDULE=  # Empty to disable
```

### Multi-Region Deployment

Modal supports regional deployment; configure in `modal_app.py`:
```python
@modal.asgi_app(region="us-west-2")
def web_app():
    # ...
```

## Related Documentation

- [Modal Documentation](https://modal.com/docs)
- [Vecinita Architecture](./docs/architecture/)
- [API Gateway Documentation](./backend/src/api/README.md)
- [Embedding Service API](./backend/src/embedding_service/README.md)
