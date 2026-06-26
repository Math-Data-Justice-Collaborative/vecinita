# Deploy Checklist — S002 Admin Job Management

> **Generated**: 2026-06-26  
> **Status**: **not ready** (Modal redeploy + typecheck fix required)  
> **Deployment plan**: [deployment-integration.md](../../deployment-integration.md)  
> **Stage**: 12-verify-deploy (S002 delta — F32 + #88)  
> **Branch**: `main` @ `6b72ba0`  
> **Session**: S002-admin-job-management  
> **Prior checklist**: [deploy-checklist.md](../../deploy-checklist.md) (EV-002 @ 2026-05-27)

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete | **PASS** | `GET /jobs` in OpenAPI + `create_app()`; Jobs route in admin FE |
| Secrets configured | **PASS** | `vecinita-data-management` Modal secret; DO proxy keys documented |
| Data assets staged | **PASS** | D1–D9 verified; no new migrations for F32 |
| Resource allocation | **PASS** | No new GPU apps; data-mgmt Modal CPU-only delta |
| Rollback plan | **PENDING** | User sign-off required (see below) |
| H0c CORS unit tests | **PASS** | `OPTIONS /jobs` on data-mgmt included |
| `VITE_*` ↔ API matrix | **PASS** | Jobs tab uses existing `VITE_VECINITA_JOBS_API_URL` / proxy key |
| `VECINITA_CORS_ORIGINS` | **PASS** | Admin frontend origin already in data-mgmt CORS |
| Post-deploy H4–H5 | **DOCUMENTED** | `scripts/deploy/verify_connectivity.sh` |

### S002-specific deploy surfaces

| Surface | Change | Deploy command |
|---------|--------|----------------|
| Modal data-management | `GET /jobs` + `list_jobs` | `modal deploy -m infra.modal.data_management_app` (profile **vecinita**) |
| Admin frontend (DO) | Jobs tab + aria `SheetDescription` | DO static deploy / `scripts/deploy/do_apps.py` |
| Chat-rag / write-api | #88 best-effort tagging (ingest path) | Redeploy only if ingest worker image stale |

**Blocker:** Production Modal returns 405 on `GET /jobs` — must redeploy before Jobs tab works (BUG-2026-06-26).

**Advisory:** Staging DO apps pinned to `feat/S001-modal-cold-start-snapshot` — update branch pin when merging S002.

## Configuration validation (Agent 1)

| Item | Status |
|------|--------|
| `infra/modal/data_management_app.py` | OK — vecinita workspace |
| `openapi/data-management.yaml` | OK — `GET /jobs` documented |
| `apps/data-management-backend` `create_app()` | OK — route registered |
| `apps/data-management-frontend` `/jobs` route | OK — `listJobs()` client |
| `⚠️ Needs human input` markers | None |

## Secrets (Agent 2)

| Secret | Status |
|--------|--------|
| `VECINITA_MODAL_PROXY_KEY` (Modal + admin FE) | Documented |
| `vecinita-data-management` Modal secret | Exists (prior deploys) |
| DO admin frontend build env | Documented in staging-secrets-matrix |

## Data & volumes (Agent 3)

| Asset | Status |
|-------|--------|
| D1–D9 fixtures/migrations | verified |
| D6 FastEmbed | verified |
| D7 Qwen LLM | staged_procedure |
| New DB migration for F32 | **N/A** — uses existing `jobs` store |

## Template conformance (Agent 5)

| Criterion | Status |
|-----------|--------|
| `import modal` only under `infra/modal/` | PASS |
| Modal workspace `vecinita` | PASS |
| Deploy URLs `vecinita--` prefix | PASS |
| No `DATABASE_URL` in Modal worker paths | PASS |
| CI matches tech stack | PASS |

## Browser connectivity (Agent 6)

| Check | Status |
|-------|--------|
| `test_cors_policy.py` | PASS |
| `configure_cors` on data-mgmt `create_app` | PASS |
| `verify_connectivity.sh` present | PASS |
| `test_staging_connectivity.py` present | PASS |
| Jobs tab CORS (`GET /jobs` from admin origin) | PASS (unit H0c); live H4 after deploy |

## Failure Mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Modal deploy fails / wrong workspace | `scripts/modal_ensure_workspace.sh`; verify `vecinita--` URL | pending user approval |
| 2 | GET /jobs 405 persists | Verify image SHA after deploy; run live bug repro test | **required** |
| 3 | Admin FE bundle stale | Redeploy admin static after merge; H5 bundle check | pending |
| 4 | DO branch pin on S001 feature branch | Update `github` branch to `main` post-merge | advisory |
| 5 | Ingest tag regression (#88) | `test_uj002_ingest_tag_resilience.py` in CI e2e path | approved (T0 green) |
| 6 | Typecheck CI fail on bug test | Fix `reportAny` before push | **blocking** |
| 7 | Auth/CORS on Jobs tab | Existing proxy key + CORS origins | approved |

## Rollback

- **Modal data-mgmt**: `modal app stop vecinita-data-management` or redeploy prior image tag
- **Admin FE**: Redeploy previous DO static build from last known good commit
- **Database**: No schema change — rollback is deploy-only (Option A: leave data)
- **Last known good (staging)**: `4f3f741` on `feat/S001-modal-cold-start-snapshot` (pre-F32)

## Sign-Off

- [ ] User approved implementation (11-verify-impl)
- [ ] Failure mitigations reviewed
- [ ] Rollback plan approved
- [ ] Modal data-mgmt redeploy scheduled
- [ ] Ready for 13-deploy-smoke

**Deploy gate: NOT READY** — resolve QA-S002-001 (typecheck) and QA-S002-002 (Modal GET /jobs) first.
