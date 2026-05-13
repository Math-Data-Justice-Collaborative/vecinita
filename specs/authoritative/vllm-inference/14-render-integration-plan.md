# Render Integration Plan: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

**N/A — this service runs on Modal, not Render.**

The vllm-inference service requires GPU compute for LLM inference, which is provided by Modal's serverless GPU infrastructure. Render does not offer GPU instances, making it unsuitable for this workload.

## Why Not Render

| Concern | Detail |
|---------|--------|
| GPU availability | Render does not provide GPU instances; vLLM requires CUDA-capable GPUs |
| Cost model | GPU inference is bursty (10–100 req/day); Modal's per-second billing is more cost-effective than a persistent Render instance |
| Consistency | All existing Modal apps (embedding, scraper) use the same deployment model |

## Render Interaction (Indirect)

While the service itself does not deploy on Render, it is consumed by Render-hosted services:

| Render Service | How It Calls vLLM Inference |
|---------------|---------------------------|
| `vecinita-agent` | OpenAI-compatible REST API via LlamaIndex `llama-index-llms-vllm` |
| `vecinita-gateway` | Modal SDK `Function.from_name().remote()` |

These Render services need `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` environment variables to invoke Modal functions.

## Cross-reference

- [Render Landscape](../render/current-landscape.md)
- [Modal Integration Plan](13-modal-integration-plan.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
