# Vecinita Agent — Dependencies

> Auto-generated: 2026-05-12

## Overview

The agent service depends on the shared gateway Python package tree (it copies `apis/gateway/src/` as its base module layer), LangChain/LangGraph for RAG orchestration, and psycopg2 for direct PostgreSQL access. Heavy ML dependencies (PyTorch, sentence-transformers) are avoided at runtime — embeddings are delegated to an external service.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| Gateway shared modules | `apis/gateway/src/` | Config, services (LLM, embedding, Modal invoker), utilities |
| LLM Client Manager | `apis/gateway/src/services/llm/client_manager.py` | LLM provider routing, model selection, client construction |
| Modal invoker | `apis/gateway/src/services/modal/invoker.py` | Modal SDK function invocation for LLM chat |
| Embedding client | `apis/gateway/src/embedding_service/client.py` | HTTP client for embedding service |
| Tag utilities | `apis/gateway/src/utils/tags.py` | Tag parsing, normalization, auto-inference |
| Config module | `apis/gateway/src/config.py` | Centralized env var resolution, feature flags |
| Service endpoints | `apis/gateway/src/service_endpoints.py` | Endpoint logging utility |
| OpenAPI examples (shared) | `apis/gateway/src/gateway_openapi_ask_examples.py` | Shared OpenAPI example values |

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| fastapi | latest | HTTP framework | yes |
| uvicorn | latest | ASGI server | yes |
| langchain | latest | Core LLM abstractions | yes |
| langchain-core | latest | Base message types, tool decorators | yes |
| langchain-community | latest | DuckDuckGo search tool | no |
| langchain-ollama | latest | ChatOllama LLM client | yes (local dev) |
| langchain-openai | latest | OpenAI-compatible LLM client | no |
| langchain-groq | latest | Groq provider (legacy) | no |
| langchain-tavily | latest | Tavily web search | no |
| langchain-huggingface | latest | HuggingFace embeddings fallback | no |
| langgraph | latest | StateGraph, ToolNode, MemorySaver | yes |
| psycopg2-binary | latest | PostgreSQL driver for vector search | yes |
| pydantic | latest | Data validation and API schemas | yes |
| python-dotenv | latest | Environment variable loading | yes |
| httpx | latest | HTTP client for Modal/LLM endpoints | yes |
| langdetect | latest | Language detection (en/es) | yes |
| guardrails-ai | latest | Safety validation SDK | no (graceful fallback) |
| modal | >= 1.3.5 | Modal SDK for function invocation | yes (Render) |
| beautifulsoup4 | latest | HTML parsing in utilities | no |
| ddgs | latest | DuckDuckGo search fallback | no |
| tqdm | latest | Progress bars for vector loader | no |
| requests | latest | HTTP utilities | no |
| langsmith | latest | LLM tracing/observability | no |

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| PostgreSQL + pgvector | Render (vecinita-postgres) | Vector storage and similarity search |
| Embedding service | Modal (vecinita-embedding) | Query embedding generation |
| LLM inference | Modal (vecinita-model) / local Ollama | Chat completion for answer generation |

## Service Dependencies (runtime calls)

| Service | Required | Fallback |
|---------|----------|----------|
| vecinita-postgres | yes | None — empty retrieval results if unreachable |
| Embedding service | yes | HuggingFace local embeddings (`langchain-huggingface`) if available; otherwise fails |
| LLM endpoint (Modal/Ollama) | yes | Rate-limit errors return localized retry message; connection errors return 500 |
| Tavily web search | no | DuckDuckGo fallback; returns `[]` if both fail |
| Guardrails AI Hub | no | Local regex-based guardrails (injection, PII, toxicity) |
| LangSmith | no | Tracing disabled if API key not set |

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
