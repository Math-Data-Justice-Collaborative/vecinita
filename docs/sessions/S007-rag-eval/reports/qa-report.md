# QA Report — S007 / EV-008 / F36 (#99)

> **Project**: Vecinita  
> **Date**: 2026-07-01  
> **Skill**: 09-qa (delta — admin RAG evaluation + interactive dashboard)  
> **Scope**: EV-008 F36 — eval runs API, criteria CRUD, timeseries, pivot explore dashboard (M59–M64, ADR-034, UJ-041–043)  
> **Branch**: `feat/S007-rag-eval`  
> **Session**: [S007-rag-eval](../)

```text
QA Results:
  Lint:           FAIL — 1 issue (I001 import sort, internal-write-api/app.py)
  Format:         FAIL — 1 file (eval_criteria_service.py)
  Typecheck:      FAIL — 3 errors (test_eval_dashboard_routes.py)
  Tests (Python): FAIL — 768 passed, 41 skipped, 1 failed
  Tests (FE):     PASS — chat 142/142; admin 360/360; i18n 17/17; ui 12/12
  Coverage gate:  FAIL — blocked by privacy unit test failure
  Security:       PASS — 0 CVEs; 0 secrets (check_secrets.sh); 1 gitleaks false positive (advisory)
  Cross-file:     PASS — 0 unused imports (F401/F841); 0 dangerous eval/exec patterns
  Template:       PASS — Modal isolated to infra/modal/ (+ deploy scripts)
  Data / Modal:   D6 verified; D7 verified; workspace vecinita (per data-staging-state)
  H0c CORS:       PASS — blocking test suite green
  H4/H5 live:     SKIPPED — no VECINITA_STAGING_* env vars set
```

**Overall: fail** — four blocking Python toolchain/test failures must be fixed before 12-verify-deploy. Frontends and security baselines pass.

## Executive summary

| Area | Blocking | Result |
|------|----------|--------|
| Python lint / format / typecheck | yes | **FAIL** (lint 1, format 1, typecheck 3) |
| Python full test suite | yes | **FAIL** (1 failure — privacy test stale after `eval_criteria` table) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** |
| Chat FE lint + Vitest | yes | **PASS** (142/142) |
| Admin FE lint + Vitest | yes | **PASS** (360/360) |
| Shared FE packages (i18n, ui) | yes | **PASS** (17 + 12) |
| Coverage gate (`make test-unit-coverage`) | yes | **FAIL** (same privacy test) |
| Security (CVE + secrets scripts) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, secrets, operator specs) | yes | **PASS** |
| Template conformance | yes | **PASS** |
| gitleaks working tree | no | **ADVISORY** — false positive on localStorage key |
| Staging H4–H5 live | no | **SKIPPED** — no staging URLs in env |
| D6/D7 Modal live smoke | no | **ADVISORY** — not re-run (verified 2026-06-30 per data-staging-state) |
| Outdated PyPI packages | no | **ADVISORY** — ~16 intentional pins |

**Delta scope (EV-008):** `apps/internal-write-api` (eval runs, criteria, timeseries), `apps/data-management-frontend` (EvalDashboard, criteria panels, explore pivot), `packages/eval`, `packages/shared-schemas` (eval models), `apps/database` (`eval_criteria` migration + privacy `EVAL_TABLES`), `tests/integration/test_eval_dashboard_routes.py`, `tests/e2e/test_uj041_eval_dashboard.py`, TC-117–TC-122.

**Prerequisite note:** Workflow-state routing still lists `07-build` / `08-verify-build` as `pending`, but execution plan marks M64 complete and user invoked 09-qa explicitly. This report covers the full-repo delta for EV-008.

## Commands run

```bash
# Repo root — Python (CI parity paths)
uv sync --group dev
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs
uv run pytest tests/unit/test_cors_policy.py -v
uv run ruff check --select F401,F841 apps packages tests
uv run pip-audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
gitleaks detect --no-git --config .gitleaks.toml -v
make test-unit-coverage

# Frontend (fresh npm ci at repo root required — corrupted uri-js on first attempt)
npm ci
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
npm run lint -w vecinita-frontend-i18n && npm test -w vecinita-frontend-i18n -- --run
npm run lint -w vecinita-frontend-ui && npm test -w vecinita-frontend-ui -- --run
```

**Environment:** No `VECINITA_STAGING_*` or `VECINITA_MODAL_*` env vars set. D6/D7 status read from `docs/data-staging-state.md` (verified 2026-06-30).

## Per-check details

### Lint — FAIL

```
apps/internal-write-api/vecinita_internal_write_api/app.py:3:1 I001
Import block is un-sorted or un-formatted
```

1 fixable issue (`ruff check --fix`).

### Format — FAIL

```
Would reformat: apps/internal-write-api/vecinita_internal_write_api/eval_criteria_service.py
1 file would be reformatted, 283 files already formatted
```

### Typecheck — FAIL

```
tests/integration/test_eval_dashboard_routes.py:103:16 - reportUnknownArgumentType
tests/integration/test_eval_dashboard_routes.py:103:43 - reportUnknownMemberType
tests/integration/test_eval_dashboard_routes.py:103:72 - reportUnknownVariableType
```

Line 103: `assert any(isinstance(item, dict) and item.get("slug") == slug for item in items)` — `items` from `listed.get("items")` needs narrowing after `isinstance(items, list)` check.

### Python tests — FAIL

```
1 failed, 768 passed, 41 skipped in 44.39s
```

**Failure:**

