# QA Report — S008 / EV-009 (F36 follow-ons + F37)

> **Project**: Vecinita  
> **Date**: 2026-07-03  
> **Skill**: 09-qa (delta — eval UX polish, playground, super-admin runtime promote)  
> **Scope**: EV-009 F36 follow-ons (M65–M67) + F37 eval playground + super-admin runtime promote (M68–M70, ADR-035, UJ-045–047)  
> **Branch**: `feat/S008-eval-ux-playground` @ `24eff9f`  
> **Session**: [S008-eval-ux-playground](../)

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files (327 checked)
  Typecheck:      PASS — 0 errors, 2 warnings (modal_url_validate import)
  Tests (Python): PASS — 940 passed, 45 skipped, 0 failed
  Tests (FE):     PASS — chat 142/142; admin 583/583; i18n 17/17; ui 12/12
  Tests (UI):     PASS — Playwright 30 passed, 2 skipped (staging env-gated)
  Coverage gate:  FAIL — chat-rag-backend branch 91.2%; internal-write-api line 92.2% / branch 87.5%
  Security:       PASS — 0 CVEs (1 ignored nltk); gitleaks clean (tree)
  Cross-file:     PASS — 0 unused imports; 0 dangerous eval/exec patterns
  Template:       PASS — Modal isolated to infra/modal/ (+ deploy scripts)
  Data / Modal:   D6 verified; D7 verified; workspace vecinita (per data-staging-state)
  H0c CORS:       PASS — 12 passed, 10 skipped (env-gated)
  H4/H5 live:     SKIPPED — no VECINITA_STAGING_* env vars set
```

**Overall: fail** — coverage gate blocking (EV-009 eval/playground surfaces under-tested in Python apps). All other blocking checks green.

## Executive summary

| Area | Blocking | Result |
|------|----------|--------|
| Python lint / format / typecheck | yes | **PASS** |
| Python full test suite | yes | **PASS** (940 passed, 45 skipped) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** |
| Chat FE lint + Vitest | yes | **PASS** (142/142) |
| Admin FE lint + Vitest | yes | **PASS** (583/583) |
| Shared FE packages (i18n, ui) | yes | **PASS** (17 + 12) |
| Playwright UI E2E (`make test-ui`) | yes | **PASS** (30 passed; 2 staging skipped) |
| Coverage gate (`make test-unit-coverage`) | yes | **FAIL** |
| Security (CVE + secrets scripts) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, secrets, operator specs) | yes | **PASS** |
| Template conformance | yes | **PASS** |
| gitleaks working tree | no | **PASS** — no leaks |
| Staging H4–H5 live | no | **SKIPPED** — no staging URLs in env |
| D6/D7 Modal live smoke | no | **ADVISORY** — not re-run (verified 2026-06-30 per data-staging-state) |
| Outdated PyPI packages | no | **ADVISORY** — 16 intentional pins (LlamaIndex stack) |

**Delta from S007 09-qa:** Same blocking pattern (coverage gate) but scope shifted to EV-009 surfaces — `internal-write-api` eval playground/ad-hoc routes and `chat-rag-backend` branch gaps. Frontend coverage is 100% line / 98.4% branch combined; Python apps are the gate blockers.

**Delta scope (EV-009):** `apps/internal-write-api` (eval playground, ad-hoc eval, runtime promote), `apps/data-management-frontend` (EvalPlayground, compare view, jobs tab eval rows), `packages/eval`, Playwright UJ-045–047 specs, integration/e2e tests TC-128–TC-130.

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
make audit   # pip-audit with audit/pip-audit-ignore.txt
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
gitleaks detect --no-git --config .gitleaks.toml

# Coverage gate
make test-unit-coverage

# Frontend
npm ci
npm run lint -w vecinita-chat-rag-frontend && npm test -w vecinita-chat-rag-frontend -- --run
npm run lint -w vecinita-data-management-frontend && npm test -w vecinita-data-management-frontend -- --run
npm run lint -w vecinita-frontend-i18n && npm test -w vecinita-frontend-i18n -- --run
npm run lint -w vecinita-frontend-ui && npm test -w vecinita-frontend-ui -- --run

# Playwright UI E2E
make test-ui
```

