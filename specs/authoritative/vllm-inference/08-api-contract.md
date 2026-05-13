# API Contract: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service exposes an **OpenAI-compatible REST API** via vLLM's built-in server. This means any client written for the OpenAI API (including `openai` Python SDK and LlamaIndex's `llama-index-llms-vllm`) can connect without modification — only the base URL changes.

## Base URL

| Environment | URL |
|-------------|-----|
| Modal (production) | `https://<workspace>--vecinita-vllm-inference-serve.modal.run` |
| Modal (dev/serve) | `https://<workspace>--vecinita-vllm-inference-serve-dev.modal.run` |
| Local (Docker) | `http://localhost:8000` |

## Authentication

| Method | Details |
|--------|---------|
| Production | No application-level auth; secured via Modal's network layer and caller-side auth |
| API key passthrough | vLLM accepts any `api_key` by default (set `--api-key` flag to enforce) |

## Endpoints

### POST /v1/chat/completions

Primary endpoint for chat-based inference. Used by the agent service via LlamaIndex.

| Property | Value |
|----------|-------|
| Auth | None (or configurable `--api-key`) |
| Content-Type | `application/json` |
| Request body | `ChatCompletionRequest` |
| Response (200) | `ChatCompletionResponse` |
| Response (streaming) | `text/event-stream` (SSE) |
| Error responses | `422` (validation), `500` (inference error), `503` (model loading) |

**Request body:**

```json
{
  "model": "google/gemma-3-4b-it",
  "messages": [
    {"role": "system", "content": "You are a helpful civic information assistant."},
    {"role": "user", "content": "What affordable housing resources exist in Oakland?"}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

**Response (non-streaming):**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1715500000,
  "model": "google/gemma-3-4b-it",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Oakland offers several affordable housing resources..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 128,
    "total_tokens": 170
  }
}
```

**Response (streaming, `stream: true`):**

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":"Oakland"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":" offers"},"finish_reason":null}]}

data: [DONE]
```

### POST /v1/completions

Raw text completion endpoint.

| Property | Value |
|----------|-------|
| Auth | None (or configurable) |
| Request body | `CompletionRequest` |
| Response (200) | `CompletionResponse` |

**Request body:**

```json
{
  "model": "google/gemma-3-4b-it",
  "prompt": "The three most important tenant rights in California are:",
  "max_tokens": 256,
  "temperature": 0.3
}
```

### GET /v1/models

List available models.

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | `ModelList` |

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "google/gemma-3-4b-it",
      "object": "model",
      "created": 1715500000,
      "owned_by": "vllm"
    }
  ]
}
```

### GET /health

Custom health check endpoint (vLLM built-in).

| Property | Value |
|----------|-------|
| Auth | None |
| Response (200) | Empty body (engine ready) |
| Response (503) | Engine not ready / loading |

### GET /v1/models (LlamaIndex discovery)

LlamaIndex's `llama-index-llms-vllm` calls this endpoint to discover the served model ID. The response must include the model name matching what was passed as `--model` to vLLM.

## Versioning

- **Strategy:** The API follows the OpenAI API specification. vLLM maintains backward compatibility with OpenAI's API surface.
- **Breaking changes:** Only when vLLM upgrades change the OpenAI-compatible interface (rare; vLLM prioritizes compatibility).
- **Version prefix:** `/v1/` (matches OpenAI convention).

## Rate Limits

No application-level rate limiting. Throughput is bounded by:
- GPU compute capacity (tokens/second)
- Modal container concurrency (`allow_concurrent_inputs`)
- Modal scaling limits (max containers)

## Schemas

All request/response schemas follow the [OpenAI API reference](https://platform.openai.com/docs/api-reference). vLLM implements these schemas natively.

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
