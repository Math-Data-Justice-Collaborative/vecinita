# Technical Decisions: Scraper Worker
> Auto-generated: 2026-05-12

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Web crawling engine | Crawl4AI | Scrapy, Beautiful Soup + requests, Selenium | 2025 | Moderate |
| TD-002 | Browser automation | Playwright | Selenium, Puppeteer | 2025 | Easy |
| TD-003 | PDF extraction | Docling | PyPDF2, pdfminer, Tika | 2025 | Easy |
| TD-004 | Pipeline architecture | 5-stage Modal queues | Single monolithic function, Celery, Redis streams | 2025 | Hard |
| TD-005 | Chunking strategy | Token-bounded with overlap | Fixed character splits, semantic chunking, recursive LangChain | 2025 | Easy |
| TD-006 | Token counting | tiktoken (cl100k_base) | spaCy tokenizer, word-count approximation | 2025 | Easy |
| TD-007 | Serverless platform | Modal | AWS Lambda, Cloud Functions, self-hosted workers | 2025 | Hard |
| TD-008 | Database driver | psycopg2-binary | asyncpg, SQLAlchemy ORM, Prisma | 2025 | Moderate |
| TD-009 | REST API framework | FastAPI | Flask, Django REST, Starlette | 2025 | Moderate |
| TD-010 | Deployment model | Dual (Modal + Render) | Modal-only, Render-only | 2025 | Moderate |

---

### TD-001: Crawl4AI as Web Crawling Engine

**Context:** The scraper needs to crawl JavaScript-rendered websites common in civic/government contexts, including SPAs, client-rendered content, and dynamically-loaded pages.

**Decision:** Use Crawl4AI with Playwright backend for web content extraction.

**Rationale:**
- Built-in Playwright integration handles JS rendering out of the box
- Recursive crawling with configurable depth
- Built-in content extraction and cleaning
- Active maintenance and Python-native API
- Supports robots.txt compliance

**Consequences:**
- Heavy dependency (pulls in Playwright + Chromium)
- 10-20s cold start due to browser initialization
- Memory-intensive per container (~500MB for Chromium)

**Alternatives considered:**
- **Scrapy:** Faster but poor JS rendering support; would need Splash or Playwright middleware
- **Beautiful Soup + requests:** No JS rendering; unsuitable for modern government sites
- **Selenium:** Heavier, slower, less Pythonic API than Playwright

### TD-002: Playwright for Browser Automation

**Context:** JavaScript rendering is required for many target civic websites.

**Decision:** Use Playwright (Chromium) as the browser engine.

**Rationale:**
- Modern, well-maintained, Microsoft-backed
- Excellent async Python API
- Lighter than Selenium
- Built-in screenshot and PDF capabilities
- Works well in containerized environments

**Consequences:**
- ~200MB Chromium binary in Modal image
- Cold start penalty (browser launch)

**Alternatives considered:**
- **Selenium:** Legacy, heavier, slower
- **Puppeteer:** Node.js-native; Python wrappers exist but less stable

### TD-003: Docling for PDF Extraction

**Context:** Civic documents often include PDFs (meeting minutes, reports, ordinances).

**Decision:** Use Docling for PDF content extraction.

**Rationale:**
- High-quality text extraction with layout understanding
- Handles complex PDF structures (tables, columns)
- Active development with good Python API

**Consequences:**
- Additional dependency weight
- Some PDFs may still fail (scanned images without OCR)

**Alternatives considered:**
- **PyPDF2:** Basic text extraction; poor handling of complex layouts
- **pdfminer:** Better than PyPDF2 but slower and less maintained
- **Tika:** Java dependency; overhead in containerized Python environment

### TD-004: 5-Stage Queue-Based Pipeline

**Context:** Web scraping involves multiple processing stages with different resource requirements and failure modes. A monolithic approach would couple fast operations (status checks) with slow operations (crawling, embedding).

**Decision:** Implement a 5-stage pipeline using Modal queues: scrape → process → chunk → embed → store.

**Rationale:**
- Each stage scales independently
- Failures are isolated to individual stages
- Bounded concurrency prevents resource exhaustion
- Queue persistence provides automatic retry on container failures
- `trigger_reindex` can drain all queues without resubmitting jobs
- Clear observability per stage (queue depth, latency)

