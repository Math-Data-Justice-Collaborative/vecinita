# Infrastructure Plan: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/src/vecinita/app.py`, `modal-apps/embedding-modal/.github/workflows/deploy.yml`

## Overview

The embedding worker runs entirely on Modal as a serverless function app. There is no Dockerfile, no Kubernetes, no Render deployment. Modal handles container provisioning, scaling, and lifecycle.

## Deployment Platform

| Attribute | Value |
|-----------|-------|
| Platform | Modal |
| Type | Serverless functions |
| Compute | Default CPU (no GPU) |
| Scaling | Auto (Modal-managed) |
| Region | Modal default (US) |

## Container Image

| Property | Value |
|----------|-------|
| Base | `debian_slim` (Modal built-in) |
| Python | 3.11 |
| Pip packages | `fastembed>=0.7.4` |
| Image size | ~200MB (estimated) |

```python
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    ["fastembed>=0.7.4"]
)
```

Modal caches built images. Rebuilds only occur when the image definition changes.

## Storage

| Resource | Type | Name | Mount | Purpose |
|----------|------|------|-------|---------|
| Model cache | Modal Volume | `embedding-models` | `/models` | Persist downloaded model weights |

Volume is created automatically on first deployment (`create_if_missing=True`). Model files (~100MB for BAAI/bge-small-en-v1.5) persist indefinitely.

## Functions

| Function | Timeout | Compute | Volume | Description |
|----------|---------|---------|--------|-------------|
| `embed_query` | 600s | Default CPU | `/models` | Single text → embedding |
| `embed_batch` | 600s | Default CPU | `/models` | Batch texts → embeddings |

## Deployment

### Manual Deployment

```bash
export MODAL_TOKEN_ID=...
export MODAL_TOKEN_SECRET=...
modal deploy src/vecinita/app.py
```

### CI/CD Deployment

Source: `modal-apps/embedding-modal/.github/workflows/deploy.yml`

| Trigger | Condition |
|---------|-----------|
| Push to `main` | Automatic |
| `workflow_dispatch` | Manual trigger |

Pipeline: Lint → Test → Verify Modal credentials → `modal deploy main.py`

| Secret | Source | Required |
|--------|--------|----------|
| `MODAL_TOKEN_ID` | GitHub Secrets (`MODAL_TOKEN_ID` or `MODAL_AUTH_KEY`) | Yes |
| `MODAL_TOKEN_SECRET` | GitHub Secrets (`MODAL_TOKEN_SECRET` or `MODAL_AUTH_SECRET`) | Yes |
| `MODAL_PROFILE` | GitHub Secrets/Vars (`MODAL_API_PROFILE`, default: `vecinita`) | Optional |

Concurrency: `group: deploy-main`, `cancel-in-progress: true` — only one deploy runs at a time.

## Scaling and Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Cold start | ~5-10s | Model load from Volume |
| Warm latency | <2s | Per query |
| Invocations/day | 50-500 | Typical load |
| Concurrent containers | Auto-scaled by Modal | Based on demand |
| Idle timeout | Modal default | Containers recycled after inactivity |

## Observability

| Capability | Implementation |
|------------|---------------|
| Logging | `logging` module → stderr → Modal log viewer |
| Log level | INFO for `vecinita.*` package |
| Input logging | Truncated text preview (240 chars max) |
| Output logging | Model name, dimension, first 4 floats |
| Metrics | Modal dashboard (invocations, duration, errors) |
| Alerting | Not configured (use Modal dashboard) |

## Security

| Aspect | Implementation |
|--------|---------------|
| Authentication | Modal token pair (SDK-level) |
| Network access | No inbound ports exposed (Modal-managed) |
| Secrets | `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` in CI via GitHub Secrets |
| No external calls | Service makes no outbound API calls (model cached locally) |

## Disaster Recovery

| Scenario | Recovery |
|----------|----------|
| Container failure | Modal auto-restarts on next invocation |
| Volume corruption | Delete Volume → recreate → model re-downloads on next cold start |
| Deploy failure | Previous version remains active until successful deploy |
| Credential rotation | Update GitHub Secrets → redeploy |

## Cost Considerations

| Factor | Impact |
|--------|--------|
| Compute tier | Default CPU (lowest tier) |
| Volume storage | ~100MB (model cache) — minimal cost |
| Invocation volume | 50-500/day — well within free/low-cost tier |
| No GPU | Significant cost savings vs GPU-based alternatives |

See: [Architecture](07-architecture.md) | [Modal Integration Plan](13-modal-integration-plan.md) | [Technical Decisions](10-technical-decisions.md)
