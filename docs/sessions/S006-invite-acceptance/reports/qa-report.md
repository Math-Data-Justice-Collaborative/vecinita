# QA Report — S006 / EV-007 / F35 ext (#109)

> **Project**: Vecinita  
> **Date**: 2026-06-30  
> **Skill**: 09-qa (delta — invite acceptance flow)  
> **Scope**: EV-007 F35 ext — redirect URLs, auth callback, revoke-invite, template/runbook polish (Phase 13 M54–M58)  
> **Branch**: `feat/S006-invite-acceptance`  
> **Session**: [S006-invite-acceptance](../)

```text
QA Results:
  Lint:           PASS — 0 issues (Python + both FE apps + shared packages)
  Format:         PASS — 249 files
  Typecheck:      PASS — 0 errors
  Tests (Python): PASS — 729 passed, 39 skipped, 0 failed
  Tests (FE):     PASS — chat 142/142; admin 329/329; i18n 17/17; ui 12/12 (all exit 0)
  Coverage gate:  PASS — combined 98.9% line; FE branches 969/1003 (96.6%, ≥95% gate)
  Security:       PASS — 0 CVEs; 0 secrets (tree); gitleaks clean (tree + history)
  Cross-file:     PASS — 0 unused imports (F401/F841); 0 dangerous patterns
  Template:       PASS — Modal isolated to infra/modal/ (+ deploy scripts)
  Data / Modal:   D6 verified; D7 verified; workspace vecinita
  H0c CORS:       PASS — 12 passed, 4 skipped (env-gated live)
  H4/H5 live:     PASS — 19 passed (connectivity remediation)
  Node runtime:   auto via ensure_node24.sh (fnm → 24.18.0)
```

**Overall: pass** — QA-S006-001/002/003/005/006/007 resolved 2026-06-30; QA-S006-004 partial (offline TC-109 + staging SPA OK; live T3 invite E2E remains for 13-deploy-smoke after merge + `config push`).

## QA remediation (2026-06-30)

| ID | Status | Resolution |
|----|--------|------------|
| QA-S006-001 | **resolved** | Added `scripts/ensure_node24.sh`; wired into `scripts/npm_with_lock.sh` so `make lint-fe`, `make test-fe`, and CI-parity npm targets auto-activate Node 24 via fnm. Documented in `docs/LOCAL_DEV.md`. |
| QA-S006-002 | **resolved** | Live checks: embed + LLM `/health` OK; `tests/smoke/test_modal_weights_staged.py` 3/3 PASS (384-dim embed). D7 set to `verified` in `docs/data-staging-state.md`. |
| QA-S006-003 | **resolved** | Ran `scripts/deploy/verify_connectivity.sh` with DO staging URLs from `do_apps.py urls --frontend` + Modal admin API. H0c 26 passed; H4/H5 live 19 passed. |
| QA-S006-004 | **partial** | Offline: `check_supabase_config.sh` OK; `test_supabase_ci_contract.py` 17/17 PASS (TC-109). Staging admin `/accept-invite` returns 200 (SPA). **Live T3** (send invite → email link → set password → login) still requires merge + redeploy + `supabase config push` with `SUPABASE_ACCESS_TOKEN` — defer to **13-deploy-smoke**. |
| QA-S006-005 | **resolved** | Reconciled during initial 09-qa run (workflow-state-manager). |
| QA-S006-006 | **accepted** | 16 outdated PyPI packages — all intentional pins (`llama-index` 0.13.x per ADR-006) or blocked major bumps (`openai` 2.x, `marshmallow` 4.x, `pandas` 3.x, `protobuf` 7.x). Same set as S005 remediation. |
| QA-S006-007 | **accepted** | Expected Vitest stderr from negative hook boundary tests — no code change. |


