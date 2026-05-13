# Vecinita Agent — API Contract

> Auto-generated: 2026-05-12

## Overview

The agent exposes a RESTful HTTP API via FastAPI. All endpoints use query parameters for input (no JSON request bodies except `POST /model-selection`). The primary consumer is the gateway service; operators can access diagnostic endpoints directly.

## Base URL

| Environment | URL |
|-------------|-----|
| Local | `http://localhost:8000` |
| Render | `https://vecinita-agent.onrender.com` (internal: `vecinita-agent:10000`) |

## Endpoints

### GET /ask

| Property | Value |
|----------|-------|
| Auth | None (gateway handles auth) |
| Content-Type | `application/json` |
| Response (200) | `AgentAskJsonResponse` |
| Error responses | 400 (missing question), 422 (invalid params), 500 (unhandled) |
| Rate limit | None at agent level; rate-limit errors from LLM provider are caught and returned as localized messages |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| question | string \| null | null | Primary question text |
| query | string \| null | null | Legacy alias for `question` |
| thread_id | string | "default" | Conversation thread identifier |
| lang | string \| null | null | Force language (en/es); auto-detected if omitted |
| provider | string \| null | null | LLM provider override (only "ollama" supported) |
| model | string \| null | null | Model ID override (must exist in `/config`) |
| context_answer | string \| null | null | Prior assistant answer for contextual follow-ups |
| tags | string \| null | null | Comma-separated metadata tags for retrieval filtering |
| tag_match_mode | "any" \| "all" | "any" | How tags are matched |
| include_untagged_fallback | bool | true | Include untagged docs when tag filter is active |
| rerank | bool | false | Enable lexical reranking of retrieved chunks |
| rerank_top_k | int (1-50) | 10 | Number of chunks to retain after reranking |

**Response (200):**

```json
{
  "answer": "Nearby clinics include Eastside Community Health Center...",
  "thread_id": "default",
  "response_time_ms": 842,
  "sources": [{"url": "https://example.com", "title": "Source"}],
  "latency_breakdown": {
    "retrieval_invoke_ms": 120,
    "llm_ms": 700,
    "db_search": {"embedding_ms": 50, "retrieval_ms": 70, "status": "ok"}
  }
}
```

### GET /ask-stream

| Property | Value |
|----------|-------|
| Auth | None |
| Content-Type | `text/event-stream` (SSE) |
| Response | Stream of JSON events |
| Error responses | 400 (missing question), inline `error` event for runtime failures |

Same query parameters as `GET /ask` plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| clarification_response | string \| null | null | Reserved for future clarification flows |

**SSE Event Types:**

| Type | Fields | Description |
|------|--------|-------------|
| `thinking` | message, stage, progress, status | Progress update (precheck, analysis, finalizing) |
| `tool_event` | phase (start/result), tool, message | Tool invocation status |
| `complete` | answer, sources, suggested_questions, thread_id, plan, metadata | Final response |
| `error` | message, stage, progress, status | Error fallback |

### GET /health

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | `{"status": "ok"}` |

### GET /

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | `AgentRootInfo` — service discovery with endpoint links |

### GET /config

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | `AgentLlmConfigApiResponse` — providers, models, runtime flags |

**Response (200):**

```json
{
  "providers": [{"key": "ollama", "label": "Modal (Ollama-compatible)", "default": true}],
  "models": {"ollama": ["gemma3"]},
  "defaultProvider": "ollama",
  "defaultModel": "gemma3",
  "runtime": {
    "fast_mode": true,
    "max_response_sentences": 4,
    "max_response_chars": 700,
    "reachable": true
  }
}
```

### GET /model-selection

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | `ModelSelectionGetApiResponse` — current selection + available options |

### POST /model-selection

| Property | Value |
|----------|-------|
| Auth | None |
| Request body | `{"provider": "ollama", "model": "gemma3", "lock": false}` |
| Response (200) | `ModelSelectionPostResponse` |
| Error responses | 400 (unsupported provider/model), 403 (locked) |

### GET /privacy

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | `{"markdown": "# Privacy Policy\n..."}` |

### GET /test-db-search

| Property | Value |
|----------|-------|
| Auth | None |
| Query params | `query` (default: "community resources") |
| Response (200) | `AgentTestDbSearchResponse` — diagnostic payload with similarity scores |

### GET /db-info

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | `AgentDbInfoResponse` — table stats, sample rows, RPC test |

## Schemas

All request/response schemas are defined as Pydantic models in:
- `apis/agent/src/agent/http_api_schemas.py`
- `apis/gateway/src/services/agent/models.py`

OpenAPI schema is auto-generated at `GET /openapi.json`.

## Versioning

No formal versioning strategy. The `version` field in the root endpoint returns `"2.0"`. Breaking changes are coordinated by gateway–agent deployment alignment. The `query` parameter is maintained as a legacy alias for `question`.

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
