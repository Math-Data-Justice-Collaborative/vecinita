# Context brief — S022-ingest-resilience (scoped)

**Mode:** scoped delta (S022-D4). No paper-analyst / org ecosystem scan.

## Topology (unchanged)

| Surface | Role for this cycle |
|---------|---------------------|
| Admin / data-management backend | Ingest job pipeline (scrape → chunk → embed → write) |
| `apps/internal-write-api` | Document upsert + chunk delete/insert |
| `packages/embedding-client` + Modal embed app | `/embed/batch` |
| `packages/ingest` | Chunking (`chunk.py`), content hash |
| ChatRAG | **Out of scope** except indirect retrieval quality from F49 |

## Code anchors (from tickets)

| Ticket | Anchors |
|--------|---------|
| #163 | Ingest `content_hash = sha256(text)`; write path always deletes chunks + re-embeds |
| #166 | `embed_client.embed_batch(chunks)` one-shot; ≥400 / dim mismatch fails whole URL job |
| #160 | `packages/ingest/.../chunk.py` — paragraph pack, `len(text.split())`, no overlap |

## Related ADRs

- ADR-008 — FastEmbed Modal app
- ADR-023 — ingest tag resilience (fail-open contrast for tags vs embeds)
- ADR-037 — unified LLM (not primary for this cycle)

## Browser / CORS

Admin FE may surface new job options (`force`, overlap knobs). Re-check connectivity H4–H5 at 12–13 if UI changes.
