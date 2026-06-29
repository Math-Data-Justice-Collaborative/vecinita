# E2E Behavior Report — S004 Supabase Admin Auth

> **Generated**: 2026-06-29  
> **Session**: S004-supabase-auth  
> **Mechanism**: API + Frontend (pytest `TestClient`, mocked Modal; Vitest)  
> **Branch**: `feat/S004-supabase-auth`  
> **Scope**: EV-005 / F34 — UJ-026–UJ-029 (Supabase admin auth) + regression on UJ-001–UJ-025  
> **Journeys tested**: 29 (full index)

## Summary

| Tier | Command | Result |
|------|---------|--------|
| **T0** | `uv run pytest tests/e2e/ -m "e2e and not live"` | **59 passed**, 0 failed |
| **T1** | `uv run pytest tests/integration/` | **35 passed**, 0 failed |
| **T3 live** | `tests/smoke/test_staging_*.py -m live` | **NOT RUN** — `VECINITA_STAGING_*` unset; auth not deployed |
| **FE Vitest** | both frontends + shared packages | **363 passed** (admin 223, chat 134, packages 6) |

| # | Journey | Mechanism | T0 | T3 | Status |
|---|---------|-----------|----|----|--------|
| 26 | **UJ-026 Admin login** | Vitest + API (UJ-028) | **PASS** | pending | Protected routes + JWT bearer verified T0 |
| 27 | **UJ-027 Invite-only registration** | API | **PASS** | pending | Public sign-up disabled asserted T0 |
| 28 | **UJ-028 Unauthenticated admin rejected** | API | **PASS** | pending | 401 on missing/invalid JWT; ChatRAG anonymous |
| 29 | **UJ-029 Viewer blocked from writes** | API | **PASS** | pending | viewer 403 / admin 200; audit opaque UUID |
| 1–25 | UJ-001–UJ-025 | mixed | **PASS** | pending/waived | No regressions vs S002 baseline |

**Overall T0: PASS** — 59/59 API e2e + 363 Vitest  
**Overall T3: NOT RUN** — deferred to 13-deploy-smoke / 15-service-health post-deploy

---

## EV-005 delta journeys (F34)

### UJ-026: Admin logs in to the Data Management UI

- **Feature**: F34 — Supabase Auth for admin surfaces
- **Mechanism**: Vitest (`test_auth_login_protected_routes.test.tsx`, `test_login_page.test.tsx`, `test_auth_context.test.tsx`)
- **Steps verified (T0)**:
  1. Unauthenticated visit → redirect to login — **PASS**
  2. Valid session → dashboard with current user + logout — **PASS**
  3. API calls carry `Authorization: Bearer` — covered by UJ-028/029 API tests — **PASS**
- **T3 browser**: deferred (consistent with other admin UI journeys)

### UJ-027: Admin invites an operator; invitee accepts

- **Feature**: F34 — invitation-only registration
- **Test module**: `tests/e2e/test_uj027_invite_only_registration.py`
- **Steps verified (T0)**:
  1. Public sign-up disabled / unauthorized — **PASS**
- **T3**: Live invite email flow deferred (Supabase admin operation; not exercised in CI)

### UJ-028: Unauthenticated admin request rejected

- **Feature**: F34 — JWT gate on admin APIs
- **Test module**: `tests/e2e/test_uj028_unauthenticated_admin.py` (9 tests)
- **Steps verified (T0)**:
  1. DM API + internal-write without `Authorization` → 401 — **PASS**
  2. Invalid/expired JWT → 401 — **PASS**
  3. ChatRAG `/api/v1/*` remains anonymous (no auth required) — **PASS**
- **T3**: H4 preflight with `Authorization` header — deferred to 13-deploy-smoke

### UJ-029: Viewer is blocked from write actions

- **Feature**: F34 — `admin` vs `viewer` roles
- **Test module**: `tests/e2e/test_uj029_role_gating.py` (4 tests)
- **Steps verified (T0)**:
  1. `viewer` → 403 on DM write routes (job create, etc.) — **PASS**
  2. `admin` → 200 on same writes — **PASS**
  3. `audit_log` records opaque `actor_id` + `actor_role` (no PII) — **PASS**
- **UI gating**: `test_role_gated_controls.test.tsx` asserts viewer cannot see delete/manage-tags/bulk controls or ingest form; admin sees all write controls. Implemented via `useIsAdmin` in `CorpusList`/`JobForm` and `AdminWriteGate` in `DocumentAdmin`.

---

## Regression spot-check (UJ-001–UJ-025)

All prior API e2e modules pass without change. Notable modules:

| Module | Tests | Journey |
|--------|-------|---------|
| `test_uj001_ask_stream.py` | 2+ | UJ-001 |
| `test_uj002_ingest_job.py` + tag resilience | 3+ | UJ-002 |
| `test_uj023_job_management.py` | 4 | UJ-023 |
| `test_uj028_unauthenticated_admin.py` | 9 | UJ-028 |
| `test_uj029_role_gating.py` | 4 | UJ-029 |

UI-only journeys (UJ-010, UJ-013–014, UJ-019–022, UJ-024–025) covered by Vitest component/app smoke per `tests/e2e/README.md` waiver.

**Planned-but-absent API modules** (covered by Vitest instead): `test_uj013_admin_dashboard.py`, `test_uj014_health_dashboard.py`, `test_uj019_top_served.py` — documented in user-journeys as "planned"; Vitest equivalents (`test_dashboard.test.tsx`, `test_health_page.test.tsx`) pass.

---

## Connectivity Matrix

| Column | Status | Evidence |
|--------|--------|----------|
| T0 in-process | **PASS** | 59 e2e + 35 integration + 363 Vitest |
| T2 connectivity (H4–H5) | **NOT RUN** | Staging env vars unset locally |
| T3 browser | **NOT RUN** | Deferred to 13-deploy-smoke / 15-service-health |

**Important:** T0 PASS does **not** prove live Supabase login or production JWT verification — T3 required after deploy.

---

## Upstream gate note

09-qa reported `overall: fail` on initial run (admin nav test + coverage gate). Remediation documented in session QA report (QA-S004-001/002 resolved). Re-run during this stage confirms admin FE **223/223** Vitest PASS — consistent with 08-verify-build PASS.

---

## Findings for 11-verify-impl (skipped in S004 lite path)

| ID | Journey | Finding | Action |
|----|---------|---------|--------|
| E2E-S004-001 | UJ-026–029 | T0 PASS — 14 new auth tests green | Approve F34 local behavior |
| E2E-S004-002 | UJ-029 UI | `test_role_gated_controls.test.tsx` added; write controls gated via `useIsAdmin` | **Resolved** (2026-06-29) |
| E2E-S004-003 | UJ-013/014/019 | API e2e modules still "planned" | Vitest covers T0; optional API modules for parity |
| E2E-S004-004 | T3 | Auth + H4 `Authorization` preflight | Verify at 13-deploy-smoke after deploy |

---

## Commands

```bash
uv run pytest tests/e2e/ -m "e2e and not live" -v
uv run pytest tests/integration/ -v
cd apps/data-management-frontend && npm test -- --run
cd apps/chat-rag-frontend && npm test -- --run
# Live (requires VECINITA_STAGING_* + Supabase deploy):
uv run pytest tests/smoke/ -m live -v
```
