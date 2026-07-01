# QA Report — S007 / EV-008 / F36 (#99)

> **Project**: Vecinita  
> **Date**: 2026-07-01 (rerun)  
> **Skill**: 09-qa (delta — admin RAG evaluation + interactive dashboard)  
> **Scope**: EV-008 F36 — eval runs API, criteria CRUD, timeseries, pivot explore dashboard (M59–M64, ADR-034, UJ-041–043)  
> **Branch**: `feat/S007-rag-eval` @ `9361e4a`  
> **Session**: [S007-rag-eval](../)

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files
  Typecheck:      PASS — 0 errors
  Tests (Python): PASS — 769 passed, 41 skipped, 0 failed
  Tests (FE):     PASS — chat 142/142; admin 360/360; i18n 17/17; ui 12/12
  Tests (UI):     PASS — Playwright 20 passed, 2 skipped (staging env-gated)
  Coverage gate:  FAIL — internal-write-api + data-management-frontend below 95%
  Security:       PASS — 0 CVEs; gitleaks clean (tree)
  Cross-file:     PASS — 0 unused imports; 0 dangerous eval/exec patterns
  Template:       PASS — Modal isolated to infra/modal/ (+ deploy scripts)
  Data / Modal:   D6 verified; D7 verified; workspace vecinita (per data-staging-state)
  H0c CORS:       PASS — 12 passed, 6 skipped (env-gated)
  H4/H5 live:     SKIPPED — no VECINITA_STAGING_* env vars set
```

**Overall: fail** — coverage gate blocking (EV-008 eval surfaces under-tested). All prior B01–B04 blockers from the 2026-07-01 first pass are **resolved**.

## Executive summary

| Area | Blocking | Result |
|------|----------|--------|
| Python lint / format / typecheck | yes | **PASS** |
| Python full test suite | yes | **PASS** (769 passed, 41 skipped) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** |
| Chat FE lint + Vitest | yes | **PASS** (142/142) |
| Admin FE lint + Vitest | yes | **PASS** (360/360) |
| Shared FE packages (i18n, ui) | yes | **PASS** (17 + 12) |
| Playwright UI E2E (`make test-ui`) | yes | **PASS** (20 passed; 2 staging skipped) |
| Coverage gate (`make test-unit-coverage`) | yes | **FAIL** |
| Security (CVE + secrets scripts) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, secrets, operator specs) | yes | **PASS** |
| Template conformance | yes | **PASS** |
| gitleaks working tree | no | **ADVISORY** — 4 false positives |
| Staging H4–H5 live | no | **SKIPPED** — no staging URLs in env |
| D6/D7 Modal live smoke | no | **ADVISORY** — not re-run (verified 2026-06-30 per data-staging-state) |
| Outdated PyPI packages | no | **ADVISORY** — 16 intentional pins |

**Delta from prior 09-qa (same day):** QA-S007-B01 through B04 (lint, format, typecheck, privacy test) are green. New blocking finding: unit-test coverage below the 95% line/branch gate for EV-008 components.

**Delta scope (EV-008):** `apps/internal-write-api` (eval runs, criteria, timeseries), `apps/data-management-frontend` (EvalDashboard, criteria panels, explore pivot), `packages/eval`, `packages/shared-schemas`, `apps/database` (`eval_criteria` migration + privacy `EVAL_TABLES`), integration/e2e tests TC-117–TC-122.

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

# Coverage gate (requires Node >= 24 per .nvmrc)
export PATH="$HOME/.local/share/fnm:$PATH" && eval "$(fnm env)" && fnm use 24
make test-unit-coverage

# Frontend
npm ci
npm run lint -w vecinita-chat-rag-frontend && npm test -w vecinita-chat-rag-frontend -- --run
npm run lint -w vecinita-data-management-frontend && npm test -w vecinita-data-management-frontend -- --run
npm run lint -w vecinita-frontend-i18n && npm test -w vecinita-frontend-i18n -- --run
npm run lint -w vecinita-frontend-ui && npm test -w vecinita-frontend-ui -- --run

# Playwright UI E2E (Node 24)
make test-ui
```

**Environment:** No `VECINITA_STAGING_*` or `VECINITA_MODAL_*` env vars set. Shell default Node v22.23.0; coverage gate re-run with fnm Node v24.18.0 per `.nvmrc`.

## Per-check details

### Lint — PASS

All checks passed (284 files checked under `apps packages tests infra scripts`).

### Format — PASS

284 files already formatted.

### Typecheck — PASS

0 errors, 0 warnings, 0 notes.

### Python tests — PASS

```
769 passed, 41 skipped in 101.56s
```

Skips are env-gated (staging, Modal URLs, live connectivity) — expected.

### H0c CORS — PASS

```
12 passed, 6 skipped in 1.56s
```

### Frontend — PASS

