# Feature Specification: Queued page ingestion pipeline

**Feature Branch**: `014-queued-page-ingestion-pipeline`  
**Spec & artifacts directory**: `specs/012-queued-page-ingestion-pipeline` (see repo root `.specify/feature.json` **feature_directory**; branch name and spec folder prefix may differ.)  
**Created**: 2026-04-24  
**Status**: Draft  
**Input**: User description: "Set up processing so each discovered page is enqueued; each page runs through the scraper; when scraping completes the content is split into chunks, enriched by a managed language service, converted to embeddings via a managed embedding service, and persisted to the database configured for the deployment. Language and embedding capabilities are reached through the same gateway used for other hosted workloads."

## Clarifications

### Session 2026-04-24

- Q: How should cross-service correctness be anchored (contract source of truth and role of consumer-driven contracts)? → A: The deployment gateway’s published HTTP contract (OpenAPI or equivalent) is canonical; consumer-driven contract tests (for example Pact) and schema-aligned checks validate declared consumers against that surface; scraping, language, and embedding workloads reached via managed backend compute are only integrated **behind** that gateway for this product—not as separate browser-facing API contracts.
- Q: How should the browser reach HTTP APIs (single vs multiple origins)? → A: **Single configured gateway base URL** for all frontend calls that depend on ingestion, chat, or related auth/session flows against the Render-hosted stack (paths differ; no direct managed-backend origin in the browser).
- Q: Which Render-side components may call managed backend compute (e.g. Modal) for scrape / language / embedding? → A: **Only the deployment gateway and worker processes co-released or explicitly coupled to that gateway** for this pipeline; other Render HTTP services do **not** call managed backend directly for these flows.
- Q: When managed backend fails or times out, what must the browser-visible HTTP contract expose? → A: **Stable error mapping**: documented HTTP status codes (including timeout/overload) and a **consistent JSON error envelope** (same core fields across ingestion- and chat-related gateway routes that depend on managed backend).
- Q: Should the published gateway contract require a correlation identifier on responses for tracing? → A: **Yes, required** — every **success and error** response on routes covered by **FR-011** includes a **documented correlation identifier** (for example a response header and/or a field in the stable error envelope); the same value is available in gateway and managed-backend structured logs for join-up.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - End-to-end page processing after discovery (Priority: P1)

When the system learns about a new page URL that is in scope for ingestion, that page is placed in a work queue. A worker picks it up, retrieves and normalizes the page content, splits it into meaningful chunks, improves chunk text for retrieval using the language service, produces embedding vectors using the embedding service, and saves chunks and vectors to the configured database so they can be retrieved later with attribution to the source page.

**Why this priority**: Without this flow, the corpus does not grow and search or chat cannot ground answers in newly ingested public documents.

**Independent Test**: Ingest a small set of known URLs in a test environment and verify that every page either finishes with stored chunks and embeddings linked to the page, or ends in a documented failure state with a reason.

**Acceptance Scenarios**:

1. **Given** a page URL that passed crawl policy checks, **When** it is submitted for ingestion, **Then** it enters a queued state and is processed without manual intervention until completion or a terminal failure.
2. **Given** a page that scraped successfully, **When** the pipeline runs, **Then** at least one chunk is persisted with metadata tying it to that page and a stable ordering or identifier within the page.
3. **Given** persisted chunks, **When** an operator or downstream feature inspects stored records, **Then** each chunk can be traced to its source URL (and page-level job or run identifier if applicable).

---

### User Story 2 - Orderly handling of overload and failures (Priority: P2)

When many pages arrive at once or an upstream step fails (scrape blocked, language service unavailable, embedding errors), the queue backs off or retries according to policy, and no silent data loss occurs: failures are visible and pages can be retried without duplicating committed outcomes incorrectly.

**Why this priority**: Production ingestion must stay reliable under load and honest about partial outages.

**Independent Test**: Simulate scrape failure and service outage; confirm queue behavior, retry limits, and that successful pages still complete while failed ones surface clear outcomes.

**Acceptance Scenarios**:

1. **Given** a transient failure in scraping or downstream enrichment, **When** retries are still allowed, **Then** the same logical page is retried without creating duplicate committed chunk sets for the same successful completion criteria.
2. **Given** a permanent failure (for example policy violation or unrecoverable content), **When** processing ends, **Then** the page is marked with a terminal failure reason and does not block the rest of the queue indefinitely.
3. **Given** a burst of N pages within a short window, **When** the system is configured with normal capacity limits, **Then** work is deferred or throttled rather than overwhelming operators with opaque crashes (bounded concurrency or equivalent behavior).