**Environment:** No `VECINITA_STAGING_*` or `VECINITA_MODAL_*` env vars set. Node v24.18.0 (system).

## Per-check details

### Lint — PASS

All checks passed (327 files under `apps packages tests infra scripts`).

### Format — PASS

327 files already formatted.

### Typecheck — PASS

```
0 errors, 2 warnings, 0 notes
```

Warnings (pre-existing, non-blocking):

| File | Warning |
|------|---------|
| `scripts/deploy/do_apps.py:28` | `modal_url_validate` could not be resolved from source |
| `tests/unit/scripts/test_modal_url_validate.py:6` | same |

### Python tests — PASS

```
940 passed, 45 skipped in 262.97s
```

Skips are env-gated (staging, Modal URLs, live connectivity) — expected.

### H0c CORS — PASS

```
12 passed, 10 skipped in 1.69s
```

### Frontend — PASS

| App / package | Lint | Tests |
|---------------|------|-------|
| chat-rag-frontend | PASS | 142/142 (26 files) |
| data-management-frontend | PASS | 583/583 (72 files) |
| frontend-i18n | PASS | 17/17 (4 files) |
| frontend-ui | PASS | 12/12 (5 files) |

**Note:** One parallel `npm ci` + test invocation returned exit 1 (vitest not found mid-install). Clean sequential re-run passed 583/583. Treat as environment flake, not product failure.

### Playwright UI E2E — PASS

```
30 passed, 2 skipped in ~1.1m
```

Skipped: `tests/ui/staging/staging-smoke.spec.ts` (2 tests — no `VECINITA_STAGING_*` URLs).

New EV-009 specs exercised: UJ-045 (playground), UJ-046 (compare), UJ-044 (eval jobs tab), UJ-041 dashboard extensions.

### Coverage gate — FAIL

`make test-unit-coverage` / `scripts/test/print_unit_coverage_summary.py --enforce`:

```
Coverage gate failed:
  apps/chat-rag-backend: branch coverage 91.2% below 95%
  apps/internal-write-api: line coverage 92.2% below 95%
  apps/internal-write-api: branch coverage 87.5% below 95%
```

Combined totals (informational): 98.3% line, 97.0% branch — gate fails on **per-component** thresholds.

| Component | Lines | Branches | Line % | Branch % | Gate |
|-----------|-------|----------|--------|----------|------|
| apps/chat-rag-backend | 354/363 | 62/68 | 97.5% | **91.2%** | branch FAIL |
| apps/internal-write-api | 1016/1102 | 245/280 | **92.2%** | **87.5%** | line + branch FAIL |
| apps/data-management-frontend | 2165/2165 | 1417/1444 | 100.0% | 98.1% | PASS |
| apps/chat-rag-frontend | 419/419 | 266/266 | 100.0% | 100.0% | PASS |

**Likely under-covered EV-009 paths:** `eval_service.py` ad-hoc/playground handlers, runtime promote routes, error branches in new eval compare flows.

### Security — PASS

| Layer | Result |
|-------|--------|
| `make audit` (with ignore list) | PASS — 0 CVEs, 1 ignored (`PYSEC-2026-597` nltk transitive) |
| `check_secrets.sh` | PASS |
| gitleaks `--no-git` | PASS — no leaks in working tree |
| Dangerous patterns (`eval(`/`exec(`/`pickle.loads`) | PASS — no matches in app code |

Raw `uv run pip-audit` (without ignore list) reports `PYSEC-2026-597` — **non-blocking**; listed in `audit/pip-audit-ignore.txt` and suppressed in CI via `make audit`.

### CI guards — PASS

