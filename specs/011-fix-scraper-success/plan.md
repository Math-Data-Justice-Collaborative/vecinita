# Implementation Plan: Reliable scrape outcomes for protected pages

**Branch**: `013-fix-scraper-success` | **Date**: 2026-04-24 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/011-fix-scraper-success/spec.md`

## Summary

Improve the **Modal scraper service** (`services/scraper`) so single-URL jobs **reliably obtain substantive extractable content** for **HTML**, **direct PDF**, and **direct plain text** responses, and so **failures are classified** per the spec (transport vs. empty/shell vs. bot/HTML-family vs. policy vs. PDF/text-specific faults). Today, **Crawl4AI-only** HTML paths and Crawl4AI’s `success` flag drive `processed_count`; anti-bot / CSR shells and **non-HTML URLs misfetched through the browser** yield **zero successful pages** with opaque messaging. The technical approach is: **(1)** response-type routing (sniff `Content-Type` + magic bytes + URL heuristics), **(2)** **httpx**-based fetch for **PDF** and **text/plain** with dedicated extractors, **(3)** retain **Crawl4AI** for HTML with tunable wait/extraction and clearer mapping from library signals to **stable operator categories**, **(4)** persist **response kind** and **failure category** (gateway contract extension or backward-compatible encoding), **(5)** versioned **smoke URL list** + automated checks for SC-001.

## Technical Context

**Language/Version**: Python 3.11+ (`services/scraper/`).  
**Primary Dependencies**: **Crawl4AI** (browser crawl), **httpx** (typed/binary fetch), **Docling** (existing processing for html/pdf/docx), **Pydantic**, **Modal**, **FastAPI** (job API), **structlog**.  
**Storage**: Crawl outcomes persisted via **gateway HTTP** to DM/store (`scraping_jobs`, `crawled_urls`, `extracted_content`); schema today has `crawled_urls.error_message` / `status` only—**optional new fields** (see contracts) or structured error prefix for backward compatibility.  
**Testing**: `pytest` under `services/scraper/tests/` (`unit`, `integration`; `live` for smoke URLs behind marker).  
**Target Platform**: **Modal** Linux containers for workers; local dev with same venv.  
**Project Type**: Monorepo **service** — `services/scraper/src/vecinita_scraper/`.  
**Performance Goals**: Per-job wall clock bounded by existing `CrawlConfig.timeout_seconds`; binary fetch capped (e.g. max PDF bytes TBD in tasks, align with Modal memory).  
**Constraints**: **FR-004** / constitution — no deceptive client fingerprinting; robots/rate limits respected; **no CAPTCHA bypass**. Prefer **wait strategies**, **honest User-Agent**, and **type-correct fetch paths** over evasion.  
**Scale/Scope**: Single-URL and shallow crawl (`max_depth`); smoke list ≥5 entries per SC-001; classification matrix ~10 categories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design. Source: `.specify/memory/constitution.md`.*

| Principle | Status | Notes |
|-----------|--------|--------|
| **Community benefit** | **Pass** | Improves access to **public** government/health documents for RAG; no paywall circumvention. |
| **Trustworthy retrieval** | **Pass** | FR-003: preserve URL, job id, timestamps; classifications must not imply success when content is empty. |
| **Data stewardship** | **Pass** | Robots/rate limits unchanged; type routing reduces **accidental** over-fetch of wrong representation; audit fields extended, not removed. |
| **Safety & quality** | **Pass** | Add tests for classification matrix + fetch routing; gateway contract versioning documented. |
| **Service boundaries** | **Pass** | Primary code in **`services/scraper`**; **gateway OpenAPI** / DM `crawled-urls` payload only if new columns agreed—otherwise contract documents **compat** strategy. |

**Post–Phase 1 re-check**: `contracts/crawled-url-outcome.md` defines the persistence boundary; scraper remains the owner of crawl semantics; DM schema changes are **additive** and optional for MVP (structured `error_message` JSON prefix as fallback).

## Project Structure

### Documentation (this feature)

```text
specs/011-fix-scraper-success/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── crawled-url-outcome.md
└── tasks.md             # /speckit.tasks (not produced here)
```

### Source code (implementation targets)

```text
services/scraper/
  src/vecinita_scraper/
    crawlers/
      crawl4ai_adapter.py       # HTML path: map Crawl4AI success + heuristics; optional run_config tuning
      document_fetcher.py       # NEW (or split): httpx HEAD/GET, Content-Type + magic-byte routing
      text_extractors.py        # NEW: PDF text extraction, plain-text charset handling
    workers/
      scraper.py                # Orchestrate router: choose adapter vs direct fetch; aggregate failures
    core/
      models.py                 # Optional: CrawlConfig knobs for fetch caps; enums for kinds/categories
    persistence/
      gateway_http.py           # Extend JSON payload if contract adds fields
  tests/
    unit/                       # Router, extractors, classification unit tests
    integration/                # Mock httpx / Crawl4AI boundaries
  smoke/
    crawl_smoke_urls.yaml       # NEW: versioned list (or data/…) — composition per SC-001
```

**Structure Decision**: All behavioral changes live under **`services/scraper`**; **no** dependency on `backend/` active crawl for this feature. Smoke assets colocated with scraper tests or `services/scraper/smoke/`.

## Complexity Tracking

> No constitution violations requiring justification.

## Phase 0: Research

Consolidated in [research.md](./research.md). Unknowns around PDF library choice and gateway column additions are resolved there for planning purposes.

## Phase 1: Design & contracts

- [data-model.md](./data-model.md) — entities, fields, state.  
- [contracts/crawled-url-outcome.md](./contracts/crawled-url-outcome.md) — persisted outcome and optional API extensions.  
- [quickstart.md](./quickstart.md) — local run, smoke execution, env flags.

## Next step

Run **`/speckit.tasks`** to generate `tasks.md`, then implement or **`/speckit-implement`** when ready.
