# Vecinita Agent — Data Flow

> Auto-generated: 2026-05-12

## Overview

Data enters the agent as HTTP query parameters, is enriched through embedding and retrieval, transformed by LLM generation, and exits as structured JSON or SSE streams. Persistent state lives in PostgreSQL; runtime state (model selection, embedding cache) is in-process memory.

## Inbound Data

| Source | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| Gateway `/ask` | Query params (question, thread_id, lang, tags, etc.) | User question | Ask router (`routers/ask.py`) |
| Gateway `/ask-stream` | Query params (same as `/ask`) | User question | Stream router (`routers/ask.py`) |
| Gateway `/config` | None | Frontend model discovery | Config router (`routers/config.py`) |
| Gateway `/health` | None | Container probe | System router (`routers/system.py`) |
| Operator `/test-db-search` | Query param (query) | Diagnostics | Diagnostics router (`routers/diagnostics.py`) |
| Operator `/model-selection` | JSON body (provider, model, lock) | Model switch | Config router (`routers/config.py`) |

## Internal Processing

| Stage | Input | Transformation | Output |
|-------|-------|----------------|--------|
| Parameter coercion | Raw query strings | `_coerce_ask_query_parameters()` — strip, lowercase, null sentinel handling | Clean typed params |
| Language detection | Question text | `langdetect.detect()` with Spanish marker heuristics | ISO language code (`en`/`es`) |
| Input guardrails | Question text + language | Regex injection/SQLi check → Hub PII → local PII → topic relevance | `GuardResult` (pass/reject/redact) |
| Intent classification | Effective question + language | Keyword heuristics (`_is_answer_seeking_query`) | Boolean `answer_seeking` |
| Static FAQ match | Effective question + language | Exact/cleaned/partial match against `FAQ_DATABASE` | Answer string or None |
| Query embedding | Question text | HTTP call to embedding service → 384-dim float vector | Embedding vector (cached in LRU) |
| Vector retrieval | Embedding + tags + threshold | pgvector cosine similarity search on `document_chunks` | List of `{content, source_url, similarity, ...}` |
| Reranking | Query + retrieved docs | Lexical overlap (0.75 × similarity + 0.25 × recall) | Reordered top-K docs |
| RAG prompt build | Question + docs + language + weak flag | Template with system rules, retrieved context, generation instructions | Full prompt for LLM |
| LLM generation | Prompt messages | `LocalLLMClientManager.build_client().invoke()` | Raw answer text |
| Output guardrails | Answer text | Toxicity blocklist → hallucination heuristic | Final answer or safe fallback |
| Link sanitization | Answer + allowed URLs | Remove fabricated URLs not in retrieved sources | Clean answer text |
| Response assembly | Answer + sources + timing | Build JSON payload with latency breakdown | `AgentAskJsonResponse` |

## Outbound Data

| Destination | Format | Trigger | Content |
|-------------|--------|---------|---------|
| Gateway (JSON) | `application/json` | `/ask` response | `{answer, thread_id, response_time_ms, sources, latency_breakdown}` |
| Gateway (SSE) | `text/event-stream` | `/ask-stream` response | Sequence of `{type, message/answer, stage, progress}` events |
| Gateway (JSON) | `application/json` | `/config` response | `{providers, models, defaultProvider, runtime}` |
| Gateway (JSON) | `application/json` | `/health` response | `{status: "ok"}` |
| PostgreSQL | SQL query | `/test-db-search`, `/db-info` | Diagnostic SELECT queries |

## Data Persistence

| Store | Technology | What's Stored | Retention |
|-------|------------|---------------|-----------|
| Knowledge base | PostgreSQL + pgvector | `document_chunks` (content, embeddings, metadata) | Indefinite; managed by data-management pipeline |
| Processing queue | PostgreSQL | `processing_queue` (batch load tracking) | Indefinite |
| Model selection | Local JSON file | `model_selection.json` (provider, model, locked) | Persistent across restarts; ephemeral on Render redeploys |
| Embedding cache | In-process memory (LRU) | Recent query embeddings (256 entries default) | Process lifetime |
| FAQ database | In-process memory | Static FAQ entries (en/es) | Process lifetime (hardcoded) |

## Diagrams

- [Data Flow Diagram](diagrams/data-flow.md)

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
