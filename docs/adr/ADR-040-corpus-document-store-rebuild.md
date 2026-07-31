# ADR-040: Corpus document store + rebuild job + version stamps

**Status:** Accepted (EV-015 / S017 / #167)  
**Date:** 2026-07-30  
**Context:** F41 — prerequisite for #159–#166 corpus shape changes

## Context

Ingest today scrapes URL → chunks → embeds → upserts via internal-write (ADR-007). The
`documents` row stores `url`, `title`, `content_hash`, `language` — **not** the normalized
body. Re-chunk without re-scrape is therefore unsafe (cannot reconstruct authoritative text
from chunks alone). Operators also need a repeatable rebuild path (re-embed / re-chunk /
rescrape) with dry-run, force-bypass of hash-skip (#163), and version tracking before
embedding-model or chunk-size changes land.

## Decision

### 1. Postgres document store (normalized body)

- Persist **normalized scrape text** on the corpus DB (DO Postgres) as the authoritative
  body for rebuilds.
- Prefer: `documents.body_text` (current body) plus **`document_revisions`** history rows
  (immutable snapshots keyed by `revision_id`, `content_hash`, timestamps).
- Writes only through **internal-write API** (ADR-007). Modal never opens `DATABASE_URL`.
- Initial ingest and optional `rescrape` mode refresh the store; rebuild ops for EV-015
  staging prefer **store-backed** `reembed` / `rechunk` (no live scrape).

### 2. Rebuild job

- Single Modal/`JobStore` type: `job_type=rebuild` with `mode ∈ {reembed, rechunk, rescrape}`.
- Options: `force` (bypass content_hash skip), `dry_run` (shadow dual-write), optional
  `document_ids[]` (default = whole corpus).
- **reembed**: re-embed existing chunk text (or store→same chunks); no boundary change.
- **rechunk**: chunk from store body with current chunk settings → re-embed.
- **rescrape**: fetch URL → update store → chunk → embed (implemented; EV-015 staging
  smokes use store modes, not live scrape, unless operator explicitly chooses rescrape).
- Retag remains a **separate** `retag` job (#164 / F20) — rebuild does not retag.
- Operator UX: Admin Jobs UI enqueue + Jobs SSE / `/jobs/:id` (F32); no new % widget.

### 3. Shadow dry-run + promote

- `dry_run=true` writes preview chunks/embeddings into **shadow tables** (or rows keyed by
  `rebuild_run_id` with `status=shadow`) — no swap of live retrieval until **promote**.
- **F36 eval runs against shadow** (or shadow-backed staging config) **before** promote is
  allowed (02-verify-plan M2).
- Promote copies/activates shadow → live; operator with **`admin`** role invokes promote from
  **Admin UI** as well as the internal-write API (02 M3/M6). Staging cutover atomic enough for
  EV-015; prod cutover documented in runbook only this cycle.

### 4. Version stamps

- Stamp each rebuild / revision with at least: `embedding_model_id`, `embedding_dim`,
  `chunk_size_tokens`, `rebuild_mode`, `rebuild_run_id`, timestamps.
- Live retrieval continues on current active revision; history enables compare / rollback
  checklist (dual-write dim migration for #159 remains deferred — stamp + checklist only).

### 5. Backfill (in F41 scope)

- One-time **backfill** populates `body_text` / `document_revisions` for existing corpus
  documents (scrape once and/or reconstruct best-effort from chunks with operator ack)
  (02-verify-plan M4).

## Consequences

- Schema migration required (body + revisions + shadow/rebuild metadata).
- Ingest must write body into the store going forward; **backfill** is an F41 deliverable
  (not merely a runbook precondition).
- Enables #159/#160 without ad-hoc SQL; force flag unblocks rebuilds when #163 hash-skip ships.
- Prod live rebuild **out of scope** for EV-015 (runbook only — S017-D6).
- Admin FE includes enqueue **and** promote controls (full build this session).

## Related

- ADR-007 write boundary · ADR-008 FastEmbed 384-d · ADR-038 Modal job lifecycle
- Issues #167, #159, #160, #163, #164, #166 · F41 · F36 eval gate
- 02-verify-plan M1–M4 (2026-07-30)
- 04-tech-plan TP-S017-01–09 (2026-07-30): dedicated shadow tables; transactional promote;
  eval `rebuild_run_id`; Phase 20 M86–M90; staging requires live equivalence **and**
  shadow→F36→promote
