# Feature Specification: Make-invoked CLI web corpus crawler

**Feature Branch**: `010-make-cli-web-crawler`  
**Created**: 2026-04-22  
**Status**: Draft  
**Input**: User description: "Setup a CLI scraper script that I can fire with a make command to see the database at DATABASE_URL from .env. It should include these lists and be a crawler to crawl through and scrape all these websites and links on them. Some of them may require javascript heavy interactions."

## Clarifications

### Session 2026-04-22

- Q: Default crawl scope for discovered links → A: Same registrable domain as each seed-led crawl branch; off-domain links are not followed unless explicitly allowlisted in configuration (accepted recommendation, Option A).
- Q: What must be persisted for each successful page by default → A: Always persist primary extracted text plus metadata; persist raw page snapshot when policy and configured size limits allow, with operator configuration to disable raw retention (accepted recommendation, Option B).
- Q: When should script-capable (browser-like) retrieval run → A: Static fetch first; use script-capable retrieval only when per-seed or per-rule configuration requires it or documented heuristics indicate insufficient primary body content from static fetch (accepted recommendation, Option A).
- Q: In-scope PDF and similar binary document links → A: Fetch file, retain binary artifact (subject to size and raw-retention rules), best-effort text extraction with explicit success or failure of extraction recorded (accepted recommendation, Option A).
- Q: Same URL fetched again on a later run → A: Append-only fetch history—each attempt is a new immutable record tied to its crawl run and canonical URL; “latest successful per canonical URL” (or equivalent) is a documented query or view convention, not silent overwrite (accepted recommendation, Option A).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a crawl from the project root (Priority: P1)

An operator working on the Vecinita repo wants to start a crawl of a fixed seed list of community and reference sites using a single documented command (for example via the project’s `Makefile`), without hand-editing connection strings each time. The tool reads the database connection from the same environment configuration the rest of the project uses so stored crawl results are visible in that database.

**Why this priority**: Without a repeatable, one-command run tied to `DATABASE_URL`, operators cannot reliably populate or inspect the corpus backing RAG work.

**Independent Test**: From a machine with valid `.env` and network access, run the documented make target; confirm the process starts, respects configuration, and persists crawl run and fetch records in the database so they can be queried.

**Acceptance Scenarios**:

1. **Given** a valid `.env` with `DATABASE_URL` and required credentials, **When** the operator runs the documented make target, **Then** the crawler starts using that connection without prompting for a duplicate connection string.
2. **Given** the seed list is present in configuration, **When** the crawl runs, **Then** each seed entry is visited at least once and outcomes (success, partial, or failure) are recorded in a way that can be inspected later.

---

### User Story 2 - Discover and capture linked pages within policy (Priority: P2)

The operator needs the crawler to follow links discovered on seed pages (and optionally deeper), so that related program pages, PDFs, and subdomains are collected—not only the homepage—while staying within agreed scope and politeness rules.

**Why this priority**: Single-page snapshots miss most actionable community content; bounded crawling delivers a more useful corpus.

**Independent Test**: Run against a small test seed; verify discovered same-site links are enqueued and processed up to configured depth or domain rules, with deduplication by canonical URL.

**Acceptance Scenarios**:

1. **Given** a seed page containing internal links, **When** the crawler processes it, **Then** eligible links are scheduled according to scope rules and previously seen URLs are not re-fetched unnecessarily.
2. **Given** a link points to a different registrable domain than the seed that started the current branch (the default scope), **When** the crawler evaluates it, **Then** it is skipped or logged with an explicit reason unless an operator allowlist explicitly permits that target domain.
3. **Given** an in-scope link resolves to a PDF or similar document type, **When** the crawler fetches it, **Then** the binary artifact is stored when retention rules allow, best-effort extracted text is stored or absent with an explicit extraction-outcome field, and the fetch remains correlated to the crawl run.

---

### User Story 3 - Handle pages that need rich client behavior (Priority: P3)

Some seed sites load meaningful content only after scripts run or user-like interaction. The operator still expects those pages to be retrievable to the same degree as static HTML where licensing and robots rules allow.

**Why this priority**: Several listed sites are application-like; static fetch alone would under-deliver on corpus completeness.

**Independent Test**: Run against at least one known script-dependent seed; verify final stored content reflects post-render text or structured extracts where the feature claims support, or records a clear “render not supported / blocked” outcome.

**Acceptance Scenarios**:

1. **Given** a seed URL that requires client-side rendering for primary content, **When** static fetch yields insufficient body content or per-seed configuration forces script-capable retrieval, **Then** the crawler escalates to script-capable retrieval and the stored artifact or extracted text matches what a human sees in a normal browser session for public pages, within acceptable delay bounds.
2. **Given** a site blocks automated browsers or requires disallowed interaction, **When** the crawler runs, **Then** the failure is recorded with enough context for an operator to adjust seeds or scope without guessing.

---

### User Story 4 - Inspect what landed in the database (Priority: P2)

