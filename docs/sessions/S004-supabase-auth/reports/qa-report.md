# QA Report — S004 / EV-005 / F34

> **Project**: Vecinita  
> **Date**: 2026-06-29 (re-run)  
> **Skill**: 09-qa (delta — F34 Supabase admin auth)  
> **Scope**: EV-005 F34 — admin FE/API, internal-write-api, `vecinita_shared_schemas.auth`, UJ-026–029, TC-077–086  
> **Branch**: `feat/S004-supabase-auth`  
> **Session**: [S004-supabase-auth](../)

```text
QA Results:
  Lint:           PASS — 0 issues (Python + both FE apps)
  Format:         PASS — 234 files
  Typecheck:      PASS — 0 errors
  Tests (Python): PASS — 603 passed, 33 skipped, 0 failed
  Tests (FE):     FAIL — chat 142/142; admin 230/230 assertions but npm exit 1 (2 vitest unhandled errors)
  Coverage gate:  PASS — 100% line/branch (make test-unit-coverage)
  Security:       PASS — 0 CVEs; 0 secrets (tree); gitleaks clean
  Cross-file:     PASS — 0 unused imports (F401/F841)
  Template:       PASS — Modal isolated to infra/modal/ (+ deploy script); guards green
  Data / Modal:   D6 verified; D7 staged_procedure; workspace vecinita
  H0c CORS:       PASS — 10/10
```

**Overall: FAIL → remediated (pass_with_advisories)** — admin frontend Vitest exited non-zero despite all assertions passing (unhandled rejection in `DashboardPage` async cleanup). Fixed 2026-06-29; see [QA remediation](#qa-remediation-2026-06-29).

## QA remediation (2026-06-29)

| ID | Status | Resolution |
|----|--------|------------|
| QA-S004-010 | **resolved** | Added `isActive()` guards (matching `CorpusList`/`JobsPage`, BUG-2026-06-14) to `DashboardPage`, `HealthPage`, `AuditPage` so on-mount fetches no longer `setState` after unmount. Fixed `test_auth_login_protected_routes.test.tsx` (added `afterEach(cleanup)` + stubbed the dashboard stats fetch). Added regression test `test_bug_2026_06_29_admin_page_unmount_during_load.test.tsx` (resolve + reject scenarios per page). Admin FE Vitest now **exits 0** (242 passed); coverage gate **100%** line/branch. |
| QA-S004-011 | **resolved** | Bumped **Node 20 → 24 LTS**: `ci.yml` `setup-node` ×3, added `.nvmrc` (24), root `package.json` `engines.node>=24`; docs updated (`spec.md` H10, `execution-plan.md`, `LOCAL_DEV.md`, `decisions.md` TP-031 + new **TP-S004-11**, `ADR-019`, `dependency-inventory.md`). |
| QA-S004-003 | **resolved (pre-existing)** | Auth hooks already split into `src/auth/authContext.ts` (hooks) vs `src/auth/AuthContext.tsx` (provider); `eslint src` is clean — no `react-refresh/only-export-components` warnings. |
| QA-S004-004 | **documented** | `docs/LOCAL_DEV.md` + this report: always `npm ci` at **repo root** (hoisted workspace) before FE lint/test. |
| QA-S004-012 | **accepted exception** | `scripts/deploy/read_data_mgmt_secret.py` imports `modal` — it is a one-off deploy/ops helper, not app code; outside the `infra/modal/` app-isolation rule by design. No CI guard flags it. |
| QA-S004-005/006/007/008/009 | **deferred (advisory)** | Bookkeeping, staging deploy + H4–H5 live, D7 LLM weights, and outdated-pin items unchanged — require env/GPU/ops actions outside this remediation. |

Re-verification (local, after `npm ci` at repo root):

```text
  Admin FE Vitest:  242 passed — exit 0
  Coverage gate:    PASS — combined 100% (1278/1278 branches; FE 464/464)
  Lint / typecheck / format (admin FE): PASS
```

## Executive summary

| Area | Blocking | Result |
|------|----------|--------|
| Python lint / format / typecheck | yes | **PASS** |
| Python full test suite | yes | **PASS** (603 passed, 33 skipped) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** (10/10) |
| Chat FE lint + Vitest | yes | **PASS** (142/142) |
| Admin FE lint | yes | **PASS** |
| Admin FE Vitest | yes | **FAIL** — exit 1; 230 assertions passed, 2 unhandled errors |
| Coverage gate (`make test-unit-coverage`) | yes | **PASS** (100% line/branch) |
| Security (CVE + secrets + gitleaks tree) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, secrets, operator specs) | yes | **PASS** |
| Template conformance | yes | **PASS** (minor advisory: `modal` in deploy script) |
| Staging H4–H5 live | no | **SKIPPED** — no `VECINITA_STAGING_*` env |
| D7 LLM weights verify | no | **ADVISORY** — `staged_procedure` |

**Regression vs prior 09 (2026-06-29 remediation):** QA-S004-001/002 were resolved earlier today (admin nav + coverage). This re-run shows a **new** blocking item: Vitest unhandled errors causing npm exit 1 even when all test assertions pass.

## Commands run

```bash
# Repo root — Python (CI parity paths)
uv sync --group dev
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
cd apps/database && uv run alembic upgrade head
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs
uv run pytest tests/unit/test_cors_policy.py -v
uv run ruff check --select F401,F841 apps packages tests infra scripts
uv run pip-audit  # with audit/pip-audit-ignore.txt
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
gitleaks detect --no-git --config .gitleaks.toml

# Frontend (root npm ci required for hoisted workspace deps)
npm ci   # repo root
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
make test-unit-coverage
```

