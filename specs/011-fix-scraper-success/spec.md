# Feature Specification: Reliable scrape outcomes for protected pages

**Feature Branch**: `013-fix-scraper-success`  
**Created**: 2026-04-24  
**Status**: Draft  
**Input**: User description: "Investigate this issue and solve why we're not able to get successful scrapes" — observed behavior: crawl jobs complete with HTTP success but zero usable extracted text; jobs end with "no successful pages" and logs describe blocked or shell-only pages (e.g., public health agency home pages with heavy client-side rendering or bot mitigation).

## Clarifications

### Session 2026-04-24

- Q: Which primary content types require first-class robustness for classification and extraction? → A: HTML plus direct-target PDF and plain text (accepted recommendation, Option B). Linked-only binaries (discovered only as links from an HTML page, not the job URL) are out of scope for this feature’s type-specific handling.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand why a crawl failed (Priority: P1)

An operator submits a single-URL crawl for a legitimate public information site. When the page does not yield usable body text, they need to know whether the failure is due to network or server errors, empty or delayed rendering, bot protection, or policy constraints—without inferring from low-level logs alone.

**Why this priority**: Without a clear failure category, operators cannot choose retries, configuration changes, or escalation; repeated opaque "no successful pages" outcomes block corpus updates and erode trust.

**Independent Test**: Submit a crawl for a URL known to return a full document in a normal browser but minimal visible text to an automated client; verify the job outcome includes a human-readable category and enough context to decide next steps.

**Acceptance Scenarios**:

1. **Given** a crawl job for a URL that responds with a normal success code but yields no substantive extractable content for its response type, **When** the job finishes, **Then** the outcome distinguishes "transport or server error" from "document fetched but no extractable public content" from "likely bot or client-environment limitation" (where applicable to HTML-family responses) using consistent labels.
2. **Given** a crawl job that completes without any page marked successful, **When** an operator reviews the job summary, **Then** they see at least one primary reason per attempted page (not only a generic aggregate error).

---

### User Story 2 - Increase successful captures for typical public-sector sites (Priority: P2)

A corpus maintainer crawls home pages of government and health-information domains that rely on scripts or anti-automation measures. The system should maximize the chance of obtaining substantive, attributable text suitable for retrieval, within ethical and policy bounds (robots, rate limits, terms of use).

**Why this priority**: Vecinita’s mission depends on public-document access; many authoritative sources match this pattern, so improving capture without breaking stewardship materially improves corpus coverage.

**Independent Test**: Run a maintained smoke set of representative public-sector URLs that includes **HTML pages**, at least one **direct PDF** URL, at least one **direct plain-text** URL, and at least one previously failing HTML pattern; measure how many produce substantive extracted text versus explicit, categorized non-success.

**Acceptance Scenarios**:

1. **Given** a smoke list of approved public URLs agreed for regression testing, **When** each URL is crawled under default production-equivalent settings, **Then** the share of URLs with substantive extracted text meets the success threshold defined in Success Criteria, or each failure is classified per User Story 1.
2. **Given** a URL that eventually exposes content after client-side work completes, **When** the crawl is configured to wait for content within documented limits, **Then** the job either captures substantive text or reports time-bounded "content not ready" rather than a misleading success with empty body.
3. **Given** a single-URL job whose target returns **PDF** or **plain text** with substantive body content, **When** the job completes, **Then** successful outcomes preserve the same traceability expectations as HTML captures, **or** failures use classifications that distinguish **corrupt or unreadable file**, **empty or non-extractive body**, and **encoding or charset problems** from HTML-centric patterns such as script-only shells (without mis-applying HTML-only labels to PDF/text-specific faults).

---

### User Story 3 - Stable job semantics for downstream systems (Priority: P3)

Integrations (queues, dashboards, data-management APIs) treat "job finished with zero successful pages" as a hard failure. Stakeholders need predictable semantics: when partial or diagnostic-only results are acceptable, that must be explicit in the product contract so callers do not mis-handle recoverable situations.

**Why this priority**: Prevents silent data gaps and wrong retries; aligns with auditability and service-boundary expectations in the constitution.

**Independent Test**: Trigger jobs that end with no successful pages under different root causes; verify downstream-visible status and messages remain consistent with documented semantics.

**Acceptance Scenarios**:

1. **Given** a job where every page is classified as blocked or non-extractive, **When** the job completes, **Then** the externally visible status and message match the documented contract for "no retrievable content" (and do not imply a transient infrastructure fault unless that is true).
2. **Given** documentation for operators and integrators, **When** they map outcomes to runbooks, **Then** each outcome category lists recommended actions (retry, widen wait, manual capture, exclude URL, policy review).

---

### Edge Cases