```
tests/unit/database/test_privacy.py::test_find_missing_eval_tables_reports_absent_tables
AssertionError: assert {'eval_criteria', 'eval_run_items', 'eval_runs'} == {'eval_run_items', 'eval_runs'}
Extra items in the left set: 'eval_criteria'
```

**Root cause:** EV-008 added `eval_criteria` to `EVAL_TABLES` in `apps/database/vecinita_database/privacy.py` but the unit test expectation was not updated.

### H0c CORS — PASS

`tests/unit/test_cors_policy.py` — all collected tests passed (env-gated skips expected).

### Frontend — PASS

| App / package | Lint | Tests |
|---------------|------|-------|
| chat-rag-frontend | PASS | 142/142 (26 files) |
| data-management-frontend | PASS | 360/360 (57 files) |
| vecinita-frontend-i18n | PASS | 17/17 |
| vecinita-frontend-ui | PASS | 12/12 |

**Note:** First chat-rag-frontend lint attempt failed with corrupted `node_modules/uri-js` (`SyntaxError: Unexpected end of input`). Fresh `npm ci` at repo root resolved it — not a source defect.

Expected Vitest stderr from negative hook boundary tests (`useAuth`, `useTheme`, `useLocale` outside providers) — not failures.

### Coverage gate — FAIL

`make test-unit-coverage` exits non-zero due to the same `test_find_missing_eval_tables_reports_absent_tables` failure before FE branch gate is evaluated.

### Security — PASS (with advisory)

| Layer | Result |
|-------|--------|
| pip-audit | No known vulnerabilities (workspace packages skipped — expected) |
| check_secrets.sh | OK |
| check_modal_no_database_url.sh | OK |
| check_openapi_specs.sh | OK |
| check_no_operator_specs_tracked.sh | OK |
| gitleaks (tree) | 1 hit — **false positive** (see QA-S007-001) |
| Dangerous patterns (`pickle.loads`, `eval()`, `exec()`) | 0 in apps/ + packages/ |

### Cross-file — PASS

- F401/F841: 0 issues.
- Circular deps: not detected (import graph stable).
- Public docstrings: not audited (advisory).

### Template & platform — PASS

| Criterion | Result |
|-----------|--------|
| Layout (`apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/`) | OK |
| `import modal` only under `infra/modal/` + deploy scripts | OK (5 files) |
| Modal workspace | `vecinita` per data-staging-state D6/D7 |
| No `DATABASE_URL` in Modal paths | OK |
| OpenAPI YAML parse | OK |

### Data staging & deploy readiness

| Asset | Status | Notes |
|-------|--------|-------|
| D1–D5, D8–D9 | verified | Fixtures + migrations |
| D6 FastEmbed | verified | 2026-06-30; `vecinita--vecinita-embedding-*` |
| D7 Qwen LLM | verified | 2026-06-30; not re-smoked this run |
| Phase 4 H1–H3 live | advisory | No `VECINITA_STAGING_CHAT_URL` — defer to 13-deploy-smoke |
| H4–H5 connectivity | advisory | No `VECINITA_STAGING_*_FRONTEND_URL` — see connectivity-gates |

## Findings for 11-verify-impl / 12-verify-deploy

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S007-B01 | **blocking** | I001 unsorted imports in `internal-write-api/app.py` | `uv run ruff check --fix apps/internal-write-api/vecinita_internal_write_api/app.py` |
| QA-S007-B02 | **blocking** | `eval_criteria_service.py` needs format | `uv run ruff format apps/internal-write-api/vecinita_internal_write_api/eval_criteria_service.py` |
| QA-S007-B03 | **blocking** | basedpyright errors in `test_eval_dashboard_routes.py:103` | Narrow `items` list element type before `any(...)` |
| QA-S007-B04 | **blocking** | Privacy test expects 2 eval tables; `EVAL_TABLES` now includes `eval_criteria` | Update `test_find_missing_eval_tables_reports_absent_tables` assertion |
| QA-S007-001 | advisory | gitleaks flags `EXPLORE_STORAGE_KEY = "vecinita.eval.explore.v1"` as generic-api-key | Add allowlist entry in `.gitleaks.toml` or rename constant pattern |
| QA-S007-002 | advisory | H4–H5 live connectivity not run | Set staging URLs + `scripts/deploy/verify_connectivity.sh` at 13-deploy-smoke |
| QA-S007-003 | advisory | ~16 outdated PyPI packages | Accepted intentional pins (same as S006 QA-S006-006) unless ADR bump |
| QA-S007-004 | advisory | workflow-state routing lists 07/08 pending while execution plan shows M64 complete | Reconcile via workflow-state-manager after 08-verify-build |
| QA-S007-005 | advisory | Vitest stderr from negative hook tests | Accepted — expected test behavior |

## Phase / execution-plan alignment

- **Phase 14 (EV-008)** M59–M64 marked complete in `docs/execution-plan.md`.
- **Blocking for merge:** QA-S007-B01 through B04 must be green before PR merge / 12-verify-deploy.
- **Next stages after fix:** 08-verify-build (if not recorded) → re-run 09-qa → 10-e2e → 12-verify-deploy → 13-deploy-smoke.

## Handoff

**11-verify-impl** is skipped in evolve-lite routing. Present blocking items at fix pass or **12-verify-deploy**:

1. Fix four blocking Python issues (lint, format, typecheck, privacy test).
2. Re-run `make test-unit-coverage` to confirm FE branch ≥95% gate.
3. Defer live staging/connectivity advisories to **13-deploy-smoke**.