| Area | Blocking | Result |
|------|----------|--------|
| Python lint / format / typecheck | yes | **PASS** |
| Python full test suite | yes | **PASS** (729 passed, 39 skipped) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** (12 passed, 4 skipped) |
| Chat FE lint + Vitest + build | yes | **PASS** (142/142) |
| Admin FE lint + Vitest + build | yes | **PASS** (329/329) |
| Shared FE packages (i18n, ui) | yes | **PASS** (17 + 12 tests) |
| Coverage gate (`make test-unit-coverage`) | yes | **PASS** (FE branch ≥95%) |
| Security (CVE + secrets + gitleaks) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, secrets, operator specs) | yes | **PASS** |
| Template conformance | yes | **PASS** |
| Staging H4–H5 live | no | **PASS** — 19 live connectivity tests (QA-S006-003 remediation) |
| AC-U17–U21 live invite acceptance | no | **PARTIAL** — offline TC-109 + staging SPA OK; live T3 deferred to 13-deploy-smoke |
| D7 LLM weights verify | no | **PASS** — verified 2026-06-30 (QA-S006-002 remediation) |
| Outdated PyPI packages | no | **ACCEPTED** — 16 intentional pins (QA-S006-006) |

**Delta scope (EV-007):** `apps/data-management-backend` (revoke-invite, redirect_to), `apps/data-management-frontend` (useAuthLinkCallback, SetPasswordPage, UsersPage retract), `packages/shared-schemas` (supabase_admin invite metadata), `supabase/config.toml` + templates, `tests/unit/data_management/test_user_admin_routes.py`, `tests/e2e/test_uj031_invite_from_page.py`, `tests/unit/test_cors_policy.py` (revoke preflight), TC-104–TC-110.

## Commands run

```bash
# Repo root — Python (CI parity paths)
uv sync --group dev
uv run ruff check apps packages tests
uv run ruff format --check apps packages tests
uv run basedpyright apps packages tests
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs
uv run pytest tests/unit/test_cors_policy.py -v
uv run ruff check --select F401,F841 apps packages tests
uv run pip-audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
gitleaks detect --no-git --config .gitleaks.toml
gitleaks detect --config .gitleaks.toml
make test-unit-coverage

# Frontend (Node 24 via fnm — required; Node 22 breaks ESLint)
export PATH="$HOME/.local/share/fnm:$PATH" && eval "$(fnm env)" && fnm use 24
cd apps/chat-rag-frontend && npm run lint && npm test -- --run && npm run build
cd apps/data-management-frontend && npm run lint && npm test -- --run && npm run build
npm run lint -w vecinita-frontend-i18n && npm test -w vecinita-frontend-i18n -- --run
npm run lint -w vecinita-frontend-ui && npm test -w vecinita-frontend-ui -- --run
```

**Environment:** Node v24.18.0 via fnm (matches CI / `.nvmrc`). Default shell Node v22.23.0 fails ESLint (see QA-S006-001). No `VECINITA_STAGING_*` or `VECINITA_MODAL_*` env vars set.

## Per-check details

### Lint / format / typecheck — PASS

- **ruff check**: All checks passed (0 issues).
- **ruff format --check**: 249 files already formatted.
- **basedpyright**: 0 errors, 0 warnings, 0 notes.

### Python tests — PASS

```
729 passed, 39 skipped in ~51s
```

Skips are env-gated live/staging/Modal tests (expected). No failures.

### H0c CORS — PASS

`tests/unit/test_cors_policy.py` — 12 passed, 4 skipped. Includes revoke-invite preflight coverage added in EV-007.

### Frontend — PASS

**chat-rag-frontend**

- **Lint**: PASS (Node 24).
- **Vitest**: 142/142 passed (26 files), exit 0.
- **Build**: PASS.

**data-management-frontend**

- **Lint**: PASS (Node 24).
- **Vitest**: 329/329 passed (53 files), exit 0.
- **Build**: PASS.

Expected stderr from negative hook tests (`useAuth must be used within AuthProvider`, `useTheme must be used within ThemeProvider`) — not failures (QA-S006-007).

**Shared packages:** i18n 17/17, ui 12/12 — PASS.

