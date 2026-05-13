# Integration Points: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service has a narrow integration surface: it receives inference requests from the agent service and optionally from the gateway, and downloads model weights from Hugging Face Hub. It does not call any other Vecinita services.

## Internal Integrations

| Target | Protocol | Direction | Purpose | Config |
|--------|----------|-----------|---------|--------|
| Agent service (`apis/agent/`) | OpenAI-compatible REST | **inbound** | Chat completions for RAG responses | Agent configures via `llama-index-llms-vllm` pointed at Modal URL |
| Gateway (`apis/gateway/`) | Modal SDK (`Function.from_name`) | **inbound** | Direct Modal function invocation for chat completion | `MODAL_MODEL_APP_NAME`, `MODAL_MODEL_CHAT_FUNCTION` |

## External Integrations

| Provider | Protocol | Purpose | Auth | Config |
|----------|----------|---------|------|--------|
| Hugging Face Hub | HTTPS | Model weight downloads | HF token (optional for public models) | `HF_TOKEN` env var |
| Modal | SDK + HTTPS | Serverless GPU compute, volume storage | `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | Modal secrets |

## Integration Details

### Agent → vLLM (Primary Path)

- **Endpoint:** `POST /v1/chat/completions` (OpenAI-compatible)
- **Client:** LlamaIndex `llama-index-llms-vllm` configured with vLLM's Modal URL as `api_url`
- **Request format:** OpenAI `ChatCompletionRequest` JSON
- **Response format:** OpenAI `ChatCompletionResponse` JSON (or SSE stream)
- **Error handling:** HTTP 500 with error detail; LlamaIndex retries at the client level
- **Retry/timeout policy:** Agent-side timeout configured via `AGENT_TIMEOUT` (default 180s); no server-side retry (inference is not idempotent)

### Gateway → vLLM (Modal SDK Path)

- **Function:** `modal.Function.from_name("vecinita-vllm-inference", "chat_completion").remote()`
- **Request format:** Python dict with `model`, `messages`, `temperature` keys
- **Response format:** Python dict (OpenAI-compatible shape)
- **Error handling:** Modal SDK raises `modal.exception.Error` on function failure; gateway catches and returns 502
- **Retry/timeout policy:** Single attempt; `scaledown_window` keeps containers warm for burst traffic

### Hugging Face Hub → Model Weights

- **Endpoint:** `https://huggingface.co/<org>/<model>/resolve/main/`
- **Request format:** HTTP GET (via `huggingface_hub` library or vLLM's built-in downloader)
- **Response format:** Binary model weight files (safetensors/bin)
- **Error handling:** vLLM retries downloads with exponential backoff
- **Auth:** `HF_TOKEN` environment variable for gated models (Llama, Gemma); optional for public models

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
