# Research: 011-fix-scraper-success

## 1. Response-type routing (HTML vs PDF vs plain text)

**Decision**: Before invoking **Crawl4AI**, perform a lightweight **`httpx` HEAD** (fallback **GET** with size cap if HEAD unsupported) to read **`Content-Type`**, **`Content-Length`** (when present), and optionally first bytes for **magic-number** validation (`%PDF-`, UTF-8 BOM, etc.). **Route**:

| Signal | Path |
|--------|------|
| `text/html` (or missing type but HTML-like after GET sniff) | **Crawl4AI** `AsyncWebCrawler` (current behavior, improved classification) |
| `application/pdf` or PDF magic | **`httpx` GET** full body (within byte cap) → **PDF text extractor** (see §2) → synthesize `CrawledPage`-like result |
| `text/plain` or `text/*` readable as text | **`httpx` GET** with **`charset-normalizer`** / `response.encoding` fallback → plain `CrawledPage` |

**Rationale**: Crawl4AI/browser is the wrong tool for **binary PDF** and often **worse** for **simple text** endpoints; misrouting causes false anti-bot classifications. HEAD+GET is standard, testable, and respects stewardship when combined with size limits and robots (existing job context).

**Alternatives considered**:

- **Crawl4AI only** for all types — rejected; reproduces current PDF/text failures and inflates browser work.
- **Always full GET before browser** — rejected for large HTML; use HEAD + bounded GET sniff only when type uncertain.

## 2. PDF text extraction

**Decision**: Use **`pypdf`** (pure Python, permissive license) to extract text from downloaded bytes; if extraction yields empty text, classify **empty or non-extractive PDF** (image-only / scanned) per spec edge cases. **Password-protected** PDFs: catch library error → **PDF-specific** category.

**Rationale**: Docling is already a dependency for **processing**, but crawl stage needs **fast, synchronous** text check for “substantive content” without temp-file **DocumentConverter** round-trip for every PDF; **`pypdf`** keeps Modal image smaller than adding **PyMuPDF** unless profiling demands it later.

**Alternatives considered**:

- **Docling-only in crawl** — heavier cold start and file-path plumbing in Modal.
- **PyMuPDF (`fitz`)** — faster; defer unless `pypdf` fails on representative gov PDFs in smoke tests.

## 3. HTML “success” vs substantive content

**Decision**: Treat **Crawl4AI `success`** as necessary but **not sufficient**: after crawl, compute **extractable text metrics** (stripped markdown length, visible text heuristic, or reuse Crawl4AI error_message when present). If HTTP OK but metrics below rubric threshold, set **`success=False`** with a **spec-aligned category** (e.g. `non_extractable_html` / `likely_bot_or_shell`) distinct from transport errors—**do not** overwrite raw Crawl4AI diagnostics; **append** normalized `failure_category` for persistence.

**Rationale**: Aligns worker behavior with FR-001 and stops enqueueing **empty** “successful” rows that fail downstream Docling silently.

**Alternatives considered**:

- **Trust Crawl4AI success only** — rejected; current production pain.
- **Second browser pass** — policy-heavy; defer to future spike unless smoke list still fails.

## 4. Persisting response kind and failure category

**Decision**: **Preferred**: extend gateway **`POST /crawled-urls`** body with optional **`response_kind`**, **`failure_category`** (string enums), backward-compatible defaults. **Fallback MVP**: single JSON object string in `error_message` when `status=failed`, and mirror summary in job-level `error_message` for multi-page jobs—**documented in contract** until DM migrates.

**Rationale**: FR-002/SC-002 require operator-visible categories; gateway owns persistence schema.

**Alternatives considered**:

- **New table** for crawl diagnostics — overkill for v1.

## 5. Smoke list location and CI

**Decision**: Add **`services/scraper/smoke/crawl_smoke_urls.yaml`** (or `.json`) with **stable ordering**, **tags** (`html`, `pdf`, `text`, `regression-shell`), and **optional** `live: false` fixture URLs pointing to **local static server** for CI. **Live** marker runs against real public URLs on scheduled/manual job only.

**Rationale**: Satisfies FR-005 / SC-001 composition without hardcoding secrets; matches pytest marker patterns already in `pyproject.toml`.

## 6. `determine_content_type` after routing

**Decision**: Derive processor **`content_type`** from **resolved `response_kind`** (`html`, `pdf`, `text/plain` → `markdown` or `pdf` per existing `DoclingProcessor` expectations), not from URL suffix alone.

**Rationale**: Fixes `.pdf` URLs that return HTML error pages (**Content-Type mismatch** edge case).
