# QA Report — EV-027 / S030 (F75–F77)

> Generated: 2026-08-12  
> Scope: Phase 30 delta QA after 07-build + 08-verify-build (M127–M130)  
> Branch: `evolve/EV-027-corpus-automations` @ `3466b2b`  
> Mode: evolve / delta · next parallel **10-e2e**  
> Decision: S030-D55 (Gate C→D → 09-qa)

[Corpus: feature-list.md §F75] [Corpus: feature-list.md §F76] [Corpus: feature-list.md §F77]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]  
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]  
[Spec: docs/test-plan.md §TC-252–265]  
[Spec: docs/sessions/S030-corpus-automations/reports/verification-report.md]

```text
QA Results:
  Lint:           PASS — 0 issues (ruff); FE eslint 0 errors (3 refresh warnings)
  Format:         PASS — 590 files
  Typecheck:      PASS — 0 errors (1 pre-existing missing-module warning)
  Tests (Python): FAIL (1) — integration alembic head pin (see QA-S030-001);
                  unit+privacy PASS; F75–F77 e2e scoped PASS; H0c CORS PASS
  Tests (FE):     PASS — chat-rag 190; DM 813
  Tests (UI):     PASS — Playwright T0-ui 52 passed, 2 staging skipped
  Coverage gate:  PASS — FE branches ≥95% (make test-unit-coverage); combined 98.9% lines
  Security:       PASS (tree) — make audit 0; secrets OK; Modal no DATABASE_URL;
                  OpenAPI OK; make security-scan PASS (post-08 maxItems fix)
  Cross-file:     PASS — F401/F841 0; no pickle.loads; Modal imports only infra/
  Dependencies:   ADVISORY — nltk 3.9.4 ignores documented (audit/pip-audit-ignore.txt)
  Template:       PASS — api+worker; Modal under infra/modal/; openapi parse OK
  Data / Modal:   D1–D9 / D6 / D7 verified; H4–H5 deferred to 13 (URLs unset)
```

## Overall

**FAIL** (blocking H0i) — one integration assertion is stale against Alembic tip
`20260812_0016` (EV-027 freshness migration). In-cycle F75–F77 unit/API e2e/Vitest/
Playwright/lint/types/security/coverage are green. Disposition at **11-verify-impl**
(or fix-before-10): update `test_alembic_head_includes_ev002_migration` to assert tip
`20260812_0016` and keep prior revisions in `alembic history` only.

## Executive summary

| Area | Blocking | Advisory | Status |
|------|----------|----------|--------|
| Lint / format / types | 0 | 1 pyright warning | PASS |
| H0c CORS | 0 | — | PASS |
| Unit + privacy | 0 | 17 skipped | PASS (1581 passed) |
| H0i integration (+ compose suites) | 1 | 34 skipped | **FAIL** → QA-S030-001 |
| F75–F77 e2e (scoped) | 0 | — | PASS (7) |
| Frontend Vitest | 0 | 3 eslint refresh warnings | PASS |
| Playwright T0-ui | 0 | 2 staging skipped | PASS (52) |
| Coverage gate | 0 | — | PASS |
| Security tree | 0 | nltk ignores | PASS |
| H4–H5 live | — | staging FE URLs unset | ADVISORY → 13 |

## Commands run

```bash
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
uv run ruff check --select F401,F841 apps packages tests
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
make audit
make security-scan
make lint
uv run pytest tests/unit tests/privacy -q
uv run pytest tests/unit/test_cors_policy.py -q
uv run pytest tests/integration tests/e2e tests/smoke tests/eval tests/bugs -q
uv run pytest tests/e2e -k 'automation or freshness or finetune or uj080 or uj081 or uj082 or TC-25' -q
npm test -w vecinita-chat-rag-frontend -- --run
npm test -w vecinita-data-management-frontend -- --run
make test-unit-coverage
make test-ui
```

## Per-check detail

### Lint / format / typecheck
PASS. Pre-existing: `test_modal_url_validate.py` missing-module warning; DM eslint
`react-refresh/only-export-components` ×3.

### Python tests

| Suite | Result | Notes |
|-------|--------|-------|
| `tests/unit` + `tests/privacy` | PASS | 1581 passed, 17 skipped |
| H0c `test_cors_policy.py` | PASS | Blocking connectivity |
| Compose (`integration`/`e2e`/`smoke`/`eval`/`bugs`) | **1 FAIL** | See QA-S030-001; ~377 passed, 34 skipped |
| F75–F77 e2e scoped | PASS | 7 passed |

### Frontend

| App | Result |
|-----|--------|
| chat-rag-frontend | 37 files / **190** tests PASS |
| data-management-frontend | 96 files / **813** tests PASS |

### Playwright
52 passed, 2 skipped (staging T3-ui). Includes UJ-080 / UJ-081 / UJ-082. PASS.

### Coverage gate (`make test-unit-coverage`)
PASS. Combined lines 98.9%. FE branches: chat-rag 384/402 (97.2% lines / ≥95% branch gate);
DM 2137/2180 branches.

### Security
- `make audit`: 0 vulns (4 ignored — nltk PYSEC/CVE per `audit/pip-audit-ignore.txt`)
- Tree secrets / Modal DATABASE_URL / OpenAPI parse: PASS
- `make security-scan`: PASS (KICS MEDIUM cleared at 08 via `AutomationRunListResponse.maxItems`)
- gitleaks CLI: not installed locally (CI covers working-tree scan)
- Dangerous-pattern rg: only false positives (`enqueue_eval`, RegExp `.exec`)

### Cross-file / template
F401/F841 0. No `import modal` under `apps/`/`packages/`. OpenAPI present. Layout
`apps/*` + `packages/*` + `infra/modal/` matches api+worker.

### Data / Modal / connectivity
| Asset | Status |
|-------|--------|
| D1–D5, D8–D9 | verified |
| D6 FastEmbed / D7 Qwen | verified (`vecinita` workspace) |
| H4–H5 live | **ADVISORY** — `VECINITA_STAGING_*_FRONTEND_URL` unset → 13 |
| Modal live URL checks | SKIPPED — env unset |

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S030-001 | **blocking** | `tests/integration/test_ev002_schema.py::test_alembic_head_includes_ev002_migration` asserts tip `20260806_0014` but Alembic head is `20260812_0016` (`20260812_0016_ev027_freshness_fields.py`). Comment already says prior revs belong in **history**, not tip. | Update asserts: tip/heads → `20260812_0016`; keep `20260806_0014` (+ EV-002 chain) in `alembic history` only. TDD: red→green on that test. |
| QA-S030-002 | advisory | Staging H4–H5 / Playwright staging project skipped (URLs unset) | Run at 13-deploy-smoke with staging env |
| QA-S030-003 | advisory | nltk 3.9.4 transitive ignores (llama-index) | Keep until nltk inisec cwd fix; see ignore file |
| QA-S030-004 | advisory | DM eslint react-refresh warnings ×3 (playground download context) | Pre-existing; defer |
| QA-S030-005 | advisory | Live prod automation enable / FT promote AskQuestion | Deferred to 13 (S030-D10 / TP9) |

## Phase / execution-plan alignment

- Phase 30 M127–M130 07+08 complete; Gate C→D passed (S030-D55)
- AC live verify remains 09–11; this 09 run surfaces QA-S030-001 before merge
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) — leave open

## Next

Run **10-e2e** in parallel (per Full routing). Fix QA-S030-001 before or during 11.
