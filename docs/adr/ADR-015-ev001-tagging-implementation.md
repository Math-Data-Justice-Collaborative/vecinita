# ADR-015: EV-001 tagging implementation (technical)

**Status:** Accepted  
**Stage:** 04-tech-plan (EV-001 delta)  
**Date:** 2026-05-24  
**Features:** F19, F20, F21, F22  
**Evolve cycle:** EV-001

## Context

Product decisions for corpus tagging and browse are captured in ADR-014 and RD-024–RD-033. Several implementation choices were left open for 04-tech-plan: ingest pipeline ordering, admin re-tag mechanics, retrieval SQL, LLM reuse, browse UX routing, and cost posture.

## Decision

| Topic | Choice | Rationale |
|-------|--------|-----------|
| Ingest LLM tagging step | **After chunking, before embed** | Tags apply to text only; persist with chunks before vectors |
| Admin LLM re-tag | **Async Modal job** | Consistent with UJ-002 ingest; avoids HTTP timeout on large docs |
| Re-tag job model | **Extend `jobs` table** with `job_type=retag`; poll `GET /jobs/{id}` | Reuses existing admin job UI patterns |
| Retrieval tag filter SQL | **Union match** — filter tag on document OR chunk | RD-025; chunk tags augment document tags |
| Ask-time tag inference | **Same Modal vLLM** (Qwen2.5-1.5B) with `VECINITA_LLM_TAG_MAX_TOKENS=128` | No new deployable; scale-to-zero already provisioned |
| Browse UI | **`/corpus` route** in ChatRAG frontend + tag chips in chat sidebar | Clear navigation; sidebar chips for F22 |
| EV-001 git branch | **`evolve/EV-001-corpus-tags`** from `main` | Per workflow-state evolve convention |
| LLM cost (EV-001) | **Within existing ≤ $50/mo cap** | Extra ingest + inference calls at pilot volume; monitor via cost-monitoring.md |

## Consequences

- Ingest worker order: scrape → chunk → **LLM tag** → embed → DO write (tags included in batch upsert).
- Internal write API implements tag PATCH, chunk list, and `POST .../retag` → enqueues Modal retag job.
- `packages/rag` retriever adds tag JOIN with union semantics; user-selected `tags[]` skip inference.
- New Alembic revision for `tags`, `document_tags`, `chunk_tags`; `jobs.job_type` enum extended.
- ChatRAG backend adds public GET `/api/v1/documents`, `/api/v1/tags`, `/api/v1/documents/{id}` — H4 CORS verification extended (TC-046).
- Data fixtures D8 (seed tags — exists), D9 (tagged corpus) required before browse/RAG E2E tasks.

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Tag after embed | Unnecessary ordering; tags do not depend on vectors |
| Sync retag HTTP | Timeout risk; inconsistent with ingest job UX |
| Separate tagging LLM service | Extra Modal surface + cost for marginal benefit at pilot scale |
| Keyword-only tag inference | Weaker retrieval when user does not select tags (RD-027 requires LLM infer) |
| Slide-over browse panel | User chose dedicated `/corpus` route for discoverability |

## References

- ADR-014 (product tagging model)
- ADR-009 (vLLM on Modal)
- RD-025, RD-027, RD-032 (requirements-decisions.md)
- TP-010–TP-017 (requirements-decisions.md §04-tech-plan EV-001)
