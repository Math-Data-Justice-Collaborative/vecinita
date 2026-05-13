# Infrastructure Plan: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker will be deployed **exclusively on Modal** as a serverless GPU service. It has no Dockerfile, no container registry, and no persistent server. Infrastructure concerns focus on Modal configuration, GPU provisioning, shared volumes, and database connectivity.

## Deployment Platform

| Property | Value |
|----------|-------|
| Platform | Modal (serverless) |
| Region | Modal default (us-east / us-west, auto-selected) |
| Runtime | Python 3.11 |
| GPU | NVIDIA T4 (default), configurable per function |
| Persistent infrastructure | None (fully serverless) |
| Cost model | Pay-per-second of function execution (GPU time) |

## Compute Resources

### Per-Function Resource Allocation

| Function | CPU | Memory | GPU | Timeout | Concurrency |
|----------|-----|--------|-----|---------|-------------|
| `index_document` | 2 cores | 4 GB | T4 (16 GB VRAM) | 300s | Platform-managed |
| `index_batch` | 1 core | 2 GB | None | 600s | 1 (orchestrator) |
| `reindex_changed` | 1 core | 2 GB | None | 600s | 1 (orchestrator) |
| `rebuild_all` | 1 core | 2 GB | None | 3600s | 1 (singleton) |
| `health_check` | 0.5 core | 512 MB | None | 30s | Platform-managed |

### Warm Container Policy

| Function | Keep Warm | Rationale |
|----------|-----------|-----------|
| `index_document` | 1 | Reduce cold start for on-demand single-doc indexing |
| All others | 0 | Infrequent invocation; cold start acceptable |

### Cold Start Budget

| Phase | Duration | Notes |
|-------|----------|-------|
| Container boot | ~5s | Modal base image |
| Python imports | ~3s | LlamaIndex, fastembed, psycopg2 |
| Model load (from volume) | ~10-20s | First invocation per container |
| Model load (warm) | 0s | Subsequent invocations reuse in-memory model |
| **Total cold start** | **~20-30s** | |
| **Warm invocation** | **~200-500ms** | Per document, GPU embedding only |

## Storage

### Modal Volumes

| Volume | Name | Purpose | Shared With | Mount Path |
|--------|------|---------|-------------|------------|
| Model cache | `vecinita-embedding-models` | Cache embedding model weights | embedding-worker | `/models` |

Volume lifecycle:
- Created once, persists across deployments
- Model files downloaded on first container access (if not cached)
- Shared read access across indexing-worker and embedding-worker containers
- No automatic cleanup — managed manually or via Modal CLI

### Database Storage

| Resource | Provider | Connection |
|----------|----------|------------|
| PostgreSQL | Render Managed | `DATABASE_URL` env var |
| pgvector extension | Pre-installed on Render Postgres | Required for `vector(384)` column type |

Estimated storage growth:
- ~18 KB vectors + ~50 KB chunk text per document
- 1,000 documents ≈ 68 MB
- 10,000 documents ≈ 680 MB
- 100,000 documents ≈ 6.8 GB

## Networking

| Connection | Source | Destination | Protocol | Auth |
|------------|--------|-------------|----------|------|
| Modal → PostgreSQL | Modal container | Render Postgres | TCP (port 5432) | `DATABASE_URL` with SSL |
| Gateway → Modal | Render web service | Modal API | Modal SDK (gRPC) | MODAL_TOKEN_ID / MODAL_TOKEN_SECRET |
| Scraper → Modal | Modal container | Modal API | Modal SDK (internal) | Workspace tokens |
| Modal → HuggingFace | Modal container | huggingface.co | HTTPS | Public (model download) |

### SSL Requirements

- PostgreSQL connection: `sslmode=require` (Render Postgres default)
- Modal SDK: TLS by default (managed by Modal platform)
- HuggingFace model download: HTTPS

## Environment Variables

| Variable | Required | Default | Source | Purpose |
|----------|----------|---------|--------|---------|
| MODAL_TOKEN_ID | Yes | — | Modal secrets | SDK authentication |
| MODAL_TOKEN_SECRET | Yes | — | Modal secrets | SDK authentication |
| DATABASE_URL | Yes | — | Modal secrets | PostgreSQL connection string |
| EMBEDDING_MODEL | No | BAAI/bge-small-en-v1.5 | App config | Model for vector generation |
| CHUNK_SIZE | No | 512 | App config | Token chunk size |
| CHUNK_OVERLAP | No | 50 | App config | Token overlap between chunks |
| INDEX_BATCH_SIZE | No | 100 | App config | Max documents per batch call |
| LOG_LEVEL | No | INFO | App config | structlog level |

### Modal Secrets Configuration

```python
secrets = [modal.Secret.from_name("vecinita-db-credentials")]
```

The `vecinita-db-credentials` secret will contain:
- `DATABASE_URL` — PostgreSQL connection string (Render internal URL)

Modal tokens (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`) are automatically available in the Modal runtime environment.

## Scaling

| Dimension | Strategy | Limit |
|-----------|----------|-------|
| Horizontal (containers) | Modal auto-scaling (new container per `spawn_map` call) | Platform-managed |
| Vertical (GPU) | Fixed T4 per `index_document` invocation | 1 GPU per container |
| Batch concurrency | Limited by `INDEX_BATCH_SIZE` (default 100) | 100 concurrent containers max per batch |
| Rebuild concurrency | Singleton (only one `rebuild_all` at a time) | 1 |
| Scale to zero | Automatic when no invocations | $0 cost at idle |

## Observability

| Concern | Tool | Details |
|---------|------|---------|
| Function logs | Modal dashboard | Structured JSON logs via `structlog` |
| Execution metrics | Modal dashboard | Duration, GPU utilization, cold starts, errors |
| Job tracking | PostgreSQL `agent.indexing_jobs` | Per-job status, duration, document counts |
| Cost tracking | Modal billing dashboard | Per-function GPU-seconds |
| Alerting | Modal webhooks (planned) | Notify on job failures |

### Structured Log Format

```json
{
  "timestamp": "2026-05-12T12:00:00Z",
  "level": "info",
  "event": "document_indexed",
  "job_id": "uuid",
  "document_id": "uuid",
  "chunks": 12,
  "duration_ms": 450,
  "correlation_id": "uuid"
}
```

## Disaster Recovery

| Scenario | Recovery |
|----------|----------|
| Modal outage | No indexing occurs; documents queue in gateway until Modal recovers |
| PostgreSQL outage | All functions fail with connection error; auto-recover when DB is back |
| Model volume corruption | Delete volume, recreate, models re-download on next cold start |
| Failed rebuild (partial state) | Re-run `rebuild_all` — idempotent, starts fresh |
| Accidental vector deletion | Re-run `rebuild_all` from source documents |

## Cost Estimates

| Operation | GPU Time | Estimated Cost |
|-----------|----------|----------------|
| Single document (warm) | ~0.5s T4 | ~$0.0003 |
| Batch of 100 documents | ~50s T4 (parallel) | ~$0.03 |
| Full rebuild (1,000 docs) | ~500s T4 (parallel batches) | ~$0.30 |
| Full rebuild (10,000 docs) | ~5,000s T4 (parallel batches) | ~$3.00 |
| Idle | 0s | $0.00 |

*Costs based on Modal T4 pricing (~$0.000576/s). Actual costs depend on cold starts and container reuse.*

## Cross-References

- Modal configuration details: [13-modal-integration-plan.md](13-modal-integration-plan.md)
- Render integration: [14-render-integration-plan.md](14-render-integration-plan.md) (N/A)
- Environment variables: [Environments](../environments/ENVIRONMENTS.md)
