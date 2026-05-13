# Data Flow: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

Data flows through the vllm-inference service in a stateless request-response pattern. There is no persistent application state — the service receives inference requests, processes them on GPU, and returns completions. Model weights are the only persistent data, cached on a Modal volume.

## Inbound Data

| Source | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| Agent service | OpenAI `ChatCompletionRequest` JSON | `POST /v1/chat/completions` | vLLM inference engine |
| Agent service | OpenAI `CompletionRequest` JSON | `POST /v1/completions` | vLLM inference engine |
| Gateway (Modal SDK) | Python dict (model, messages, temperature) | `Function.from_name().remote()` | Modal function → vLLM engine |
| Hugging Face Hub | Safetensors/bin model weight files | `modal run download_model` | Modal persistent volume |

## Internal Processing

| Stage | Input | Transformation | Output |
|-------|-------|----------------|--------|
| Request validation | HTTP JSON body | Parse and validate against OpenAI schema | Validated request object |
| Tokenization | Message text | Apply chat template, tokenize via model tokenizer | Token IDs |
| KV cache allocation | Token IDs | PagedAttention allocates GPU memory blocks | Memory-mapped attention cache |
| GPU inference | Token IDs + KV cache | Autoregressive decoding with sampling (temperature, top_p) | Output token IDs |
| Detokenization | Output token IDs | Decode tokens to text | Completion text |
| Response formatting | Completion text + metadata | Package into OpenAI-compatible response shape | `ChatCompletionResponse` |

## Outbound Data

| Destination | Format | Trigger | Content |
|-------------|--------|---------|---------|
| Agent service | OpenAI `ChatCompletionResponse` JSON | Request completion | Model-generated text, usage stats, finish reason |
| Agent service (streaming) | SSE `text/event-stream` | `stream: true` in request | Incremental token deltas, `[DONE]` sentinel |
| Gateway (Modal SDK) | Python dict | Function return | Same data as REST response, as dict |

## Data Persistence

| Store | Technology | What's Stored | Retention |
|-------|------------|---------------|-----------|
| `vecinita-vllm-models` | Modal Volume | Model weight files (safetensors) | Permanent until manually cleaned |

No database, no cache, no queue. The service is purely compute-bound.

## Diagrams

- [Data Flow Diagram](diagrams/data-flow.md)

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
