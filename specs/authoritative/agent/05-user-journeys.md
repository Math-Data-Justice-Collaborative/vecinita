# Vecinita Agent — User Journeys

> Auto-generated: 2026-05-12

## Overview

These journeys describe how different actors interact with the agent service end-to-end. Since the agent is an internal service, all user-facing journeys pass through the gateway.

## Journeys

### Community Question (Answer-Seeking)

**Persona:** Community Member (via Gateway)
**Goal:** Get an accurate answer about a local community resource

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | User types question in Chat Frontend | Frontend sends to Gateway | e.g., "Where can I find a food pantry near Olneyville?" |
| 2 | Gateway proxies to `GET /ask?question=...` | Agent receives request | Gateway adds `lang`, `tags` if configured |
| 3 | Agent runs input guardrails | Pass / reject | Checks injection, PII, topic relevance |
| 4 | Agent classifies intent | `answer_seeking=true` | `_is_answer_seeking_query()` |
| 5 | Agent embeds query | 384-dim vector via embedding service | LRU cache checked first |
| 6 | Agent searches `document_chunks` | Cosine similarity via pgvector | Tag filtering applied if tags present |
| 7 | Agent optionally reranks results | Top-K reordered by lexical overlap | Only if `rerank=true` |
| 8 | Agent builds RAG prompt | System rules + retrieved docs + question | `_build_deterministic_rag_answer()` |
| 9 | Agent calls LLM | Generated answer text | Via `LocalLLMClientManager` |
| 10 | Agent runs output guardrails | Pass / filter | Toxicity check, hallucination heuristic |
| 11 | Agent sanitizes links | Only source-backed URLs preserved | `_sanitize_answer_links()` |
| 12 | Agent returns JSON response | `{answer, sources, response_time_ms, latency_breakdown}` | Gateway forwards to frontend |

**Happy path outcome:** User receives accurate, sourced answer in their language within 1-3 seconds.
**Failure modes:** Empty retrieval (weak answer), LLM timeout (500 error), rate limiting (localized retry message), off-topic rejection.

### Streaming Question

**Persona:** Community Member (via Gateway)
**Goal:** See real-time progress while the agent processes a question

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | User types question | Frontend connects to `GET /ask-stream` via SSE | |
| 2 | Agent emits `thinking` event | "Checking FAQ..." | progress: 10 |
| 3 | Agent emits `thinking` event | "Analyzing question..." | progress: 25 |
| 4 | Agent emits `tool_event` (start) | "Searching knowledge base..." | progress: 40 |
| 5 | Agent performs retrieval | pgvector search completes | |
| 6 | Agent emits `tool_event` (result) | "Found N relevant documents" | progress: 62 |
| 7 | Agent generates answer via LLM | | |
| 8 | Agent emits `thinking` event | "Finalizing answer..." | progress: 95 |
| 9 | Agent emits `complete` event | `{answer, sources, suggested_questions}` | progress: 100 |

**Happy path outcome:** User sees progressive updates, then receives final answer with follow-up suggestions.
**Failure modes:** Stream disconnects, LLM error yields `error` SSE event with localized fallback.

### Operator Diagnostics

**Persona:** Operator / Developer
**Goal:** Diagnose why retrieval is returning poor results

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Operator calls `GET /test-db-search?query=community resources` | Agent runs diagnostic flow | |
| 2 | Agent checks table existence | `table_exists: true/false` | |
| 3 | Agent samples embeddings | `embeddings_exist`, `stored_embedding_dimension` | |
| 4 | Agent tests RPC function | `rpc_function_exists: true/false` | |
| 5 | Agent generates query embedding | `query_embedding_dimension: 384` | |
| 6 | Agent runs vector search | Results with similarity scores | |
| 7 | Agent returns diagnostic payload | `{status, diagnostics, similarity_range, sample_result}` | |

**Happy path outcome:** Operator identifies dimension mismatch, missing embeddings, or RPC errors.
**Failure modes:** DATABASE_URL not set, psycopg2 unavailable.

### Model Selection

**Persona:** Operator / Developer
**Goal:** Switch the active LLM model

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Operator calls `GET /model-selection` | Returns current provider, model, locked status | |
| 2 | Operator calls `POST /model-selection` | Validates model exists in `/config` | |
| 3 | Agent persists selection to file | `model_selection.json` updated | |
| 4 | Subsequent `/ask` requests use new model | LLM calls routed to updated model | |

**Happy path outcome:** Model switched, selection persisted.
**Failure modes:** Model not in available list (400), selection locked (403).

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)