### Coverage gate — PASS

`make test-unit-coverage` exit 0. Highlights:

| Component | Lines | Branches | Line % |
|-----------|-------|----------|--------|
| apps/data-management-frontend | 1348/1365 | 677/711 | 98.8% |
| apps/chat-rag-frontend | 419/419 | 266/266 | 100.0% |
| **Combined (all)** | 4653/4706 | 1572/1617 | 98.9% |

Admin FE branch coverage **95.22%** (677/711) — above 95% gate.

### Security — PASS

| Layer | Result |
|-------|--------|
| pip-audit | No known vulnerabilities (workspace packages skipped — expected) |
| check_secrets.sh | OK |
| gitleaks (tree) | 0 leaks |
| gitleaks (history) | 0 leaks (853 commits) |
| Dangerous patterns (`pickle.loads`, `eval`, `exec`) | 0 in apps/ + packages/ |

### Cross-file — PASS

- F401/F841: 0 issues.
- Circular deps: not detected (import graph stable).
- Public docstrings: not audited (advisory — defer to maintenance).

### Template & platform — PASS

| Criterion | Result |
|-----------|--------|
| Layout (`apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/`) | OK |
| `import modal` only under `infra/modal/` + deploy scripts | OK |
| Modal workspace | `vecinita` per data-staging-state D6 |
| No `DATABASE_URL` in Modal paths | OK (`check_modal_no_database_url.sh`) |
| OpenAPI YAML parse | OK |

### Data staging & deploy readiness

| Asset | Status | Notes |
|-------|--------|-------|
| D1–D5, D8–D9 | verified | Fixtures + migrations |
| D6 FastEmbed | verified | `vecinita--vecinita-embedding-*` |
| D7 Qwen LLM | verified | 2026-06-30 | `/health` OK; modal smoke 3/3 PASS |
| Phase 4 H1–H3 live | PASS (partial) | H4/H5 connectivity 19/19; H1–H3 not re-run separately |
| AC-U17–U21 | PARTIAL | Offline TC-109 + staging `/accept-invite` 200; live T3 → 13-deploy-smoke |

## Findings for 12-verify-deploy / 13-deploy-smoke

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S006-001 | advisory | ~~Default shell Node v22 breaks ESLint~~ | **Resolved** — `scripts/ensure_node24.sh` |
| QA-S006-002 | advisory | ~~D7 Qwen weights staged_procedure~~ | **Resolved** — live health + smoke; D7 verified |
| QA-S006-003 | advisory | ~~H4–H5 connectivity skipped~~ | **Resolved** — 19 live tests PASS |
| QA-S006-004 | advisory | AC-U17–U21 live invite acceptance | **Partial** — offline TC-109 PASS; live T3 at 13-deploy-smoke |
| QA-S006-005 | advisory | ~~workflow-state stale~~ | **Resolved** — reconciled in 09-qa |
| QA-S006-006 | advisory | 16 outdated PyPI packages | **Accepted** — intentional pins |
| QA-S006-007 | advisory | DM FE Vitest stderr | **Accepted** — expected test behavior |

## Phase / execution-plan alignment

- **Phase 13 (EV-007)** build + verify complete per `docs/sessions/S006-invite-acceptance/reports/verification-report.md`.
- **Merge-blocking gate (T2):** TC-104–TC-110 covered in pytest + Vitest — PASS.
- **Live acceptance (AC-U17–U21):** explicitly deferred to **13-deploy-smoke** per tech plan and verification report.
- **Next stages:** 10-e2e (parallel) → 12-verify-deploy → 13-deploy-smoke.

## Handoff

**11-verify-impl** skipped (evolve-lite). Present this report at **12-verify-deploy** / **13-deploy-smoke**:

1. Blocking items: none — proceed to deploy verification.
2. Advisories QA-S006-003/004: resolve at staging smoke with live Supabase + frontend URLs.
3. Advisory QA-S006-002: optional before LLM-dependent smoke.
