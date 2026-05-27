# Deploy Checklist

> **Generated**: 2026-05-27 (EV-002 delta update)
> **Status**: **ready** (staging DB migration required before deploy — operator action)
> **Deployment plan**: [deployment-integration.md](deployment-integration.md)
> **Stage**: 12-verify-deploy (EV-002 delta — F23–F29)
> **Previous run**: 2026-05-25 (EV-001 delta)
> **Branch verified**: `evolve/EV-002-admin-overhaul` @ `98bb7f8`

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete (no gaps) | **PASS** | Infra YAMLs updated for EV-002; docs reconciled with runtime env names |
| All secrets configured | **PASS** | DO staging keys verified via `doctl`; `verify_secrets.sh` pass; Modal secret `vecinita-data-management` exists |
| Data assets staged | **CONDITIONAL** | D1–D9 verified; **staging DB at `20260524_0002`** — must run `alembic upgrade head` before deploy |
| Resource allocation verified | **PASS** | No new GPU/Modal apps; EV-002 endpoints on existing DO services; cost within ≤ $50/mo cap |
| Rollback plan reviewed | **APPROVED** | User sign-off 2026-05-27; reverse TP-029 order; Option A leave tables |
| H0c CORS unit tests pass | **PASS** | 14 passed, 4 skipped (no local `DATABASE_URL`); includes `test_cors_ev002.py` TC-060 |
| Frontend `VITE_*` ↔ API URL matrix complete | **PASS** | No new VITE vars for EV-002; admin uses existing corpus API URL/key |
| `VECINITA_CORS_ORIGINS` documented per API service | **PASS** | chat-rag-backend + internal-write-api + Modal data-mgmt in staging-secrets-matrix |
| Post-deploy H4–H5 command documented | **PASS** | `verify_connectivity.sh` + `test_staging_connectivity.py` (EV-002 routes added) |

### EV-002 specific checks

| Check | Result | Evidence |
|-------|--------|----------|
| Alembic EV-002 migration exists | **PASS** | Revision `20260526_0003`: `audit_log`, `document_versions`, `document_serving_stats` |
| Staging DB at head | **PASS** | `20260526_0003` confirmed 2026-05-27 (`alembic current`) |
| Admin endpoints implemented | **PASS** | stats, health/all, bulk ops, audit, document history on internal-write-api |
| ChatRAG stats integration | **PASS** | Fire-and-forget `POST /internal/v1/stats/served` after successful ask |
| Admin UI overhaul | **PASS** | Dashboard, health, audit, bulk ops pages; shadcn/ui (F23) |
| Health aggregator env on DO | **PASS (runtime)** | DO has `VECINITA_CHAT_RAG_URL`, `VECINITA_*_FRONTEND_URL`, Modal URLs |
| Deploy order documented | **PASS** | ADR-017 TP-029: migration → write-api → chat-rag → admin frontend |
| D7 LLM weights verified | **PASS (EV-001)** | Verified during prior deploy; unchanged for EV-002 |

## Configuration validation (Agent 1)

| Item | Status |
|------|--------|
| `infra/do/*.yaml` (4 deployables) | OK |
| `scripts/deploy/modal.sh` | OK — not required for EV-002 redeploy |
| `docs/staging-runbook.md` | **Advisory** — EV-001 order only; TP-029 in ADR-017 |
| `docs/staging-secrets-matrix.md` | OK — health env names match runtime code |
| App names: `vecinita-embedding`, `vecinita-data-management`, `vecinita-llm` | OK |
| `⚠️ Needs human input` in deployment-integration | None |
| Alembic revision `20260526_0003` | OK |
| EV-002 endpoints on internal-write-api | OK |
| ChatRAG → write API stats vars on DO | OK (configured; under-documented in matrix ChatRAG section) |
| `VECINITA_STATS_ENABLED` | chat-rag-backend | Wired in `ChatRagSettings` / `_fire_stats` |
| `VECINITA_AUDIT_RETENTION_DAYS` | internal-write-api | Wired in `POST /internal/v1/audit/cleanup` |

## Secrets check (Agent 2)

