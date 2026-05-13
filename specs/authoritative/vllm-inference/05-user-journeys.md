# User Journeys: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

End-to-end journeys that personas take through or involving the vllm-inference service.

## Journeys

### Chat Completion Request (Agent Service)

**Persona:** Agent Service
**Goal:** Obtain a chat completion for a user's civic information question

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Agent constructs prompt with RAG context and user question | — | LlamaIndex orchestration |
| 2 | Agent sends `POST /v1/chat/completions` to vLLM endpoint | vLLM receives request, queues for inference | Via `llama-index-llms-vllm` |
| 3 | vLLM engine runs inference on GPU | Tokens generated via PagedAttention | Continuous batching optimizes throughput |
| 4 | vLLM returns `ChatCompletionResponse` | Agent receives completion | Standard OpenAI response shape |
| 5 | Agent post-processes and returns to gateway | — | Includes source citations |

**Happy path outcome:** Agent receives a coherent, contextually relevant answer within the configured timeout.
**Failure modes:**
- GPU unavailable → Modal queues container spin-up, adds cold start latency (15–60s)
- Model OOM → vLLM returns HTTP 500; agent falls back to shorter context
- Network timeout → LlamaIndex raises `TimeoutError`; gateway returns 504

### Streaming Chat Completion (Agent Service)

**Persona:** Agent Service
**Goal:** Stream response tokens for real-time display in the chat frontend

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Agent sends `POST /v1/chat/completions` with `stream: true` | vLLM opens SSE stream | |
| 2 | vLLM generates tokens incrementally | SSE events: `data: {"choices":[{"delta":{"content":"..."}}]}` | One event per token batch |
| 3 | Final event sent | `data: [DONE]` | Stream terminates |
| 4 | Agent forwards tokens to gateway SSE stream | Tokens appear in real-time in chat UI | |

**Happy path outcome:** User sees response text appearing word-by-word with low perceived latency.
**Failure modes:**
- Connection drop mid-stream → Client reconnects; partial response may be lost
- GPU memory pressure → Generation slows; higher inter-token latency

### Model Deployment (Platform Operator)

**Persona:** Platform Operator
**Goal:** Deploy a new model version or swap models

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Update `MODEL_ID` in config/env | — | e.g., switch from Gemma 3 to Llama 3.1 |
| 2 | Run `modal run app.py::download_model` | Weights downloaded to `vecinita-vllm-models` volume | Can take 5–30 min for large models |
| 3 | Run `modal deploy app.py` | New containers built with updated config | CI does this automatically on main push |
| 4 | Verify via `GET /health` | Returns `{"status": "ok", "model": "..."}` | |
| 5 | Monitor first requests for latency | Cold start includes vLLM engine initialization | ~15–30s for first request |

**Happy path outcome:** New model serving traffic within minutes of deploy.
**Failure modes:**
- Model too large for GPU → vLLM crashes with OOM; operator must select larger GPU
- HF token missing for gated model → Download fails; clear error in logs
- Volume quota exceeded → Download fails; operator must clean old model weights

### Health Monitoring (Gateway Service)

**Persona:** Gateway Service
**Goal:** Verify inference service is operational

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Gateway calls `GET /health` | vLLM checks engine status | Periodic health probe |
| 2 | Health response received | `{"status": "ok", "model": "gemma-3-4b-it"}` | |
| 3 | If error, gateway marks inference as degraded | Returns fallback or error to frontends | |

**Happy path outcome:** Health check returns `ok` within 2 seconds.
**Failure modes:**
- Container scaled to zero → Cold start before health response; probe may timeout
- GPU fault → vLLM returns error status; gateway switches to fallback provider

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)
