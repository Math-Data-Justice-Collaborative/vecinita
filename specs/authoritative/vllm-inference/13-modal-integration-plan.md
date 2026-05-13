# Modal Integration Plan: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service is a **Modal-native application** — it runs entirely on Modal serverless GPUs with no secondary deployment target. This document details the Modal app configuration, GPU selection strategy, model loading workflow, and invocation patterns.

## Modal App

| Property | Value |
|----------|-------|
| App name | `vecinita-vllm-inference` |
| Source | `apps/vllm-inference/` |
| Deploy command | `modal deploy apps/vllm-inference/app.py` |
| Serve command | `modal serve apps/vllm-inference/app.py` |
| Python version | >=3.11 |

## Functions

| Function | Timeout | Resources | Purpose |
|----------|---------|-----------|---------|
| `serve` (ASGI) | configurable (default 600s) | GPU (A100/H100), 4+ CPU | vLLM OpenAI-compatible API server |
| `chat_completion` | configurable (default 600s) | GPU (same as serve) | Modal SDK-callable function wrapper |
| `download_model` | 3600s | CPU only (no GPU) | Download model weights to volume |
| `download_default_model` | 3600s | CPU only | Download configured default model |

### `serve` — ASGI Web Endpoint

The primary function exposes vLLM's OpenAI-compatible API as a Modal web endpoint:

```python
@app.function(
    image=vllm_image,
    gpu=modal.gpu.A100(count=1, size="40GB"),
    volumes={MODELS_PATH: models_volume},
    timeout=settings.timeout,
    scaledown_window=settings.scaledown_window,
    allow_concurrent_inputs=settings.max_concurrent,
    container_idle_timeout=settings.container_idle_timeout,
)
@modal.asgi_app()
def serve():
    from vllm.entrypoints.openai.api_server import build_async_engine_client
    # ... vLLM ASGI app setup
```

### `chat_completion` — Modal Function (SDK invocation)

Wraps the vLLM engine for direct Modal SDK calls from the gateway:

```python
@app.function(
    image=vllm_image,
    gpu=modal.gpu.A100(count=1, size="40GB"),
    volumes={MODELS_PATH: models_volume},
    timeout=settings.timeout,
    scaledown_window=settings.scaledown_window,
)
def chat_completion(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> dict:
    # ... invoke vLLM engine and return OpenAI-compatible dict
```

### `download_model` — Weight Preloading

```python
@app.function(
    image=vllm_image,
    volumes={MODELS_PATH: models_volume},
    timeout=3600,
)
def download_model(model_id: str) -> None:
    from huggingface_hub import snapshot_download
    snapshot_download(model_id, local_dir=f"{MODELS_PATH}/{model_id}")
    models_volume.commit()
```

## Volumes and Secrets

| Volume/Secret | Mount/Bind | Purpose |
|---------------|------------|---------|
| `vecinita-vllm-models` | `/models` (volume) | Persistent cache for model weight files (safetensors) |
| `vecinita-vllm-secrets` | Modal Secret | `HF_TOKEN`, `VLLM_API_KEY` |

### Volume Strategy

- Volume `vecinita-vllm-models` is created with `create_if_missing=True`
- Model weights are downloaded once via `download_model` function and persisted
- vLLM reads weights from the volume at container startup (`--model /models/<model_id>`)
- `models_volume.commit()` called after download to persist changes
- Multiple models can coexist on the same volume (one loaded per deployment)

## GPU Selection Strategy

| Model Size | Recommended GPU | Modal Spec | Estimated VRAM Usage |
|------------|----------------|------------|---------------------|
| ≤4B params | A10G | `modal.gpu.A10G()` | ~8–12 GB |
| 4–8B params | A100 40GB | `modal.gpu.A100(size="40GB")` | ~16–24 GB |
| 8–13B params | A100 80GB | `modal.gpu.A100(size="80GB")` | ~24–40 GB |
| 13B+ params | H100 80GB | `modal.gpu.H100()` | 40+ GB |

The GPU is configured in `app.py` and can be changed per environment via settings:

```python
GPU_MAP = {
    "a10g": modal.gpu.A10G(),
    "a100-40": modal.gpu.A100(count=1, size="40GB"),
    "a100-80": modal.gpu.A100(count=1, size="80GB"),
    "h100": modal.gpu.H100(),
}
```

## Model Loading Workflow

```
1. CI pipeline (or manual): modal run app.py::download_model --model-id google/gemma-3-4b-it
   └─ Downloads weights from HF Hub → /models/google/gemma-3-4b-it/
   └─ Commits to vecinita-vllm-models volume

2. modal deploy app.py
   └─ Builds image with vLLM + CUDA
   └─ Registers serve() web endpoint and chat_completion() function

3. First request arrives:
   └─ Modal spins up GPU container
   └─ Mounts vecinita-vllm-models volume at /models
   └─ vLLM loads weights from /models/google/gemma-3-4b-it into GPU memory
   └─ Engine becomes ready (~15-30s)
   └─ Request processed
```

## Invocation Patterns

### REST API (Primary — Agent)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://<workspace>--vecinita-vllm-inference-serve.modal.run/v1",
    api_key="<VLLM_API_KEY>",
)
response = client.chat.completions.create(
    model="google/gemma-3-4b-it",
    messages=[{"role": "user", "content": "..."}],
)
```

### Modal SDK (Secondary — Gateway)

```python
import modal

fn = modal.Function.from_name("vecinita-vllm-inference", "chat_completion")
result = fn.remote(
    model="google/gemma-3-4b-it",
    messages=[{"role": "user", "content": "..."}],
    temperature=0.7,
)
```

## Environment Variables

| Variable | Source | Required | Default |
|----------|--------|----------|---------|
| `MODAL_TOKEN_ID` | CI secret / local env | yes | — |
| `MODAL_TOKEN_SECRET` | CI secret / local env | yes | — |
| `HF_TOKEN` | Modal Secret | conditional (gated models) | — |
| `VLLM_API_KEY` | Modal Secret | recommended | — |
| `MODEL_ID` | Environment / config | yes | `google/gemma-3-4b-it` |
| `GPU_TYPE` | Environment / config | no | `a100-40` |
| `MODELS_PATH` | Config | no | `/models` |
| `SCALEDOWN_WINDOW` | Config | no | `300` |
| `TIMEOUT` | Config | no | `600` |
| `MAX_CONCURRENT` | Config | no | `10` |

## Container Lifecycle

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Scale from 0 │ ──► │ Mount volume │ ──► │ Load model  │ ──► │ Serve traffic│
│ (cold start) │     │ + start vLLM │     │ into GPU    │     │ (warm)       │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                     │
                                                         scaledown_window
                                                         no requests
                                                                     │
                                                              ┌──────▼───────┐
                                                              │ Scale to 0   │
                                                              │ (container   │
                                                              │  terminated) │
                                                              └──────────────┘
```

## Cross-reference

- [Modal Landscape](../modal/current-landscape.md)

## Related Documents

- [Integration Points](03-integration-points.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
