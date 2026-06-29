# QA Report — S004 / EV-005 / F34

> **Project**: Vecinita  
> **Date**: 2026-06-29  
> **Skill**: 09-qa (delta — F34 Supabase admin auth)  
> **Scope**: EV-005 F34 — admin FE/API, internal-write-api, `vecinita_shared_schemas.auth`, UJ-026–029, TC-077–086  
> **Branch**: `feat/S004-supabase-auth` (uncommitted work)  
> **Session**: [S004-supabase-auth](../)

```text
QA Results:
  Lint:           PASS — 0 issues (Python); chat FE PASS after root npm ci; admin FE 2 warnings
  Format:         PASS — 0 files
  Typecheck:      PASS — 0 errors
  Tests (Python): PASS — 546 passed, 38 skipped, 0 failed
  Tests (FE):     FAIL — chat 134/134; admin 219 passed, 1 failed (+ 2 worker errors)
  Coverage gate:  FAIL — admin FE vitest --coverage worker crash + 1 assertion failure
  Security:       PASS — 0 CVEs; 0 secrets (tree); gitleaks clean
  Cross-file:     PASS — 0 unused imports (F401/F841)
  Template:       PASS — Modal isolated to infra/modal/; guards green
  Data / Modal:   D6 verified; D7 staged_procedure; workspace vecinita
  H0c CORS:       PASS
```

**Overall: FAIL** — admin frontend Vitest failure and coverage gate regression block sign-off.

## QA remediation (2026-06-29)

| ID | Status | Resolution |
|----|--------|------------|
| QA-S004-001 | **resolved** | Moved unknown-route redirect to top-level `path="*"` in `App.tsx` (RR6 nested splat did not match absolute child paths); added `waitFor` in `test_admin_nav` |
| QA-S004-002 | **resolved** | `make test-unit-coverage` PASS — combined 99.1% line, FE branches ≥95% |

Re-verification (post-fix, root `npm ci`):

```text
  Tests (admin FE): 223/223 passed
  Coverage gate:    PASS
```

## Executive summary

| Area | Blocking | Result |
|------|----------|--------|
| Python lint / format / typecheck | yes | **PASS** |
| Python full test suite | yes | **PASS** (546 passed, 38 skipped) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** |
| Chat FE lint + Vitest | yes | **PASS** (134/134; lint requires root `npm ci`) |
| Admin FE lint | yes | **PASS** (0 errors, 2 `react-refresh` warnings) |
| Admin FE Vitest | yes | **FAIL** — `test_admin_nav` unknown-route redirect |
| Coverage gate (`make test-unit-coverage`) | yes | **FAIL** — admin FE under `--coverage` |
| Security (CVE + secrets + gitleaks tree) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, secrets) | yes | **PASS** |
| Template conformance | yes | **PASS** |
| Staging H4–H5 live | no | **SKIPPED** — no `VECINITA_STAGING_*` env |
| D7 LLM weights verify | no | **ADVISORY** — `staged_procedure` |
| 07-build / Phase 11 gate bookkeeping | no | **ADVISORY** — M43–M46 statuses open |

**Regression vs 08-verify-build (2026-06-29):** Milestone verify reported admin FE **223/223** and coverage gate **PASS**. This 09 re-run shows **1 failing** admin nav test and coverage failure — likely auth-route guard interaction or flaky vitest worker under load. Treat as blocking until green on a clean `npm ci` + full suite re-run.

## Commands run

```bash
# Repo root — Python
uv run ruff check apps packages tests
uv run ruff format --check apps packages tests
uv run basedpyright apps packages tests
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval
uv run pytest tests/unit/test_cors_policy.py
uv run ruff check --select F401,F841 apps packages tests
uv run pip-audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
gitleaks detect --no-git --config .gitleaks.toml

# Frontend (requires root npm ci first)
npm ci   # repo root
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
make test-unit-coverage
```

## Per-check details

### Lint / format / typecheck — PASS

- **ruff check**: All checks passed (0 issues).
- **ruff format --check**: 197 files already formatted.
- **basedpyright**: 0 errors, 0 warnings, 0 notes.

### Python tests — PASS

```
546 passed, 38 skipped in ~26–107s (varies by DB/migrate warmup)
```

Skips are env-gated live/staging tests (expected). No failures.

### H0c CORS — PASS

`tests/unit/test_cors_policy.py` — all runnable cases green (4 passed, remainder skipped per env).

### Frontend — mixed

**chat-rag-frontend**

- **Lint**: PASS after root `npm ci`. Initial app-only `npm ci` produced corrupted `esquery.min.js` (SyntaxError) — see QA-S004-004.
- **Vitest**: **134/134 passed** (25 files).

**data-management-frontend**

