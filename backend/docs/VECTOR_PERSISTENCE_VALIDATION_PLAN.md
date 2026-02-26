# Vector Persistence Implementation & Validation Plan

## Scope

This project uses:
- **Primary vector store:** Chroma
- **Fallback/cloud sync:** Supabase `document_chunks`

This plan validates that vector data is **not ephemeral** unless volumes are intentionally deleted.

## Implementation Summary (This Iteration)

1. **Persistence hardening**
   - Chroma containers now run with explicit persistence settings:
     - `IS_PERSISTENT=TRUE`
     - `PERSIST_DIRECTORY=/data`
   - Applied in:
     - `docker-compose.yml`
     - `docker-compose.dev.yml`
     - `deploy/gcp/docker-compose.prod.yml`

2. **Dual-write sync (degraded mode)**
   - Scraper uploader writes to Chroma first, then syncs to Supabase (`document_chunks`).
   - If Supabase write fails:
     - request still succeeds (degraded mode),
     - retries are attempted,
     - failed rows are queued for replay.

3. **Read fallback behavior**
   - Runtime retrieval remains Chroma-primary.
   - If Chroma query fails, agent db search falls back to Supabase RPC (`search_similar_documents`).

4. **Operational safety**
   - Destructive scripts now warn before data-destroying operations (`--volumes`, `--clean`).

## Validation Matrix

### A) Unit Validation (fast)

Run:

```bash
cd backend
uv run pytest tests/test_services/scraper/test_uploader_chroma_metadata.py tests/test_db_search_tool.py -q
```

Expected:
- all tests pass,
- includes coverage for:
  - dual-write retry behavior,
  - degraded mode queueing,
  - Supabase read fallback when Chroma fails.

### B) Integration Validation (stack lifecycle)

Use the dev stack first:

```bash
docker compose -f docker-compose.dev.yml up -d --build
backend/scripts/run_scraper.sh --docker --no-confirm
curl -s http://localhost:18004/api/v1/documents/overview
```

Capture total chunk count as `COUNT_1`.

#### Restart persistence check

```bash
docker compose -f docker-compose.dev.yml restart chroma vecinita-agent-dev vecinita-gateway-dev
curl -s http://localhost:18004/api/v1/documents/overview
```

Expected: count remains `COUNT_1`.

#### Down/up (without volume deletion) check

```bash
docker compose -f docker-compose.dev.yml down --remove-orphans
docker compose -f docker-compose.dev.yml up -d
curl -s http://localhost:18004/api/v1/documents/overview
```

Expected: count remains `COUNT_1`.

#### Destructive reset check (control)

```bash
docker compose -f docker-compose.dev.yml down --remove-orphans --volumes
docker compose -f docker-compose.dev.yml up -d
curl -s http://localhost:18004/api/v1/documents/overview
```

Expected: count resets (intentional data wipe).

### C) Fallback Usage Validation

1. Ingest data (same as above).
2. Stop Chroma only:

```bash
docker compose -f docker-compose.dev.yml stop chroma
```

3. Call ask endpoint:

```bash
curl -G 'http://localhost:18004/api/v1/ask' --data-urlencode 'question=housing assistance'
```

Expected:
- request still returns relevant answer using Supabase fallback path,
- no service crash,
- logs show Chroma failure + Supabase fallback attempt.

4. Restart Chroma and verify primary path resumes.

## Success Criteria

All criteria must be true:

1. **Durability:** data survives container restart and compose down/up without `--volumes`.
2. **Predictable reset:** data is removed only when explicit destructive commands are used.
3. **Sync resilience:** Supabase sync failure does not break ingestion; retries/queue preserve eventual sync intent.
4. **Fallback correctness:** retrieval continues via Supabase if Chroma is unavailable.
5. **Regression safety:** targeted unit tests pass in CI/local.

## Iteration Loop (Required)

Repeat until all success criteria pass:

1. Execute validation matrix (A/B/C).
2. Record failures with exact command, logs, and failing criterion.
3. Patch smallest root-cause fix.
4. Re-run A (unit), then failed B/C checks, then full B/C.
5. Exit only when all criteria are green in the same run.

## Notes

- Chroma remains source-of-truth for normal runtime reads/writes.
- Supabase remains synchronized cloud fallback.
- `--clean` and `--volumes` are intentionally destructive and should be used only for controlled resets.
