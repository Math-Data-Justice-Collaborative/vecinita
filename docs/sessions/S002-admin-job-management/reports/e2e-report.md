# E2E Behavior Report — S002 Admin Job Management

> **Generated**: 2026-06-26  
> **Session**: S002-admin-job-management  
> **Mechanism**: API + Frontend (pytest `TestClient`, mocked Modal; Vitest)  
> **Branch**: `main` @ `6b72ba0`  
> **Journeys tested**: 23 (UJ-001–UJ-023) + #88 tag resilience

## Summary

| Tier | Command | Result |
|------|---------|--------|
| **T0** | `uv run pytest tests/e2e/ -m "e2e and not live"` | **45 passed**, 0 failed |
| **T1** | `uv run pytest tests/integration/` | **35 passed**, 0 failed |
| **T3 live** | `tests/bugs/...get_jobs_405...` + staging smoke | **FAIL** — production `GET /jobs` → 405 (undeployed Modal) |
| **FE Vitest** | both frontends + packages | **283 passed** |

| # | Journey | Mechanism | Tests | T0 | T3 | Status |
|---|---------|-----------|-------|----|----|--------|
| 23 | **UJ-023 View & track jobs** | API | `test_uj023_job_management.py` (4) | **PASS** | **FAIL** | T0 green; live blocked by Modal deploy |
| 2 | **UJ-002 Ingest URLs** (+ #88) | API | `test_uj002_ingest_tag_resilience.py` | **PASS** | pending | Best-effort tagging verified T0 |
| 1–22 | UJ-001–UJ-022 | mixed | existing modules | PASS | pending/waived | No regressions |

**Overall T0: PASS** — 45/45  
**Overall T3 (F32 Jobs tab): FAIL** — production Modal lacks `GET /jobs` route until redeploy

---

## Journey Details

### UJ-023: View & track jobs in Job Management tab (F32, #89)

- **Feature**: F32 — Admin Job Management tab + `GET /jobs` list API (ADR-023)
- **Mechanism**: API via full data-management `create_app()` TestClient
- **Test module**: `tests/e2e/test_uj023_job_management.py`
- **Steps verified (T0)**:
  1. `GET /jobs` returns all jobs newest-first — **PASS**
  2. `GET /jobs?status=failed` filters correctly — **PASS**
  3. Failed jobs expose `error_code` / `error_message` — **PASS**
  4. Jobs persist independent of client navigation (server source of truth) — **PASS**
- **T3**: Production `GET https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs` → **405** (BUG-2026-06-26). Code on `main` registers route; Modal image stale.

### UJ-002 extension: Ingest resilient to non-JSON LLM tags (#88)

- **Feature**: F20 tagging (best-effort per ADR-023)
- **Test module**: `tests/e2e/test_uj002_ingest_tag_resilience.py`
- **Steps verified (T0)**:
  1. `POST /jobs` ingest with LLM returning non-JSON — job reaches `completed` (not `failed`) — **PASS**
  2. Document written without LLM tags — **PASS**
- **Interview (11)**: "When tag inference fails, does ingest still complete?"

### UJ-022: Admin i18n (F31) — regression spot-check

- **FE**: `JobsPage` uses `admin.nav.jobs` / `admin.jobs.*` keys — covered in data-mgmt Vitest suite (193 tests pass)
- **T3 browser**: deferred (no browser MCP this run)

---

## Connectivity Matrix

| Column | Status | Evidence |
|--------|--------|----------|
| T0 in-process | **PASS** | 45 e2e + 35 integration |
| T2 connectivity (H4–H5) | **ADVISORY** | Staging env vars unset locally; prior S001 H4–H5 pass documented |
| T3 browser | **NOT RUN** | Deferred to 13-deploy-smoke / 15-service-health post-deploy |

**Important:** T0 PASS does **not** prove production Jobs tab works — T3 blocked on Modal redeploy (QA-S002-002).

---

## Findings for 11-verify-impl

| ID | Journey | Finding | Action |
|----|---------|---------|--------|
| E2E-S002-001 | UJ-023 | T0 PASS; T3 FAIL (405) | Modal data-mgmt deploy before sign-off |
| E2E-S002-002 | UJ-002 | #88 tag resilience T0 PASS | Approve best-effort behavior |
| E2E-S002-003 | UJ-023 FE | No dedicated Vitest journey test for Jobs page table | Optional: add `JobsPage.test.tsx` (advisory) |

---

## Commands

```bash
uv run pytest tests/e2e/ -m "e2e and not live" -v
uv run pytest tests/integration/ -v
cd apps/data-management-frontend && npm test -- --run
# Live (requires VECINITA_MODAL_PROXY_KEY):
uv run pytest tests/bugs/test_bug_2026_06_26_get_jobs_405_modal_production.py -m live -v
```
