# Dependencies: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service has a focused dependency set centered on vLLM for inference and Modal for serverless GPU deployment. It is intentionally lean compared to the previous Ollama-based implementation.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| None | — | Standalone service; no shared packages from the monorepo |

The service is self-contained. Unlike the gateway and agent, it does not depend on shared config, schemas, or service-client packages.

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| vllm | >=0.8.0 | LLM inference engine with PagedAttention | **yes** |
| modal | >=1.0.0 | Serverless GPU compute platform SDK | **yes** |
| torch | >=2.4.0 | PyTorch (vLLM dependency, GPU compute) | **yes** |
| transformers | >=4.45.0 | Hugging Face model loading and tokenizers | **yes** |
| fastapi | >=0.115.0 | HTTP server (vLLM's built-in OpenAI server) | yes |
| pydantic | >=2.0.0 | Request/response validation | yes |
| pydantic-settings | >=2.0.0 | Environment-based configuration | yes |
| uvicorn | >=0.23.0 | ASGI server | yes |
| huggingface-hub | >=0.25.0 | Model weight downloads | yes |
| safetensors | >=0.4.0 | Model weight file format | yes |
| ray | (vLLM dep) | Distributed inference (if multi-GPU) | conditional |

### Dev / CI only

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=9.0.0 | Test runner |
| pytest-asyncio | >=0.24.0 | Async test support |
| pytest-cov | >=7.0.0 | Coverage reporting |
| ruff | >=0.8.0 | Linting and formatting |
| httpx | >=0.27.0 | HTTP test client |

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| GPU (H100 80GB / A100 40GB) | Modal | LLM inference compute |
| `vecinita-vllm-models` volume | Modal | Persistent model weight cache |
| CUDA 12.1+ runtime | Modal (image) | GPU compute libraries |

## Service Dependencies (runtime calls)

| Service | Required | Fallback |
|---------|----------|----------|
| Modal platform | **yes** | None — service cannot run without Modal |
| Hugging Face Hub | At deploy time | Cached weights on volume allow offline serving |

No runtime dependencies on other Vecinita services. The vllm-inference service is a **leaf service** — it is called by others but does not call out to any Vecinita service.

## Comparison with Previous Implementation

| Dependency | Previous (Ollama) | New (vLLM) |
|------------|-------------------|------------|
| Inference engine | ollama binary + ollama Python client | vllm (pip) |
| GPU runtime | None (CPU inference) | CUDA 12.1+ / PyTorch |
| Model format | Ollama GGUF blobs | Safetensors / HF Hub |
| HTTP server | Custom FastAPI routes | vLLM built-in OpenAI server |
| Modal SDK | modal >=0.73.0 | modal >=1.0.0 |

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