After a run, the operator wants to confirm counts, recent fetches, errors, and sample rows through the same database pointed to by `DATABASE_URL` (using existing or documented query paths), so ingestion is auditable.

**Why this priority**: Constitution and operations require traceability of what was ingested, when, and from where.

**Independent Test**: After a short crawl, query or use the documented “inspect” path; verify job or run identifiers, timestamps, source URLs, and status fields are present.

**Acceptance Scenarios**:

1. **Given** a completed crawl run, **When** the operator inspects the database, **Then** they can list runs and drill into pages or documents associated with a run.
2. **Given** a failed fetch, **When** they inspect records, **Then** HTTP or retrieval error information is stored or logged in a correlatable way.
3. **Given** the same canonical URL was successfully fetched on two different runs, **When** the operator inspects history, **Then** two distinct persisted records exist (each tied to its run) and documented guidance explains how to obtain the latest successful snapshot per URL if needed.

---

### Edge Cases

- `DATABASE_URL` missing, invalid, or database unreachable at start: the tool fails fast with a clear message and does not claim success.
- Robots disallow or rate limiting: crawler backs off or stops per policy; operator sees partial completion and reason codes.
- Very large pages, infinite link generators, or redirect loops: depth limits, max pages per host, and redirect caps prevent runaway work; operator can tune limits.
- Raw snapshot exceeds configured size or storage policy: primary extracted text is still stored when available; raw omission is explicit in the record (e.g., partial or text-only outcome).
- Authentication-gated or paywalled content: out of scope unless explicitly configured with approved credentials; otherwise skipped with explicit status.
- Duplicate URLs with different fragments or tracking query parameters: deduplication strategy avoids redundant **work** within a run while preserving canonical source attribution; **cross-run** revisits of the same canonical URL create **new** fetch records (append-only), not silent replacement of prior run data.
- Seeds with probable hostname typos: operators correct the configured list; assumptions document likely corrections for known ambiguous entries.
- Partner or third-party links on a seed page (different registrable domain): by default not followed; operators must add allowlist entries if a specific cross-domain target is intentionally in scope.
- Heuristic escalation misclassifies a page (e.g., triggers or skips script-capable retrieval incorrectly): operators can override via per-seed retrieval rules; outcomes remain auditable.
- PDF or binary exceeds size or retention caps: fetch may be rejected or truncated per policy with explicit status; partial storage rules mirror HTML raw-snapshot handling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST expose a documented operator workflow to start the crawler from the repository root using the project’s standard automation entry point (the same class of command the team uses for `make` targets), without requiring ad-hoc copy-paste of `DATABASE_URL` when it is already defined for the environment.
- **FR-002**: On startup, the crawler MUST obtain the database connection solely from the project’s environment configuration (including the variable named `DATABASE_URL` as referenced from `.env` in local workflows), or fail with an explicit error if it cannot.
- **FR-003**: The crawler MUST ship with a default or checked-in **seed list** that includes at least the following hostnames or URL prefixes as starting points (exact spelling as provided by stakeholders; operators MAY fix obvious typos in configuration before runs): chartercare.org; errollri.org; rifreeclinic.org; github.com; health-careservices.com; health.ri.gov; healthsourceri.com; lifespan.erg; lincolnugentcareri.com; medassociatesofri.com; nhchc.org; nuestrasalud.com; open.spotify.com; pressreader.com; rihca.org; math-data-justice-collaborative.github.io; rimedicine.com; dhs.ri.gov; providencechc.org; providencejournal.com; rihispanicchamber.org; riosinstitute.org; rmisticeurgentcare.com; va.gov; vecina.wrwc.org; womenandinfants.org.
- **FR-004**: The crawler MUST visit each configured seed and MUST follow hyperlinks discovered on fetched pages according to configurable **scope** and **politeness** (rate limits, concurrency caps). **Default scope** (unless operator configuration overrides): only enqueue URLs whose registrable domain matches that of the seed URL that started the crawl branch for that workstream; links to any other registrable domain MUST be skipped or logged with an explicit skip reason unless the target domain is permitted via explicit **allowlist** configuration.
- **FR-005**: The crawler MUST persist retrievable outcomes for each URL attempt—including success, redirect chain terminus, HTTP errors, retrieval timeouts, and policy skips—with **source URL**, **timestamp**, and correlation to a **run or job identifier** suitable for audit.
- **FR-012**: Persisted fetch outcomes for a given canonical URL MUST be **append-only across runs**: a new crawl run MUST NOT silently overwrite or delete prior run’s stored fetch rows. Operators MUST have **documented** means (queries, views, or tooling) to derive a **“latest successful fetch per canonical URL”** (or similar) view when a single current snapshot is needed for downstream use.
- **FR-010**: For **successful** fetches of HTML or equivalent web documents, the crawler MUST persist **primary extracted text** suitable for downstream search/RAG use, along with HTTP or transport metadata and content fingerprinting (e.g., hash or length) as needed for audit. The crawler MUST also persist a **raw page snapshot** (HTML or rendered equivalent) when site policy and configured **size or retention limits** allow; operators MUST be able to **disable raw snapshot retention** via configuration while retaining extracted text and metadata.
- **FR-006**: The crawler MUST support retrieval for both mostly static HTML and **script-heavy** public pages. **Default behavior**: attempt **static** retrieval first. **Script-capable (browser-like) retrieval** MUST be used when **per-seed or per-rule configuration** requires it, or when **documented heuristics** determine the static response lacks meaningful primary body content; otherwise the static outcome MUST be accepted without mandatory browser rendering. Escalation decisions and retrieval path used MUST be representable in persisted records for audit.
- **FR-007**: The crawler MUST respect published machine-readable crawl policies (e.g., robots rules) and applicable terms for public pages unless the operator explicitly documents an exception path for internal testing with mock servers.
- **FR-008**: Operators MUST be able to cap resource usage per run (for example maximum pages, maximum depth, maximum wall time) so that a single invocation cannot exhaust local or shared infrastructure without configuration.
- **FR-009**: The feature MUST document how to **inspect** stored crawl data using the configured database (counts, recent errors, sample rows, or equivalent), reusing existing project conventions where they already exist for database inspection.
- **FR-011**: For **in-scope** URLs whose successful response is a **PDF or similar binary document** intended for the corpus, the crawler MUST fetch the resource, MUST persist the **binary artifact** when policy and configured **size or retention limits** allow (with the same operator option to disable heavy binary retention as for HTML raw snapshots where technically equivalent), and MUST run **best-effort text extraction** for RAG use. Text extraction success or failure MUST be explicit in persisted fields (not indistinguishable from an empty page).