| Secret / env | Platform | Status |
|--------------|----------|--------|
| `DATABASE_URL` | DO (backends) | **PASS** |
| `VECINITA_INTERNAL_API_KEY` | DO + Modal | **PASS** |
| `VECINITA_INTERNAL_WRITE_URL` + key | ChatRAG backend (F28) | **PASS on DO** — add to matrix ChatRAG section |
| `VECINITA_CORS_ORIGINS` | All API services | **PASS** |
| `VECINITA_CHAT_RAG_URL` + frontend URLs | internal-write-api (F26) | **PASS on DO** |
| `VECINITA_HEALTH_TIMEOUT_MS` | internal-write-api | **PASS on DO** |
| `VECINITA_MODAL_*` URLs | ChatRAG + write API + Modal | **PASS** |
| `VITE_VECINITA_*` (5 vars) | Admin + chat frontends | **PASS** |
| `DATABASE_URL` in Modal | Forbidden (ADR-007) | **PASS** — absent |
| Modal secret `vecinita-data-management` | Modal | **PASS** — exists (used 2026-05-27) |

**EV-002:** No new secret *types* required. F23–F29 reuse existing corpus API URL/key + CORS.

## Data & volumes (Agent 3)

| Asset | Status | Notes |
|-------|--------|-------|
| D1–D5 corpus/migrations | **PASS (repo)** | Revision `20260526_0003` at HEAD |
| D6 FastEmbed | **PASS** | Volume `embedding-models` |
| D7 Qwen weights | **PASS** | Volume `llm-models`; verified EV-001 |
| D8–D9 tag fixtures | **PASS** | Unchanged |
| Staging Postgres at `20260526_0003` | **PASS** | Head confirmed 2026-05-27 |
| EV-002 corpus fixtures | **N/A** | None required |
| New Modal volumes | **N/A** | Reuses D6/D7 |

## Resource allocation (Agent 4)

| Resource | Plan | Actual | Status |
|----------|------|--------|--------|
| LLM GPU | T4, scale-to-zero | `gpu="T4"`, `scaledown_window=300` | OK |
| Embed / data-mgmt | CPU Modal | No GPU | OK |
| ChatRAG DO | basic-xxs, nyc | `chat-rag-backend.yaml` | OK |
| Internal write API | basic-xxs | `internal-write-api.yaml` | OK |
| EV-002 new resources | None | Endpoints on existing services | OK |
| Cost pilot | ≤ $50/mo | ~$42–48/mo unchanged | OK |

## Template deploy validation (Agent 5 — `api+worker` hybrid)

| Check | Status | Notes |
|-------|--------|-------|
| Template ID `api+worker` | OK | Hybrid DO + Modal, not Modal job template |
| Modal deploy command | OK | `scripts/deploy/modal.sh` → `infra/modal/*.py` |
| Deploy workflow | N/A | Manual deploy per staging-runbook + `deploy-preflight.yml` |
| GitHub `MODAL_TOKEN_*` | OK | Wired in `deploy-preflight.yml` |
| EV-002 Modal redeploy | **Not required** | Health aggregator on DO write API (ADR-017) |
| `DATABASE_URL` not in Modal | OK | ADR-007 enforced |

## Connectivity Gates (H4/H5) — EV-002 readiness

| Gate | Status | Detail |
|------|--------|--------|
| H0c EV-001 CORS (`test_cors_policy.py`) | **PASS** | 9 tests (4 skip without local DB) |
| H0c EV-002 CORS (`test_cors_ev002.py`) | **PASS** | TC-060: bulk DELETE/PATCH, stats, audit, health |
| H0c DELETE/PATCH bulk routes | **PASS** | `allow_methods` includes DELETE, PATCH |
| H4 ChatRAG CORS (live) | **PENDING** | Post-deploy: `verify_connectivity.sh` |
| H4 Write API CORS (live) | **PENDING** | Post-deploy: bulk, stats, audit, health preflights |
| H4 Modal data-mgmt CORS | **WAIVER** | `requires_proxy_auth` blocks OPTIONS; user-approved EV-001 waiver |
| H5 Admin frontend bundle | **PENDING** | Post-deploy: corpus API + Modal hosts in bundle |
| H5 Chat frontend bundle | **PENDING** | Unchanged for EV-002 |
| H4 EV-002 full coverage | **PASS** | Live preflight for `bulk/retag`, `stats/served`, `stats/top-served` |
| T3 EV-002 admin smokes | **PASS (script)** | `test_staging_ev002_admin.py` + `staging_smoke.sh` when env set |

## Failure Mitigations

