# Render Deployment Troubleshooting Runbook

Last updated: April 2, 2026

This runbook covers common failure modes for the Vecinita Render deployment:
private-network connectivity, modal-proxy routing, strict-mode enforcement,
and ordered triage steps aligned to Render platform behavior.

---

## Architecture Quick Reference

```
Browser
  ↓ HTTPS
vecinita-gateway (Render web service, port 8004)
  ↓ Render private network
vecinita-agent (Render private service, port 8000)
  ↓ Render private network
vecinita-modal-proxy-v1 (Render private service, port 10000)
  ↓ Modal HTTP calls
  ├─ /model     → vecinita-model (Modal)
  ├─ /embedding → vecinita-embedding (Modal)
  └─ /jobs      → vecinita-scraper (Modal)
```

All inter-service traffic on Render uses **private-network hostnames** (no
`http://`, just the service name as the hostname). The proxy injects Modal
credentials; the agent MUST NOT forward `Authorization` or `Modal-*` headers.

---

## Ordered Triage Steps

### Step 1 — Read the logs

```bash
# In Render dashboard → service → Logs tab
# Look for the service_endpoints_summary log line:
# service_endpoints_summary model=... embedding=... strict_mode=... on_render=...
```

- `on_render=False` means `RENDER` / `RENDER_SERVICE_ID` env vars are unset.
- `strict_mode=False` means `AGENT_ENFORCE_PROXY` or `RENDER_REMOTE_INFERENCE_ONLY` is not truthy.
- `proxy_token_set=False` means `PROXY_AUTH_TOKEN` is missing (proxy auth will fail).

### Step 2 — Config parity check

Run the env contract validator locally against `.env.prod.render`:

```bash
python3 scripts/github/validate_render_env.py .env.prod.render
```

Expected output: `Render env contract OK` with at most a warning about staging origins.

If it fails, fix the missing/mismatched keys before redeploying.

### Step 3 — Health path check

For each Render service, verify the health endpoint responds:

```bash
# From within the Render network (via shell tab in dashboard):
curl http://vecinita-modal-proxy-v1:10000/health
curl http://vecinita-agent:8000/health
curl http://vecinita-gateway:8004/api/v1/health
```

### Step 4 — Hostname resolution

Private-network services must be reachable by the Render internal hostname,
not by localhost or external URLs.

Failure signatures:
- `Connection refused` on `localhost:PORT` → env var still points to localhost
- `Name does not resolve` on `vecinita-modal-proxy-v1` → service name typo or
  service not deployed in the same region

Verify all services are deployed in the **same Render region** (Virginia `ohio`).
Cross-region private networking is not supported.

### Step 5 — Upstream Modal health check

If the proxy is healthy but model/embedding calls fail:

1. Open Modal dashboard → App `vecinita-model` / `vecinita-embedding`.
2. Verify the app is deployed and the endpoint URL matches `VECINITA_MODEL_API_URL`
   / `VECINITA_EMBEDDING_API_URL` in the Render env group.
3. Check Modal logs for cold-start timeout errors.

Test the Modal endpoint directly from the proxy container:

```bash
# In Render shell for modal-proxy service:
curl -H "Modal-Key: $MODAL_TOKEN_ID" \
     -H "Modal-Secret: $MODAL_TOKEN_SECRET" \
     "$VECINITA_MODEL_API_URL/health"
```

### Step 6 — Resource limits

If the service health endpoint returns 200 but `/ask` requests time out:

- Check Render "Resources" tab for memory/CPU throttling indicators.
- The agent service should not require more than 512 MB RAM in normal operation.
- If memory spikes, check for local embedding model initialization (fallback path
  active — indicates strict mode is not working).

---

## Known Failure Signatures

### 1. `Connection refused` on agent startup

**Symptom**: Agent exits with `ConnectionRefusedError` at startup.

**Cause**: Embedding service health check fails because `EMBEDDING_SERVICE_URL`
still points to `http://embedding-service:8001` (Docker internal hostname).

**Fix**: Verify `MODAL_EMBEDDING_ENDPOINT` or `EMBEDDING_SERVICE_URL` is set
to `http://vecinita-modal-proxy-v1:10000/embedding` in the Render env group.

