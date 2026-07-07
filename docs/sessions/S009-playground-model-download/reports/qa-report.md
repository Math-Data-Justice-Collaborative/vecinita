# QA Report — S009 / EV-010 (F38)

> **Project**: Vecinita  
> **Date**: 2026-07-07  
> **Skill**: 09-qa (delta — playground Ollama model download; invoked with prerequisites unmet)  
> **Scope**: EV-010 F38 — super-admin Ollama model pull UI, catalog API, full-stack tests  
> **Branch**: `fix/ollama-pull-do-503` @ `9bdfb18` (session branch `feat/S009-playground-model-download`; **uncommitted WIP**)  
> **Session**: [S009-playground-model-download](../)

```text
QA Results:
  Lint:           FAIL — 4 issues (ruff D102/D107 in tests/helpers/ollama_library_mock.py)
  Format:         PASS — 0 files (348 checked)
  Typecheck:      FAIL — 2 errors (test_ollama_models_list.py); 1 warning (modal_url_validate import)
  Tests (Python): PASS — 1014 passed, 45 skipped, 0 failed
  Tests (FE):     FAIL — chat 142/142; admin 606/607 (1 fail); i18n 17/17; ui 12/12
  Tests (UI):     FAIL — Playwright blocked (admin FE tsc build error)
  Coverage gate:  FAIL — admin Vitest failure before threshold check
  Security:       PASS — 0 CVEs (1 ignored nltk); gitleaks clean (tree); secrets scripts OK
  Cross-file:     PASS — 0 unused imports (F401/F841); 0 real eval/exec patterns
  Template:       PASS — Modal isolated to infra/modal/
  Data / Modal:   D6 verified; D7 verified; workspace vecinita (per data-staging-state)
  H0c CORS:       PASS — 12 passed, 10 skipped (env-gated)
  H4/H5 live:     SKIPPED — no VECINITA_STAGING_* env vars set
```

**Overall: fail** — lint, typecheck, admin FE lint/tests, coverage gate, and Playwright UI blocked. Python suite and security checks green.

## Prerequisites (workflow deviation)

| Prerequisite | Status | Notes |
|--------------|--------|-------|
| 07-build complete | **unmet** | Routing plan `pending`; F38 build extension still uncommitted |
| 08-verify-build PASS | **unmet** | No S009 `verification-report.md` |
| 11-verify-impl | completed early | 2026-07-06 partial signoff; formal 08→09→10 still required |

QA was invoked explicitly (`/09-qa`) despite unmet build gates. Results reflect **working tree + branch `fix/ollama-pull-do-503`**, not a clean `feat/S009-playground-model-download` commit.

## Executive summary

| Area | Blocking | Result |
|------|----------|--------|
| Python lint (`ruff check`) | yes | **FAIL** — 4 docstring violations in new test helper |
| Python format | yes | **PASS** |
| Python typecheck (`basedpyright`) | yes | **FAIL** — 2 errors in integration test |
| Python full test suite | yes | **PASS** (1014 passed, 45 skipped) |
| H0c CORS (`test_cors_policy.py`) | yes | **PASS** |
| Admin FE ESLint | yes | **FAIL** — 2 errors, 3 warnings |
| Admin FE Vitest | yes | **FAIL** — 606/607 |
| Chat FE lint + Vitest | yes | **PASS** (142/142) |
| Shared FE (i18n, ui) | yes | **PASS** (17 + 12) |
| Playwright UI E2E (`make test-ui`) | yes | **FAIL** — admin `tsc` build error |
| Coverage gate (`make test-unit-coverage`) | yes | **FAIL** — same admin test/lint blockers |
| Security (CVE + secrets + gitleaks) | yes | **PASS** |
| CI guards (Modal DB, OpenAPI, operator specs) | yes | **PASS** |
| Template conformance | yes | **PASS** |
| gitleaks working tree | no | **PASS** |
| Staging H4–H5 live | no | **SKIPPED** |
| D6/D7 Modal live smoke | no | **ADVISORY** — not re-run (verified 2026-06-30) |
| Outdated PyPI packages | no | **ADVISORY** — 19 packages (intentional LlamaIndex pins) |

**Delta scope (EV-010 / F38):** `apps/internal-write-api` (Ollama catalog/pull routes), `apps/data-management-frontend` (EvaluationModelDownloadTab, ollamaModelDownloadContext, useOllamaModelDownload), `packages/shared-schemas` (ollama_models), `tests/integration/test_ollama_models_list.py`, `tests/helpers/ollama_library_mock.py`, Playwright mock helpers.

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
# pip-audit with audit/pip-audit-ignore.txt
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
gitleaks detect --no-git --config .gitleaks.toml

# Coverage gate
make test-unit-coverage

# Frontend (root workspace)
npm ci
npm run lint -w vecinita-data-management-frontend
npm run lint -w vecinita-chat-rag-frontend
npm test -w vecinita-data-management-frontend -- --run
npm test -w vecinita-chat-rag-frontend -- --run
npm run lint -w vecinita-frontend-i18n && npm test -w vecinita-frontend-i18n -- --run
npm run lint -w vecinita-frontend-ui && npm test -w vecinita-frontend-ui -- --run

# Playwright
make test-ui
```

## Per-check details

### Lint — FAIL (4 issues)

```
tests/helpers/ollama_library_mock.py:
  D107 — Missing docstring in __init__
  D102 — Missing docstring in list_families, list_tags, close
