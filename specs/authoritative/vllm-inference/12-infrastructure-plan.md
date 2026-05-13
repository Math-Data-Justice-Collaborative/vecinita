# Infrastructure Plan: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service runs exclusively on Modal serverless GPU infrastructure. There is no Dockerfile or Render deployment — the Modal SDK defines the container image, GPU allocation, and scaling behavior declaratively in Python.

## Build

| Property | Value |
|----------|-------|
| Build system | Modal Image (declarative, no Dockerfile) |
| Base image | `modal.Image.debian_slim(python_version="3.11")` |
| GPU runtime | CUDA 12.1+ (via Modal GPU image) |
| Key packages | vllm, torch, transformers, huggingface-hub |
| Image size | ~10–15 GB (PyTorch + CUDA + vLLM + model tokenizer) |
| Build cache | Modal caches image layers; rebuilds only on dependency changes |

### Modal Image Definition (target)

```python
vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm>=0.8.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
    )
    .add_local_dir("apps/vllm-inference/src", remote_path="/root/vllm_inference")
)
```

## Deployment

| Property | Value |
|----------|-------|
| Platform | **Modal** (serverless GPU) |
| Service type | GPU function + ASGI web endpoint |
| Deploy command | `modal deploy apps/vllm-inference/app.py` |
| Dev serve | `modal serve apps/vllm-inference/app.py` |
| Region | Modal auto-selects (US regions, GPU-dependent) |
| Auto-deploy | CI on push to `main` (after lint + test pass) |

## GPU Allocation

| Configuration | Value |
|---------------|-------|
| Production GPU | `modal.gpu.A100(count=1, size="40GB")` (recommended) |
| Development GPU | `modal.gpu.A10G()` (for ≤4B models) |
| High-throughput | `modal.gpu.H100()` (for maximum tokens/sec) |
| CPU allocation | Default (Modal auto-allocates) |
| Memory | GPU-dependent (40–80 GB GPU + system RAM) |

## Scaling

| Property | Value |
|----------|-------|
| Min instances | 0 (scales to zero when idle) |
| Max instances | Configurable via `max_containers` (default: Modal limit) |
| Scaledown window | Configurable (recommended: 300–600s to avoid cold starts) |
| Scale-up trigger | Incoming request when no warm containers available |
| Cold start time | ~15–30s (model loading from volume into GPU memory) |
| Warm request latency | ~1–10s (depends on prompt length and max_tokens) |

### Cold Start Optimization

| Strategy | Implemented | Notes |
|----------|-------------|-------|
| Persistent model volume | Yes | Weights cached on `vecinita-vllm-models`; no download on cold start |
| Extended scaledown window | Yes | Keep containers warm for 5–10 min after last request |
| Model weight snapshots | Planned | Modal CPU+GPU memory snapshots can reduce cold start to ~5s |
| Preloaded containers | Planned | `min_containers=1` for always-warm (increases cost) |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | stdout (structured) | vLLM logs to stdout; Modal captures automatically |
| Request metrics | vLLM built-in `/metrics` (Prometheus) | tokens/s, queue depth, cache utilization |
| Health check | `GET /health` | Returns 200 when engine is ready |
| GPU utilization | Modal dashboard | Per-container GPU/memory metrics |
| Error alerting | Modal webhook (planned) | Notify on container crash or OOM |
| Cost tracking | Modal billing dashboard | Per-function GPU-seconds |

## Estimated Costs

| Profile | Requests/day | GPU | Est. Monthly Cost |
|---------|-------------|-----|-------------------|
| Development | 10–20 | A10G | $5–15 |
| Staging | 50–100 | A100 40GB | $20–50 |
| Production | 100–500 | A100 40GB | $50–200 |
| High traffic | 500+ | H100 | $200+ |

Based on Modal's ~$0.001–0.004/s GPU pricing and ~5–15s per inference request. Costs dominated by cold start GPU time when traffic is sparse.

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md) (N/A)
- [Modal Integration Plan](13-modal-integration-plan.md)
