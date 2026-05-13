# User Journeys: Gateway
> Auto-generated: 2026-05-12

See [diagrams/user-journeys.md](diagrams/user-journeys.md) for Mermaid journey maps.
See [diagrams/sequence-flows.md](diagrams/sequence-flows.md) for sequence diagrams.

## Journey 1: Ask a Question (Community Member)

**Persona:** Community Member
**Goal:** Get an answer about a civic/community topic

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 1 | User | Types question in chat UI | Frontend calls `GET /api/v1/ask/stream?question=...` |
| 2 | Gateway | Validates auth (if enabled), applies rate limit | Passes or returns 401/429 |
| 3 | Gateway | Assigns correlation ID, forwards to agent `/ask-stream` | Opens SSE connection |
| 4 | Agent | Retrieves context, runs LLM, streams events | SSE events: thinking → tool_event → complete |
| 5 | Gateway | Forwards raw SSE bytes to frontend | User sees streaming answer |
| 6 | Frontend | Renders answer with source citations | Journey complete |

**Failure modes:**
- Agent unreachable → 503 + SSE error event
- Agent timeout → 504 + SSE timeout event
- Rate limit exceeded → 429 with `Retry-After` header

## Journey 2: Submit a Scrape Job (Data Manager)

**Persona:** Data Manager
**Goal:** Ingest new community resource content

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 1 | Admin | Submits URL via data management UI | `POST /api/v1/modal-jobs/scraper` with URL + user_id |
| 2 | Gateway | Validates auth, checks dedup against completed jobs | Returns `duplicate_skipped` or creates new job |
| 3 | Gateway | Persists job row to Postgres (`scraping_jobs`) | Job ID assigned |
| 4 | Gateway | Invokes `modal_scrape_job_submit` via Modal SDK | Modal enqueues work |
| 5 | Gateway | Auto-kicks pipeline via `trigger_reindex` spawn | Drain workers activated |
| 6 | Admin | Polls `GET /api/v1/modal-jobs/scraper/{job_id}` | Returns status, pipeline_stage |
| 7 | Modal worker | Calls back `POST /internal/scraper-pipeline/jobs/{id}/status` | Gateway updates pipeline_stage |
| 8 | Modal worker | Persists chunks via `/internal/scraper-pipeline/chunks` | Chunks stored in Postgres |

**Failure modes:**
- Modal SDK not configured → 503
- DATABASE_URL missing → 503
- Modal RPC failure → 500

## Journey 3: Browse Documents (Community Member)

**Persona:** Community Member
**Goal:** Explore available knowledge base content

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 1 | User | Opens documents dashboard | `GET /api/v1/documents/overview` |
| 2 | Gateway | Queries `sources` + `document_chunks` from Postgres | Returns total_chunks, sources list |
| 3 | User | Clicks a source to preview | `GET /api/v1/documents/preview?source_url=...` |
| 4 | Gateway | Fetches first N chunks for source URL | Returns chunk excerpts |
| 5 | User | Filters by tag | `GET /api/v1/documents/tags?locale=es` |
| 6 | Gateway | Aggregates tag counts from chunk metadata | Returns bilingual tag inventory |

**Failure modes:**
- Database unavailable → 503 "Document index temporarily unavailable"
- Source not found → 404

## Journey 4: Monitor Service Health (Operator)

**Persona:** Platform Operator
**Goal:** Verify all integrations are operational

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 1 | Operator | Calls `GET /health` or `GET /integrations/status` | — |
| 2 | Gateway | Probes agent HTTP health (2s timeout) | ok / error / not_configured |
| 3 | Gateway | Probes database TCP socket (2s timeout) | ok / error / not_configured |
| 4 | Gateway | Returns aggregated status | `{ status: "ok" | "degraded", components: {...} }` |

**Failure modes:**
- Agent down → status=degraded, agent=error
- Database unreachable → status=degraded, database=error

## Journey 5: Trigger Reindex (Data Manager)

**Persona:** Data Manager
**Goal:** Re-embed or reprocess all documents

| Step | Actor | Action | System Response |
|------|-------|--------|-----------------|
| 1 | Admin | Triggers reindex from UI or API | `POST /api/v1/modal-jobs/reindex/spawn` |
| 2 | Gateway | Validates Modal invocation is enabled | — |
| 3 | Gateway | Calls `spawn_modal_scraper_reindex` (non-blocking) | Returns `FunctionCall` ID |
| 4 | Gateway | Registers in Modal job registry | Returns `gateway_job_id` |
| 5 | Admin | Polls registry | `GET /api/v1/modal-jobs/registry/{gateway_job_id}?refresh=true` |
| 6 | Gateway | Optionally resolves `FunctionCall.get(timeout=0.05)` | Updates status to completed/failed |