**Environment:** Node v22.23.0 locally (CI uses Node 20 LTS per `.github/workflows/ci.yml`).

## Per-check details

### Lint / format / typecheck — PASS

- **ruff check**: All checks passed (0 issues).
- **ruff format --check**: 234 files already formatted.
- **basedpyright**: 0 errors, 0 warnings, 0 notes.

### Python tests — PASS

```
603 passed, 33 skipped in ~30–102s
```

Skips are env-gated live/staging tests (expected). No failures.

### H0c CORS — PASS

`tests/unit/test_cors_policy.py` — 10/10 passed.

### Frontend — mixed

**chat-rag-frontend**

- **Lint**: PASS.
- **Vitest**: **142/142 passed** (26 files), exit 0.

**data-management-frontend**

- **Lint**: PASS.
- **Vitest**: **230/230 assertions passed** (37 files) but **npm exit 1** due to 2 unhandled errors:

1. **Worker spawn race** — `Cannot find module '.../vitest/suppress-warnings.cjs'` during parallel fork startup (intermittent; file exists after `npm ci` completes).
2. **Unhandled rejection** — `ReferenceError: window is not defined` in `DashboardPage.tsx:38` (`setLoading(false)` in async `finally`) while `test_auth_login_protected_routes.test.tsx` runs.

Expected stderr from negative tests (`useAuth must be used within AuthProvider`, `useTheme must be used within ThemeProvider`) — not failures.

### Coverage gate — PASS

`make test-unit-coverage` completed with **100%** line and branch coverage across Python and frontend components. Combined totals: 3658/3658 lines, 1259/1259 branches.

### Security — PASS

| Layer | Result |
|-------|--------|
| pip-audit | 0 vulnerabilities (workspace packages skipped — expected) |
| check_secrets.sh | OK |
| gitleaks `--no-git` | no leaks found (~10.6 MB scanned) |
| Dangerous patterns (`pickle.loads`, `eval(`, `exec(`) in apps/packages | none |

### Cross-file — PASS

- F401/F841: 0 unused imports/vars.
- Circular deps: not exhaustively scanned (advisory).

### Template & platform — PASS (one advisory)

| Criterion | Status |
|-----------|--------|
| Layout `apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/` | OK |
| Modal isolation | OK in app code (`infra/modal/` ×3); **advisory**: `scripts/deploy/read_data_mgmt_secret.py` also imports `modal` |
| No `DATABASE_URL` in Modal paths | OK |
| OpenAPI YAML parse | OK |
| Operator specs not tracked | OK |
| Modal workspace | `vecinita` per `docs/data-staging-state.md` D6 |

### Data staging & deploy — advisories

| Asset | Status |
|-------|--------|
| D1–D5, D8–D9 | verified |
| D6 FastEmbed | verified (`vecinita--` prefix) |
| D7 Qwen LLM | staged_procedure |
| `VECINITA_STAGING_*` | not set in QA environment |

### Dependencies — advisory

~53 outdated pip packages (`uv pip list --outdated`); intentional LlamaIndex pins per `docs/dependency-inventory.md`.

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S004-010 | **blocking** | Admin FE Vitest exits 1: unhandled `window is not defined` in `DashboardPage` async cleanup + intermittent worker spawn error | Guard async `setState` after unmount in `DashboardPage`; consider `vi.useFakeTimers` / `waitFor` in auth route tests; re-run on Node 20 (CI parity) |
| QA-S004-003 | advisory | `AuthContext.tsx` react-refresh warnings (if still present) | Extract hooks to separate file |
| QA-S004-004 | advisory | App-only `npm ci` breaks hoisted ESLint/vitest deps | Always `npm ci` at repo root before FE QA |
| QA-S004-005 | advisory | `07-build` / M43–M46 bookkeeping may be open | Close execution-plan tasks after commits |
| QA-S004-006 | advisory | Staging does not include F34 auth | Deploy + run `staging_smoke.sh` when ready |
| QA-S004-007 | advisory | H4–H5 live connectivity skipped | Set `VECINITA_STAGING_*_FRONTEND_URL`; run `verify_connectivity.sh` |
| QA-S004-008 | advisory | D7 LLM weights `staged_procedure` | `scripts/stage_modal_weights.sh` when approved |
| QA-S004-009 | advisory | ~53 outdated pip packages | Defer unless ADR bump |
| QA-S004-011 | advisory | Local Node 22 vs CI Node 20 | Re-run admin Vitest under Node 20 before merge to confirm CI parity |
| QA-S004-012 | advisory | `import modal` in `scripts/deploy/read_data_mgmt_secret.py` | Document as deploy-tool exception or relocate |

### Prior remediation (still valid)

| ID | Status | Resolution |
|----|--------|------------|
| QA-S004-001 | resolved | Unknown-route redirect fix in `App.tsx` |
| QA-S004-002 | resolved | Coverage gate PASS (100%) |

## Phase / execution-plan alignment

- **Phase 11** (EV-005 F34): M47 complete; session at `12-verify-deploy`.
- **Lite path**: 11-verify-impl skipped per routing plan.
- Python suite grew to 603 tests (was 546 in earlier 09 run).

## Handoff

1. Fix **QA-S004-010** before merge — CI frontend matrix will fail on non-zero Vitest exit even when assertions pass.
2. Confirm on **Node 20** (QA-S004-011) to rule out local-only worker issues.
3. Proceed to **12-verify-deploy** / **13-deploy-smoke** only after blocking item green or explicit waiver.
