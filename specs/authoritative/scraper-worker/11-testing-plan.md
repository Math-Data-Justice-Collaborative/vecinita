# Testing Plan: Scraper Worker
> Auto-generated: 2026-05-12

## Overview

The scraper worker testing strategy covers unit, integration, contract, and end-to-end layers. The primary challenge is testing browser automation and Modal serverless functions in isolation.

Source: `modal-apps/scraper/tests/`

## Testing Layers

| Layer | Tools | Scope | CI Integration |
|-------|-------|-------|----------------|
| Unit | pytest, pytest-mock | Individual functions, utilities, chunking logic | GitHub Actions |
| Integration | pytest, psycopg2, Docker | Database operations, pipeline stage transitions | GitHub Actions (with test DB) |
| Contract | pact-python, schemathesis | Gateway ↔ Scraper API contract | GitHub Actions |
| Property-based | hypothesis | Chunking edge cases, URL validation | GitHub Actions |
| E2E | pytest, Modal sandbox | Full pipeline from URL to embeddings | Manual / nightly |

## Unit Tests

### Target Modules

| Module | Key Test Scenarios | Priority |
|--------|-------------------|----------|
| `config.py` | Default values, env var parsing, validation | High |
| Chunking logic | Token boundary splits, min/max enforcement, overlap calculation | High |
| URL validation | Valid/invalid URLs, scheme handling, encoding | High |
| Content extraction | HTML cleaning, metadata extraction, title parsing | Medium |
| Pydantic models | Serialization, validation, defaults | Medium |
| Job status transitions | Valid state machine transitions | High |

### Critical Unit Test Scenarios

| ID | Scenario | Input | Expected Output |
|----|----------|-------|----------------|
| U-001 | Chunk respects max token size | 2000-token document, max=1024 | 2+ chunks, each ≤1024 tokens |
| U-002 | Chunk respects min token size | 300-token document, min=256 | 1 chunk (no tiny remainder) |
| U-003 | Chunk overlap applied | 1500-token document, overlap=0.2 | Chunks overlap by ~20% |
| U-004 | URL validation rejects invalid | `not-a-url`, `ftp://x` | `ValueError` raised |
| U-005 | Job status transition valid | `queued` → `scraping` | Transition accepted |
| U-006 | Job status transition invalid | `completed` → `scraping` | Transition rejected |
| U-007 | Config defaults applied | No env vars set | `CHUNK_MAX_SIZE_TOKENS=1024`, etc. |
| U-008 | HTML cleaning | `<script>...</script><p>text</p>` | `text` |

## Integration Tests

### Database Integration

| ID | Scenario | Setup | Assertion |
|----|----------|-------|-----------|
| I-001 | Create scraping job | Test PostgreSQL, seed user | Row exists with `status=queued` |
| I-002 | Update job pipeline stage | Existing job | `pipeline_stage` and `updated_at` changed |
| I-003 | Store crawled URL | Existing job | `crawled_urls` row linked to job |
| I-004 | Store document chunks | Existing document | `document_chunks` rows with correct ordering |
| I-005 | Store embeddings | Existing chunk | `chunk_embeddings` row with correct dimension |
| I-006 | List jobs by user | Multiple jobs, different users | Filtered and ordered correctly |
| I-007 | Cancel job | Running job | Status updated, pipeline stages skip |

### Pipeline Integration

| ID | Scenario | Setup | Assertion |
|----|----------|-------|-----------|
| I-008 | Scrape → Process handoff | Mock scraper output | Process queue receives item |
| I-009 | Process → Chunk handoff | Cleaned document | Chunk queue receives item |
| I-010 | Chunk → Embed handoff | Token-bounded chunks | Embed queue receives batch |
| I-011 | Embed → Store handoff | Embedding vectors | Store queue receives finalization |
| I-012 | Full pipeline (mock crawl) | Mock URL response | Chunks and embeddings in DB |

## Contract Tests

### Gateway ↔ Scraper Contract

Using pact-python for consumer-driven contracts.

| Contract | Consumer | Provider | Interaction |
|----------|----------|----------|-------------|
| CT-001 | Gateway | Scraper | `modal_scrape_job_submit` request/response shape |
| CT-002 | Gateway | Scraper | `modal_scrape_job_get` response shape |
| CT-003 | Gateway | Scraper | `modal_scrape_job_list` response shape |
| CT-004 | Gateway | Scraper | `modal_scrape_job_cancel` response shape |
| CT-005 | Gateway | Scraper | `trigger_reindex` response shape |

### REST API Contract

Using schemathesis for OpenAPI schema validation.

| Test | Target | Validation |
|------|--------|-----------|
| Schema coverage | All REST endpoints | Request/response match OpenAPI schema |
| Edge cases | Boundary values | Status codes match spec |
| Auth | All protected endpoints | 401 without key, 200 with key |

## Property-Based Tests

Using hypothesis.

| ID | Property | Generator | Assertion |
|----|----------|-----------|-----------|
| P-001 | Chunking preserves all content | Random text (1-10K tokens) | Concatenated chunks (minus overlap) ≈ original |
| P-002 | Chunk sizes within bounds | Random text | All chunks between min and max tokens |
| P-003 | Chunk indices are sequential | Random text | Indices are 0, 1, 2, ... N-1 |
| P-004 | URL normalization is idempotent | Random valid URLs | `normalize(normalize(url)) == normalize(url)` |

## End-to-End Tests

| ID | Scenario | Environment | Duration |
|----|----------|-------------|----------|
| E-001 | Scrape single static page | Modal sandbox + test DB | ~30s |
| E-002 | Scrape page with JS rendering | Modal sandbox + test DB | ~60s |
| E-003 | Scrape multi-page with depth=2 | Modal sandbox + test DB | ~120s |
| E-004 | Cancel running job | Modal sandbox + test DB | ~30s |
| E-005 | Reindex after failed scrape | Modal sandbox + test DB | ~60s |

E2E tests require Modal credentials and a test database. Run manually or in nightly CI.

## Test Infrastructure

| Component | Purpose | Setup |
|-----------|---------|-------|
| Test PostgreSQL | Database integration tests | Docker container or Render test DB |
| Mock HTTP server | Simulate target websites | pytest fixture with `aiohttp` |
| Modal sandbox | E2E Modal function testing | `modal.Sandbox` or `modal run --detach` |
| Fixture factories | Generate test data | pytest fixtures for jobs, URLs, chunks |

## Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Unit | ≥80% line coverage | TBD |
| Integration | All DB operations covered | TBD |
| Contract | All gateway interactions | TBD |
| E2E | Happy paths for all journeys | TBD |

## CI Pipeline

```
pytest (unit + integration)
├── unit tests (no external deps)
├── integration tests (test DB via Docker)
├── contract tests (pact verification)
└── coverage report

Nightly:
└── E2E tests (Modal sandbox)
```

### GitHub Actions Triggers

| Trigger | Tests Run |
|---------|-----------|
| Push to `main` (scraper submodule) | Unit + integration + contract |
| Pull request | Unit + integration |
| Nightly schedule | All including E2E |
| Manual dispatch | Selectable test suite |

## Test Data Management

| Concern | Strategy |
|---------|----------|
| Test URLs | Fixture HTML files served by mock HTTP server |
| Test database | Fresh schema per test run; teardown after |
| Test secrets | Fixture env vars (non-production values) |
| Test embeddings | Deterministic mock embedding service (fixed vectors) |
