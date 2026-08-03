# QA Report — EV-022 / S024 (F59–F61 website scrape & crawl)

> Generated: 2026-08-03  
> Scope: delta — F59 robust scrape · F60 website crawl · F61 corpus tree  
> Branch: `evolve/EV-022-website-scrape-crawl` @ `aeb76a9`  
> Mode: evolve / delta_only · parallel with 10-e2e  
> Prior: 08-verify-build **PASS** · Gate C→D **passed** (S024-D42) · Phase 26 M108–M111 complete

```text
QA Results:
  Lint:           PASS — 0 errors (3 pre-existing FE react-refresh warnings)
  Format:         PASS — 484 files
  Typecheck:      PASS — 0 errors, 1 warning (test_modal_url_validate)
  Tests (Python): PASS (delta) — 54 unit + UJ-064/065 e2e + H0c (UJ-066 skip-without-Postgres)
  Tests (FE):     PASS — DM Vitest 702/702; make check-fast lint/tsc all workspaces
  Tests (UI):     PASS — Playwright 43 passed / 2 skipped (staging); UJ-066 included
  Coverage gate:  SKIPPED locally — CI on PR (make test-unit-coverage)
  Security:       PASS — make audit (workspace pkgs skipped); secrets OK
  Cross-file:     PASS — ruff clean; no pickle.loads / bare eval/exec in apps+packages
  Dependencies:   advisory — workspace packages skipped by pip-audit; npm audit 7 high (transitive)
  Template:       PASS — Modal no DATABASE_URL; OpenAPI OK; operator specs untracked
  Data / Modal:   D1–D9 verified; D6/D7 verified (2026-06-30)
```

**Overall: pass_with_advisories** — blocking local delta checks green; full pytest/integration + FE coverage deferred to CI (Docker/Postgres unavailable — S024-D41).

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| Ruff lint | yes | **PASS** |
| Ruff format | yes | **PASS** |
| basedpyright | yes | **PASS** (0 errors) |
| `make check-fast` (incl. FE lint/tsc) | yes | **PASS** (3 react-refresh warnings DM FE) |
| H0c `test_cors_policy.py` | yes | **PASS** |
| Corpus reset guard | yes | **PASS** |
| Secrets / Modal DB / OpenAPI / operator specs | yes | **PASS** |
| `make audit` | yes | **PASS** (workspace packages not on PyPI) |
| F59–F61 delta pytest (unit + e2e) | yes | **PASS** — see commands |
| Full pytest + integration (Postgres) | yes (CI) | **SKIPPED locally** — Docker unavailable (S024-D41) |
| Frontend Vitest (DM) | yes | **PASS** — 702/702 |
| Coverage gate | yes (CI) | **SKIPPED locally** — CI on PR |
| Playwright T0-ui | yes | **PASS** — 43 passed / 2 skipped (staging) |
| Staging H4–H5 | no | **ADVISORY** — deferred to 12/13 |

## Commands run

```bash
make check-fast
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
make audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
bash scripts/check_corpus_reset_guard.sh
uv run pytest tests/unit -k "scrape or crawl or corpus_tree or trafilatura or nested_source or openapi"
uv run pytest \
  tests/e2e/test_uj064_robust_scrape.py \
  tests/e2e/test_uj065_website_crawl.py \
  tests/e2e/test_uj066_corpus_tree.py \
  tests/unit/test_cors_policy.py -v
npm test -w vecinita-data-management-frontend -- --run --maxWorkers=2
make test-ui
```

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S024-A01 | advisory | Local Docker/Postgres unavailable — TC-204 / full integration deferred to CI (S024-D41) | Confirm green `ci.yml` after push |
| QA-S024-A02 | advisory | FE coverage gate not re-run locally | CI `coverage` job on PR |
| QA-S024-A03 | advisory | npm audit reports 7 high on transitive FE deps (recharts/etc.) | Track separately; not introduced by EV-022 product code |
| QA-S024-A04 | info | basedpyright warning on `deploy.modal_url_validate` import (pre-existing) | No action for EV-022 |
| QA-S024-A05 | info | 3 DM FE `react-refresh/only-export-components` warnings (pre-existing playground context) | No action for EV-022 |
| QA-S024-A06 | ship-path | Alembic `20260803_0011_ev022_nested_source_fields` must apply on deploy DB | Confirm at 12/13 |

## Connectivity (stage 09)

| Gate | Status | Evidence |
|------|--------|----------|
| H0c CORS | **PASS** | `tests/unit/test_cors_policy.py` |
| H0i integration | **SKIPPED** | Docker/Postgres unavailable |
| H4–H5 staging FE | **ADVISORY** | Deferred to 12/13 |

## Data / Modal

| Asset | Status |
|-------|--------|
| D1–D5, D8–D9 | verified |
| D6 FastEmbed / D7 Qwen | verified (2026-06-30) |
| Modal workspace | `vecinita` (expected) |

## Phase / plan alignment

Phase 26 M108–M111 complete; Gate C→D **PASS** (S024-D42). Next: 11-verify-impl after 10-e2e report.
