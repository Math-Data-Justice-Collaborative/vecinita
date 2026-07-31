# Runbook outline — Corpus rebuild (staging → prod)

**Status:** Ops outline ready (EV-015 / F41 / #167) — T90.5 2026-07-30  
**Prod live rebuild:** not executed in EV-015 (S017-D6)

## Preconditions

- [ ] F41 deployed to staging (Modal data-mgmt + internal-write + admin FE)
- [ ] Document store migration applied; ingest writing `body_text` / revisions
- [ ] Backfill complete for existing docs (or scoped `document_ids` only)
- [x] `force` / dry-run / promote paths verified in CI (T88–T90 local + CI)
- [ ] F36 golden eval baseline recorded on current live corpus

## Staging procedure (TP-S017-01 / TP-S017-07)

### A — Live same-settings equivalence (pipeline proof)

1. Enqueue `job_type=rebuild`, `mode=reembed` or `rechunk`, **same** chunk/embed settings as
   today, `dry_run=false`, `force=true` if hash-skip would no-op (Admin **Corpus** → Rebuild corpus).
2. Monitor Jobs SSE / `/jobs/:id`.
3. Confirm job completes; spot-check retrieval unchanged in quality (same settings).

### B — Shadow → F36 → promote (**required** this cycle)

1. Enqueue rebuild with `dry_run=true` (store-backed reembed/rechunk preferred).
2. Confirm shadow rows for `rebuild_run_id`; **live** retrieval unchanged.
3. Run **F36** with `rebuild_run_id` set (TP-S017-04); compare vs baseline.
4. If gate passes, **promote** via Admin Corpus → Promote shadow rebuild (or promote API).
5. Record run ids, stamps, and eval links in session deploy notes.

## Production cutover (follow-on / runbook execution)

1. Announce maintenance window if retrieval quality may briefly change.
2. Ensure **backfill** completed for target docs (F41 deliverable).
3. Prefer shadow dry-run on prod store — **do not promote** until F36-on-shadow policy met.
4. Optional: dual-write / dim migration checklist if #159 model change.
5. Promote via Admin UI / promote API.
6. Verify ChatRAG smoke (H4/H5); keep prior revision for rollback.
7. Rollback: re-activate prior `rebuild_run_id` / revision snapshot.

## Rollback sketch

- Keep prior live embeddings until promote; after promote retain prior `rebuild_run_id` if possible.
- Never TRUNCATE corpus without corpus-db-safety guards.

## Related

- ADR-040 · TP-S017-01–09 · F36 · issues #167, #159–#166
- Phase 20 gate: `reports/phase20-gate.md`