**Consequences:**
- Increased complexity (5 queue definitions, 5 drainer functions)
- Inter-stage latency adds to total job duration
- Queue ordering is not guaranteed; items may process out of order
- Debugging requires inspecting multiple queues and function logs

**Alternatives considered:**
- **Single monolithic function:** Simpler but no isolation; one failure kills entire job
- **Celery + Redis:** Proven but requires self-managed infrastructure; Modal queues are zero-ops
- **Redis Streams:** More control but requires Redis instance; against serverless philosophy

### TD-005: Token-Bounded Chunking with Overlap

**Context:** Document chunks feed into the RAG retrieval pipeline. Chunk size directly impacts retrieval quality and embedding accuracy.

**Decision:** Token-bounded chunking with configurable max (1024), min (256), and overlap ratio (0.2), preferring sentence/paragraph boundaries.

**Rationale:**
- Token-based sizing ensures consistent embedding input
- Overlap prevents information loss at chunk boundaries
- Configurable via environment variables for tuning without redeploy
- Sentence-boundary preference produces more coherent chunks

**Consequences:**
- Slightly more complex than fixed-character splitting
- Token counting adds processing overhead (tiktoken)
- Overlap increases total chunk count by ~20%

**Alternatives considered:**
- **Fixed character splits:** Simple but ignores token semantics; inconsistent embedding quality
- **Semantic chunking:** Better quality but much slower; requires LLM calls per document
- **Recursive LangChain splitting:** Good alternative but less control over token boundaries

### TD-006: tiktoken for Token Counting

**Context:** Chunk sizing needs accurate token counts to stay within embedding model limits.

**Decision:** Use OpenAI's `tiktoken` library with the `cl100k_base` encoding.

**Rationale:**
- Industry-standard tokenizer matching OpenAI/most embedding models
- Very fast (Rust-based implementation)
- Deterministic output

**Consequences:**
- Tied to `cl100k_base` encoding; may need updating if embedding model changes tokenizer

### TD-007: Modal as Serverless Platform

**Context:** The scraper workload is bursty (10-50 jobs/day) with high resource requirements per job (browser, memory). Always-on infrastructure would be wasteful.

**Decision:** Deploy all scraping functions on Modal serverless.

**Rationale:**
- Scale-to-zero between jobs
- Built-in queue infrastructure
- Simple Python decorator-based API
- GPU access available if needed (e.g., local embeddings)
- Secret management integrated
- Pay-per-use pricing suits bursty workloads

**Consequences:**
- Vendor lock-in to Modal platform
- Cold start latency (10-20s)
- Modal SDK API changes can break deployments
- Limited debugging tools compared to traditional infrastructure

### TD-008: psycopg2-binary for Database Access

**Context:** The scraper needs to write to Render-managed PostgreSQL.

**Decision:** Use `psycopg2-binary` with direct SQL queries (no ORM).

**Rationale:**
- Lightweight, no ORM overhead
- Binary wheel avoids libpq build dependency
- Well-suited for ephemeral Modal containers (no connection pooling needed)
- Direct SQL provides maximum control for batch inserts

**Consequences:**
- No query builder; SQL strings in code
- No migration tooling bundled (handled separately)
- Synchronous driver; blocks briefly during queries (acceptable for worker context)

**Alternatives considered:**
- **asyncpg:** Async but more complex; overkill for ephemeral workers
- **SQLAlchemy ORM:** Heavy abstraction layer; unnecessary for targeted queries
- **Prisma:** TypeScript-oriented; poor Python support

### TD-009: FastAPI for REST API

**Context:** The DM frontend and external callers need HTTP access to scraper functionality.

**Decision:** Use FastAPI for the REST API facade.

**Rationale:**
- Consistent with gateway and other Vecinita services
- Automatic OpenAPI schema generation
- Pydantic integration for validation
- Modal ASGI deployment support

### TD-010: Dual Deployment (Modal + Render)

**Context:** The scraper worker functions run on Modal, but the DM frontend needs a stable HTTP endpoint for REST access.

**Decision:** Deploy the FastAPI ASGI app on both Modal (for Modal-native access) and Render (as `vecinita-data-management-api-v1` for stable HTTP access).

**Rationale:**
- Render provides stable URL for frontend
- Modal deployment provides ASGI access alongside functions
- Render DM API acts as a facade over the same codebase
- Separates concerns: Modal for compute, Render for HTTP routing

