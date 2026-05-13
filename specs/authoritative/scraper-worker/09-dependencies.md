# Dependencies: Scraper Worker
> Auto-generated: 2026-05-12

## Overview

The scraper worker has a large dependency surface due to its browser automation, content extraction, and ML-adjacent workloads. Dependencies are split between Modal runtime (serverless functions) and Render runtime (FastAPI facade).

Source: `modal-apps/scraper/`

## Runtime Dependencies

### Core

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| modal | ≥0.59.0 | Serverless platform SDK, queues, secrets | Yes |
| fastapi | Latest | REST API framework | Yes |
| pydantic | ≥2.0 | Request/response validation | Yes |
| psycopg2-binary | Latest | PostgreSQL driver | Yes |
| structlog | Latest | Structured logging | Yes |
| python-dotenv | Latest | Environment variable loading | No |

### Web Scraping

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| crawl4ai | ≥0.4.0 | Web crawling engine with JS rendering | Yes |
| playwright | Latest | Browser automation (Chromium) | Yes |
| docling | ≥0.4.0 | PDF content extraction | Yes |
| pypdf | Latest | PDF parsing fallback | No |

### Text Processing

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| langchain | ≥0.1.0 | Text splitting, document processing | Yes |
| tiktoken | Latest | Token counting (`cl100k_base` encoding) | Yes |

### Embeddings

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| fastembed | Latest | Local embedding generation (fallback) | No |

### HTTP / Networking

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| httpx | Latest | HTTP client for embedding upstream | Yes |
| uvicorn | Latest | ASGI server for FastAPI | Yes |

## Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | Latest | Test runner |
| pytest-asyncio | Latest | Async test support |
| pytest-cov | Latest | Coverage reporting |
| pytest-mock | Latest | Mock fixtures |
| black | Latest | Code formatter |
| ruff | Latest | Linter |
| mypy | Latest | Static type checker |
| isort | Latest | Import sorting |
| schemathesis | Latest | API schema testing |
| pact-python | Latest | Contract testing |
| hypothesis | Latest | Property-based testing |

## Infrastructure Dependencies

| Resource | Provider | Required | Purpose |
|----------|----------|----------|---------|
| PostgreSQL | Render Managed | Yes | Job state, documents, chunks, embeddings |
| Modal Platform | Modal | Yes | Serverless compute, queues, secrets |
| Chromium | Playwright (bundled) | Yes | Browser for JS-rendered pages |
| Render Web Service | Render | Yes (REST) | DM API facade hosting |

## Service Dependencies

| Service | Type | Required | Fallback |
|---------|------|----------|----------|
| Gateway | Inbound caller | Soft | DM API can function independently via REST |
| Embedding service (`vecinita-embedding`) | Outbound | Soft | `fastembed` local fallback |
| Supabase | Outbound | Conditional | Only if `SUPABASE_*` vars configured |
| Render PostgreSQL | Outbound | Hard | No fallback; service fails without DB |
| Modal platform | Runtime | Hard | No fallback; all functions require Modal |

## Monorepo Dependencies

| Package/Module | Path | Purpose |
|---------------|------|---------|
| Git submodule | `modal-apps/scraper` → `vecinita-scraper.git` | Source code |
| Shared types (future) | `packages/shared-types/` | Common Pydantic models (planned) |

## System Dependencies

| Dependency | Required By | Notes |
|-----------|------------|-------|
| Python ≥3.11 | All | Language runtime |
| Chromium | Playwright | Bundled in Modal image |
| libpq | psycopg2-binary | Statically linked in binary wheel |
| CA certificates | HTTPS crawling | System package |

## Dependency Risk Assessment

| Risk | Package | Impact | Mitigation |
|------|---------|--------|-----------|
| Breaking API change | modal | Service outage | Pin to `≥0.59.0`, test before upgrading |
| Chromium version drift | playwright | Rendering differences | Pin Playwright version in image |
| Crawl4AI API instability | crawl4ai | Scraping failures | Wrap in adapter layer |
| tiktoken encoding changes | tiktoken | Chunk size drift | Pin encoding name (`cl100k_base`) |
| psycopg2 vs psycopg3 | psycopg2-binary | Migration effort | Document psycopg3 migration path |