- `check_modal_no_database_url.sh` — OK
- `check_openapi_specs.sh` — OK
- `check_no_operator_specs_tracked.sh` — OK
- `check_secrets.sh` — OK

### Cross-file analysis — PASS

- Unused imports (F401/F841): 0
- Circular deps: not run (no cycles observed in prior sessions; advisory)
- Dangerous patterns: 0 in `apps/` + `packages/`

### Template conformance — PASS

| Criterion | Result |
|-----------|--------|
| Layout (`apps/*`, `packages/*`, `tests/`, `infra/`) | OK |
| `import modal` only under `infra/modal/` + deploy scripts | OK |
| OpenAPI specs parse | OK |
| No `DATABASE_URL` in Modal worker paths | OK |

### Data staging & Modal — ADVISORY

Per `docs/sessions/S000-internal-docs-archive/data-staging-state.md` (2026-06-30):

| Asset | Status |
|-------|--------|
| D1–D5, D8–D9 | verified |
| D6 FastEmbed | verified (`vecinita--vecinita-embedding`) |
| D7 Qwen LLM | verified (`vecinita--vecinita-llm`) |

Live Modal smoke not re-run this session (no `VECINITA_MODAL_*` env vars).

### Connectivity — ADVISORY

| Gate | Result |
|------|--------|
| H0c CORS unit tests | **PASS** (blocking) |
| H4–H5 staging live | **SKIPPED** — set `VECINITA_STAGING_CHAT_FRONTEND_URL` / `VECINITA_STAGING_ADMIN_FRONTEND_URL` per `connectivity-gates.md` |

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| **QA-S008-B05** | **blocking** | Coverage gate FAIL: `internal-write-api` line 92.2% / branch 87.5%; `chat-rag-backend` branch 91.2% (threshold 95%) | Add unit tests for EV-009 eval playground, ad-hoc eval, runtime promote, and chat-rag error branches; re-run `make test-unit-coverage` |
| QA-S008-001 | advisory | H4–H5 staging connectivity not exercised | Run `scripts/deploy/verify_connectivity.sh` when staging URLs available |
| QA-S008-002 | advisory | D6/D7 Modal live smoke not re-run | Optional: `pytest tests/smoke/test_modal_weights_staged.py` with Modal URLs |
| QA-S008-003 | advisory | basedpyright warnings on `modal_url_validate` import resolution | Add stub or fix `PYTHONPATH` for deploy script imports |
| QA-S008-004 | advisory | 16 outdated PyPI packages (LlamaIndex stack pinned) | Intentional per `dependency-inventory.md`; bump only via ADR |
| QA-S008-005 | advisory | Admin FE Vitest exit 1 during parallel `npm ci` | Use sequential `npm ci` before FE tests in CI-like runs; clean re-run passed 583/583 |

## Phase / execution-plan alignment

- **EV-009 build (07-build):** completed 2026-07-03 — M65–M70 including playground (T67.4 Playwright, T70.8 gate).
- **08-verify-build:** PASS (952 pytest + 725 Vitest at milestone verify; this 09 pass uses full CI paths → 940 pytest due to broader skip set).
- **09-qa:** FAIL on coverage gate — blocks formal **pass** for 11-verify-impl sign-off.
- **10-e2e:** pending (can run in parallel; coverage remediation does not block e2e unless user prefers sequential).
- **12-verify-deploy / 13-deploy-smoke:** pending; Phase 4 H1–H3 live gates deferred without staging env.

## Handoff

**11-verify-impl** should:

1. Present **QA-S008-B05** (coverage gate) as the sole blocking item — same class as S007 QA-S007-B05 but EV-009-scoped surfaces.
2. Offer **fix-now** (add tests for `internal-write-api` eval playground + `chat-rag-backend` branches) vs **defer** (blocks merge/CI coverage job).
3. Treat H4–H5 and Modal live as advisories unless user sets staging env vars.
4. Do not re-run full 09 unless codebase changes materially after remediation.
