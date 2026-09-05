# BUG-2026-09-03 — Staging admin Jobs Unauthorized + Monitoring metrics 404

**Status:** resolved (2026-09-03)  
**Severity:** high (staging admin Jobs + Monitoring broken)  
**Feature:** F32 jobs / F84 monitoring / F83 staging  
**Reported:** 2026-09-03  
**Environment:** Staging admin → Modal DM + staging write-api

## Error description

Signed-in staging admin operator:

- **Jobs tab** displays `{"detail":"Unauthorized"}`
- **Monitoring** displays `Metrics timeseries failed (404)` (and Unauthorized on related calls)

## Error logs

```json
{"detail":"Unauthorized"}
```

Frontend error string for metrics:

```text
Metrics timeseries failed (404)
```

## Investigation

| Step | Finding |
|------|---------|
| 1 | Staging admin bundle embeds staging hosts: Modal `vecinita-staging--…`, write-api `vecinita-staging-write-api-w7eol…`, Supabase `camkatfbjguwvymfgdme` |
| 2 | write-api OpenAPI (live): has `/internal/v1/stats/*` but **no** `/internal/v1/metrics/*` |
| 3 | Live probe: `GET …/metrics/timeseries` → **404**; `GET …/stats/summary` → **200** |
| 4 | Active staging write-api deploy commit: `cab049c4` — **before** F84 metrics (`7ee8f83c`) |
| 5 | Modal `GET /jobs` with proxy key + internal API key Bearer → **401** (expected: `auth_dep` requires Supabase JWT per F34, not service key) |

## Root cause

1. **Metrics 404 — deploy drift:** `vecinita-staging-write-api` image is stale (pre-F84). Routes exist on `main` but were never deployed to staging.
2. **Jobs 401 — Modal JWT / secret drift (likely):** Browser must send staging Supabase JWT + proxy key. Unauthorized while signed in suggests Modal staging secret `SUPABASE_URL` (or stale Modal deploy) does not match staging Supabase project used by admin FE.

## Fix

| Surface | Action | Status |
|---------|--------|--------|
| write-api | Redeploy `vecinita-staging-write-api` from current `main` | **done** — deploy `57ff6e9`, metrics routes live |
| write-api DB | Run `alembic upgrade head` on `vecinita-staging-db` (F84 `operation_metrics` / `metrics_hourly`) | **done** — summary + timeseries **200** |
| Modal DM | `MODAL_ENVIRONMENT=staging` → `sync_modal_secret.sh --merge --apply` with staging `SUPABASE_URL` + `SUPABASE_SECRET_KEY`; `modal.sh` redeploy | **done** |
| DO staging | `do_apps.py sync-all-secrets --env staging` (write-api, chat-api, admin-fe, chat-fe) | **done** |
| Supabase staging | Refresh API keys in `.env`; `seed_first_admin.py`; reset `admin@vecinita.admin` password + `app_metadata.role=admin` | **done** |
| `.env` | Staging block: `SUPABASE_STAGING_*`, `VITE_SUPABASE_STAGING_*`, `VECINITA_STAGING_*`, `VECINITA_STAGING_DATABASE_URL` | **done** |
| Guard | `tests/smoke/test_staging_f84_metrics.py` + metrics CORS in `test_staging_connectivity.py` | added (local, uncommitted) |

## Repro test

- `tests/smoke/test_staging_f84_metrics.py` (live; fails until write-api redeploy completes)

## TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-09-03 | Live OpenAPI + curl probes | RED (metrics 404, pre-F84 commit) |
| 2 | 2026-09-03 | Triggered doctl redeploy staging write-api | deploy `57ff6e9` ACTIVE |
| 3 | 2026-09-03 | Post-deploy probe | timeseries **200**; summary **500** (migration likely) |
| 4 | 2026-09-03 | Added F84 staging smoke tests | guard (local) |
| 5 | 2026-09-03 | Alembic on `vecinita-staging-db`; metrics summary **200** | GREEN (metrics) |
| 6 | 2026-09-03 | Modal secret + DO staging sync; staging Supabase keys in `.env` | GREEN (infra) |
| 7 | 2026-09-03 | Staging JWT + proxy → `GET /jobs` **200**; metrics endpoints **200** | GREEN (e2e probe) |

## Interview record

- Symptom: Jobs + Monitoring on staging admin
- Env: staging
- AC: both tabs work for signed-in admin
- Root cause: both deploy drift (operator confirmed)
- Gate: open — redeploy + smoke tests

## Prevention

- Staging smoke must assert F84 metrics routes in OpenAPI (`test_staging_f84_metrics.py`)
- After promote to `main`, confirm staging write-api deploy SHA includes F84 before closing staging UJ-088
