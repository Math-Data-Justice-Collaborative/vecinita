# Render Integration Plan: Gateway
> Auto-generated: 2026-05-12

Source: `apis/gateway/Dockerfile.gateway`

## Service Configuration

| Property | Value |
|----------|-------|
| Service name | `vecinita-gateway` |
| Service type | Web service |
| Runtime | Docker |
| Dockerfile path | `apis/gateway/Dockerfile.gateway` |
| Docker context | `.` (repository root) |
| Default port | 10000 (`PORT` env var) |
| Health check path | `/health` |

## Dockerfile Summary

| Stage | Base Image | Purpose |
|-------|-----------|---------|
| `builder` | `python:3.11-slim-bookworm` | Install build tools, pip install dependencies to `/install` |
| `runtime` | `python:3.11-slim-bookworm` | Copy deps from builder, copy source, run gateway |

### Runtime Image Contents

```
/app/
├── src/          # apis/gateway/src/
└── scripts/      # apis/gateway/scripts/
```

Runtime system packages: `curl` (for health check).

### Health Check (Docker)

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1
```

### Entrypoint

```
CMD ["sh", "./scripts/start_gateway_render.sh"]
```

## Render Environment Detection

The gateway detects Render at runtime via:

```python
def _running_on_render() -> bool:
    return bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))
```

This affects:
- **Service URL resolution**: Render-specific fallback URLs for embedding/agent/model services
- **Internal hostname filtering**: Ignores `localhost`, `127.0.0.1`, Docker-style hostnames on Render
- **Agent URL normalization**: Adds `http://` scheme to Render `fromService` bindings (which supply `host:port` only)

Source: `apis/gateway/src/config.py`

## Service Connectivity (Render Internal)

| Target Service | Connection Method | URL Pattern |
|---------------|-------------------|-------------|
| Agent service | Render internal mesh / `fromService` | `http://<agent-host>:8000` |
| PostgreSQL | Render managed database | `postgresql://...` via `DATABASE_URL` |
| Embedding (Modal) | Modal SDK (HTTPS outbound) | Not via Render mesh |

### Agent Service URL on Render

Render's `fromService` binding provides `host:port` without scheme. The gateway's `normalize_agent_service_url()` prepends `http://`:

```python
def normalize_agent_service_url(raw, *, default="http://localhost:8000"):
    candidate = (raw or "").strip()
    if not candidate:
        return default
    if "://" in candidate:
        return candidate
    return f"http://{candidate}"
```

## Render-Specific Configuration

| Variable | Render Value | Purpose |
|----------|-------------|---------|
| `RENDER` | `true` (set by platform) | Runtime detection |
| `RENDER_SERVICE_ID` | Auto-set | Service identification |
| `RENDER_SERVICE_NAME` | Auto-set | Used in health response |
| `PORT` | 10000 | Render assigns this port |
| `DATABASE_URL` | Render Postgres URL | Managed database |
| `AGENT_SERVICE_URL` | `fromService` binding | Internal mesh URL |

## Deployment Considerations

### Auto-Deploy

Trigger: push to main branch (configured in Render dashboard, not in `render.yaml`).

### Scaling

| Concern | Status |
|---------|--------|
| Horizontal scaling | Blocked by in-memory rate limiting (PTD-002) |
| Zero-downtime deploy | Supported by Render (rolling restart) |
| Blue-green | Not configured |

### Secrets Management

Secrets stored in Render environment variables (dashboard or `render.yaml` `envVars` with `sync: false`).

Critical secrets:
- `DATABASE_URL` — Render managed, auto-rotated
- `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` — Manual, from Modal dashboard
- `SCRAPER_API_KEYS` — Manual, shared with Modal scraper deployment
- `ENABLE_AUTH` — Toggle for production auth

### Static File Serving

On Render, the gateway can optionally serve the chat frontend's built assets. The `Dockerfile.gateway` does not copy frontend files — they must be built and available at `frontends/chat/dist/` relative to the gateway process.

In practice, the chat frontend is deployed as a separate Render static site, so this code path is rarely active in production.
