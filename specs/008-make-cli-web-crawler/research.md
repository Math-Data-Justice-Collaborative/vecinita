# Research: Active crawl CLI (008)

## 1. Where to implement “more active crawling”

**Decision**: Extend **`backend/src/services/scraper/`** with a new **`active_crawl`** package and a **`python -m`** entrypoint; orchestrate discovered URLs through existing **`SmartLoader.load_url`**.  
**Rationale**: `VecinaScraper` already wires `ScraperConfig`, Playwright vs recursive vs standard loaders, rate limiting, and DB upload patterns. Modal **`services/scraper`** (Crawl4AI) stays isolated for cloud jobs—user asked to keep that scraper as-is while deepening **local/repo** crawl behavior.  
**Alternatives considered**: (a) Only increase `RecursiveUrlLoader` depth in config—rejected: insufficient control for append-only audit tables and cross-page politeness caps; (b) New standalone repo script—rejected: duplicates loader logic and `.env` handling.

## 2. BeautifulSoup vs Playwright responsibilities

**Decision**: **Discovery + static signals**: use **httpx** (or minimal HTTP client) + **`BeautifulSoup`** to fetch HTML for **link extraction** and optional **cheap “body text length” heuristic** before calling `SmartLoader`. **Full page retrieval** for indexing remains **`SmartLoader`** so **Playwright** continues to flow through **`PlaywrightURLLoader`** (already in `loaders.py`) when URL matches `playwright_sites.txt` or fallback rules fire.  
**Rationale**: Matches user request (“BeautifulSoup for simpler scraping, Playwright for JS heavy”) while reusing tested loader paths and `needs_playwright` / config lists.  
**Alternatives considered**: Raw Playwright API everywhere—rejected: duplicates LangChain integration and browser lifecycle already paid for.

### 2b. Discovery fetch vs `SmartLoader` (possible double fetch)

**Decision**: **Accept** that the same URL may be fetched **twice** in one crawl step—once with **httpx** for link discovery / thin-body signal, and again via **`SmartLoader.load_url()`** for canonical extraction and persistence—unless the implementation later adds a **safe reuse** path (e.g. pass discovery HTML into a static branch when content-type is HTML and hashes match). **Politeness caps** (`RATE_LIMIT_DELAY`, per-host limits) should assume **up to two HTTP-style touches** per URL when tuning defaults.  
**Rationale**: Keeps discovery logic simple and avoids diverging from `SmartLoader`’s normalization, redirects, and Playwright escalation.  
**Alternatives considered**: Single fetch only—rejected: would duplicate link extraction and loader policy inside discovery.

## 3. Escalation heuristic (static → Playwright)

**Decision**: After static discovery fetch, if stripped visible text length **&lt; configurable threshold** (default **400** characters) **and** URL is not already forced static-only, enqueue the same URL for processing via **`SmartLoader`** with **`force_loader="playwright"`** once (guarded against infinite loops per run). Per-seed overrides in YAML/JSON crawl config can set **`retrieval: always_playwright` | `static_first` | `static_only`**.  
**Rationale**: Aligns with clarified spec (static first; escalate on thin content or config).  
**Alternatives considered**: Always run Playwright for entire domain list—rejected: cost and CI fragility.

## 4. Persistence model vs existing `document_chunks`

**Decision**: Add **new tables** **`crawl_runs`** and **`crawl_fetch_attempts`** (names may be prefixed e.g. `vecina_` per migration conventions) with **append-only inserts** for every URL attempt; store `retrieval_path`, `http_status`, `error`, `extracted_text`, `raw_bytes` or `raw_html` nullable, `content_sha256`, `pdf_extraction_status` enum/text. **Do not** overload `document_chunks` as the crawl audit log (current uploader uses `ON CONFLICT` upsert semantics). Optional **Phase 2** task: feed successful extracted text into existing **`DocumentProcessor`** / uploader for RAG.  
**Rationale**: Satisfies FR-010, FR-011, FR-012 without breaking vector upsert behavior.  
**Alternatives considered**: Single wide JSON blob in one table—rejected: harder to query and index for operators.

## 5. Seed list source

**Decision**: Ship **`data/config/active_crawl_seeds.txt`** (or reuse merge of `recursive_sites.txt` + explicit FR-003 hostnames) loaded at startup; **`SCRAPER_CONFIG_DIR`** override respected. Typos in spec list corrected only in file comments + `quickstart.md`, not silent DNS fixes at runtime.  
**Rationale**: Matches FR-003 and existing config layout (`ScraperConfig.CONFIG_DIR`).

## 6. PDF and other binary documents

**Decision**: For **`Content-Type: application/pdf`**, download bytes under size cap; run **`pypdf`** for text extraction; persist **`pdf_extraction_status`** (`ok` | `failed` | `skipped_size`). For **other** in-scope binaries (e.g. `application/msword`, `application/octet-stream` without PDF magic), **v1** treats them as **`document_format=other`**, sets **`pdf_extraction_status=na`**, stores the **artifact when retention allows** or skips with explicit status, and does **not** require text extraction in the crawler (operators can add converters later).  
**Rationale**: FR-011 names “PDF or similar”; scope is bounded to **PDF text extraction** in MVP to limit dependency and QA surface.  
**Alternatives considered**: Universal `unstructured` extraction for all MIME types—deferred to a follow-up task.

## 7. Makefile / `.env`

**Decision**: Add **`scripts/run_active_crawl.sh`** mirroring `run_scraper_postgres_batch.sh` patterns (`set -a; [ -f .env ] && . ./.env`) and **`make active-crawl`** (or `crawl-active`) delegating to it.  
**Rationale**: FR-001/FR-002 operator ergonomics.

## 8. Testing / CI

**Decision**: Unit tests with **mocked httpx** and **fake DB**; optional integration test behind **`RUN_ACTIVE_CRAWL_INTEGRATION=1`**. Document **`uv sync --extra scraping`** + `playwright install` for local full runs; default CI job may skip Playwright-heavy tests unless extra is enabled.  
**Rationale**: Matches existing `pyproject.toml` optional `scraping` group pattern.
