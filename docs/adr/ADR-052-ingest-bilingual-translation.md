# ADR-052: Ingest bilingual translation (F75 / #251)

**Status:** Accepted  
**Date:** 2026-08-22  
**Related:** ADR-037, ADR-004, ADR-048, #245, EV-029

## Context

Ingest stores scraped text as-is (`docs/data-flow.md`). English-only sources leave Spanish UI under-served until operators manually translate (#245) or ChatRAG uses cross-language retrieval supplements (PR #250).

## Decision

1. **Opt-in** via `JobOptions.translate_locales` on ingest/crawl jobs (default off).
2. **Paired documents:** sibling row per locale, `paired_document_id` → source document.
3. **URL uniqueness:** composite `(url, language)` on `documents`.
4. **Draft gate:** translations default `publish_status=draft`; ChatRAG retriever excludes drafts.
5. **Engine:** `vecinita-llm` per-chunk MT with community-resource prompt (no PII).
6. **Promote:** operator `PATCH /internal/v1/documents/{id}` with `publish_status=published`.

## Consequences

- #245 dashboard parity can consume `paired_document_id` without new pairing heuristics.
- Re-ingest with `force` + translate replaces draft ES sibling via upsert on `(url, es)`.
- Latency grows with chunk count × LLM RTT; acceptable for operator-opt-in batches.
