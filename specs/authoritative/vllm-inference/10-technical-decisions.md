# Technical Decisions: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

Key architectural and technical decisions for the vllm-inference service, including both resolved decisions informing the rewrite from Ollama to vLLM, and pending choices requiring resolution during implementation.

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Inference engine | vLLM | Ollama, TGI, llama.cpp, TensorRT-LLM | 2026-05-12 | moderate |
| TD-002 | API surface | OpenAI-compatible (vLLM native) | Custom Ollama-style API, gRPC | 2026-05-12 | easy |
| TD-003 | Deployment platform | Modal serverless GPU | Self-managed GPU, Replicate, RunPod, AWS SageMaker | 2026-05-12 | hard |
| TD-004 | Model per deployment | Single model per deployment | Multi-model registry (previous approach) | 2026-05-12 | easy |
| TD-005 | Agent integration client | LlamaIndex `llama-index-llms-vllm` | Direct OpenAI SDK, custom HTTP client | 2026-05-12 | easy |

### TD-001: Inference Engine — vLLM

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2026-05-12 |
| Context | The previous implementation used Ollama (wrapping llama.cpp) on CPU-only Modal containers. This limited throughput and prevented GPU acceleration. The rewrite needs GPU-optimized inference with an OpenAI-compatible API for LlamaIndex integration. |
| Decision | Use vLLM as the inference engine |
| Rationale | vLLM provides PagedAttention for efficient GPU memory management, continuous batching for high throughput (~30K input tokens/s on H100), native OpenAI-compatible API server, and broad model support. It is the de facto standard for self-hosted LLM inference on GPU. |
| Alternatives considered | **Ollama** — simple but CPU-focused, no continuous batching, custom API. **TGI** (Hugging Face) — good GPU support but less community adoption than vLLM, weaker OpenAI compatibility. **llama.cpp** — excellent for CPU/edge but vLLM outperforms on GPU. **TensorRT-LLM** — highest raw performance but complex setup, NVIDIA-only, less portable. |
| Consequences | Requires GPU containers (cost increase vs CPU-only). Adds PyTorch/CUDA dependency (~10GB image). Cold starts are longer due to model loading. |
| Reversibility | moderate — API is OpenAI-compatible, so swapping engines only requires changing the server, not the clients |

### TD-002: OpenAI-Compatible API Surface

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2026-05-12 |
| Context | The agent service uses LlamaIndex which supports OpenAI-compatible endpoints natively via `llama-index-llms-vllm`. The previous Ollama API required a custom integration layer. |
| Decision | Expose vLLM's native OpenAI-compatible API (`/v1/chat/completions`, `/v1/completions`, `/v1/models`) |
| Rationale | Zero custom API code needed. LlamaIndex, OpenAI SDK, and any OpenAI-compatible client work out of the box. Standard API contract reduces integration bugs. |
| Alternatives considered | **Custom Ollama-style API** — would require maintaining custom routes and schema translation. **gRPC** — higher performance but no LlamaIndex support, more complex clients. |
| Consequences | Locked to OpenAI API semantics. vLLM-specific features (e.g., `best_of`, prompt caching) available via extra parameters but not guaranteed stable across versions. |
| Reversibility | easy — any OpenAI-compatible server can be swapped in |

### TD-003: Modal Serverless GPU Deployment

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2026-05-12 |
| Context | Vecinita already uses Modal for embedding and scraping workloads. The team has Modal expertise, CI/CD integration, and billing in place. GPU inference is bursty (10–100 requests/day), making serverless cost-effective vs. reserved instances. |
| Decision | Deploy on Modal with serverless GPU containers (H100/A100) |
| Rationale | Pay-per-use GPU pricing (~$0.001/request at current volumes). Existing Modal infrastructure and team familiarity. Auto-scaling to zero when idle. Persistent volumes for model weight caching. |
| Alternatives considered | **Self-managed GPU** — lowest per-token cost at scale but requires ops investment; premature for current volume. **Replicate/RunPod** — viable but less integrated with existing Modal tooling. **AWS SageMaker** — enterprise-grade but expensive and complex for a small team. |
| Consequences | Cold start latency (15–60s) for first request after scale-to-zero. GPU costs are per-second. Vendor lock-in to Modal. |
| Reversibility | hard — deep integration with Modal SDK, volumes, and CI |

### TD-004: Single Model Per Deployment

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2026-05-12 |
| Context | The previous Ollama implementation supported 9 models via a registry, but only 1 was used in production (gemma3). vLLM loads a single model into GPU memory at startup. |
| Decision | Deploy a single model per Modal app instance. Model swaps require redeployment. |
| Rationale | Simpler configuration. Full GPU memory available for one model (larger context, faster inference). No model-switching latency. vLLM's architecture assumes single-model serving. |
| Alternatives considered | **Multi-model with model switching** — possible via multiple vLLM instances but doubles GPU cost and adds complexity. **LoRA adapter loading** — vLLM supports runtime LoRA swap but Vecinita doesn't use fine-tuned models yet. |
| Consequences | Changing models requires redeploy. Cannot A/B test models without parallel deployments. |
| Reversibility | easy — can add a second Modal function for a second model |