### Key Entities *(include if feature involves data)*

- **Crawl run**: A single operator-triggered execution with start/end time, configuration snapshot identifier, aggregate counts (pages fetched, skipped, failed), and status.
- **Fetched document / page record**: **Immutable** logical unit per fetch attempt, tied to a canonical URL and **one** crawl run, holding **primary extracted text** for successful fetches (including PDF-derived text when extraction succeeds), optional **raw or binary snapshot** when retention rules allow (or explicit omission reason), HTTP metadata, content hash or length, retrieval path used, **document format** (e.g., HTML vs PDF), text-extraction outcome for binaries, and outcome classification (full, text-only partial, failure). Later runs add new rows; they do not replace earlier ones.
- **URL queue item**: Work item for a URL with state (pending, in progress, completed, skipped, failed) and reason codes for skips and failures.
- **Seed configuration**: Ordered list of seed URLs or domains, optional per-seed overrides (scope, max depth, **retrieval path preference** such as static-only, script-capable when needed, or always script-capable), and optional **cross-domain allowlist** entries that extend follow scope beyond the default same-registrable-domain rule.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new operator can follow written instructions and complete the first successful crawl run (including verifying rows in the database) in under 30 minutes assuming valid `.env`, network access, and no blocking by target sites.
- **SC-002**: For a standard acceptance seed subset defined in test documentation (at least five hosts spanning static and script-heavy behavior), at least 90% of reachable public pages within the **default same-registrable-domain scope** and configured depth or page caps are either stored with extractable text or recorded with a specific non-success reason on a single run under default caps.
- **SC-003**: For every stored page, an auditor can answer “which run, which URL, when, and how retrieved” from persisted fields alone in at least 95% of sampled records across a mixed success/failure run.
- **SC-004**: With default politeness settings, the crawler does not exceed configured per-host request rates during steady-state operation (verified in test or staging logs).

## Assumptions

- Operators are trusted project members using public pages for community-good corpus building; authentication to third-party accounts (e.g., streaming or paid news) is out of scope unless separately specified.
- Hostnames in the stakeholder list may contain typographical errors; operators correct seeds in configuration; `lifespan.erg` is assumed to mean the organization’s public site at `lifespan.org` unless the team confirms otherwise.
- “See the database” means inspect via existing project tooling, SQL clients, or a small documented query recipe—not a requirement for a new graphical product in this specification.
- The database schema for crawl storage may extend existing tables or add new ones during planning, but must remain consistent with traceability and audit expectations in the constitution.
- JavaScript-heavy support is required for public content that does not violate site policy; it is not a mandate to bypass CAPTCHAs, logins, or paywalls.
- Heuristic rules for “insufficient static body content” are defined at planning time and documented for operators; they err toward fewer unnecessary browser sessions while preserving a path to force script-capable retrieval per seed.
- Long-term **storage growth** from append-only history may be managed in planning (optional archival or TTL policies); the specification requires **auditability**, not unbounded retention forever without operator choice.

## Dependencies

- Valid `DATABASE_URL` (and any companion secrets) in operator environment aligned with project norms.
- Network egress to listed seeds from the environment where the tool runs.
- Legal and policy review for high-volume crawling of third-party domains remains the responsibility of operators; the feature provides technical guardrails only.