- **Lint**: PASS with 2 warnings in `AuthContext.tsx` (`react-refresh/only-export-components`).
- **Vitest**: **FAIL** — 219 passed, **1 failed**, 2 worker errors.

Failing test:

```
src/test/test_admin_nav.test.tsx > Admin navigation > redirects unknown routes to /dashboard
TestingLibraryElementError: Unable to find an element with the text: /overview of your corpus/i
```

Likely cause: F34 auth gate redirects unauthenticated `/unknown` to login instead of dashboard, or dashboard copy changed post-auth.

Worker errors (`vitest-pool: Worker exited unexpectedly`) occurred under parallel load — may amplify flakiness.

### Coverage gate — FAIL

`make test-unit-coverage` → `scripts/test/unit_coverage.sh`:

- Python unit coverage: completed (first stage).
- Admin FE `vitest run --coverage`: **FAIL** — 1 failed test (`test_admin_nav`), 1 unhandled worker error.
- Gate never reached `print_unit_coverage_summary.py --enforce`.

Prior 08 run reported ≥95% FE branches; this run did not complete enforcement.

### Security — PASS

| Layer | Result |
|-------|--------|
| pip-audit | 0 vulnerabilities (workspace packages skipped — expected) |
| check_secrets.sh | OK |
| gitleaks `--no-git` | no leaks found (~9.4 MB scanned) |
| Dangerous patterns (`pickle.loads`, `eval(`, `exec(`) in apps/packages | none |

### Cross-file — PASS

- F401/F841: 0 unused imports/vars.
- Circular deps: not exhaustively scanned (advisory).
- `import modal` only under `infra/modal/` (3 files) — conforms to template.

### Template & platform — PASS

| Criterion | Status |
|-----------|--------|
| Layout `apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/` | OK |
| Modal isolation | OK |
| No `DATABASE_URL` in Modal paths | OK (`check_modal_no_database_url.sh`) |
| OpenAPI YAML parse | OK |
| Modal workspace | `vecinita` per `docs/data-staging-state.md` D6 |

### Data staging & deploy — advisories

| Asset | Status |
|-------|--------|
| D1–D5, D8–D9 | verified |
| D6 FastEmbed | verified (`vecinita--` prefix) |
| D7 Qwen LLM | staged_procedure |
| Staging deploy | Pre-F34 commit (`4f3f741`); H4–H5 not run |
| `VECINITA_STAGING_*` | not set in QA environment |

### Dependencies — advisory

~53 outdated pip packages (`uv pip list --outdated`); intentional LlamaIndex pins per `docs/dependency-inventory.md`.

## Findings for 11-verify-impl (lite path: user sign-off)

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S004-001 | **blocking** | Admin FE `test_admin_nav` fails: unknown route no longer lands on dashboard copy | Fix auth/route guard or update test for F34 login redirect; re-run admin Vitest |
| QA-S004-002 | **blocking** | `make test-unit-coverage` fails on admin FE `--coverage` | Resolve QA-S004-001; investigate vitest worker OOM/crash under coverage |
| QA-S004-003 | advisory | `AuthContext.tsx` react-refresh warnings (2) | Extract hooks to separate file or suppress with justification |
| QA-S004-004 | advisory | App-only `npm ci` breaks hoisted ESLint deps | Document: always `npm ci` at repo root before FE QA/CI parity |
| QA-S004-005 | advisory | `07-build` routing_plan still `in_progress`; M43–M46 tasks `pending` in execution-plan | Close bookkeeping after commits; run Phase 11 gate |
| QA-S004-006 | advisory | Staging does not include F34 auth | Deploy + run `staging_smoke.sh` / H4–H5 when ready |
| QA-S004-007 | advisory | H4–H5 live connectivity skipped (no staging URLs) | Set `VECINITA_STAGING_*_FRONTEND_URL`; run `verify_connectivity.sh` |
| QA-S004-008 | advisory | D7 LLM weights `staged_procedure` | `scripts/stage_modal_weights.sh` when GPU budget approved |
| QA-S004-009 | advisory | ~53 outdated pip packages | Defer unless ADR bump; pip-audit clean |

## Phase / execution-plan alignment

- **Phase 11** (EV-005 F34): M47 marked complete; M43–M46 code on branch, tasks still `pending` in plan.
- **Lite path**: 11-verify-impl skipped; this report feeds user sign-off directly.
- **Parallel**: 10-e2e still pending in routing plan.

## Handoff

1. Fix **QA-S004-001** and **QA-S004-002** before merge/deploy.
2. Re-run `make test-unit-coverage` and full admin Vitest on clean `npm ci`.
3. Proceed to **10-e2e** after blocking items green (or document waiver in 11/user sign-off).