- URL returns success but body is entirely redirect or consent interstitial in HTML with no main content yet.
- Site serves different content by geography or language without explicit failure codes.
- Rate limiting or temporary 503 during crawl window—must not be mislabeled as permanent bot block.
- Robots or policy disallows automated fetch: outcome must reflect policy constraint, not "unknown block."
- Very large script-only shell within timeout: classified as time-bounded failure, not silent success.
- Direct **PDF** URL: password-protected, corrupted binary, or image-only pages (no extractable text) must yield PDF-appropriate failure classes, not generic HTML “shell” messaging.
- Direct **plain text** URL: wrong or undeclared charset producing mojibake must be classifiable separately from “empty body” and from HTML rendering issues.
- `Content-Type` / declared format disagrees with actual bytes (e.g., HTML error page labeled as PDF): outcome must reflect **format mismatch or unusable payload**, not a misleading success.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The crawl pipeline MUST classify each attempted URL (document response) into at least: successful substantive extractable content for the response type; transport or HTTP-level failure; successful fetch but no substantive extractable content (including HTML shell-only or script-heavy patterns, empty or non-extractive PDF, empty plain text); likely bot or client-environment limitation where distinguishable for HTML-family responses; and policy or configuration constraint where detectable.
- **FR-002**: For any job that completes with zero successful pages, the operator-visible summary MUST list each attempted URL with its primary classification and a short plain-language explanation (no requirement to expose raw HTML).
- **FR-003**: The system MUST preserve traceability for successful captures (which URL, when, under which job) consistent with trustworthy retrieval and attribution principles in the project constitution.
- **FR-004**: Crawling behavior MUST remain within documented robots, rate-limit, and licensing expectations for target corpora; improvements to capture MUST NOT depend on misrepresenting the client or bypassing lawful access controls without an approved policy path.
- **FR-005**: A maintained, versioned smoke list of public URLs (or equivalent regression fixture descriptions) MUST exist—covering at least the **composition required by SC-001**—so that releases can verify that the share of substantive successes and classification accuracy does not regress without review.
- **FR-006**: When "wait for content" (or equivalent) is enabled, the system MUST bound total wait time and surface timeout as a distinct outcome from immediate block detection.
- **FR-007**: Job identifiers and timestamps MUST remain available for audit and support, matching existing operator expectations for ingestion jobs.
- **FR-008**: For single-URL jobs whose successful HTTP response is **HTML**, **PDF**, or **plain text**, the system MUST follow a **response-type-appropriate** path to obtain substantive extractable content and type-appropriate failure classifications. Following stewardship and best-practice norms, detection MUST rely on declared **and** inferred type signals where reasonable; **linked-only** resources (not the job’s target URL) are **not** required to receive PDF/text-specific handling in this feature.

### Key Entities *(include if feature involves data)*

- **Scrape job**: A unit of work targeting one or more URLs with configuration (depth, timeouts, wait-for-content behavior) and a stable job identifier.
- **Page attempt outcome**: Per-URL result including **document/response kind** (HTML family, PDF, plain text, or other for this scope), classification, whether substantive extractable content was captured, optional excerpt-length or text-length metrics, and operator-safe explanation text.
- **Smoke / regression corpus entry**: Approved public URL or fixture description used only to validate crawl behavior across releases.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the agreed smoke list of **at least five** approved public entries—including **at least two HTML document URLs**, **at least one direct PDF URL**, **at least one direct plain-text URL**, and **at least one additional** public-sector or health-information URL of any allowed type—at least 80% yield substantive extractable content suitable for retrieval, **or** each failing entry has a non-generic classified reason recorded in the job summary (not both missing).
- **SC-002**: For jobs that previously surfaced only "no successful pages" with a single technical error string, 100% of such jobs in acceptance testing expose at least one categorized per-page explanation operators can map to a runbook action within two minutes of reading the summary alone.
- **SC-003**: Zero acceptance-test cases classify a clear HTTP transport failure (e.g., connection refused) as "bot protection" without human-review override—classification confusion rate zero on the defined negative test set.
- **SC-004**: Corpus maintainers report (via acceptance sign-off) that they can decide retry vs. manual vs. exclude for 90% of blocked jobs without developer assistance, measured on a sample of ten historical failure scenarios replayed after the change.

## Assumptions

- Target improvement focuses on legitimate public information sites commonly used in the corpus, not arbitrary paywalled or authenticated experiences.
- "Substantive extractable content" means enough natural-language text for a human to confirm the document topic: for **HTML**, visible body text (order of hundreds of characters, excluding boilerplate-only pages); for **PDF**, extractable text of comparable substance; for **plain text**, a comparable non-empty body—each validated by the smoke list rubric.
- **Out of scope for v1 (type handling):** resources encountered only as hyperlinks from an HTML page; crawling **XML feeds, Office formats, or video/audio** as primary targets unless a later feature explicitly extends the allowed response-type set.
- Existing job and persistence boundaries remain; this feature improves classification, waits, and capture strategies inside the current crawl product rather than replacing the entire crawling approach in one step.
- Legal and policy review applies before any technique that could be construed as evading explicit site bans or CAPTCHA walls.