**Validation**: `service_endpoints_summary` log should show
`embedding=http://vecinita-modal-proxy-v1:10000/embedding`

---

### 2. Modal HTTP 401 on model call

**Symptom**: Model API call returns 401 Unauthorized.

**Cause**: The agent is forwarding `Authorization: Bearer` or `Modal-Key` / 
`Modal-Secret` headers to the proxy, which conflicts with the proxy's own
Modal credential injection.

**Fix**: Ensure `LocalLLMClientManager.headers()` returns `{}` for proxy URLs.
This is governed by `_via_proxy()` check on `"modal-proxy" in base_url`.

**Validation**: Check that `base_url` in `service_endpoints_summary` contains
`modal-proxy`. No `Authorization` header should appear in proxy request logs.

---

### 3. Embedding service validation failed in strict mode

**Symptom**: Agent aborts startup with:
```
RuntimeError: Embedding service validation failed in Render remote-only mode.
```

**Cause**: `RENDER_REMOTE_INFERENCE_ONLY=true` and the embedding proxy `/health`
is unreachable.

**Fix**:
1. Verify `vecinita-modal-proxy-v1` is running in Render.
2. Verify `MODAL_EMBEDDING_ENDPOINT`/`EMBEDDING_SERVICE_URL` matches the proxy URL.
3. Verify Modal `vecinita-embedding` app is healthy.

---

### 4. `proxy_token_set=False` in startup log

**Symptom**: No X-Proxy-Token header on proxy requests; proxy may reject with 403.

**Cause**: `PROXY_AUTH_TOKEN` (or its aliases `MODAL_PROXY_AUTH_TOKEN`,
`X_PROXY_TOKEN`) is not set in the Render env group.

**Fix**: Set `PROXY_AUTH_TOKEN` in the `.env.prod.render` env group.

---

### 5. CORS error in browser: `No 'Access-Control-Allow-Origin'`

**Symptom**: Browser blocks requests from the frontend origin.

**Cause**: `ALLOWED_ORIGINS` does not include the frontend URL.

**Fix**: Ensure `ALLOWED_ORIGINS` in the Render env group contains the Render
frontend URL (e.g. `https://vecinita-frontend.onrender.com`).

**Validation**: `service_endpoints_summary` log shows `allowed_origins=` list
including the frontend origin.

---

### 6. `strict_mode=False` but service is live on Render

**Symptom**: Agent starts and serves requests but may be silently using local
fallback paths.

**Cause**: `AGENT_ENFORCE_PROXY` or `RENDER_REMOTE_INFERENCE_ONLY` absent or set
to `false`.

**Fix**: Set both flags to `true` in the Render env group. Run the env contract
validator to confirm.

---

## Render Platform Rules (reference)

| Rule | Detail |
|------|--------|
| Private networking | Services communicate via hostname `<service-name>:PORT`, no scheme. Render resolves DNS internally. |
| Same region required | Private services must be in the same Render region. Virginia (`ohio`) is the canonical region for this project. |
| Port binding | Web services must bind to `0.0.0.0:PORT` (not `localhost`). Private services bind on the configured port internally. |
| Workers | Render does not support generic spawned worker processes for background tasks — use cron jobs or background workers in the Render service type. |
| Env group scope | All services share the `.env.prod.render` env group; changes take effect on next deploy. |
| Health checks | Configure the `healthCheckPath` in `render.yaml`; Render will probe this path after each deploy. |

---

## Local Render Simulation

Use `docker-compose.render-local.yml` and `scripts/local-render-check.sh`
to simulate the Render private-network environment locally before deploying:

```bash
# Start the local Render-like environment
docker compose -f docker-compose.render-local.yml up -d --build

# Run health + smoke checks
./scripts/local-render-check.sh

# Validate env contract
python3 scripts/github/validate_render_env.py .env.render-local
```

---

## Deploy Ordering

1. Deploy Modal services (`vecinita-model`, `vecinita-embedding`, `vecinita-scraper`) first.
2. Deploy `vecinita-modal-proxy` once Modal apps are healthy.
3. Deploy `vecinita-agent` (depends on proxy).
4. Deploy `vecinita-gateway` (depends on agent).
5. Deploy frontend(s) last.

Do not promote staging to production until all startup health checks pass
and the strict-mode flag summary confirms no silent fallback.