**Consequences:**
- Two deployment targets to maintain
- Configuration must work in both environments
- Potential for drift between Modal and Render versions

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | Connection pooling strategy | pgbouncer, internal pool, per-request | Performance under load | Medium — acceptable at current scale | Per-request (current) |
| PTD-002 | Chunk deduplication | Content hash, URL+position, none | Storage efficiency | Low — manageable at current volume | Content hash |
| PTD-003 | psycopg2 → psycopg3 migration | Migrate, stay, conditional | Async support, maintenance | Low — psycopg2 still maintained | Document path, defer |
| PTD-004 | Embedding model versioning | Version column, separate tables, re-embed all | Data consistency | Medium — grows with corpus | Version column |

### PTD-001: Connection Pooling Strategy

**Context:** Modal containers are ephemeral with short lifetimes. Each function invocation creates a new `psycopg2` connection. At current scale (10-50 jobs/day), this is not a bottleneck, but could become one during batch reindexing or increased usage.

**Why it matters:** Under high concurrency, Render PostgreSQL may hit connection limits (typically 97 for starter plan).

**Options researched:**
- **PgBouncer:** External connection pooler; Render supports it. Pros: transparent to application. Cons: additional infrastructure, slight latency.
- **Internal pool (psycopg2.pool):** Application-level pooling. Pros: no infrastructure. Cons: ineffective in ephemeral containers (pool is per-container and short-lived).
- **Per-request (current):** One connection per function invocation. Pros: simple, stateless. Cons: connection overhead, risk of connection exhaustion.

**Recommendation:** Stay with per-request at current scale. Monitor connection count; if approaching limits, enable Render's PgBouncer add-on.

**Risk of continued deferral:** Connection exhaustion during batch operations. Mitigated by Modal's bounded concurrency.

**Decision deadline:** Before scaling beyond 100 jobs/day.

### PTD-002: Chunk Deduplication

**Context:** Re-scraping the same URL produces duplicate chunks. Currently, each scrape creates new chunk and embedding records.

**Why it matters:** Storage growth, embedding computation waste, potential retrieval quality issues (duplicate results).

**Options researched:**
- **Content hash:** SHA-256 of chunk text; skip insert if hash exists. Pros: simple, effective. Cons: slightly different formatting produces different hashes.
- **URL + position:** Deduplicate by source URL + chunk index. Pros: handles reformatting. Cons: misses cross-URL duplicates.
- **None (current):** Accept duplicates. Pros: simple. Cons: storage waste.

**Recommendation:** Content hash with upsert semantics. Low implementation effort, immediate storage savings.

**Risk of continued deferral:** Linear storage growth with re-scrapes; retrieval quality degradation from duplicates.

**Decision deadline:** Before first production reindex.

### PTD-003: psycopg2 → psycopg3 Migration

**Context:** psycopg2 is in maintenance mode. psycopg3 offers async support, better type handling, and active development.

**Why it matters:** Long-term maintenance and async support for FastAPI.

**Options researched:**
- **Migrate now:** Pros: async support, future-proof. Cons: API differences, testing effort.
- **Stay on psycopg2:** Pros: stable, no work. Cons: maintenance mode.
- **Conditional:** Use psycopg3 for FastAPI (async), psycopg2 for Modal workers (sync). Pros: best of both. Cons: two drivers to maintain.

**Recommendation:** Document migration path. Defer until a feature requires async DB access in the scraper.

**Risk of continued deferral:** Low — psycopg2 is stable and functional.

**Decision deadline:** Next major refactor or when async DB is needed.

### PTD-004: Embedding Model Versioning

**Context:** If the embedding model changes, existing embeddings become incompatible. There is no versioning column in `chunk_embeddings` to distinguish model generations.

**Why it matters:** Model upgrades require either re-embedding the entire corpus or mixing incompatible vectors (poor retrieval quality).

**Options researched:**
- **Version column:** Add `model_version` to `chunk_embeddings`. Pros: cheap, flexible. Cons: query complexity for filtering.
- **Separate tables:** New table per model version. Pros: clean separation. Cons: schema sprawl.
- **Re-embed all:** Wipe and regenerate on model change. Pros: clean state. Cons: expensive for large corpus.

**Recommendation:** Add `model_version` column now (already have `model_name`; extend to include version). Enables gradual migration.

**Risk of continued deferral:** Forced full re-embed on model change with no rollback path.

**Decision deadline:** Before first embedding model upgrade.
