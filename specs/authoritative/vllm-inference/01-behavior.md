# Behavior: vLLM Inference
> Auto-generated: 2026-05-12

## Purpose

The vllm-inference service is the **LLM inference engine** for the Vecinita civic information RAG system. It runs open-weight language models on Modal serverless GPUs using [vLLM](https://docs.vllm.ai/), exposing an OpenAI-compatible REST API that the agent service consumes via LlamaIndex's `llama-index-llms-vllm` integration. This service replaces the previous Ollama-based implementation (`modal-apps/model-modal/`) with a purpose-built vLLM deployment optimized for GPU throughput and API compatibility.

Source: `apps/vllm-inference/` (target path; rewrite of `modal-apps/model-modal/`)

## Core Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| 1 | LLM inference | Serve chat completions and text completions via vLLM's high-throughput inference engine |
| 2 | OpenAI-compatible API | Expose `/v1/chat/completions`, `/v1/completions`, and `/v1/models` endpoints matching the OpenAI API spec |
| 3 | Model weight management | Download and cache model weights in a Modal persistent volume for fast cold starts |
| 4 | GPU resource management | Run on H100/A100 GPUs via Modal with configurable scaledown windows and timeouts |
| 5 | Health reporting | Expose `/health` endpoint for readiness probes and model availability checks |

## Key Behaviors

### Chat Completion

| Property | Value |
|----------|-------|
| Trigger | `POST /v1/chat/completions` from agent service (via LlamaIndex `llama-index-llms-vllm`) |
| Process | vLLM engine tokenizes input, runs GPU inference with PagedAttention, decodes output tokens |
| Outcome | OpenAI-compatible `ChatCompletion` response with `choices[].message.content` |

- Supports streaming via `stream: true` (SSE with `data:` chunks followed by `data: [DONE]`)
- Supports multi-turn conversation history (system, user, assistant roles)
- Parameters: `temperature`, `top_p`, `max_tokens`, `stop`, `frequency_penalty`, `presence_penalty`

### Text Completion

| Property | Value |
|----------|-------|
| Trigger | `POST /v1/completions` |
| Process | Raw prompt completion without chat template wrapping |
| Outcome | OpenAI-compatible `Completion` response with `choices[].text` |

### Model Discovery

| Property | Value |
|----------|-------|
| Trigger | `GET /v1/models` |
| Process | Return metadata for the loaded model |
| Outcome | OpenAI-compatible model list (single model per deployment) |

### Model Weight Preloading

| Property | Value |
|----------|-------|
| Trigger | CI deploy pipeline or manual `modal run` invocation |
| Process | Download model weights from Hugging Face Hub into Modal persistent volume |
| Outcome | Weights cached on `vecinita-vllm-models` volume, ready for fast container startup |

### Health Check

| Property | Value |
|----------|-------|
| Trigger | `GET /health` from load balancers or operators |
| Process | Check vLLM engine readiness and GPU availability |
| Outcome | `{"status": "ok", "model": "<model_id>"}` or error status |

## Service Boundaries (Does NOT Own)

| Concern | Owned By |
|---------|----------|
| RAG retrieval logic, prompt construction, graph orchestration | agent service (`apis/agent/`) |
| Embedding generation | Modal `vecinita-embedding` app |
| Web scraping and document ingestion | Modal `vecinita-scraper` app |
| Request routing, auth, rate limiting, CORS | gateway service (`apis/gateway/`) |
| Frontend rendering | chat-frontend, data-management-frontend |
| Model fine-tuning or training | Out of scope (use pre-trained weights) |

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [API Contract](08-api-contract.md)
- [Architecture Diagram](diagrams/architecture.md)