---

### User Story 3 - Operator visibility and audit (Priority: P3)

Operators can see enough about each page’s journey (queued, scraping, enriching, embedding, stored, or failed) to answer “what happened to this URL?” and to support constitution-aligned stewardship (source, time, outcome).

**Why this priority**: Supports trust, debugging, and compliance with responsible ingestion expectations.

**Independent Test**: For a sample URL, retrieve status and outcome from logs or a status surface without reading raw application internals.

**Acceptance Scenarios**:

1. **Given** a completed page, **When** an operator looks up the URL or job identifier, **Then** they can see completion time and high-level step outcomes.
2. **Given** a failed page, **When** an operator looks up the URL or job identifier, **Then** they can see which step failed and a short human-readable reason category.
3. **Given** a user or operator reports a gateway correlation identifier from the browser or client, **When** support searches standard logs, **Then** they can tie that identifier to the same request’s gateway and managed-backend trace material within the support workflow described in **SC-007**.

---

### Edge Cases

- Page returns empty or non-textual main content after scraping: system defines whether to skip chunking, mark as “no indexable content,” or fail explicitly.
- Duplicate URLs or redirects to the same canonical content: deduplication or explicit “already processed” behavior is defined so the corpus does not sprawl with duplicates.
- Very large pages: chunking respects size limits; if limits are exceeded, behavior is defined (truncate with notice, split, or fail).
- Language or embedding service rate limits or timeouts: retries and backoff; eventual terminal failure with reason if limits persist.
- Partial success (chunks written but embedding fails mid-page): system either rolls back to a consistent state for that page or marks partial state clearly for reprocessing.
- Misconfigured frontend pointing at a non-gateway host for the same features: MUST be detectable (failing contract or health checks) before production promotion, not a silent partial deployment.
- Upstream managed-backend failures: browser-visible responses use the **gateway’s documented error contract**, not raw upstream payloads that could leak internal implementation details.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept new in-scope page URLs for ingestion and represent each as a distinct unit of work with a lifecycle (for example: queued, in progress, succeeded, failed).
- **FR-002**: The system MUST process queued pages in an order that is fair under load (for example FIFO per tenant or global queue) unless a documented priority rule overrides it.
- **FR-003**: For each page, the system MUST run content acquisition and normalization (scraping) before any chunking or enrichment that depends on that content.
- **FR-004**: After successful scraping, the system MUST split page content into chunks suitable for retrieval, with rules documented for boundaries (headings, size, overlap) at the planning stage.
- **FR-005**: The system MUST call the managed language service (via the deployment gateway) to enrich or normalize chunk text for retrieval quality, without replacing the requirement to retain traceability to the original source text where the product requires it.
- **FR-006**: The system MUST call the managed embedding service (via the deployment gateway) to produce a vector representation for each chunk that will be stored for similarity search.
- **FR-007**: The system MUST persist chunks, embeddings, and required linkage metadata to the primary database configured for the environment (the “database URL” configuration), such that retrieval can associate an embedding with its chunk and chunk with its source page.
- **FR-008**: The system MUST record ingestion outcomes in a way that supports audit: at minimum source URL, processing timestamps, and success or failure with a categorized reason.
- **FR-009**: The system MUST respect existing crawl and policy constraints (robots, licensing, rate limits) before enqueueing or while scraping; pages that fail policy checks MUST NOT be enriched or embedded as if they were valid public corpus entries.
- **FR-010**: On unrecoverable errors after partial writes, the system MUST either reconcile storage to a consistent per-page view or expose an explicit reprocessing path that does not misrepresent incomplete data as complete.
- **FR-011**: The deployment gateway’s published HTTP interface description MUST be the authoritative contract for browser-originated and other supported callers for ingestion- and chat-related operations that this feature depends on; any change that alters observable request or response shapes for those callers MUST ship with an updated published contract and evidence that declared consumers (including the frontend) still conform (for example via consumer-driven contract tests that do not regress on the supported release path).
- **FR-012**: The frontend MUST use exactly **one configured base URL** (the deployment gateway) for all HTTP operations covered by **FR-011**; operators or deployers MUST NOT rely on a second public origin for the same logical capabilities unless a future specification explicitly expands scope and updates contract tests accordingly.
- **FR-013**: Invocations of managed backend compute for scraping, language, and embedding in this pipeline MUST originate only from the deployment gateway or from **worker processes documented as part of the same release train** as that gateway; other independently deployed Render services MUST NOT hold or use credentials to call managed backend for these same pipeline steps unless a future specification explicitly expands scope and updates security review and tests.
- **FR-014**: For gateway routes covered by **FR-011** that depend on managed backend compute, the gateway MUST map failures—including timeouts, overload, and upstream errors—to **documented HTTP status codes** and a **JSON error object** whose **core field names and semantics** are stable across minor releases unless accompanied by a **contract version bump** and updated consumer verification; raw upstream diagnostic text MUST NOT be required for clients and MUST NOT be the only machine-readable signal.
- **FR-015**: For every **successful and failed** HTTP response on routes covered by **FR-011**, the gateway MUST return a **correlation identifier** whose location and format are specified in the published contract (for example a dedicated response header and/or a required field in successful JSON bodies and in the **FR-014** error envelope); pipeline code MUST record the same identifier in structured gateway and managed-backend logs for requests it processes so operators can align user-visible failures with backend traces.

