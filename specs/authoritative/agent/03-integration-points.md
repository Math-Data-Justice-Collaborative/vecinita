# Vecinita Agent — Integration Points

> Auto-generated: 2026-05-12

## Overview

The agent operates as an internal backend service. It receives requests from the gateway via HTTP, queries PostgreSQL for vector search, calls an embedding service for query embedding, and reaches an Ollama-compatible LLM endpoint (Modal vLLM or local Ollama) for generation. Optionally it calls external web search APIs.

## Internal Integrations

| Target | Protocol | Direction | Purpose | Config |
|--------|----------|-----------|---------|--------|
| vecinita-gateway | HTTP REST | inbound | Receives proxied `/ask` and `/ask-stream` queries from users | `AGENT_SERVICE_URL` on gateway (fromService binding) |
| vecinita-postgres | PostgreSQL (psycopg2) | outbound | Vector similarity search on `document_chunks` table | `DATABASE_URL` env var |
| Embedding service | HTTP REST | outbound | Generate query embeddings (384-dim, all-MiniLM-L6-v2) | `EMBEDDING_SERVICE_URL` env var |
| Modal model service | HTTP/SDK | outbound | LLM inference via Ollama-compatible `/chat` endpoint or Modal SDK | `OLLAMA_BASE_URL`, `MODAL_FUNCTION_INVOCATION`, `MODAL_TOKEN_*` |

## External Integrations

| Provider | Protocol | Purpose | Auth | Config |
|----------|----------|---------|------|--------|
| Tavily | REST API | Web search for supplemental information | API key | `TAVILY_API_KEY` / `TVLY_API_KEY` |
| DuckDuckGo | HTTP (ddgs) | Fallback web search when Tavily unavailable | None | Automatic fallback |
| Guardrails AI Hub | SDK | PII detection, toxicity filtering validators | API key | `GUARDRAILS_API_KEY` |
| LangSmith | SDK | LLM observability and tracing | API key | `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` |

## Integration Details

### Gateway → Agent (inbound)

- **Endpoint:** `GET /ask`, `GET /ask-stream`, `GET /health`, `GET /config`
- **Request format:** Query parameters (`question`, `thread_id`, `lang`, `provider`, `model`, `tags`, etc.)
- **Response format:** JSON body (`AgentAskJsonResponse`) or SSE stream (`text/event-stream`)
- **Error handling:** 400 for missing question, 422 for invalid parameters, 500 with detail for unhandled errors; rate-limit errors return localized retry message
- **Retry/timeout policy:** Gateway controls timeout; agent has no outbound retry to gateway

### Agent → PostgreSQL (outbound)

- **Endpoint:** Direct psycopg2 connection via `DATABASE_URL`
- **Request format:** Parameterized SQL with `document_chunks` table and `search_similar_documents()` RPC function
- **Response format:** Row tuples mapped to dicts via cursor description
- **Error handling:** Catches connection and query errors, returns empty results on failure, logs warnings
- **Retry/timeout policy:** `connect_timeout=5` seconds (configurable via `DB_SEARCH_POSTGRES_CONNECT_TIMEOUT_SECONDS`); no automatic retry on query failure

### Agent → Embedding Service (outbound)

- **Endpoint:** `EMBEDDING_SERVICE_URL` (HTTP REST)
- **Request format:** Text string for embedding
- **Response format:** 384-dimensional float vector
- **Error handling:** Falls back to HuggingFace local embeddings if available; errors propagate to caller
- **Retry/timeout policy:** Embedding cache (LRU, 256 entries by default) reduces redundant calls

### Agent → LLM Provider (outbound)

- **Endpoint:** `OLLAMA_BASE_URL` — either `*.modal.run` (Modal native) or localhost Ollama
- **Request format:** OpenAI-compatible chat messages (`model`, `messages`, `temperature`)
- **Response format:** OpenAI-compatible JSON (`choices[0].message.content`) or Ollama format (`message.content`)
- **Error handling:** Rate-limit detection returns localized retry message; connection errors logged and raised as 500
- **Retry/timeout policy:** `timeout=60s` for HTTP calls; Modal SDK has its own retry policy

### Agent → Web Search (outbound)

- **Endpoint:** Tavily API or DuckDuckGo (fallback)
- **Request format:** Query string
- **Response format:** JSON list of `{title, content, url}` results
- **Error handling:** Returns empty `[]` on any failure; Tavily failure triggers DuckDuckGo fallback
- **Retry/timeout policy:** No explicit retry; relies on provider defaults

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
