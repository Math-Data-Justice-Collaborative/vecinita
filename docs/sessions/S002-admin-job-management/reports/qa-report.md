# QA Report — S002 Admin Job Management

> **Project**: Vecinita  
> **Date**: 2026-06-26  
> **Skill**: 09-qa (partial rerun post-14-hotfix)  
> **Scope**: S002 delta — F32 (#89), #88 ingest tag resilience, 14-hotfix bugs  
> **Branch**: `main` @ `6b72ba0` (uncommitted hotfix artifacts on working tree)  
> **Session**: S002-admin-job-management

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files need formatting (186 checked)
  Typecheck:      FAIL — 2 errors (reportAny in uncommitted bug repro test)
  Tests (Python): FAIL — 549 passed, 38 skipped, 1 failed (live Modal GET /jobs)
  Tests (FE):     PASS — 283 passed (chat 84, data-mgmt 193, i18n 5, ui 1)
  Coverage gate:  PASS — FE branch ≥95% (chat 95.7%, data-mgmt 95.6%)
  Security:       PASS — 0 CVEs; 0 secrets (tree); 0 gitleaks (tree)
  Cross-file:     PASS — 0 unused imports (F401/F841)
  Dependencies:   ~52 outdated (advisory; LlamaIndex pins intentional)
  Template:       PASS — api+worker layout, Modal isolation, OpenAPI, CI parity
  Data / Modal:   D1–D5,D8–D9 verified; D6 verified; D7 staged_procedure; workspace vecinita
```

**Overall: FAIL** (blocking: typecheck; live deploy probe)

---

## Executive Summary

| Category | Status | Blocking | Advisory |
|----------|--------|----------|----------|
| Lint (ruff) | **PASS** | 0 | 0 |
| Format (ruff format) | **PASS** | 0 | 0 |
| Typecheck (basedpyright) | **FAIL** | 2 | 0 |
| Tests (Python, full QA path) | **FAIL** | 1 live | 38 env-gated skips |
| Tests (Python, CI parity) | **PASS** | 0 | — |
| Tests (Frontend) | **PASS** | 0 | 0 |
| Coverage gate | **PASS** | 0 | 0 |
| Security — CVEs | **PASS** | 0 | 0 |
| Security — secrets | **PASS** | 0 | 0 |
| Security — gitleaks tree | **PASS** | 0 | 0 |
| Security — dangerous patterns | **PASS** | 0 | 0 |
| Cross-file | **PASS** | 0 | 0 |
| Template conformance | **PASS** | 0 | 0 |
| H0c CORS | **PASS** | 0 | 4 skipped (no `DATABASE_URL`) |
| H0i integration | **PASS** | 0 | 0 |
| H4–H5 staging live | **ADVISORY** | — | Not run (staging env vars unset locally) |
| Production GET /jobs | **FAIL** | 1 | Deploy gap — code on `main`, Modal image stale |

**Scope note:** Initial S002 09-qa completed before **14-hotfix**. This rerun includes uncommitted bug repro tests and local aria fix in `AdminLayout.tsx`. **14-hotfix** remains `in_progress` until Modal redeploy clears live GET /jobs probe.

---

## Commands Run

```bash
uv run ruff check apps packages tests
uv run ruff format --check apps packages tests
uv run basedpyright apps packages tests
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs -q --tb=no
uv run pytest tests/unit/test_cors_policy.py -q
make test-unit-coverage
uv run pip-audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
gitleaks detect --no-git --config .gitleaks.toml
uv run ruff check --select F401,F841 apps packages tests
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
cd packages/frontend-i18n && npm test -- --run
cd packages/frontend-ui && npm test -- --run
```

---

## Blocking Failures

### Typecheck — `tests/bugs/test_bug_2026_06_26_get_jobs_405_modal_production.py`

```
reportAny: Type of "body" is Any (line 44)
reportAny: Type of "get" is Any (line 45)
```

`response.json()` is untyped. Fix: use `response_json_object` helper (existing pattern in e2e tests) before merge.

### Live probe — GET /jobs 405 on production Modal

```
FAILED tests/bugs/test_bug_2026_06_26_get_jobs_405_modal_production.py::test_live_modal_get_jobs_list_returns_200
Expected GET /jobs 200 on production Modal, got 405: {"detail":"Method Not Allowed"}
```

**Root cause (BUG-2026-06-26):** infra/deploy — `GET /jobs` exists in `create_app()` on `main`; production Modal image predates deploy. **Not a code defect.** CI does not include `tests/bugs/` in pytest path.

---

## CI Parity Note

`.github/workflows/ci.yml` runs:

```bash
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval
```

Without `tests/bugs/`, Python suite is **green** (549 passed, 38 skipped). **basedpyright** on `tests/` will fail CI if the untyped bug repro test is committed without fix.

---

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|----------------|
| QA-S002-001 | **blocking** | basedpyright `reportAny` in live GET /jobs repro test | Type `response.json()` via `response_json_object` before commit |
| QA-S002-002 | **blocking** | Production Modal `GET /jobs` → 405 | `modal deploy` data-management app from S002/`main` HEAD; re-run live probe |
| QA-S002-003 | advisory | Admin FE aria fix uncommitted | Commit `SheetDescription` in `AdminLayout.tsx`; redeploy admin static site |
| QA-S002-004 | advisory | Staging still on S001 branch (`4f3f741`) | Update DO branch pins + redeploy after merge; see `deployment.staging` in workflow-state |
| QA-S002-005 | advisory | D7 `staged_procedure` | Run `scripts/stage_modal_weights.sh` if LLM volume unverified |
| QA-S002-006 | advisory | ~52 outdated PyPI packages | Intentional LlamaIndex pins; no action unless ADR bump |

---

## Connectivity

| Gate | Status | Notes |
|------|--------|-------|
| H0c (`test_cors_policy.py`) | **PASS** | Includes data-mgmt `OPTIONS /jobs` |
| H0i (`tests/integration`) | **PASS** | 35 tests |
| H4–H5 live | **ADVISORY** | `VECINITA_STAGING_*` unset in this run; prior S001 health pass on staging URLs |

---

## Phase / Execution Alignment

S002 evolve-lite routing: 07-build ✅ → 09-qa (this rerun) → 14-hotfix (in progress) → 10-e2e → 12-verify-deploy → 13-deploy-smoke. **11-verify-impl** user-amended into this invocation (was originally skipped).