| App / package | Lint | Tests |
|---------------|------|-------|
| chat-rag-frontend | PASS | 142/142 (26 files) |
| data-management-frontend | PASS | 360/360 (57 files) |
| vecinita-frontend-i18n | PASS | 17/17 |
| vecinita-frontend-ui | PASS | 12/12 |

Expected Vitest stderr from negative hook boundary tests (`useAuth`, `useTheme`, `useLocale` outside providers) — not failures.

### Playwright UI E2E — PASS

```
20 passed, 2 skipped (29.8s)
```

Skipped: `tests/ui/staging/staging-smoke.spec.ts` (no staging URLs). Includes UJ-041 eval dashboard tab specs.

### Coverage gate — FAIL

`make test-unit-coverage` (Node 24) exits non-zero:

```
Coverage gate failed:
apps/internal-write-api: line coverage 87.9% below 95%
apps/internal-write-api: branch coverage 82.8% below 95%
apps/data-management-frontend: line coverage 94.3% below 95%
apps/data-management-frontend: branch coverage 85.8% below 95%
```

Combined totals (all components): **96.0% lines**, but per-component enforcement fails on EV-008 surfaces. Primary gaps align with new eval API (`eval_criteria_service`, `eval_service`, timeseries routes) and dashboard components (explore pivot, criteria CRUD panels).

### Security — PASS (with advisory)

| Layer | Result |
|-------|--------|
| pip-audit | No known vulnerabilities (workspace packages skipped — expected) |
| check_secrets.sh | OK |
| check_modal_no_database_url.sh | OK |
| check_openapi_specs.sh | OK |
| check_no_operator_specs_tracked.sh | OK |
| gitleaks (tree) | 4 hits — **false positives** (see QA-S007-001) |
| Dangerous patterns (`pickle.loads`, `eval()`, `exec()`) | 0 in apps/ + packages/ |

### Cross-file — PASS

- F401/F841: 0 issues.
- Circular deps: not detected.
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

## Advisory remediation (2026-07-01)

All QA-S007-001 through QA-S007-006 advisories addressed. See findings table below. **Blocking QA-S007-B05 (coverage gate) remains open.**

## Findings for 11-verify-impl / 12-verify-deploy

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S007-B05 | **blocking** | Coverage gate: `internal-write-api` 87.9% lines / 82.8% branches; `data-management-frontend` 94.3% lines / 85.8% branches — all below 95% threshold | Add unit tests for eval criteria/timeseries API paths and dashboard explore/criteria components; re-run `make test-unit-coverage` on Node 24 |
| QA-S007-B01 | ~~blocking~~ **resolved** | I001 unsorted imports | Fixed — lint PASS |
| QA-S007-B02 | ~~blocking~~ **resolved** | `eval_criteria_service.py` format | Fixed — format PASS |
| QA-S007-B03 | ~~blocking~~ **resolved** | basedpyright errors in integration test | Fixed — typecheck PASS |
| QA-S007-B04 | ~~blocking~~ **resolved** | Privacy test stale `EVAL_TABLES` | Fixed — 769 pytest PASS |
| QA-S007-001 | ~~advisory~~ **resolved** | gitleaks false positives | `.gitleaks.toml` path + regex allowlists; `docs/security/gitleaks-resolution.md` §QA-S007-001 |
| QA-S007-002 | ~~advisory~~ **resolved** | H4–H5 live connectivity not run locally | `infra/staging/.env.example`, `make verify-connectivity`, `tests/smoke/test_verify_connectivity_script.py`; live run at 13-deploy-smoke |
| QA-S007-003 | ~~advisory~~ **resolved** | 16 outdated PyPI packages (LlamaIndex stack) | Documented intentional pins in `docs/dependency-inventory.md` §PyPI packages intentionally not upgraded |
| QA-S007-004 | ~~advisory~~ **resolved** | workflow-state 07/08 pending | Reconciled via workflow-state-manager; `verification-report.md` added |
| QA-S007-005 | ~~advisory~~ **resolved** | Vitest stderr from negative hook tests | Shared `vitestConsoleFilter` + `silent: 'passed-only'` in both frontend vitest configs |
| QA-S007-006 | ~~advisory~~ **resolved** | Default shell Node 22 fails coverage gate script guard | `ensure_node24.sh` prepends fnm to PATH; `npm_with_lock.sh` already invokes it |

## Phase / execution-plan alignment

- **Phase 14 (EV-008)** M59–M64 marked complete in `docs/execution-plan.md`.
- **08-verify-build** not yet recorded complete in workflow-state routing (07/08 still `pending`).
- **Handoff:** 10-e2e may proceed in parallel per routing plan, but **12-verify-deploy blocked** until QA-S007-B05 resolved.

## Prior report

First pass same day (pre-remediation): overall **fail** on B01–B04. This rerun confirms those fixes and surfaces coverage as the remaining blocker.
