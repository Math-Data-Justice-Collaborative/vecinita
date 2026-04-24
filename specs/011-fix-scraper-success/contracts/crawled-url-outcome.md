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

## Operator runbook (failure_category → action)

| failure_category | Suggested operator action |
|------------------|---------------------------|
| `transport_error` | Retry later; check DNS/TLS/firewall; confirm URL reachable from browser. |
| `http_error` | Inspect HTTP status; widen crawl timeout only if 408/504; fix URL if 404. |
| `policy_blocked` | Respect robots/terms; exclude URL or obtain permission path. |
| `non_extractable_html` | Enable longer waits; try manual capture; consider alternate URL on same site. |
| `likely_bot_or_client_limitation` | Retry off-peak; reduce automation footprint; manual capture if policy allows. |
| `content_not_ready` | Increase `timeout_seconds` / wait-for-content tuning; retry once. |
| `pdf_corrupt_or_unreadable` | Re-fetch source; validate URL; try manual download. |
| `pdf_password_protected` | Manual capture or obtain password under policy. |
| `pdf_empty_non_extractive` | Expect image-only PDF; use OCR/manual path outside this worker. |
| `text_encoding_failure` | Report encoding issue; try alternate mirror URL. |
| `format_mismatch` | Verify URL is correct; report misconfigured server response. |
| `text_empty` | Confirm resource has body content; pick alternate URL. |
