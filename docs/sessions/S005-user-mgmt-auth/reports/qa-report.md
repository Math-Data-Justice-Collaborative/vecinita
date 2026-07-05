# QA Report — S005 / EV-006 / F35

> **Project**: Vecinita  
> **Date**: 2026-06-30  
> **Skill**: 09-qa (delta — F35 admin user management + auth UX)  
> **Scope**: EV-006 F35 — idle timeout, log-out-everywhere, force sign-out, deliverability test-send, audit viewer, user management (M48–M53)  
> **Branch**: `feat/S005-user-mgmt-auth`  
> **Session**: [S005-user-mgmt-auth](../)

```text
QA Results:
  Lint:           PASS — 0 issues (Python + both FE apps)
  Format:         PASS — 259 files
  Typecheck:      PASS — 0 errors
  Tests (Python): PASS — 703 passed, 39 skipped, 0 failed
  Tests (FE):     PASS — chat 142/142; admin 312/312; i18n 17/17; ui 12/12 (all exit 0)
  Coverage gate:  PASS — combined 99.0% line; FE branches 919/946 (97.1%, ≥95% gate)
  Security:       PASS — 0 CVEs; 0 secrets (tree); gitleaks clean (tree + history)
  Cross-file:     PASS — 0 unused imports (F401/F841); 0 dangerous patterns
  Template:       PASS — Modal isolated to infra/modal/ (+ deploy scripts advisory)
  Data / Modal:   D6 verified; D7 staged_procedure; workspace vecinita
  H0c CORS:       PASS — 11 passed, 4 skipped (env-gated live)
  Node runtime:   Node 24.18.0 (fnm; matches CI/.nvmrc)
```

**Overall: pass_with_advisories** — QA-S005-004/005/008 resolved 2026-06-30; staging live gates and D7 LLM verify still deferred (env/ops).

## QA remediation (2026-06-30)

| ID | Status | Resolution |
|----|--------|------------|
| QA-S005-004 | **resolved** | `uv lock --upgrade` + raised dev-tool floors in root `pyproject.toml`. Outdated count **52 → 15**; remaining are intentional pins (`llama-index` 0.13.x per ADR-006) or blocked major bumps (`openai` 2.x, `marshmallow` 4.x, `pandas` 3.x, `protobuf` 7.x). 703 pytest passed after upgrade (incl. NumPy 2.4.6). |
| QA-S005-005 | **resolved** | Removed unused `eslint-disable` in `test_password_reset.test.tsx`; admin FE `eslint src` clean (0 warnings). |
| QA-S005-008 | **resolved** | Verified FE lint + Vitest on **Node v24.18.0** via fnm; `docs/LOCAL_DEV.md` documents `fnm use` alongside `.nvmrc`. |

## Executive summary

| Area | Blocking | Result |
|------|----------|--------|
| Python lint / format / typecheck | yes | **PASS** |
| Python full test suite | yes | **PASS** (703 passed, 39 skipped) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** (11 passed, 4 skipped) |
| Chat FE lint + Vitest + build | yes | **PASS** (142/142) |
| Admin FE lint + Vitest + build | yes | **PASS** (312/312) |
| Shared FE packages (i18n, ui) | yes | **PASS** (17 + 12 tests) |
| Coverage gate (`make test-unit-coverage`) | yes | **PASS** (FE branch ≥95%) |
| Security (CVE + secrets + gitleaks) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, secrets, operator specs) | yes | **PASS** |
| Template conformance | yes | **PASS** |
| Staging H4–H5 live | no | **SKIPPED** — no `VECINITA_STAGING_*` env |
| D7 LLM weights verify | no | **ADVISORY** — `staged_procedure` |
| Outdated PyPI packages | no | **RESOLVED** — 15 remain (intentional LlamaIndex 0.13.x + major-bump blocks) |

**Delta scope (F35):** `apps/data-management-frontend` (auth UX, users, audit, idle timeout), `apps/data-management-backend` (admin user/email endpoints), `packages/shared-schemas` (auth types), `supabase/` templates + config, related tests under `tests/unit`, `tests/e2e`, `tests/integration`.

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
gitleaks detect --no-git --config .gitleaks.toml
gitleaks detect --config .gitleaks.toml

