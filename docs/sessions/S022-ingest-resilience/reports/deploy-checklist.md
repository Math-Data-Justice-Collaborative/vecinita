# Deploy Checklist — S022 / EV-019 Ingest Resilience (F47–F49)

> **Generated**: 2026-08-02  
> **Status**: **approved** — Phase 2/3 signed; Path A + Path B rechunk scheduled at 13  
> **Mode**: DELTA — Modal data-management ingest + embedding-client + ingest chunker + OpenAPI  
> **Branch tip**: `evolve/EV-019-ingest-resilience` @ `abe4608`  
> **Staging now**: `main` @ `9d1f10b` (EV-018) — lag until 13 merge/deploy  
> **Deployment plan**: `docs/deployment-integration.md` + S022-D10 Path A / RD-227 Path B  
> **11-verify-impl**: [verify-impl.md](./verify-impl.md) — **approved** F47–F49  
> **F41 runbook**: [S017 runbook-corpus-rebuild-outline.md](../../S017-corpus-reembed-migration/reports/runbook-corpus-rebuild-outline.md)

## Phase 1 — Pre-Deploy Checks (summary)

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Configuration | **PASS** | Defaults: overlap **32**, embed batch **32**, retries **3**, backoff **0.5s** |
| 2 | Secrets | **PASS** | Operator specs untracked; Modal no DATABASE_URL; OpenAPI OK |
| 3 | Data / volumes | **PASS** | D6/D7 verified; Path B rechunk scheduled at 13 (needs store `body_text`) |
| 4 | Resources | **PASS** | Same Modal DM + embed profile; rechunk may be long-running |
| 5 | Browser connectivity | **N/A-delta** | No FE knobs; H0c PASS; H4–H5 at 13 |
| 6 | Modal / DO secret parity | **PASS** | Existing embed/LLM URL keys; validate at 13 |
| 7 | Unrelated CE flag | **PASS / hold** | Keep `VECINITA_RAG_RERANK_CE=false` |

### Env defaults (ship expectation)

| Env | Default | Ship expectation |
|-----|---------|------------------|
| `VECINITA_CHUNK_OVERLAP_TOKENS` | `32` | On for **new** ingest + Path B rechunk |
| `VECINITA_CHUNK_TOKENIZER_ID` | `BAAI/bge-small-en-v1.5` | Unchanged pin (ADR-044) |
| `VECINITA_EMBED_BATCH_SIZE` | `32` | Keep |
| `VECINITA_EMBED_MAX_RETRIES` | `3` | Keep |
| `VECINITA_EMBED_RETRY_BACKOFF_S` | `0.5` | Keep |
| `VECINITA_RAG_RERANK_CE` | `false` | **OFF** |

### Redeploy order (staging Path A → then Path B)

1. Merge PR → `main` (or pin evolve tip for smoke then merge)  
2. Redeploy **Modal `vecinita-data-management`** (new chunker + hash skip + OpenAPI)  
3. Redeploy **internal-write-api** if tip includes content-hash / promote paths not yet live  
4. Smokes: `do_verify` → H1 → H4–H5  
5. **Path B:** store-backed **`mode=rechunk`** (see §Path B procedure) → shadow → F36 → promote  

## Path B procedure — rechunk + re-embed (F49)

**Goal:** Rebuild **live** chunks with HF tokenizer + `chunk_overlap_tokens=32`, then re-embed.
This is **not** a normal URL re-ingest; use F41 `job_type=rebuild` / `mode=rechunk` (store-backed).

### Preconditions (at 13)

1. Path A code deployed (Modal DM tip includes F49 chunker).  
2. Document store has `body_text` for target docs. If many docs lack store body (S021 saw ~9/49), run **backfill** first (`job_type=rebuild`, `backfill=true`) or use `mode=rescrape` for those URLs only.  
3. Prefer **shadow** path before live promote (UJ-054).

### Recommended sequence

| Step | What | How |
|------|------|-----|
| 1 | Shadow rechunk whole corpus (or scoped `document_ids`) | Admin **Corpus → Rebuild** *or* `POST /jobs` below with `dry_run=true`, `mode=rechunk`, `force=true` |
| 2 | Wait for job `completed`; note `rebuild_run_id` | Jobs UI / `GET /jobs/{id}` |
| 3 | F36 eval against shadow | Eval tab with `rebuild_run_id` set |
| 4 | Promote if gate OK | Admin promote *or* `POST /internal/v1/rebuild/{rebuild_run_id}/promote` |
| 5 | Spot-check retrieve / ask | Non-empty pools; sample ChatRAG |

