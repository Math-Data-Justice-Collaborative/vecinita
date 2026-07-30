# QA Report — EV-015 / S017 (F41)

> Generated: 2026-07-30  
> Scope: delta — F41 corpus rebuild / re-embed migration (#167)  
> Branch: `evolve/EV-015-corpus-reembed-migration` @ `a9c7eeb`  
> Mode: evolve / delta_only · parallel with 10-e2e

```text
QA Results:
  Lint:           PASS — 0 issues (ruff)
  Format:         PASS — 422 Python files; DM rebuild FE Prettier clean
  Typecheck:      PASS — 0 errors (1 pre-existing warning)
  Tests (Python): PASS (scoped) — H0c + UJ-053 + EV-015 unit; DB suite SKIPPED (no Docker)
  Tests (FE):     PASS — DM Vitest 688/688; ESLint 0 errors (3 react-refresh warnings)
  Tests (UI):     PASS — Playwright UJ-053 + UJ-054 (2/2)
  Coverage gate:  FAIL — DM FE lines 99.78% / branches 97.46% (need 100% / 98%)
  Security:       PASS — 0 CVEs (1 ignored nltk); secrets OK; gitleaks not installed
  Cross-file:     PASS — ruff clean; no modal imports outside scripts/infra
  Dependencies:   advisory — workspace packages skipped by pip-audit
  Template:       PASS — OpenAPI parse; no DATABASE_URL in Modal paths
  Data / Modal:   D6/D7 verified (staging state); live Modal/staging URLs unset
```

**Overall: fail** — sole blocking item is DM frontend coverage gate (QA-S017-B01). All other
blocking checks for F41 green. Local Postgres/Docker unavailable (same as 08).

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| Ruff lint / format | yes | PASS |
| basedpyright | yes | PASS |
| H0c CORS | yes | PASS |
| DM Vitest + ESLint | yes | PASS |
| Playwright T0-ui (UJ-053/054) | yes | PASS |
| `make audit` + secrets + OpenAPI + Modal DB guard | yes | PASS |
| DM FE coverage (`make test-coverage-fe FE_APP=data-management-frontend`) | yes | **FAIL** |
| Full pytest + integration (Postgres) | yes (CI) | SKIPPED locally |
| chat-rag Prettier drift (3 files) | no | ADVISORY — not in F41 delta |
| Staging H4–H5 / live Modal | no | ADVISORY — env unset |

## Commands run

```bash
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
uv run pytest tests/unit/test_cors_policy.py tests/e2e/test_uj053_corpus_rebuild.py \
  tests/unit/data_management/test_ev015_rebuild_shadow.py \
  tests/unit/shared_schemas/test_ev015_*.py -q
uv run pytest tests/unit tests/e2e --collect-only -q   # post a9c7eeb collection OK
cd apps/data-management-frontend && npm run lint && npm test -- --run
make test-coverage-fe FE_APP=data-management-frontend
bash scripts/ui/run_playwright.sh tests/ui/admin/uj053-corpus-rebuild.spec.ts \
  tests/ui/admin/uj054-rebuild-promote.spec.ts
make audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
```

## F41 surface coverage note

Istanbul gaps do **not** include `RebuildForm.tsx`, `RebuildPromoteForm.tsx`, or rebuild API
helpers — those meet thresholds. Residual shortfall is elsewhere in DM FE (SSE poll edges on
Jobs/JobDetail, Evaluation* tabs, BoundedTagList, auth link callback). EV-015 touched Jobs
pages only for `job_type=rebuild` i18n keys.

## Connectivity

| Item | Status |
|------|--------|
| H0c `test_cors_policy.py` | PASS |
| H0i `tests/integration` | SKIPPED (no Docker/Postgres) |
| `tests/smoke/test_staging_connectivity.py` | present |
| `scripts/deploy/verify_connectivity.sh` | present |
| H4–H5 staging frontends | ADVISORY — `VECINITA_STAGING_*` unset |

## Data / Modal

| Asset | Status |
|-------|--------|
| D1–D5, D8–D9 | verified (data-staging-state) |
| D6 FastEmbed / D7 Qwen | verified |
| Live Modal URL validate | SKIPPED — env unset |
| Workspace | vecinita (per staging state) |

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| **QA-S017-B01** | **blocking** | DM FE coverage gate FAIL: lines 99.78% / branches 97.46% (thresholds 100% / 98%). Gaps in Evaluation*, Jobs SSE edges, BoundedTagList — not Rebuild* forms. | Add branch tests for uncovered edges **or** confirm pre-existing on `main` and waive for F41; re-run `make test-coverage-fe FE_APP=data-management-frontend` |
| QA-S017-A01 | advisory | Local Postgres/Docker down — full unit/integration/UJ-054 promote not executed | CI Postgres after push; optional local compose for 11 |
| QA-S017-A02 | advisory | chat-rag Prettier dirty on 3 files (also unclean vs Prettier on `main` content) | Out of F41 scope; separate chore |
| QA-S017-A03 | advisory | Staging H4–H5 / live Modal unset | 12/13 deploy path |
| QA-S017-A04 | advisory | gitleaks not installed in PATH | Install for tree scan or rely on CI |
| QA-S017-A05 | advisory | Shadow→promote live equivalence (ISS-006 / TP-S017-07) | Staging drill at 13 |

## Phase alignment

- Phase 20 / 07-build complete; 08 PASS @ verification-report.md; collection fix `a9c7eeb`.
- Gate C→D passed; `phase_c` passed.
- Next: 11-verify-impl consumes this report + e2e-report (resolve B01 before deploy sign-off).