# Frontend (root npm ci required for hoisted workspace deps)
npm ci   # repo root
cd apps/chat-rag-frontend && npm run lint && npm test -- --run && npm run build
cd apps/data-management-frontend && npm run lint && npm test -- --run && npm run build
npm run lint -w vecinita-frontend-i18n && npm run typecheck -w vecinita-frontend-i18n && npm test -w vecinita-frontend-i18n
npm run lint -w vecinita-frontend-ui && npm run typecheck -w vecinita-frontend-ui && npm test -w vecinita-frontend-ui
make test-unit-coverage
```

**Environment:** Node v22.23.0 locally; CI and `.nvmrc` specify Node 24 LTS. No `VECINITA_STAGING_*` or `VECINITA_MODAL_*` env vars set.

## Per-check details

### Lint / format / typecheck — PASS

- **ruff check**: All checks passed (0 issues).
- **ruff format --check**: 259 files already formatted.
- **basedpyright**: 0 errors, 0 warnings, 0 notes.

### Python tests — PASS

```
703 passed, 39 skipped in ~33–108s
```

Skips are env-gated live/staging/Modal tests (expected). No failures.

### H0c CORS — PASS

`tests/unit/test_cors_policy.py` — 11 passed, 4 skipped (live-origin tests require staging URLs).

### Frontend — PASS

**chat-rag-frontend**

- **Lint**: PASS (after root `npm ci`; see QA-S005-007).
- **Vitest**: 142/142 passed (26 files), exit 0.
- **Build**: PASS.

**data-management-frontend**

- **Lint**: PASS with 1 warning — unused `eslint-disable` in `test_password_reset.test.tsx` (QA-S005-005).
- **Vitest**: 312/312 passed (51 files), exit 0.
- **Build**: PASS.

Expected stderr from negative hook tests (`useAuth must be used within AuthProvider`, `useTheme must be used within ThemeProvider`) — not failures.

**Shared packages**

- **vecinita-frontend-i18n**: lint, typecheck, 17/17 tests — PASS.
- **vecinita-frontend-ui**: lint, typecheck, 12/12 tests — PASS.

### Coverage gate — PASS

`make test-unit-coverage` exit 0. Highlights:

| Component | Lines | Branches |
|-----------|-------|----------|
| Combined | 4486/4533 (99.0%) | 1505/1542 (97.6%) |
| data-management-frontend | 1255/1269 (98.9%) | 627/654 (95.9%) |
| chat-rag-frontend | 419/419 (100%) | 266/266 (100%) |

FE branch gate (≥95%) satisfied.

### Security — PASS

| Layer | Result |
|-------|--------|
| pip-audit | 0 vulnerabilities (workspace packages skipped — expected) |
| check_secrets.sh | OK |
| gitleaks `--no-git` | no leaks found (~12.4 MB scanned) |
| gitleaks full history | no leaks found (799 commits) |
| Dangerous patterns (`pickle.loads`, `eval(`, `exec(`) in apps/packages | none |

### Cross-file — PASS

- F401/F841: 0 unused imports/vars.
- Circular deps: not exhaustively scanned (advisory).

### Template & platform — PASS

| Criterion | Status |
|-----------|--------|
| Layout (`apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/`) | OK |
| `import modal` only under `infra/modal/` | OK (+ deploy scripts — QA-S005-006) |
| Modal workspace URLs use `vecinita--` prefix | OK per `infra/modal/README.md` |
| No `DATABASE_URL` in Modal worker paths | OK (`check_modal_no_database_url.sh`) |
| OpenAPI YAML parse | OK |
| Operator spec exports not tracked | OK |

### Data staging & Modal

| Asset | Status | Notes |
|-------|--------|-------|
| D1–D5, D8–D9 | verified | Per `docs/sessions/S000-internal-docs-archive/data-staging-state.md` |
| D6 FastEmbed | verified | `vecinita` workspace; 384-dim |
| D7 Qwen LLM | staged_procedure | Run `stage_llm_weights` to verify volume |

### Connectivity (stage 09)

| Gate | Status |
|------|--------|
| H0c CORS unit tests | **PASS** (blocking) |
| H0i integration tests | **PASS** (included in full pytest run) |
| H4–H5 staging frontends | **SKIPPED** — no `VECINITA_STAGING_*_FRONTEND_URL` |
| Phase 4 H1–H3 live | **SKIPPED** — no `VECINITA_STAGING_CHAT_URL` |

## Findings for downstream stages

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S005-001 | advisory | D7 LLM weights `staged_procedure` | Run `./scripts/stage_modal_weights.sh` on `vecinita` profile; verify embed 384-dim + LLM health |
| QA-S005-002 | advisory | Staging H4–H5 live checks skipped | Set `VECINITA_STAGING_*` env; run `scripts/deploy/verify_connectivity.sh` in 13-deploy-smoke |
| QA-S005-003 | advisory | Phase 4 H1–H3 deferred | `docs/staging-runbook.md`; `scripts/deploy/staging_smoke.sh` when URLs available |
| QA-S005-004 | ~~advisory~~ **resolved** | See [QA remediation (2026-06-30)](#qa-remediation-2026-06-30) |
| QA-S005-005 | ~~advisory~~ **resolved** | Removed unused eslint-disable |
| QA-S005-008 | ~~advisory~~ **resolved** | Node 24 verified via fnm |
| QA-S005-006 | advisory | `modal` import in `scripts/deploy/*.py` | Accepted deploy/ops exception (same as QA-S004-012) |
| QA-S005-007 | advisory | Chat FE ESLint failed before root `npm ci` | Document: always `npm ci` at repo root before per-app FE checks |

## Phase / execution-plan alignment

- **EV-006 / Phase 12:** 07-build and 08-verify-build complete; 09-qa blocking criteria met.
- **11-verify-impl:** skipped in S005 evolve-lite routing — advisories above feed **10-e2e** and **13-deploy-smoke** instead.
- **Deploy criteria:** deferred to stages 12–13 per execution plan Current State.

## Handoff

- **10-e2e:** Run journey tests for F35 (UJ user-mgmt, idle timeout, audit viewer, test-send).
- **13-deploy-smoke:** Staging connectivity when env vars set; D7 verify if LLM smoke required.
