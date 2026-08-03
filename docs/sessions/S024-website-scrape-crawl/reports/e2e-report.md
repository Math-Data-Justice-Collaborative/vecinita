# E2E Behavior Report — EV-022 / S024 (F59–F61)

> Generated: 2026-08-03  
> Mechanism: API (FastAPI TestClient) + Vitest + Playwright T0-ui  
> Journeys: **UJ-064**, **UJ-065**, **UJ-066**  
> Branch: `evolve/EV-022-website-scrape-crawl` @ `aeb76a9`  
> Mode: evolve / delta_only · parallel with 09-qa  
> Features: **F59** robust scrape · **F60** website crawl · **F61** corpus tree

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-064 Robust scrape | API TestClient | T0 | **PASS** | TC-199 — 1/1 |
| 2 | UJ-065 Website crawl | API TestClient | T0 | **PASS** | TC-202 — 2/2 soft-fail + tree |
| 3 | UJ-066 Corpus tree | API TestClient | T0 | **SKIPPED** | TC-204 — skip-without-Postgres (S024-D41) |
| — | UJ-066 Corpus tree UI | Playwright | T0-ui | **PASS** | TC-207 — tree/flat toggle + bulk |
| — | F59–F61 unit TC-196–203,205–206 | pytest / Vitest | T0 | **PASS** | 54 unit passed, 1 skipped; DM Vitest 702 |
| — | T1 Integration | `tests/integration/` | T1 | **SKIPPED** | Docker unavailable |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live crawl smoke | staging | T3 | **DEFERRED** | S024-D24 post-deploy |

**Overall T0 (EV-022 delta):** **PASS** with documented TC-204 skip — UJ-064/065 green; UJ-066 covered by unit tree + Playwright TC-207 locally; live API tree CI-gated.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | UJ-064/065 API e2e + units + Playwright UJ-066 |
| **T2 connectivity** | **DEFERRED** | 13-deploy-smoke |
| **T3 browser** | **DEFERRED** | Live crawl smoke post-deploy (S024-D24) |

## Journey → test matrix

| Journey | API e2e | Unit / Vitest (TC) | UI E2E | T3 |
|---------|---------|-------------------|--------|-----|
| UJ-064 | `test_uj064_robust_scrape.py` | TC-196–198 | N/A | deferred |
| UJ-065 | `test_uj065_website_crawl.py` | TC-200–201; Vitest TC-203 | optional uj065 | deferred |
| UJ-066 | `test_uj066_corpus_tree.py` (skip local) | TC-205–206 Vitest; nested fields | `uj066-corpus-tree.spec.ts` TC-207 | deferred |

## Journey details

### UJ-064: Robust scrape (F59)

| Step | Assertion | Status |
|------|-----------|--------|
| 1 | Single-URL job completes with main-content extract | **PASS** (TC-199) |
| 2 | Supporting units: boilerplate strip, robots/rate, PDF soft-fail | **PASS** (TC-196–198) |

### UJ-065: Website crawl (F60)

| Step | Assertion | Status |
|------|-----------|--------|
| 1 | Crawl job soft-fails per page; partial success | **PASS** (TC-202) |
| 2 | Job tree payload present | **PASS** (TC-202) |
| 3 | Scope/dedup + depth/page caps | **PASS** (TC-200–201) |
| 4 | JobForm additive crawl options | **PASS** (Vitest TC-203 via DM suite) |

### UJ-066: Corpus tree (F61)

| Step | Assertion | Status |
|------|-----------|--------|
| 1 | `GET .../corpus/tree` nested payload | **SKIPPED** local (TC-204 / S024-D41) — CI-gated |
| 2 | Tree expand/collapse + flat toggle + bulk select | **PASS** (Playwright TC-207; Vitest TC-205–206) |
| 3 | Nested source fields on documents | **PASS** (unit nested_source / migration coverage) |

## Commands

```bash
uv run pytest \
  tests/e2e/test_uj064_robust_scrape.py \
  tests/e2e/test_uj065_website_crawl.py \
  tests/e2e/test_uj066_corpus_tree.py \
  tests/unit/test_cors_policy.py -v
# → 20 passed, 13 skipped (incl. UJ-066 + CORS env skips)

uv run pytest tests/unit -k "scrape or crawl or corpus_tree or trafilatura or nested_source or openapi"
# → 54 passed, 1 skipped

npm test -w vecinita-data-management-frontend -- --run --maxWorkers=2
# → 702 passed

make test-ui
# → 43 passed, 2 skipped (staging)
```

## Findings for 11-verify-impl

| ID | Severity | Finding |
|----|----------|---------|
| E2E-S024-A01 | advisory | TC-204 / UJ-066 API e2e skipped locally (no Postgres) — CI-gated per S024-D41 |
| E2E-S024-A02 | advisory | T1 integration + full e2e suite need Postgres — CI on PR |
| E2E-S024-A03 | ship-path | T3 live crawl smoke deferred to post-deploy (S024-D24) |
| E2E-S024-A04 | info | Playwright staging specs skipped (no `VECINITA_STAGING_*` URLs) — expected |

## AC mapping (pre-11)

| AC | Status (T0 evidence) |
|----|----------------------|
| AC-SC1 | **met** — TC-196 unit + TC-199 / UJ-064 |
| AC-SC2 | **met** — TC-197 |
| AC-SC3 | **met** — TC-198 |
| AC-SC4 | **met** — TC-200 |
| AC-SC5 | **met** — TC-201 |
| AC-SC6 | **met** — TC-202 / UJ-065 |
| AC-SC7 | **met** — TC-203 (Vitest in DM suite) |
| AC-SC8 | **CI-gated** — TC-204 skip-without-Postgres (S024-D41); unit nesting OK |
| AC-SC9 | **met** — TC-205 + TC-207 Playwright |
| AC-SC10 | **met** — TC-206 + TC-207 |
| AC-SC11 | **met (unit)** — nested source fields; live API assert with TC-204 in CI |
| AC-SC12 | **held** — out of scope boundaries respected |
