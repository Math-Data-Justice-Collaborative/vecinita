# Quickstart: parity checks, env verification, live Schemathesis

Feature: `003-consolidate-scraper-dm`. Read [plan.md](./plan.md) for refactoring phases.

## 1. Verify gateway / Modal DB split (fixes `dpg-*` DNS class failures)

1. Open [RENDER_SHARED_ENV_CONTRACT.md](../../docs/deployment/RENDER_SHARED_ENV_CONTRACT.md).  
2. On **Render gateway**, confirm `MODAL_SCRAPER_PERSIST_VIA_GATEWAY` and gateway `DATABASE_URL`.  
3. On **Modal** secret `vecinita-scraper-env`, confirm matching flag and **externally resolvable**
   `MODAL_DATABASE_URL` for any worker stage that still opens Postgres.  
4. Gateway-owned persistence (`modal_scraper_persist`) resolves Postgres via the same
   `get_resolved_database_url()` helper as the rest of the gateway (`DATABASE_URL` / `DB_URL`).  
5. Curl smoke:

```bash
# Example host (lx27); substitute your staging gateway.
curl -sS -o /dev/null -w "%{http_code}\n" --max-time 45 -X GET \
  "https://vecinita-gateway-lx27.onrender.com/api/v1/modal-jobs/scraper"
```

Expect **not** `500` when tier is healthy (list may be empty with **200**).

## 2. Parity: old (submodule) vs new (HTTP) — data-management-api

**Before** removing submodules:

1. Record a small set of **golden** requests the DM app issues today (paths + bodies + expected status
   + JSON keys).  
2. Point adapters at **staging** remote URLs for scraper/embedding/model.  
3. Diff normalized responses; document any intentional deltas (e.g. error message wording).

**After** removal: re-run the same suite; failures block merge.

Suggested location for fixtures: `services/data-management-api/tests/parity/` (create during
implementation).

## 3. Live Schemathesis (errors + warnings)

From repo root:

```bash
make test-schemathesis-cli
```

Prerequisites (typical):

- `SCHEMATHESIS_*` env vars from `backend/scripts/run_schemathesis_live.sh` / hooks for job and
  registry IDs.  
- Gateway OpenAPI URL reachable.

**Targets**:

- Zero **server-error** class failures on `/api/v1/modal-jobs/scraper*`.  
- Reduce **404** warnings by supplying valid resource IDs in hooks.  
- Fix **schema validation mismatch** operations by aligning OpenAPI with FastAPI.

Optional: lower `SCHEMATHESIS_COVERAGE_FAIL_UNDER` **only** for local debugging; release gate stays
per team policy.

## 4. SC-001 — 100-iteration modal scraper job smoke

After implementing `backend/scripts/smoke_modal_scraper_jobs.py` (see `tasks.md` **T015**), run against
staging with a valid bearer token and gateway base URL. Expect **≥99%** of iterations without
undocumented `5xx` (see **SC-001** in `spec.md`). Example:

```bash
# Placeholder — exact flags follow script implementation
python backend/scripts/smoke_modal_scraper_jobs.py --base-url "https://<gateway-host>" --iterations 100
```

## 5. SC-005 — Ask benchmark (three consecutive days)

Script: `backend/scripts/benchmark_ask_three_day.py` (**T035**). It issues **20** fixed `GET /api/v1/ask`
requests per run (UTC calendar day), records results in a JSON state file, and after **three
consecutive** UTC days exist in history exits **non-zero** if any of those days had fewer than
**18** successes (override with `--min-per-day`).

```bash
export GATEWAY_BASE_URL="https://<gateway-host>"
export GATEWAY_BEARER_TOKEN="..."   # when gateway auth is enabled

# One-off (no state file)
python backend/scripts/benchmark_ask_three_day.py --dry-run

# Day 1, then day 2, then day 3 (UTC); same command daily (cron-friendly)
python backend/scripts/benchmark_ask_three_day.py
# Optional: ASK_BENCHMARK_STATE_FILE=/path/state.json
```

On failure after three days, record an owner-signed waiver in
[`baseline-notes-schemathesis.md`](./baseline-notes-schemathesis.md) if the shortfall is accepted.

## 6. DM API remote-only local dev

Set:

- `SCRAPER_SERVICE_BASE_URL`  
- `EMBEDDING_SERVICE_BASE_URL`  
- `MODEL_SERVICE_BASE_URL`  

to local or tunnel URLs where sibling services run. Without these, startup should fail clearly (see
[contracts/dm-api-remote-service-integration.md](./contracts/dm-api-remote-service-integration.md)).

## 7. CI

```bash
make ci
```

Run from repository root before declaring the feature merge-ready.

## 8. Render dashboard — env groups (**T039**)

Use the Render dashboard to keep **gateway**, **agent**, **Postgres**, and **Modal** secrets aligned
with [RENDER_SHARED_ENV_CONTRACT.md](../../docs/deployment/RENDER_SHARED_ENV_CONTRACT.md):

- [Environment groups](https://render.com/docs/environment-groups) — share `DATABASE_URL`, CORS,
  and API keys across services.
- [Environment variables](https://render.com/docs/configure-environment-variables) — per-service
  overrides (e.g. gateway `AGENT_TIMEOUT`, Modal `MODAL_DATABASE_URL` external DSN).
- [Blueprint / `render.yaml`](https://render.com/docs/infrastructure-as-code) — repo root
  `render.yaml` for infrastructure-as-code review.