### API shape (Modal data-management)

```bash
# After Path A deploy — set URLs/keys from prod.env / workflow-state staging URLs
DM_URL="${VECINITA_STAGING_DM_URL:-https://vecinita--vecinita-data-management-fastapi-app.modal.run}"
# Proxy key: Modal DM edge auth (VITE_VECINITA_MODAL_PROXY_KEY / ops secret)

# 1) Shadow rechunk (store-backed — no live scrape)
curl -sS -X POST "$DM_URL/jobs" \
  -H "Content-Type: application/json" \
  -H "Modal-Key: $VECINITA_MODAL_PROXY_KEY" \
  -d '{
    "urls": [],
    "options": {
      "job_type": "rebuild",
      "mode": "rechunk",
      "force": true,
      "dry_run": true,
      "chunk_overlap_tokens": 32
    }
  }'

# Poll until completed; read rebuild_run_id from job detail

# 2) Promote (internal-write-api, admin auth)
WRITE_URL="https://vecinita-internal-write-api-icze4.ondigitalocean.app"
curl -sS -X POST "$WRITE_URL/internal/v1/rebuild/${REBUILD_RUN_ID}/promote" \
  -H "Authorization: Bearer $ADMIN_JWT"
```

**UI alternative:** Admin → Rebuild corpus → mode **rechunk** → force on → dry-run on → submit → F36 → Promote.

### What *not* to run for Path B

| Avoid | Why |
|-------|-----|
| Plain re-ingest of same URLs with `force=false` | F47 **skips** embed when hash matches — no new chunks |
| `mode=reembed` only | Keeps **old** chunk boundaries; F49 needs **`rechunk`** |
| pytest / seed against staging `DATABASE_URL` | Corpus wipe risk — use corpus-db-safety guards |
| `mode=rescrape` as default | Live scrape; only if store body missing |

### Scoped vs full

- **Scoped:** `"document_ids": ["<uuid>", …]` for a pilot (2–5 docs) before full corpus.  
- **Full:** omit `document_ids` (whole corpus) after shadow+F36 looks good.

## Failure mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Tip not on staging | Merge/deploy tip; CI + T0 | **approved** |
| 2 | Hash skip when normalize drifts | `force=true`; metrics | **approved** |
| 3 | Embed retries / exhaust → URL fail | Intentional AC-IR4; Modal embed health | **approved** |
| 4 | Live corpus ≠ HF+overlap | Path B rechunk scheduled at 13 | **approved** (C2) |
| 5 | Wrong Modal URL | `modal_url_validate` + `do_verify` at 13 | **approved** |
| 6 | Auth/CORS | H0c; H4–H5 at 13 | **approved** |
| 7 | Corpus wipe via pytest | Corpus DB guard | **approved** |
| 8 | Store body missing → rechunk fail | Backfill or scoped rescrape before full rechunk | **approved** |

## Rollback

| Item | Plan |
|------|------|
| Code | Redeploy prior Modal DM / write-API image |
| Before Path B promote | Abandon shadow `rebuild_run_id`; live unchanged |
| After Path B promote | Re-promote prior `rebuild_run_id` if retained; else DO backup |
| Knobs / CE | Keep `VECINITA_RAG_RERANK_CE=false` |

**User approved rollback** — 2026-08-02 (B1).

## Pre-Deploy checklist

- [x] Configuration complete (Path A defaults)  
- [x] Secrets / Modal / OpenAPI / operator-spec guards PASS  
- [x] H0c CORS unit tests PASS  
- [x] Connectivity scripts present  
- [x] Frontend `VITE_*` matrix — **N/A-delta**  
- [x] Post-deploy H4–H5 command documented  
- [x] Failure modes approved (Phase 2) — A1  
- [x] Rollback plan approved (Phase 3) — B1  
- [x] Path A + Path B rechunk at 13 — C2  

## Sign-Off

- [x] User approved implementation (11-verify-impl) — 2026-08-02  
- [x] User approved failure mitigations (12 Phase 2) — A1, 2026-08-02  
- [x] User approved rollback plan (12 Phase 3) — B1, 2026-08-02  
- [x] Path B rechunk scheduled for 13 — C2, 2026-08-02  
- [x] Ready for 13-deploy-smoke  

## Summary

```
Pre-deploy checks: PASS
Phase 2+3: APPROVED (A1 B1)
Ship: Path A code + Path B rechunk at 13 (C2)
Next: 13-deploy-smoke — merge/redeploy Modal DM → smokes → shadow rechunk → F36 → promote
```
