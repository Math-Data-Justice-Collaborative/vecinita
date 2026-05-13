# Architecture: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service is a **serverless GPU function** deployed on Modal. It wraps vLLM's OpenAI-compatible API server to provide high-throughput LLM inference with automatic GPU scaling. The architecture is intentionally thin — vLLM handles tokenization, KV cache management, continuous batching, and HTTP serving; the Modal layer handles container lifecycle, GPU provisioning, and volume management.

## Architecture Style

**Serverless function with embedded inference server.** Each Modal container runs a complete vLLM API server process. Modal manages container lifecycle (cold start, warm pool, scaledown). The service exposes both:

1. **REST API** — vLLM's built-in OpenAI-compatible HTTP server via `@modal.asgi_app()` or `@modal.web_endpoint()`
2. **Modal function** — Direct SDK invocation via `modal.Function.from_name()` for gateway integration

## Component Map

| Component | Responsibility | Source Path |
|-----------|---------------|-------------|
| `app.py` | Modal app definition, function registration, ASGI mount | `apps/vllm-inference/app.py` |
| `config.py` | Settings (model ID, GPU type, timeouts) via pydantic-settings | `apps/vllm-inference/config.py` |
| `engine.py` | vLLM `AsyncLLMEngine` initialization and lifecycle | `apps/vllm-inference/engine.py` |
| `download.py` | Model weight download function for volume preloading | `apps/vllm-inference/download.py` |
| vLLM server | OpenAI-compatible API server (built-in) | `vllm.entrypoints.openai.api_server` |

## Runtime Characteristics

| Property | Value |
|----------|-------|
| Language / runtime | Python >=3.11 |
| Inference engine | vLLM (with PagedAttention) |
| HTTP framework | FastAPI (vLLM's built-in OpenAI server) |
| Entry point | `apps/vllm-inference/app.py` |
| Port | 8000 (vLLM default) |
| Health check | `GET /health` |
| GPU | H100 (80GB) or A100 (40GB/80GB), configurable |
| CUDA | >=12.1 (via Modal image) |

## Concurrency Model

vLLM uses **continuous batching** for concurrent request handling:

1. **Incoming requests** are queued by the OpenAI-compatible API server (FastAPI/uvicorn)
2. **vLLM scheduler** batches requests into the GPU inference loop using PagedAttention
3. **KV cache** is managed via paged memory blocks — new requests can be interleaved with in-flight requests without waiting for earlier requests to complete
4. **Output tokens** are streamed back per-request as they're generated

This means a single container can handle multiple concurrent inference requests efficiently, unlike the previous Ollama-based design which processed requests sequentially.

**Container concurrency:** Controlled by Modal's `allow_concurrent_inputs` parameter. Recommended: 10–50 concurrent requests per container (depends on model size and GPU memory).

## Key Differences from Previous Implementation

| Aspect | Previous (Ollama) | New (vLLM) |
|--------|-------------------|------------|
| Inference engine | Ollama (wraps llama.cpp) | vLLM (PagedAttention, CUDA) |
| API surface | Custom Ollama-compatible endpoints | Native OpenAI-compatible API |
| GPU utilization | CPU-only on Modal (no GPU allocation) | Full GPU (H100/A100) |
| Batching | Sequential (one request at a time) | Continuous batching |
| Client integration | Custom HTTP calls | Standard OpenAI SDK / LlamaIndex `llama-index-llms-vllm` |
| Multi-model | Multiple models via registry | Single model per deployment |
| Server process | `ollama serve` subprocess | vLLM ASGI app (in-process) |

## Diagrams

- [Architecture Diagram](diagrams/architecture.md)

## Related Documents

- [Behavior](01-behavior.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
