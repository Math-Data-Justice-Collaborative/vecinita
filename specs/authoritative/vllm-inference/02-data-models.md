# Data Models: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service is **stateless** — it does not own any database tables or persistent data models. Its data domain consists of OpenAI-compatible request/response schemas for inference and a model registry for supported model configurations. Model weights are cached on a Modal persistent volume but are not application-managed data.

## Request/Response Schemas

### ChatCompletionRequest

OpenAI-compatible chat completion request body.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| model | string | required | Model identifier (must match loaded model) |
| messages | array[Message] | min 1 | Ordered chat turns |
| temperature | float | 0.0–2.0, default 0.7 | Sampling temperature |
| top_p | float | 0.0–1.0, default 1.0 | Nucleus sampling threshold |
| max_tokens | int \| null | >0 or null | Upper bound on generated tokens |
| stream | bool | default false | Enable SSE streaming |
| stop | string \| array \| null | optional | Stop sequences |
| frequency_penalty | float | -2.0–2.0, default 0.0 | Frequency-based repetition penalty |
| presence_penalty | float | -2.0–2.0, default 0.0 | Presence-based repetition penalty |
| n | int | default 1 | Number of completions to generate |

**Source:** vLLM's built-in OpenAI-compatible server (mirrors OpenAI `ChatCompletionRequest`)

### Message

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| role | string | "system" \| "user" \| "assistant" | Speaker role |
| content | string | required | Message text |

### ChatCompletionResponse

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique completion ID (`chatcmpl-*`) |
| object | string | Always `"chat.completion"` |
| created | int | Unix timestamp |
| model | string | Model identifier used |
| choices | array[Choice] | Generated completions |
| usage | Usage | Token counts |

### Choice

| Field | Type | Description |
|-------|------|-------------|
| index | int | Choice index |
| message | Message | Generated message |
| finish_reason | string | `"stop"` \| `"length"` \| `"tool_calls"` |

### Usage

| Field | Type | Description |
|-------|------|-------------|
| prompt_tokens | int | Input token count |
| completion_tokens | int | Output token count |
| total_tokens | int | Sum of prompt + completion |

### CompletionRequest

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| model | string | required | Model identifier |
| prompt | string \| array | required | Raw text prompt(s) |
| max_tokens | int \| null | >0 | Max tokens to generate |
| temperature | float | 0.0–2.0 | Sampling temperature |
| stream | bool | default false | Enable SSE streaming |

### HealthResponse (custom)

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"ok"` \| `"error"` |
| model | string | Currently loaded model ID |
| gpu | string \| null | GPU type if available |

## Model Registry

The service supports a configurable model, specified at deploy time. The rewrite targets a single-model-per-deployment pattern (unlike the previous multi-model Ollama approach).

| Model ID | HF Repository | Parameters | GPU Recommendation |
|----------|---------------|------------|-------------------|
| gemma-3-4b-it | `google/gemma-3-4b-it` | 4B | A100-40GB / A10G |
| llama-3.1-8b-instruct | `meta-llama/Llama-3.1-8B-Instruct` | 8B | A100-40GB |
| llama-3.2-3b-instruct | `meta-llama/Llama-3.2-3B-Instruct` | 3B | A10G |
| mistral-7b-instruct-v0.3 | `mistralai/Mistral-7B-Instruct-v0.3` | 7B | A100-40GB |

**Source:** `apps/vllm-inference/config.py` (target)

## Relationships

No entity relationships — this service is stateless. Data flows are request-response only.

## Diagrams

- [Data Model Diagram](diagrams/data-models.md)

## Related Documents

- [API Contract](08-api-contract.md)
- [Data Flow](06-data-flow.md)
