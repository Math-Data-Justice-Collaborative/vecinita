# Data Flow: Gateway
> Auto-generated: 2026-05-12

See [diagrams/data-flow.md](diagrams/data-flow.md) for Mermaid flow diagrams.

## Data Entry Points

| Source | Protocol | Format | Trigger | Endpoint |
|--------|----------|--------|---------|----------|
| Chat frontend | HTTP GET + SSE | Query params | User asks question | `/api/v1/ask`, `/api/v1/ask/stream` |
| Data management frontend | HTTP POST | JSON body | Admin submits scrape | `/api/v1/modal-jobs/scraper`, `/api/v1/scrape` |
| Data management frontend | HTTP POST | JSON body | Admin triggers embed | `/api/v1/embed`, `/api/v1/embed/batch` |
| Modal scraper workers | HTTP POST | JSON body | Pipeline stage callback | `/api/v1/internal/scraper-pipeline/*` |
| Frontends | HTTP GET | Query params | Browse documents | `/api/v1/documents/*` |

## Internal Processing

### Q&A Flow

```
Frontend → Gateway → Agent Service → Gateway → Frontend
```

1. Gateway validates auth, applies rate limit, assigns correlation ID
2. Forwards query params to agent `/ask` or `/ask-stream`
3. For streaming: raw SSE bytes forwarded without parsing
4. For non-streaming: agent JSON response mapped to `AskResponse`

No data transformation — gateway is a transparent proxy for Q&A.

### Embedding Flow

```
Frontend → Gateway → [Modal SDK | HTTP Proxy] → Gateway → Frontend
```

1. Gateway checks `modal_function_invocation_enabled()`
2. **Modal path:** calls `invoke_modal_embedding_single/batch` via `asyncio.to_thread`
3. **HTTP path:** posts to `EMBEDDING_SERVICE_URL/embed` with compatibility fallback payloads
4. Response normalized to `EmbedResponse`

### Scrape Job Flow

```
Frontend → Gateway → Postgres (persist) → Modal SDK (submit) → Modal (spawn)
Modal Workers → Gateway /internal/scraper-pipeline/* → Postgres (persist)
```

1. Gateway validates request, checks dedup against completed jobs
2. Creates `scraping_jobs` row in Postgres (when persist-via-gateway enabled)
3. Invokes `modal_scrape_job_submit` via Modal SDK
4. Auto-kicks `trigger_reindex` via `.spawn()` to activate drain workers
5. Modal workers callback with pipeline stage updates, crawled URLs, chunks, embeddings

### Documents Read Flow

```
Frontend → Gateway → Postgres (read) → Gateway → Frontend
```

1. `psycopg2.connect()` per request with 5s connect timeout
2. SQL queries against `public.sources` and `public.document_chunks`
3. Results normalized via `_normalize_public_source()`: merge sources + chunk metadata
4. Test artifacts filtered out unless `include_test_data=true`
5. Tag filtering with bilingual label generation

## Data Persistence

| Store | Technology | Tables | Access Pattern |
|-------|-----------|--------|----------------|
| Postgres (Render) | PostgreSQL via psycopg2 | `scraping_jobs`, `crawled_urls`, `extracted_content`, `processed_documents` | Write: job persistence, pipeline ingest |
| Postgres (Render) | PostgreSQL via psycopg2 | `sources`, `document_chunks` | Read: documents overview/preview/tags |
| Modal Dict | `modal.Dict` | `vecinita-gateway-modal-jobs` | Write: job registry for spawned Modal calls |
| In-memory | Python dict | Rate limit state, thread registry | Per-process, lost on restart |

## Data Exit Points

| Destination | Protocol | Format | Purpose |
|-------------|----------|--------|---------|
| Chat frontend | HTTP JSON + SSE | JSON, text/event-stream | Q&A answers, streaming events |
| Data management frontend | HTTP JSON | JSON | Job status, documents, embeddings |
| Agent service | HTTP GET | Query params | Forwarded Q&A queries |
| Modal functions | Modal SDK | Python dict/args | Scrape/embed/reindex invocations |
| Postgres | SQL | INSERT/UPDATE | Job state persistence |