### TD-005: LlamaIndex vLLM Integration

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2026-05-12 |
| Context | The agent service uses LlamaIndex for RAG orchestration. LlamaIndex provides `llama-index-llms-vllm` which wraps OpenAI-compatible endpoints. |
| Decision | Agent connects via `llama-index-llms-vllm` with the vLLM Modal URL as `api_url` |
| Rationale | Drop-in replacement — only the URL and model name change in agent config. Full streaming support. Automatic retry and timeout handling by LlamaIndex. |
| Alternatives considered | **Direct OpenAI SDK** — works but bypasses LlamaIndex's prompt management. **Custom HTTP client** — unnecessary given LlamaIndex support. |
| Consequences | Agent depends on `llama-index-llms-vllm` package. Model name must match exactly between vLLM `--model` flag and agent config. |
| Reversibility | easy — can swap to any OpenAI-compatible LLM integration |

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | Default model selection | Gemma 3 4B, Llama 3.1 8B, Llama 3.2 3B | Inference quality, cost, latency | Low — can swap post-deploy | Gemma 3 4B |
| PTD-002 | GPU tier selection | H100 80GB, A100 40GB, A100 80GB, A10G | Cost vs performance | Medium — affects budget | A100 40GB for ≤8B models |
| PTD-003 | Container concurrency | 1, 10, 25, 50 concurrent requests | Throughput vs memory | Low — tunable | 10 (conservative start) |
| PTD-004 | API key enforcement | No auth, static API key, Modal proxy auth | Security | Medium — open endpoint risk | Static API key via `--api-key` |

### PTD-001: Default Model Selection

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | Previous implementation used `gemma3` as default. Rewrite needs to select a HF Hub model compatible with vLLM. |
| Impact | Inference quality for civic information Q&A, GPU memory requirements, response latency |
| Decision deadline | Before first deployment |

**Options researched:**

**Option A: `google/gemma-3-4b-it`**
- Pros: Continuity with previous Gemma 3 default. 4B parameters fits A10G. Good multilingual support (Spanish/English for Vecinita's target community).
- Cons: Smaller model may produce less nuanced responses than 8B alternatives.
- Effort: S
- Ecosystem fit: Direct successor to previous `gemma3` default

**Option B: `meta-llama/Llama-3.1-8B-Instruct`**
- Pros: Strong instruction following. Large community. Well-tested with vLLM.
- Cons: 8B requires A100-40GB minimum. Llama license requires acceptance.
- Effort: S
- Ecosystem fit: Widely used in RAG systems

**Option C: `meta-llama/Llama-3.2-3B-Instruct`**
- Pros: Smallest, fastest, cheapest. Fits A10G easily.
- Cons: Quality trade-off at 3B parameters for civic information accuracy.
- Effort: S
- Ecosystem fit: Good for cost-sensitive deployments

**Recommendation:** Option A (`google/gemma-3-4b-it`) — balances quality, cost, and continuity with the existing deployment. Multilingual support is valuable for Vecinita's Spanish-speaking community.

**Risk of continued deferral:** Low — model can be swapped after initial deployment by changing config and redeploying.

### PTD-002: GPU Tier Selection

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | Current implementation runs on CPU-only containers. vLLM requires GPU. GPU selection affects both cost and performance. |
| Impact | Monthly GPU cost, inference latency, maximum model size |
| Decision deadline | Before first deployment |

**Options researched:**

**Option A: A100 40GB**
- Pros: Supports models up to ~13B parameters. Good price/performance ratio on Modal. ~$0.001/s.
- Cons: Cannot run 70B+ models.
- Effort: S
- Ecosystem fit: Standard choice for 7–13B models on Modal

**Option B: H100 80GB**
- Pros: Highest throughput (~30K tokens/s). Supports all model sizes. Future-proof.
- Cons: ~2x cost of A100. Overkill for ≤8B models.
- Effort: S
- Ecosystem fit: Best for production throughput needs

**Option C: A10G**
- Pros: Cheapest GPU option on Modal. Sufficient for ≤4B models.
- Cons: Limited to small models. Lower throughput.
- Effort: S
- Ecosystem fit: Good for development/staging

**Recommendation:** Option A (A100 40GB) for production, Option C (A10G) for development — A100 40GB handles all target models (≤8B) with good throughput at reasonable cost.

**Risk of continued deferral:** Medium — wrong GPU choice wastes budget or limits model options.

### PTD-003: Container Concurrency

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | vLLM supports continuous batching, allowing multiple concurrent requests per container. The `allow_concurrent_inputs` Modal parameter controls this. |
| Impact | Throughput, GPU memory pressure, tail latency |
| Decision deadline | Before production traffic |

**Recommendation:** Start with `allow_concurrent_inputs=10`, monitor GPU memory utilization and p99 latency, increase if GPU utilization is low.

**Risk of continued deferral:** Low — tunable without redeploy via config change.

### PTD-004: API Key Enforcement

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | vLLM supports `--api-key` flag for basic auth. Previous Ollama implementation had no auth. The Modal URL is semi-public. |
| Impact | Security — open endpoint could be abused for free GPU inference |
| Decision deadline | Before production deployment |

**Recommendation:** Set `--api-key` to a static secret stored in Modal secrets, configure agent and gateway to pass the key. Minimal effort, prevents unauthorized use.

**Risk of continued deferral:** Medium — open GPU endpoint is a cost and abuse risk.

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
