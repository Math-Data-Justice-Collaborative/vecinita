# BUG-2026-07-01 — Eval routes 500 (missing eval_runs / eval_criteria tables)

> Status: **resolved**  
> Feature: **F36** (admin RAG evaluation, EV-008)  
> Component: `apps/internal-write-api`, `apps/database` Alembic migrations

## Error description

Admin Evaluation page requests to internal-write-api return HTTP 500 with `{"detail":"Internal Server Error"}`:

- `GET /internal/v1/eval/runs`
- `GET /internal/v1/eval/runs/timeseries?limit=100`
- `GET /internal/v1/eval/criteria` (same class)

## Error logs

DigitalOcean App Platform (`vecinita-internal-write-api`, app id `c255dbd2-682d-4014-a7b5-4cbdfffa34bf`):

```text
GET /internal/v1/eval/runs HTTP/1.1" 500 Internal Server Error
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedTable) relation "eval_runs" does not exist
[SQL: SELECT COUNT(*) FROM eval_runs]

GET /internal/v1/eval/criteria HTTP/1.1" 500 Internal Server Error
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedTable) relation "eval_criteria" does not exist
[SQL: SELECT ... FROM eval_criteria ORDER BY slug ASC]
```

Deploy DigitalOcean workflow run `28550383516` (2026-07-01):

```text
WARN: Alembic upgrade — missing env: DATABASE_URL
::warning::DATABASE_URL not configured — skipping Alembic. Eval routes will 500 until migrations run.
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Error / crash — 500 on eval list + timeseries |
| Where | Production (DO staging — internal-write-api) |
| When | After EV-008 code deploy without DB migration |
| Frequency | Every time |
| Repro env | Production |
| Severity | High — Evaluation tab unusable |
| Evidence | User fetch + DO logs |
| Tried | Nothing before hotfix |

## Remediation path

**deploy-live** — apply Alembic migrations to staging Postgres; sync `DATABASE_URL` GitHub secret.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Eval endpoints return 200 with admin JWT (not 500) |
| Verification checks | Alembic at head; user confirms admin UI; GitHub secret synced |
| Monitoring | User confirmed fixed in browser |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | App code bug in eval routes | Rejected — routes query expected tables |
| H2 | Missing Alembic migrations on staging DB | **Confirmed** — DB at `20260628_0004`, head is `20260701_0006` |
| H3 | CI/CD skipped Alembic (no `DATABASE_URL` secret) | **Confirmed** — deploy run 28550383516 |

## Root cause

EV-008 migrations (`20260701_0005` eval_runs/eval_run_items, `20260701_0006` eval_criteria) were merged and deployed to internal-write-api, but **Alembic was never run** against DO Managed Postgres (`vecinita-staging`) because the `DATABASE_URL` GitHub Actions repository secret was empty. The deploy workflow intentionally skips migration with a warning.

Classification: **Config / infra** — missing migration step, not application logic.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F36 | In scope |
| `docs/execution-plan.md` T59.3/T61.x | Migrations exist in repo |
| `.github/workflows/deploy-digitalocean.yml` | Alembic gated on `DATABASE_URL` — working as designed |
| `docs/staging-secrets-matrix.md` | `DATABASE_URL` marked required for CI Alembic |

No blocking spec drift.

## Fix

1. Applied Alembic on staging Postgres (via `doctl databases connection` + `alembic upgrade head`):
   - `20260628_0004` → `20260701_0005` (eval_runs, eval_run_items)
   - `20260701_0005` → `20260701_0006` (eval_criteria)
2. Synced `DATABASE_URL` to GitHub Actions secrets (`sync_github_secrets.sh --apply`) so future `Deploy DigitalOcean` runs apply migrations automatically.

No code changes required.

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 — DB | pass | Tables `eval_runs`, `eval_run_items`, `eval_criteria` exist; alembic `20260701_0006` |
| L2 — API smoke | pass | Unauthenticated GET returns 401 (not 500) |
| L4 — Production | pass | User confirmed eval page loads with JWT |
| CI secret | pass | `DATABASE_URL` pushed to GitHub Actions |

## Prevention & countermeasures

| Item | Action |
|------|--------|
| Recurrence risk | Possible if `DATABASE_URL` secret removed again |
| Detection | Deploy workflow warning + eval integration tests in CI (Postgres service) |
| Automated | `DATABASE_URL` now in GitHub secrets — Alembic runs on deploy |
| Process | Add deploy checklist row: verify Alembic step not skipped in deploy logs |

## Timeline

| When | Event |
|------|-------|
| 2026-07-01 ~22:06 UTC | User reports 500 on eval routes |
| 2026-07-01 | DO logs triaged — UndefinedTable |
| 2026-07-01 | Alembic upgrade head on `vecinita-staging` |
| 2026-07-01 | User confirmed fixed; `DATABASE_URL` synced to GitHub |
