# Vecinita Agent — High-Level Behavior

> Auto-generated: 2026-05-12

## Purpose

The Vecinita Agent is the RAG (Retrieval-Augmented Generation) "brain" of the Vecinita civic information system. It receives natural-language questions about community resources, retrieves relevant document chunks from a pgvector-backed knowledge base, augments the query with retrieved context, and generates accurate bilingual (English/Spanish) answers using an LLM routed through an Ollama-compatible endpoint (primarily vLLM on Modal). The agent enforces safety guardrails, supports streaming responses, and provides latency telemetry for every request.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Intent classification | Determines whether a query is answer-seeking, conversational, or a contextual follow-up (`_is_answer_seeking_query`, `_is_contextual_follow_up`) |
| Static FAQ matching | Short-circuits retrieval for known frequently asked questions via `static_response_tool` |
| Vector retrieval | Embeds the query and performs cosine-similarity search against `document_chunks` via pgvector (`db_search` tool) |
| Tag-based filtering | Filters retrieval results by metadata tags with `any`/`all` match modes and untagged fallback |
| Reranking | Optional lexical reranking of retrieved chunks to improve top-K ordering |
| RAG answer generation | Builds a deterministic prompt with retrieved context and generates an answer via the LLM |
| Streaming SSE delivery | Streams thinking steps, tool events, and the final answer as Server-Sent Events |
| Bilingual support | Auto-detects language (en/es) via `langdetect` and responds in the detected language |
| Guardrails enforcement | Blocks prompt injection, SQL injection, and off-topic queries; redacts PII; filters toxic output |
| LLM provider management | Routes all inference through a single `LocalLLMClientManager` to Ollama-compatible endpoints |
| Model selection | Exposes `/model-selection` and `/config` endpoints for runtime model discovery and switching |
| Health checks | Provides `/health` for Render container probes and optional preflight diagnostics |
| Contextual follow-ups | Handles short follow-up questions using prior assistant answer as context without re-retrieval |

## Key Behaviors

### Deterministic RAG Query (Answer-Seeking)

- **Trigger:** `GET /ask` or `GET /ask-stream` with a question classified as answer-seeking
- **Process:** Embed query → pgvector cosine search (`db_search`) → optional rerank → build RAG prompt with retrieved docs → LLM generation → output guardrails → sanitize links → return with sources
- **Outcome:** JSON response with `answer`, `sources`, `thread_id`, `response_time_ms`, `latency_breakdown`

### Non-Answer Intent (Greeting / Conversational)

- **Trigger:** Query classified as non-answer-seeking (e.g., "hello", "thanks")
- **Process:** Check static FAQ database → if no match, send directly to LLM without retrieval
- **Outcome:** Brief conversational reply without sources

### Contextual Follow-Up

- **Trigger:** `context_answer` parameter is provided and question is a short follow-up
- **Process:** Skip retrieval → build follow-up prompt using prior answer as context → LLM generation
- **Outcome:** Quick contextual reply without re-querying the knowledge base

### Streaming Response

- **Trigger:** `GET /ask-stream` endpoint
- **Process:** Emit SSE events: `thinking` (precheck, analysis) → `tool_event` (db_search start/result) → `thinking` (finalizing) → `complete` (answer + sources + suggested_questions)
- **Outcome:** Real-time progress feedback with final answer and follow-up suggestions

### Input Guardrails

- **Trigger:** Every incoming question before processing
- **Process:** Check prompt injection patterns → SQL injection patterns → Hub SDK PII redaction → local PII regex fallback → topic relevance check
- **Outcome:** Pass-through, redacted text, or rejection with localized explanation

### Output Guardrails

- **Trigger:** Every LLM-generated answer before delivery
- **Process:** Hub SDK toxicity check → local toxic word blocklist → hallucination heuristic (source claims without URLs)
- **Outcome:** Pass-through, redacted output, or safe fallback message

## Boundaries

| Not owned by Agent | Owned by |
|--------------------|----------|
| HTTP routing, authentication, CORS policy for external clients | Gateway |
| Job orchestration and scraping pipeline | Gateway + Modal scraper |
| Document CRUD, source management, reindexing | Data Management API |
| Embedding model hosting and batch embedding | Modal embedding service |
| LLM model hosting (vLLM/Ollama) | Modal model service |
| Chat frontend rendering | Chat Frontend (React) |

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [Architecture Diagram](diagrams/architecture.md)