| # | Risk | Mitigation | Status |
|---|------|-----------|--------|
| 1 | EV-002 migration failure | Additive migration `20260526_0003`; run on staging first; H2 verifies head | **approved** |
| 2 | Deploy order violation | TP-029: migration → write-api → chat-rag → admin frontend | **approved** |
| 3 | Health dashboard "not configured" | DO has correct env vars (`VECINITA_CHAT_RAG_URL`, etc.); verify F26 post-deploy | **approved** |
| 4 | Bulk DELETE/PATCH CORS blocked | H0c TC-060 pass; PATCH in `allow_methods`; H4 live post-deploy | **approved** |
| 5 | Serving stats not recorded | ChatRAG has `VECINITA_INTERNAL_WRITE_URL` + key on DO; verify stats POST post-deploy | **approved** |
| 6 | Audit log unbounded growth | `cleanup_audit_log()` exists; retention cron not scheduled — accept for v1 pilot | **approved** |
| 7 | Doc/env name mismatch | Operators use DO keys (verified); reconcile docs post-deploy | **approved** |
| 8 | Modal/DO image build failure | `verify_build.sh` + import smoke | **approved** (EV-001) |
| 9 | Secret missing at runtime | `verify_secrets.sh` + secrets matrix | **approved** (EV-001) |

## Rollback

**Procedure (EV-002 delta — per ADR-017 TP-029 reverse order):**

1. **Admin frontend** — Redeploy previous build (removes dashboard, health, audit, bulk UI)
2. **Chat-rag-backend** — Redeploy previous build (removes stats POST integration)
3. **Internal-write-api** — Redeploy previous build (removes EV-002 endpoints)
4. **Database**
   - **Option A (preferred):** Leave EV-002 tables in place — unused if code reverted. No data loss.
   - Option B (clean): `alembic downgrade -1` only if no production audit/stats data to preserve
5. **Verify rollback**
   - `curl` DO `/health` on previous deployment
   - Re-run H1–H3 staging smoke
   - EV-001 features (browse, tags) should remain functional

| Field | Value |
|-------|-------|
| **Last known good (EV-001 staging)** | `4a1598f` — deployed 2026-05-25 |
| **Last known good (EV-002 code)** | `98bb7f8` — `evolve/EV-002-admin-overhaul` |
| **Modal stop (if needed)** | `modal app stop vecinita-data-management` / `vecinita-embedding` / `vecinita-llm` |
| **DO redeploy previous** | `doctl apps create-deployment <app-id>` with reverted spec |

## Deploy gate (upstream stages)

| Gate | Status |
|------|--------|
| QA (09) | **PASS** — [qa-report.md](qa-report.md) (2026-05-27) |
| E2E T0 (10) | **PASS** — 40/40 e2e; UJ-013–UJ-021 [e2e-report.md](e2e-report.md) |
| E2E T3 live | **PENDING** — post-deploy (waived at 11-verify-impl) |
| Implementation (11) | **Approved** — F23–F29 journeys signed off (2026-05-27) |
| Deploy strategy (12) | **This checklist** |

## Deploy order (EV-002 — TP-029)

1. **Database** — `cd apps/database && uv run alembic upgrade head` (adds audit/stats tables)
2. **internal-write-api** — new stats, health, bulk, audit endpoints
3. **chat-rag-backend** — stats POST integration after successful ask
4. **data-management-frontend** — admin UI overhaul (dashboard, health, audit, bulk)
5. **Run connectivity smoke** — `bash scripts/deploy/verify_connectivity.sh`
6. **Run staging health** — `bash scripts/deploy/staging_smoke.sh`
7. **T3 live E2E** — UJ-013–UJ-021 on staging (13-deploy-smoke)

**Note:** Modal apps do **not** need redeploy for EV-002 (health aggregator on DO write API).

## Sign-Off

- [x] User approved implementation (11-verify-impl) — F23–F29 journeys 2026-05-27
- [x] Deploy strategy verified (failure modes + rollback acknowledged 2026-05-27)
- [x] Connectivity gates: H0c pass (TC-060); H4/H5 pending post-deploy
- [x] Modal H4 waiver acknowledged (proxy auth blocks OPTIONS preflight)
- [x] Staging DB migrated to `20260526_0003` (confirmed 2026-05-27)
- [x] EV-002 deployed and smokes passed (13-deploy-smoke 2026-05-27)

### Operator commands

```bash
# Pre-deploy: migrate staging DB (BLOCKING)
cd apps/database && uv run alembic upgrade head

# Pre-deploy: build smoke
bash scripts/deploy/verify_build.sh

# Pre-deploy: secrets check
bash scripts/deploy/verify_secrets.sh

# Post-deploy: connectivity smoke (blocking)
bash scripts/deploy/verify_connectivity.sh

# Post-deploy: staging health (H1–H3)
bash scripts/deploy/staging_smoke.sh
```

## Next step

**13-deploy-smoke** completed 2026-05-27 (EV-002). Optional: merge `evolve/EV-002-admin-overhaul` → `main` and align `infra/do/*.yaml` branch pins.
