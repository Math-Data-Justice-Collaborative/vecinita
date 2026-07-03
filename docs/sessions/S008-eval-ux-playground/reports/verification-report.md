# Verification Report — S008 / EV-009 (F36 follow-ons + F37)

> Generated: 2026-07-03  
> Scope: Interim delta verify (07-build still in progress — M70/T70.8 pending)  
> Branch: `feat/S008-eval-ux-playground`  
> Session: [S008-eval-ux-playground](../)

## Workflow note

**07-build is not complete** (`routing_plan` status `in_progress`, task T69.7+). This run is an
**interim S008 delta verify** per explicit `/08-verify-build` invocation (S003 precedent). Routing
plan entry `08-verify-build` remains **pending** until 07-build closes and a formal milestone pass
is recorded.

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint (Python) | PASS | 0 | — | `ruff check` |
| Lint (Frontend) | PASS | 0 | — | ESLint (both apps) |
| Format (Python) | PASS | 0 | — | `ruff format --check` |
| Format (Frontend) | PASS | 2 files | 2 auto-fixed | Prettier |
| Typecheck (Python) | PASS | 0 errors, 2 pre-existing warnings | — | `basedpyright` |
| Typecheck (Frontend) | PASS | 0 | — | `tsc --noEmit` |
| Tests (Python) | PASS | 946 passed, 33 skipped | — | `pytest` |
| Tests (Frontend) | PASS | 713 passed | — | Vitest |
| CORS policy (H0c) | PASS | 4 passed, 9 skipped | — | `tests/unit/test_cors_policy.py` |
| CI guards | PASS | 0 | — | `make ci-guards` |
| Security (pip-audit) | PASS | 0 CVE (1 ignored) | — | `pip-audit` |
| Connectivity artifacts | PASS | present | — | see below |
| Modal run smoke | SKIPPED | M70+ / GPU budget not approved | — | ADR-004 |
| Personas | ADVISORY | 0 🔴, 0 🟡 (3 addressed) | — | personas.md |

**Overall: PASS** (interim delta verify — 07-build prerequisite still unmet; routing_plan 08 remains pending)

## Fixes applied (post-verify, same session)

| Issue | Fix |
|-------|-----|
| `super-admin` Role typing | Extended `data_management.Role`; `AssignableRole` for invite/update; OpenAPI `UserSummary.role` |
| Unknown config dict in tests | `EvalConfig(...).model_dump(mode="json")` in UJ-047 + TC-133 fixtures |
| Timeseries LIMIT truncation | `get_eval_timeseries` now selects recent runs (`DESC`) then reverses for chart order |
| UJ005 mock drift | `_EmptyRetriever` accepts `top_k` / `score_threshold` kwargs |
| Frontend format | Auto-fixed Prettier in `messages.ts`, `test_evaluation_playground.test.tsx` |

## Auto-fixed (not committed)

| File | Fix |
|------|-----|
| `packages/frontend-i18n/src/messages.ts` | Prettier format |
| `apps/data-management-frontend/src/test/test_evaluation_playground.test.tsx` | Prettier format |

## Prior failures (resolved — see Fixes applied)

### 1. `super-admin` role not in data-management `Role`

```
apps/data-management-backend/vecinita_data_management_backend/user_admin_routes.py:64
  UserSummary.role expects data_management.Role ("admin" | "viewer")
  AdminUser.role is auth.Role ("admin" | "viewer" | "super-admin")
```

**Fix:** Extend `vecinita_shared_schemas.data_management.Role` to include `"super-admin"` (ADR-035 / F37).

### 2. Unknown dict types in new tests

```
tests/e2e/test_uj047_eval_promote_config.py:67
tests/integration/test_rag_production_config.py:62
  config = {...}  → reportUnknownVariableType (list[Unknown] in criteria_ids)
```

**Fix:** Annotate as `EvalConfig` dict or use `EvalConfig.model_dump()` / typed fixture helper.

## Test failures (resolved)

### `test_get_eval_timeseries_returns_completed_points`

- **File:** `tests/unit/internal_write_api/test_eval_service.py:624`
- **Cause:** Local DB has **129** completed `eval_runs`; `get_eval_timeseries` uses
  `ORDER BY completed_at ASC LIMIT 100`, so the test's newly completed run is excluded.
- **Fix:** Test isolation — truncate/filter fixture data, or assert via direct query / higher limit
  in test, or change query to `ORDER BY completed_at DESC` for dashboard use case.

### `test_uj005_empty_retrieval_message`

- **File:** `tests/e2e/test_uj005_empty_retrieval.py:79`
- **Cause:** `_EmptyRetriever.retrieve_chunks()` mock lacks `top_k` and `score_threshold` kwargs
  added when `ChatRagService._retrieve` reads production `EvalConfig` (S008 rag production config).
- **Observed:** `TypeError` → app returns **503** `"Upstream unavailable"`.
- **Fix:** Update mock signature to accept `top_k` and `score_threshold`; optionally pass
  `settings`/`config_engine` in fixture for production-config path coverage.

## Connectivity (stage 08)

| Artifact | Status |
|----------|--------|
| `configure_cors` on browser-facing FastAPI apps | Present (`chat-rag-backend`, `data-management-backend`, `internal-write-api`) |
| `tests/unit/test_cors_policy.py` | PASS |
| `tests/smoke/test_staging_connectivity.py` | Present |
| `scripts/deploy/verify_connectivity.sh` | Present |
| `tests/smoke/test_verify_connectivity_script.py` | Present (script contract) |

## Security

- `make ci-guards`: PASS (Modal DB boundary, OpenAPI, Supabase config, secrets scan, operator specs, corpus reset guard, DO secrets)
- `pip-audit`: PASS (no high/critical; workspace packages skipped as expected)
- gitleaks: no leaks

## Frontend

| Suite | Result |
|-------|--------|
| chat-rag-frontend Vitest | 142 passed |
| data-management-frontend Vitest | 571 passed |
| ESLint | PASS both apps |
| TypeScript | PASS all workspaces |

**Note:** CI coverage gate (`make test-unit-coverage`, 95% branch) deferred to **09-qa** per S007 precedent.

## Persona panel (advisory — addressed)

| Persona | Severity | Finding | Resolution |
|---------|----------|---------|------------|
| Staff Backend | 🟡 → resolved | `auth.Role` vs `data_management.Role` split | `Role` extended; `AssignableRole` for invite/update; regression tests |
| Staff Backend | 🟡 → resolved | Timeseries `ASC LIMIT 100` vs recent runs | `DESC` + reverse; `test_get_eval_timeseries_returns_recent_runs_in_chronological_order` |
| Staff Backend | 🟡 → resolved | UJ005 mock kwargs drift | `_EmptyRetriever` accepts `top_k` / `score_threshold` |
| CTO | 🟡 | Interim 08 before 07-build close | Waived — formal gate after M70/T70.8 |

## Commands run

```bash
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
make ci-guards
make audit
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs
uv run pytest tests/unit/test_cors_policy.py
npm run lint  # both frontends
make typecheck-fe
make test-fe
make format-fe-check  # after auto-fix
```

## Recommended next steps

1. Complete **07-build** (M70 playground / T70.8 phase gate).
2. Re-run **08-verify-build** formal pass and mark routing_plan `08-verify-build` completed.
3. Proceed **09-qa** → **10-e2e** before deploy stages.
