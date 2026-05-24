# ADR-014: Corpus tagging, community browse, and tag-filtered RAG

**Status:** Accepted  
**Stage:** 00-context (EV-001 delta)  
**Date:** 2026-05-24

## Context

Community members need to discover corpus documents and filter by tags. Operators need to view chunks and curate tags (LLM-generated or human-edited) to improve RAG retrieval. The current schema has `documents`, `chunks`, and `embeddings` only — no tags, no public read API, and no chunk viewer in the admin UI.

Evolve cycle **EV-001** intake (2026-05-24) resolved product decisions R12–R18 in `docs/context-brief.md` §11.

## Decision

### Tag model

| Aspect | Choice |
|--------|--------|
| Primary granularity | **Document-level** tags for browse and default RAG filter |
| Overrides | **Chunk-level** tags allowed for admin fine-tuning (optional override of document tags at retrieval) |
| Vocabulary | **Hybrid** — controlled/suggested tag list with admin ability to add new tags |
| Provenance | Each tag assignment records `source`: `llm` \| `human` — **no operator identity** (ADR-004) |
| Storage | New tables: `tags`, `document_tags`, `chunk_tags` (Alembic revision in `apps/database/`) |

### LLM tagging

- Run **automatic LLM tagging during ingest** **after chunking, before embed** (ADR-015 TP-010).
- **Admin can re-run** LLM tagging or edit tags manually per document/batch.
- Use existing self-hosted LLM on Modal (ADR-009); no third-party tagging API by default.

### Community access (public)

- **Browse + filter by tags** in ChatRAG frontend — list/search documents by tag; **open original source URL** on user action (RD-026).
- **Public read routes** on **ChatRAG backend** (`GET /api/v1/documents`, tag list, document detail) — no API key; same CORS pattern as `/api/v1/ask`.
- Does **not** expose admin write paths or internal-write API to browsers.

### Admin access

- **Data management frontend**: chunk viewer (read-only chunk text) + tag editor at document and chunk level.
- Writes via authenticated admin paths (infra credentials — proxy key / internal API); tag edits must not require Vecinita user accounts (ADR-004).

### RAG retrieval

- **Optional tag filter** on `AskRequest` (user-selected tags from UI).
- **LLM-inferred tags** from the question when user does not select tags (both modes active per R16).
- Retriever SQL in `packages/rag` joins tag tables; document-level tags apply unless chunk override exists.

### Feature allocation (proposed for 01-requirements)

| ID | Feature |
|----|---------|
| F19 | Public corpus browse & tag filter (ChatRAG frontend + read API) |
| F20 | LLM auto-tagging at ingest + admin re-tag job |
| F21 | Admin chunk viewer & tag editor (document + chunk) |
| F22 | Tag-aware RAG retrieval (user filter + LLM inference) |

## Consequences

- OpenAPI deltas: `openapi/chat-rag.yaml`, `openapi/internal-write.yaml` (tag fields on upsert/PATCH).
- Privacy review: tag provenance must not store operator PII; `tests/privacy/` extended.
- Connectivity: new public GET routes require H4 CORS verification on chat backend; admin tag writes may need server-side proxy review (embedding `VECINITA_INTERNAL_API_KEY` in static admin bundle remains a known weakness — consider BFF in evolve tech plan).
- Ingest pipeline (`apps/data-management-backend`) gains LLM tagging step — Modal LLM call budget impact (cost cap ADR-004).

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Tags on chunks only | User chose document-level primary for simpler browse/filter |
| Separate read-only API service | Extra DO deployable increases cost (ADR-004) |
| Chat-only tag filter (no browse UI) | User wants browse + tag filter for community discovery |
| Controlled vocabulary only | Too rigid for evolving corpus; hybrid chosen |

## References

- ADR-004 (zero personal data)
- ADR-010 (multi-app DO topology)
- ADR-011 (OpenAPI source of truth)
- Resolution log R12–R18 in `docs/context-brief.md` §11