### Key Entities *(include if feature involves data)*

- **Page ingestion job**: One logical page URL (or canonical URL) moving through the pipeline; carries status, timestamps, and error classification.
- **Content chunk**: A segment of scraped text belonging to one page, with order or offset, optional enrichment fields, and linkage to the source page job.
- **Chunk embedding**: Vector and service version or model identifier associated with a chunk, stored for search.
- **Deployment gateway (canonical HTTP boundary)**: The Render-hosted HTTP entry point identified by the single frontend base URL; its published contract defines what the frontend and operators may rely on—including **required correlation identifiers** on covered responses—and together with **co-released pipeline workers** is the only place that invokes managed backend compute (for example Modal-hosted functions) for scrape, language, and embedding in this feature—never alternate public browser endpoints and not arbitrary other Render services unless explicitly expanded by specification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a controlled test of at least 20 distinct in-scope pages, 100% that complete successfully have every stored chunk and embedding traceable to the correct source URL in query results or exports used for verification.
- **SC-002**: For pages that fail scraping or policy checks, 0% produce stored embeddings in the retrieval index (no “ghost” vectors for blocked or failed pages).
- **SC-003**: Under a burst of twice the steady-state enqueue rate for a 15-minute window, at least 95% of pages that eventually succeed do so without manual intervention, using automated retries within configured limits.
- **SC-004**: Operators can determine the current or final state of any page job from audit or status data within one lookup flow, without needing code deployment access.
- **SC-005**: On each supported release candidate, automated checks show **no regressing drift** between the frontend’s usage of ingestion- and chat-related gateway operations and the gateway’s **then-current** published contract (consumer contract suite or equivalent), except where an explicit, documented compatibility exception is recorded.
- **SC-006**: In scripted failure drills for at least three representative gateway routes that depend on managed backend (for example timeout, overload, and validation failure), **100%** of browser-observed responses use **status codes and error JSON core fields** that match the **then-current** published contract for those routes.
- **SC-007**: Across a sample of at least **20** success and **20** error responses on routes covered by **FR-011**, **100%** include the **documented correlation identifier**, and in a drillbook exercise an operator can locate matching gateway log lines for **at least 95%** of sampled IDs within **one** standard support workflow (single lookup path, no code checkout required).

## Assumptions

- “Enqueue” means a durable or operationally acceptable work queue (not only in-memory) so restarts do not silently drop pending pages under normal operations.
- Language and embedding services, and other managed backend compute used for scraping or enrichment, are reachable from production only through the deployment gateway (Render-served); the browser never calls managed backend endpoints directly; credentials and routing details are environment concerns outside this specification’s detail.
- The configured database is the system of record for chunks and embeddings produced by this pipeline; search or chat consumers read from that store or an explicitly synchronized derivative defined in planning.
- Chunking parameters (sizes, overlap, language handling) will be chosen to support bilingual public-good content where applicable, aligned with existing product goals, with exact numbers left to planning.
- This feature focuses on the pipeline after page discovery; discovery, crawl frontier, and UI are bounded by existing features unless explicitly expanded in a later spec.