```

New F38 test helper lacks docstrings; `tests/**` only ignores `S101`, not `D10x`.

### Format — PASS

348 files already formatted.

### Typecheck — FAIL (2 errors, 1 warning)

```
tests/integration/test_ollama_models_list.py:63:31
  MockOllamaLibraryClient not assignable to OllamaLibraryClient | None

tests/integration/test_ollama_models_list.py:186:23
  object not assignable to JsonObject for json_str()

tests/unit/scripts/test_modal_url_validate.py:6:6 — warning: import could not be resolved (pre-existing)
```

### Python tests — PASS

```
1014 passed, 45 skipped in 72.64s
```

Skips are env-gated: staging smoke (`VECINITA_STAGING_*`), Modal live probe (`VECINITA_MODAL_PROXY_KEY`), CORS live origins.

### H0c CORS — PASS

```
12 passed, 10 skipped
```

### Admin frontend — FAIL

**ESLint (2 errors, 3 warnings):**

```
useOllamaModelDownload.test.ts:8 — MODEL_PULL_POLL_INTERVAL_MS unused
test_evaluation_playground.test.tsx:1338 — no-unsafe-assignment (any)
ollamaModelDownloadContext.tsx — react-refresh/only-export-components (3 warnings, advisory)
```

**Vitest:** 606 passed, **1 failed**

```
test_evaluation_page_search_params.test.tsx
  × calls setSearchParams when switching evaluation tabs
  Expected: setSearchParams({ tab: "explore" })
  Received: setSearchParams([Function anonymous])
```

Tab navigation now uses functional `setSearchParams` updater; test assertion stale.

**TypeScript build (blocks Playwright):**

```
useOllamaModelDownload.test.ts(8,3): error TS6133: 'MODEL_PULL_POLL_INTERVAL_MS' is declared but never read
```

### Chat frontend — PASS

142/142 Vitest; ESLint clean.

### Coverage gate — FAIL

`make test-unit-coverage` aborted on admin Vitest failure (`test_evaluation_page_search_params.test.tsx`). Threshold percentages not reached in this run.

### Security — PASS

- `pip-audit`: no known vulnerabilities (1 ignored CVE in ignore file)
- `check_secrets.sh`: OK
- `gitleaks --no-git`: no leaks
- Dangerous-pattern scan: no real `eval()`/`exec()`/`pickle.loads` in app code (false positives on `run_*_eval` function names)

### Cross-file — PASS

- F401/F841: 0 unused imports/vars
- Circular deps: not exhaustively graphed (advisory SKIPPED)
- Modal `import modal` only under `infra/modal/` (4 files); none in `apps/`

### Dependencies — ADVISORY

19 outdated PyPI packages (LlamaIndex stack pins intentional per `docs/dependency-inventory.md`).

### Template & platform — PASS

- Layout: `apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/`
- OpenAPI specs parse
- No `DATABASE_URL` in Modal worker paths
- Modal workspace `vecinita` per data-staging-state (not live-reverified)

### Data staging — PASS (documented)

D1–D5, D8–D9, D6, D7 all `verified` per `data-staging-state.md` (2026-06-30).

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S009-B01 | **blocking** | Ruff D102/D107 in `tests/helpers/ollama_library_mock.py` | Add docstrings or per-file D10x ignore (match other test modules) |
| QA-S009-B02 | **blocking** | basedpyright errors in `test_ollama_models_list.py` | Type `MockOllamaLibraryClient` as protocol/subclass or use `OllamaLibraryClient` stub; fix `json_str` arg type |
| QA-S009-B03 | **blocking** | Admin ESLint: unused import + unsafe `any` assignment | Remove `MODEL_PULL_POLL_INTERVAL_MS` import; type the playground test mock |
| QA-S009-B04 | **blocking** | `test_evaluation_page_search_params` expects object arg to `setSearchParams` | Update assertion for functional updater pattern |
| QA-S009-B05 | **blocking** | `make test-ui` / admin `tsc` build fails (TS6133) | Same as B03 — unused import blocks production build |
| QA-S009-B06 | **blocking** | Coverage gate cannot pass until B04/B03 fixed | Re-run `make test-unit-coverage` after fixes |
| QA-S009-A01 | advisory | 07-build / 08-verify-build not complete before 09 | Finish build, commit, run 08-verify-build, then re-run 09 |
| QA-S009-A02 | advisory | Branch mismatch (`fix/ollama-pull-do-503` vs session `feat/S009-…`) | Align branch or merge hotfix into session branch before PR |
| QA-S009-A03 | advisory | H4–H5 staging connectivity not exercised | Set `VECINITA_STAGING_*_FRONTEND_URL`; run `scripts/deploy/verify_connectivity.sh` |
| QA-S009-A04 | advisory | 19 outdated PyPI deps | Defer unless ADR-approved bump |
| QA-S009-A05 | advisory | react-refresh/only-export-components warnings in `ollamaModelDownloadContext.tsx` | Split hooks/context to separate file if warnings become errors |

## Phase / execution-plan alignment

- **EV-010** `current_stage`: 07-build — build not committed; QA reflects WIP tree.
- **Phase 4 H1–H3** live staging: deferred (no staging URLs in env).
- **S008 QA-S008-B05** (coverage gate on EV-009 surfaces): parked on S008; may recur after S009 blockers fixed — re-check Python app thresholds on next full pass.

## Handoff

1. Fix **QA-S009-B01–B06** on current branch (minimal: docstrings, mock typing, test assertion, unused import).
2. Complete **07-build** — commit F38 extension atomically.
3. Run **08-verify-build** → record PASS.
4. Re-run **09-qa** (or spot-check blocking commands) before **10-e2e** and deploy stages.
5. Present blocking items to user in **11-verify-impl** for approve/defer/fix-now.
