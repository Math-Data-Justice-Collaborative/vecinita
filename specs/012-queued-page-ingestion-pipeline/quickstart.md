# Quickstart: Queued page ingestion pipeline (dev + CI)

## Prerequisites

- Python **3.11+**, **uv** or project venv, **Node** for Pact consumers.  
- **Modal** CLI + account for live Modal tests (optional; mock in unit tests).  
- Local **Postgres** or Docker compose per repo root docs if testing persist paths.

## TDD loop (recommended)

1. Pick a slice (e.g. new pipeline status or new JSON error field).  
2. Add a **failing** `pytest` under `backend/tests/` or `services/scraper/tests/` (or extend Pact JSON in `frontend/pacts/`).  
3. Implement minimal code in `backend/` or `services/scraper/`.  
4. Run **`make ci`** from repo root before pushing.

Commands below match **[plan.md](./plan.md) § Technical Context** (primary CI/contract gates). Optional legs (e.g. DM API Schemathesis) live in repo root **`TESTING_DOCUMENTATION.md`**.

## Gateway + contracts

```bash
cd /root/GitHub/VECINA/vecinita
make test-schemathesis        # OpenAPI / HTTP property tests (subset); see backend/schemathesis.toml
make pact-verify-providers    # Provider-side Pact (policy: default branch / pre-release)
```

Frontend consumer tests:

```bash
cd frontend && npm run test:pact
```

## Modal worker → gateway HTTP persistence

1. Set **`SCRAPER_GATEWAY_BASE_URL`** to your local or staging gateway URL.  
2. Align **`SCRAPER_API_KEYS`** / pipeline ingest token with gateway env.  
3. Run a scraper job that completes crawl; confirm **`/api/v1/internal/scraper-pipeline/*`** receives payloads (see `services/scraper/persistence/gateway_http.py`).

## Render alignment checklist (staging/prod)

- [ ] `render.yaml` services use **`autoDeployTrigger: checksPass`** where policy requires CI green.  
- [ ] **`DATABASE_URL`** bound on gateway from managed Postgres.  
- [ ] Modal secrets: **no** Modal token in **`VITE_*`** vars.  
- [ ] **`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`** updated if new vars.  
- [ ] Health check paths respond **200** before traffic switch.

## Correlation ID drill (**SC-007**)

1. **Submit a scrape job** (gateway-owned persist + Modal invocation as in your env):

   ```bash
   curl -sS -i -X POST "$GATEWAY/api/v1/modal-jobs/scraper" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $GATEWAY_JWT" \
     -H "X-Correlation-ID: drill-$(date +%s)" \
     -d '{"url":"https://example.com","user_id":"support-smoke"}'
   ```

   Replace `$GATEWAY` / `$GATEWAY_JWT` with your staging gateway base URL and a valid bearer token.  
   From the response, copy **`X-Correlation-ID`** (echoed by middleware) and the JSON **`job_id`**.

2. **Poll job status** with the same correlation header (optional but helps log join-up):

   ```bash
   curl -sS -i "$GATEWAY/api/v1/modal-jobs/scraper/$JOB_ID" \
     -H "Authorization: Bearer $GATEWAY_JWT" \
     -H "X-Correlation-ID: $CORR"
   ```

   Confirm the JSON includes **`pipeline_stage`**, **`error_category`** (when set), **`created_at`**, **`updated_at`**, and **`metadata`** when using gateway Postgres (`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`).

3. **Worker handoff** (Modal → gateway internal ingest): workers should send **`X-Request-Id`** on pipeline POSTs when available. In gateway logs, search for **`scraper_pipeline_job_status_ingest`** lines containing the same **`correlation_id`** and **`x_request_id`** as your `curl` headers.

4. **Modal**: in the Modal dashboard or `modal app logs`, search for the same correlation string propagated on scrape submit (see `backend/src/services/modal/invoker.py` metadata).

## See also

- [plan.md](./plan.md) — implementation structure.  
- [contracts/](./contracts/) — HTTP and wiring contracts.  
- `TESTING_DOCUMENTATION.md` — full matrix.
