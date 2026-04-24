# Data model: Queued page ingestion pipeline

## Overview

Logical entities align with [spec.md](./spec.md) **Key Entities** and existing persistence tables used by **`modal_scraper_pipeline_persist`** and scraper services. Exact column names may match current schema; new fields require migration tasks if introduced.

## Page ingestion job

**Represents**: One logical URL (or canonical URL) moving through **queued → scrape → chunk → enrich → embed → stored | failed**.

| Field / concept | Notes |
|-----------------|--------|
| `job_id` | Stable string identifier; returned to clients on submit. |
| `source_url` | Raw submitted URL; may differ from canonical after redirects. |
| `canonical_url` | Optional; used for dedup (edge case in spec). |
| `status` | Enum-like string consistent with worker + gateway writers; transitions must be **monotonic** except explicit `retry` / `reprocess` operations. |
| `pipeline_stage` | Fine-grained step for operators (e.g. `scraping`, `chunking`, `llm`, `embedding`, `persisting`) — may be encoded in `metadata` jsonb if no column yet. |
| `error_category` | Short machine code for FR-008 / FR-014 mapping (not raw stack traces). |
| `correlation_id` | Echo of gateway **FR-015** id for support join-up; stored on job or latest crawl row. |
| `created_at` / `updated_at` | UTC timestamps for audit. |

**State transitions (normative)**:

1. `queued` → `scraping` when worker claims job.  
2. `scraping` → `chunking` only if extractable text exists (else terminal **no_indexable_content** or **scrape_failed**).  
3. `chunking` → `llm` → `embedding` → `persisting` → `succeeded` on happy path.  
4. Any stage → `failed` with **category** + safe message; **FR-010**: partial writes either rolled back per page or flagged **`partial`** with explicit reprocess.

**Idempotency**: Re-POST of the same pipeline stage payload with the same **`idempotency_key`** (job_id + stage + chunk ordinal) MUST NOT duplicate embeddings (UNIQUE constraint or upsert pattern — implementation detail in tasks).

## Queue fairness (**FR-002**)

**Default policy (v1):** **Global FIFO** among queued jobs at the same priority: workers MUST dequeue / claim work in **`created_at` ascending** order unless an explicit **priority** field (future) overrides. Per-tenant fairness can be layered later by sorting on `(user_id, created_at)`; until then, document any deployment that needs tenant isolation.

**Durable queue shape:** Job rows in Postgres (`scraping_jobs` and related) are the **source of truth** for “durable or operationally acceptable queue” (see `research.md` Decision 5); no separate message broker is required for v1.

## Chunking parameters (**FR-004**)

Initial **implementation targets** (tune via config/env without spec amendment for minor numeric changes):

| Parameter | Initial value | Notes |
|-----------|-----------------|--------|
| Max chunk size | ~2 000 characters (or token-equivalent if chunker is token-based) | Split on paragraph/heading boundaries when detectable. |
| Overlap | ~200 characters or **~10%** of max chunk size, whichever is smaller | Preserves context across chunk boundaries for bilingual Q&A. |
| Empty / shell page | — | After scrape, if extractable text length is below a **documented minimum** (e.g. `< 50` characters of substantive text), transition to **`no_indexable_content`** or **`scrape_failed`** with category; **do not** call LLM/embed (**SC-002**). |

Constants MUST live in one scraper-side module (see **T037** in `tasks.md`) and be referenced from tests so **FR-004** stays verifiable.

## Dedup / canonical URL (edge case)

When **`canonical_url`** (or normalized URL) matches a job already in **terminal `succeeded`** for the same corpus scope, the system SHOULD short-circuit to **`duplicate_skipped`** (idempotent no-op) without writing new embeddings. A future **`force_reprocess`** override is **out of scope for v1** tasks unless a later spec adds it—until then, treat “duplicate URL” as **skip**, not silent re-embed. Exact matching rules (trailing slash, scheme) are implementation details recorded in persist layer tests (**T038** in `tasks.md`).

## Content chunk

**Represents**: A segment of scraped text for one job.

| Field / concept | Notes |
|-----------------|--------|
| `chunk_id` / surrogate key | DB primary key. |
| `job_id` | FK-style linkage. |
| `ordinal` | Order within page for stable retrieval citations. |
| `raw_text` | Original segment; retained for traceability (**FR-005**). |
| `enriched_text` | Optional LLM output; must not be sole stored text if product requires raw traceability. |
| `metadata` | Token counts, model id, language detection, etc. |

## Chunk embedding

**Represents**: Vector + model identity for a chunk.

| Field / concept | Notes |
|-----------------|--------|
| `chunk_id` | 1:1 or 1:n if multiple embedding models (default 1:1). |
| `embedding` | pgvector or stored representation per existing schema. |
| `model_id` | Service/version for reproducibility (**SC-002** ghost-vector audits). |

## Gateway correlation & error envelope (logical)

Not separate DB tables; carried on HTTP responses per **FR-014** / **FR-015**.

| Element | Purpose |
|---------|---------|
| `X-Request-Id` (example) | Propagate to logs Modal-side when gateway forwards work. |
| JSON error body | Stable keys: e.g. `code`, `message`, `request_id` — exact names fixed in OpenAPI + Pact.

## Relationships

```text
Page ingestion job 1 ── * Content chunk * ── 0..1 Chunk embedding
        │
        └── audit / crawled_urls / extracted_content (existing tables as today)
```

## Validation rules (from spec)

- **FR-009**: No `embedding` rows for jobs that failed policy / scrape.  
- **FR-007**: Every embedding row joins to a chunk and resolvable job URL.  
- **SC-003**: Retry policy must not create duplicate **succeeded** outcomes for the same logical completion criteria.
- **FR-010** (v1 reconciliation): If embedding fails **after** chunks exist for the job, workers mark the job **failed** with structured `error_message` JSON (`partial_completion`, `requires_reprocess`) plus `metadata.pipeline_stage` / `error_category` so operators do not treat the page as fully indexed; automated deletion of orphan chunk rows is **not** required in v1 unless a later task adds gateway SQL for it.
