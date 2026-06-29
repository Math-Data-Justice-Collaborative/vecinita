# ADR-007: Modal workers persist via DO internal write API

**Status:** Accepted  
**Stage:** 01-requirements  
**Date:** 2026-05-19

## Context

Ingest runs on **Modal** (scrape, chunk, embed) while the **system of record** is DO Managed Postgres (ADR-005). A spec contradiction arose: should Modal workers hold `DATABASE_URL` and write directly, or should only DigitalOcean services touch Postgres?

Storing `DATABASE_URL` on Modal increases secret sprawl, widens the attack surface for corpus writes, and complicates network policy. Siblings split Modal compute from Supabase/Postgres with varying patterns; the greenfield design needs one clear boundary.

## Decision

| Rule | Detail |
|------|--------|
| **`DATABASE_URL` location** | **DigitalOcean backends only** (ChatRAG Backend, DO internal write API) |
| **Modal workers** | **No** direct Postgres connections in v1 |
| **Persist path** | Modal ingest worker → **DO internal write API** (authenticated HTTP) → Postgres upsert |
| **Read path** | ChatRAG Backend reads pgvector directly on DO (same `DATABASE_URL` or read replica later) |

### DO internal write API

- Thin FastAPI service on DO (may be a **separate deployable** per ADR-010).
- Accepts service-authenticated payloads: documents, chunks, embeddings, job status updates.
- Auth: shared secret (`VECINITA_INTERNAL_API_KEY`), private network, or mTLS — **not** Vecinita user accounts (ADR-004).
- Corpus list/delete for admin may live on this API or a sibling DO route.

### Ingest flow

```
Admin UI → Modal ASGI POST /jobs → queue worker → scrape → chunk → FastEmbed
         → POST DO internal write API → Postgres
```

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Modal holds `DATABASE_URL` | Secret on GPU tier; harder to audit; user resolved RD-016 against this |
| Supabase client from Modal (siblings) | Supabase host + auth patterns out of scope |
| Dual write (Modal + DO) | Consistency risk; unnecessary |

## Consequences

- Internal write API is a **required** DO component for ingest — not optional glue.
- Modal and DO must share a matching internal API key in secrets.
- Job status may be stored via write API or a small job table updated only through DO.
- `04-tech-plan` sizes network latency Modal → DO (same region US).
- OpenAPI for internal write routes documented alongside public APIs (ADR-011).

## References

- RD-016 (`docs/decisions.md#requirements-decisions-01-requirements`)
- `docs/spec.md` §DO internal write API, §Data Flow
- `docs/deployment-integration.md` §Services
- ADR-002, ADR-005, ADR-010
