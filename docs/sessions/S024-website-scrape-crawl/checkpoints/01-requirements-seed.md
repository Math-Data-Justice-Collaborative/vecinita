# 01-requirements seed — S024 / EV-022 (Website scrape & crawl)

Generated from 00-context + 16-evolve Phase 0/1 (2026-08-03). Locked decisions are **confirm-only**.

## How 01 should use this

1. Load this seed (not a greenfield interview).
2. Confirm locked decisions in one batch.
3. Apply document manifest deltas only.
4. Interview **only** open questions below.
5. Next after 01: `02-verify-plan`.

## Locked decisions

| Seed ID | Session ID | Decision |
|---------|------------|----------|
| L1 | S024-D1 | Session **S024-website-scrape-crawl** after S023/EV-020 close |
| L2 | S024-D2 | Routing **Standard**; skip 03/05/06/15 |
| L3 | S024-D3 | Epic **#185**; order **#69 → #71 → #70**; independent PRs |
| L4 | S024-D4 / D25 | Cycle **EV-022**; Fn **F59 / F60 / F61** |
| L5 | S024-D6 | Personas = admin/ops DM; ChatRAG UI deferred (licensing) |
| L6 | S024-D7 / D14 | #69 includes **JS-render** + **basic PDF text** |
| L7 | S024-D8 / D11 | Crawl via additive `POST /jobs` options |
| L8 | S024-D9 / D12 | Corpus tree: domain → path → document → chunks |
| L9 | S024-D10 | Flow: Job form → job → Jobs detail → Corpus tree |
| L10 | S024-D13 | Per-page soft fail; partial metrics; failed nodes |
| L11 | S024-D15–D16 | Additive API; public-only + robots/rate-limit/UA |
| L12 | S024-D17 | ChatRAG nesting licensing = research note only |
| L13 | S024-D18 | Apps include ChatRAG **backend** nested metadata (no FE) |
| L14 | S024-D19–D20 | Config defaults; same Admin SPA |
| L15 | S024-D21 | JS-render runtime locked in **04** spike |
| L16 | S024-D22–D24 | Defaults ≈25/2; per-slice AC; T0/T2 + T3 crawl smoke |

## Document manifest (delta)

| Document | Action |
|----------|--------|
| `docs/feature-list.md` | **Done Phase 1** — F59–F61 rows + details |
| `docs/decisions/evolve-decisions.md` | **Done Phase 1** — §Cycle EV-022 |
| `docs/spec.md` | Scrape/crawl/tree behavior |
| `docs/config-spec.md` | Crawl/politeness/UA/PDF/JS knobs |
| `docs/api-contract.md` + OpenAPI | Additive job options + hierarchy read |
| `docs/user-journeys.md` | Admin crawl + corpus tree nesting |
| `docs/test-plan.md` / `acceptance-criteria.md` | AC/TC per Fn + e2e |
| `docs/data-management-plan.md` | Crawl ops notes |
| `docs/dependency-inventory.md` | If PDF/JS-render libs added (may wait for 04) |
| Session report | `reports/01-requirements-scrape-crawl.md` |

**Excluded:** ChatRAG UI; #94; full OCR; provider ABC; auth crawl.

## Open questions for 01 (confirm or refine)

| ID | Topic | Recommended |
|----|-------|-------------|
| Q1 | Confirm L1–L16 | Approve all |
| Q2 | Hierarchy API shape | Nested JSON under corpus/jobs (detail in 01/04) |
| Q3 | PDF scope | Text-extract PDF only; skip image-only / scanned without OCR |
| Q4 | ChatRAG backend meta | Store path/parent fields on documents; no FE change |
| Q5 | Journey/TC ids | Allocate next UJ/TC/AC blocks in 01 |

## Baseline code

| Area | Path | Today |
|------|------|-------|
| Scraper | `packages/ingest/vecinita_ingest/scrape.py` | Minimal HTMLParser |
| Models | `packages/ingest/vecinita_ingest/models.py` | `ScrapedDocument(url, title, text)` |
| Jobs | `POST /jobs` | `urls[]` single-page ingest |
| Corpus UI | `CorpusList.tsx` | Flat list |

## Next after 01

`02-verify-plan` (delta consistency + statement audit on changed sections).
