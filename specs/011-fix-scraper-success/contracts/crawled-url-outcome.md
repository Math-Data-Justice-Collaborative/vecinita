# Contract: Crawled URL outcome (scraper → gateway)

**Feature**: 011-fix-scraper-success  
**Owner**: `services/scraper` worker; consumer: Data Management **gateway** persistence API.

## Purpose

Define fields operators and integrators rely on for **per-URL** crawl outcomes (FR-002, FR-008, User Story 3).

## Current baseline (`POST /crawled-urls`)

Existing JSON body (conceptual):

```json
{
  "job_id": "uuid",
  "url": "https://…",
  "raw_content": "string",
  "content_hash": "hex",
  "status": "success | failed",
  "error_message": "string | null"
}
```

## Preferred additive fields (backward compatible)

Optional keys (ignored by older gateway versions if not deployed):

| Field | Type | Required when | Description |
|-------|------|---------------|-------------|
| `response_kind` | string enum | `status=success` recommended | `html`, `pdf`, `plain_text`, `unknown` |
| `failure_category` | string enum | `status=failed` | Values from `data-model.md` § Failure categories |
| `operator_summary` | string | optional | ≤500 chars; plain language for UI |

**Versioning**: Clients MAY send `outcome_schema_version: 1` when any new field is present.

## Fallback encoding (MVP without gateway migration)

When gateway cannot store separate columns, scraper MAY set `error_message` to a single-line JSON:

```json
{"failure_category":"non_extractable_html","response_kind":"html","detail":"…"}
```

Gateway stores as TEXT unchanged; **DM API** SHOULD parse when serving job details (follow-up task if not in scraper scope).

## Job-level aggregate (`POST /jobs/{id}/status`)

When `processed_count == 0`, `error_message` SHOULD be a concise multi-line or JSON list of `{url, failure_category, operator_summary}` capped to **10** URLs with “+N more” suffix.

## Appendix: Crawl4AI string mapping (informative)

Implementation maintains a mapping from common **`Crawl4AI` `error_message` substrings** (e.g. anti-bot structural hints) to **`failure_category`** `likely_bot_or_client_limitation` vs `non_extractable_html` per product rules—mapping table is **test-owned** (golden files).
