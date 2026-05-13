# Vecinita Agent — Architecture

> Auto-generated: 2026-05-12

## Overview

The agent is a Python FastAPI application structured as a layered service: HTTP routing → intent classification → tool execution → LLM generation → response assembly. It uses LangChain/LangGraph abstractions for tool orchestration and LLM interaction, psycopg2 for direct PostgreSQL access, and a deterministic RAG pipeline (not an autonomous agent loop).

## Architecture Style

**Layered monolith with deterministic RAG pipeline.** Despite using LangGraph constructs (StateGraph, ToolNode, MemorySaver), the current production path is a hand-orchestrated deterministic flow — intent classification selects a code path, tools are invoked explicitly, and the LLM is called once with a fully constructed prompt. The LangGraph agent loop exists in the codebase but the deterministic path is the active production behavior.

## Component Map

| Component | Responsibility | Source Path |
|-----------|---------------|-------------|
| FastAPI app | HTTP server, CORS, lifespan, OpenAPI docs | `apis/agent/src/agent/main.py` |
| Ask router | `/ask` and `/ask-stream` endpoints | `apis/agent/src/agent/routers/ask.py` |
| System router | `/`, `/health`, `/privacy` endpoints | `apis/agent/src/agent/routers/system.py` |
| Config router | `/config`, `/model-selection` endpoints | `apis/agent/src/agent/routers/config.py` |
| Diagnostics router | `/test-db-search`, `/db-info` endpoints | `apis/agent/src/agent/routers/diagnostics.py` |
| db_search tool | Vector similarity search against PostgreSQL/pgvector | `apis/agent/src/agent/tools/db_search.py` |
| web_search tool | External web search (Tavily/DuckDuckGo) | `apis/agent/src/agent/tools/web_search.py` |
| static_response tool | FAQ matching against in-memory database | `apis/agent/src/agent/tools/static_response.py` |
| rewrite_question tool | LLM-based question rewriting for better retrieval | `apis/agent/src/agent/tools/rewrite_question.py` |
| rank_retrieval tool | Lexical reranking of retrieval results | `apis/agent/src/agent/tools/rank_retrieval.py` |
| clarify_question tool | Generates clarification prompts for ambiguous queries | `apis/agent/src/agent/tools/clarify_question.py` |
| Guardrails config | Input/output safety validation (injection, PII, toxicity, topic) | `apis/agent/src/agent/guardrails_config.py` |
| LocalLLMClientManager | LLM provider routing, model selection, client construction | `apis/gateway/src/services/llm/client_manager.py` |
| Agent rules | System prompt loaded from markdown file | `apis/agent/src/agent/data/agent_rules.py` |
| HTTP API schemas | Pydantic models for request/response validation | `apis/agent/src/agent/http_api_schemas.py` |
| OpenAPI examples | Schemathesis-compatible example values | `apis/agent/src/agent/openapi_examples.py` |
| Vector loader | Batch data loading utility for document chunks | `apis/agent/src/agent/utils/vector_loader.py` |
| HTML cleaner | Sanitizes HTML from scraped content | `apis/agent/src/agent/utils/html_cleaner.py` |

## Runtime Characteristics

| Property | Value |
|----------|-------|
| Language / runtime | Python 3.11 |
| Framework | FastAPI 0.100+ with uvicorn ASGI server |
| Entry point | `apis/agent/src/agent/main.py` → `app` |
| ASGI command | `uvicorn src.agent.main:app --host 0.0.0.0 --port ${PORT:-8000}` |
| Port | 10000 (Render), 8000 (local dev) |
| Health check | `GET /health` |
| OpenAPI | `GET /openapi.json`, Swagger UI at `/docs`, ReDoc at `/redoc` |

## Concurrency Model

- **ASGI async:** FastAPI runs on uvicorn's asyncio event loop.
- **Thread offloading:** CPU-bound and blocking operations (`db_search`, LLM calls, embedding) are dispatched via `asyncio.to_thread()` to avoid blocking the event loop.
- **Thread safety:** Embedding cache uses a `threading.Lock`; search metrics use `ContextVar` for request-scoped isolation plus a global `threading.Lock` fallback.
- **No worker pool:** Single-process uvicorn (no `--workers` flag in CMD); Render may run multiple instances at the service level.

## Diagrams

- [Architecture Diagram](diagrams/architecture.md)

## Related Documents

- [Behavior](01-behavior.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
