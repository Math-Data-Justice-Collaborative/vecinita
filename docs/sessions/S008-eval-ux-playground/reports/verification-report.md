# Verification Report — S008 / EV-009 (F36 follow-ons + F37)

> Generated: 2026-07-03  
> Scope: Formal milestone verify (Phase 15 gate — M65–M70 complete)  
> Branch: `feat/S008-eval-ux-playground`  
> Session: [S008-eval-ux-playground](../)

## Workflow note

**07-build is complete** (`routing_plan` status `completed` 2026-07-03; Phase 15 gate T2 PASS;
M65–M70 including T67.4 Playwright and T70.8 gate checklist). This run is the **formal S008
milestone verify** closing stage `08-verify-build`.

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint (Python) | PASS | 0 | — | `ruff check` |
| Lint (Frontend) | PASS | 0 | — | ESLint (4 workspaces) |
| Format (Python) | PASS | 0 | — | `ruff format --check` |
| Format (Frontend) | PASS | 0 | — | Prettier (4 workspaces) |
| Typecheck (Python) | PASS | 0 errors, 2 pre-existing warnings | — | `basedpyright` |
| Typecheck (Frontend) | PASS | 0 | — | `tsc --noEmit` |
| Tests (Python) | PASS | 952 passed, 33 skipped | — | `pytest` |
| Tests (Frontend) | PASS | 725 passed | — | Vitest |
| CORS policy (H0c) | PASS | 12 passed, 9 skipped | — | `tests/unit/test_cors_policy.py` |
| CI guards | PASS | 0 | — | `make ci-guards` |
| Security (pip-audit) | PASS | 0 CVE (1 ignored) | — | `pip-audit` |
| Security (npm audit) | PASS | 0 vulnerabilities | — | `npm audit` |
| Secrets scan | PASS | 0 leaks | — | `check_secrets.sh` + gitleaks |
| Connectivity artifacts | PASS | present | — | see below |
| Modal run smoke | SKIPPED | GPU budget not approved | — | ADR-004 |
| Personas | ADVISORY | 0 🔴, 1 🟡 | — | personas.md |

**Overall: PASS**

## Typecheck warnings (pre-existing, non-blocking)

| File | Warning |
|------|---------|
| `scripts/deploy/do_apps.py:28` | `modal_url_validate` import could not be resolved from source |
| `tests/unit/scripts/test_modal_url_validate.py:6` | same |

## Connectivity (stage 08)

| Artifact | Status |
|----------|--------|
| `configure_cors` on browser-facing FastAPI apps | Present (`chat-rag-backend`, `data-management-backend`, `internal-write-api`) |
| `tests/unit/test_cors_policy.py` | PASS (blocking H0c) |
| `tests/smoke/test_staging_connectivity.py` | Present |
| `scripts/deploy/verify_connectivity.sh` | Present |
| `tests/smoke/test_verify_connectivity_script.py` | Present (script contract) |

Live H4/H5 staging connectivity deferred to **12-verify-deploy** / **13-deploy-smoke** (staging
not yet deployed for S008).

## Security

- `make ci-guards`: PASS (Modal DB boundary, OpenAPI, Supabase config, secrets scan, operator
  specs, corpus reset guard, DO secrets)
- `pip-audit`: PASS (no high/critical; workspace packages skipped as expected)
- `npm audit`: PASS (0 vulnerabilities both frontends)
- gitleaks: no leaks
- Pattern scan (`eval`, `pickle.loads`, explicit `Any`): no hits in changed production code

## Frontend

| Suite | Result |
|-------|--------|
| chat-rag-frontend Vitest | 142 passed |
| data-management-frontend Vitest | 583 passed |
| ESLint | PASS all workspaces |
| TypeScript | PASS all workspaces |

**Note:** CI coverage gate (`make test-unit-coverage`, 95% branch) deferred to **09-qa** per
S007 precedent.

## Persona panel (advisory)

| Persona | Severity | Finding |
|---------|----------|---------|
| Staff Backend | 🟢 | Eval config presets, production promote, and timeseries fixes covered by integration + unit tests |
| Staff Frontend | 🟢 | Playground, Jobs tab, dashboard charts have Vitest + Playwright (UJ-041/044/045) |
| Senior DevOps | 🟡 | S008 not yet deployed to staging; H4/H5 live connectivity pending deploy stages |
| CTO | 🟢 | ADR-035 scope (F36+F37) implemented; super-admin promote path tested |
| Data & Privacy Steward | 🟢 | `tests/privacy/test_eval_config_tables.py` present; sandbox config isolated from production |
| Community Partner | 🟢 | i18n messages extended for eval UX strings |

## Delta scope (vs `main`)

147 files changed across eval API routes, playground UI, migrations, OpenAPI, and test suites
(M65–M70).

## Commands run

```bash
make lint
make format-check
make typecheck
make ci-guards
bash scripts/check_secrets.sh
make audit
make audit-fe
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs
uv run pytest tests/unit/test_cors_policy.py
make test-fe
```

## Recommended next steps

1. Proceed **09-qa** (full CI parity: `make ci-push`, coverage gate).
2. Proceed **10-e2e** (Playwright UJ suite + staging smokes when URLs available).
3. **12-verify-deploy** → **13-deploy-smoke** per TP-S008-16 deploy order (migration → API → FE).
