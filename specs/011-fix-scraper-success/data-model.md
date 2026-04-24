# Data model: 011-fix-scraper-success

## Overview

Extends the **scrape job → crawled URL → extracted content** pipeline with explicit **response typing** and **failure classification** so operators and downstream jobs can interpret outcomes without raw stack traces.

## Entities

### Scrape job (existing)

- **id**: UUID  
- **status**: enum `JobStatus` (unchanged progression)  
- **error_message**: optional aggregate message when **FAILED** — should summarize **per-URL primary categories** when zero successes (FR-002).

*No schema change required on `scraping_jobs` for MVP if multi-line or structured string is acceptable; optional JSON later.*

### Crawled URL attempt (logical extension)

Maps to `crawled_urls` row + worker in-memory **`CrawledPage`**.

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | UUID | Parent job |
| `url` | text | Target URL |
| `status` | string | `success` \| `failed` (unchanged) |
| `raw_content` / hash | text / varchar | Stored representation for successful rows (markdown/HTML/text/PDF-derived text policy TBD in tasks) |
| `error_message` | text | Human-safe explanation; may embed structured JSON per contract fallback |
| **`response_kind`** (new optional) | enum string | `html` \| `pdf` \| `plain_text` \| `unknown` |
| **`failure_category`** (new optional) | enum string | See § Failure categories |

### Page attempt outcome (worker / API shape)

Aligns with spec **Key Entities** — used in logs and ideally persisted.

| Field | Description |
|-------|-------------|
| `response_kind` | Document family after sniff |
| `failure_category` | Null on success |
| `extractable_char_count` | Integer metric for rubric (not necessarily persisted) |
| `operator_message` | Short plain language |

### Smoke / regression corpus entry

| Field | Description |
|-------|-------------|
| `url` | HTTPS public URL |
| `kind_tag` | `html` \| `pdf` \| `text` \| `shell_regression` |
| `notes` | Why included, expected category if failure |
| `live` | boolean — whether safe for automated live CI |

## Failure categories (normative strings for code + docs)

Stable snake_case values (subset may ship in v1):

1. `transport_error` — connection, DNS, TLS  
2. `http_error` — non-success status  
3. `policy_blocked` — robots / explicit disallow  
4. `non_extractable_html` — loaded but shell / minimal text / script-heavy per heuristics  
5. `likely_bot_or_client_limitation` — Crawl4AI or heuristic anti-bot signal  
6. `content_not_ready` — wait/timeout bounded (FR-006)  
7. `pdf_corrupt_or_unreadable`  
8. `pdf_password_protected`  
9. `pdf_empty_non_extractive`  
10. `text_encoding_failure`  
11. `format_mismatch` — declared vs actual bytes  
12. `text_empty`  

*Mapping table from Crawl4AI raw strings → these codes lives in implementation + contract appendix.*

## State transitions

Unchanged at job level: `PENDING` → `VALIDATING` → `CRAWLING` → `EXTRACTING` → (`PROCESSING` | `FAILED`).  

**Semantic change**: `EXTRACTING` may receive **zero** queued process jobs when all pages `failed` with explicit categories; job still transitions to **FAILED** with structured summary.

## Validation rules

- Every **failed** page row MUST have **`failure_category`** (or JSON block) set.  
- Every **success** page MUST have **`response_kind`** and substantive content per rubric.  
- **`format_mismatch`** MUST NOT be labeled `likely_bot_or_client_limitation` (SC-003 spirit).
