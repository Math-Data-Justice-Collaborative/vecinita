# Technical Decisions: Embedding Worker
> Auto-generated: 2026-05-12

## Decided

### ADR-001: fastembed over sentence-transformers

| Attribute | Value |
|-----------|-------|
| Status | **Decided** |
| Date | 2025 |
| Context | Need a text embedding library for CPU-based inference on Modal |

**Decision:** Use `fastembed` instead of `sentence-transformers`.

**Rationale:**

| Factor | fastembed | sentence-transformers |
|--------|----------|----------------------|
| Runtime | ONNX Runtime (CPU-optimized) | PyTorch (GPU-oriented) |
| Image size | ~200MB (debian_slim + fastembed) | ~2GB+ (PyTorch + transformers) |
| Cold start | ~5-10s | ~30-60s |
| GPU required | No | Recommended |
| API complexity | Simple (`TextEmbedding.embed()`) | More setup required |
| Modal cost | Default CPU tier | Would benefit from GPU tier |

**Consequences:**
- Dramatically smaller container image → faster cold starts
- CPU-only inference is sufficient for 50-500 invocations/day
- Limited to models supported by fastembed (ONNX format)
- No GPU cost overhead

---

### ADR-002: BAAI/bge-small-en-v1.5 as Default Model

| Attribute | Value |
|-----------|-------|
| Status | **Decided** |
| Date | 2025 |
| Context | Need to choose a default embedding model for civic/community text |

**Decision:** Use `BAAI/bge-small-en-v1.5` as the default model.

**Rationale:**

| Factor | bge-small-en-v1.5 | all-MiniLM-L6-v2 | bge-large-en-v1.5 |
|--------|-------------------|-------------------|-------------------|
| Dimensions | 384 | 384 | 1024 |
| MTEB score | Strong | Good | Best |
| Size | ~33M params | ~22M params | ~335M params |
| Inference speed | Fast | Fastest | Slower |
| Memory | ~100MB | ~80MB | ~1.2GB |

**Consequences:**
- Good balance of quality and speed for civic information retrieval
- 384 dimensions keeps vector storage manageable in PostgreSQL
- Model is well-supported by fastembed
- The `model` parameter in schemas allows future model override without code changes

---

### ADR-003: Modal Function Invocation over HTTP

| Attribute | Value |
|-----------|-------|
| Status | **Decided** |
| Date | 2025 |
| Context | Gateway needs to call embedding functions — HTTP vs Modal SDK |

**Decision:** Use `modal.Function.from_name().remote()` instead of HTTP calls to `*.modal.run` endpoints.

**Rationale:**

| Factor | Modal SDK (`.remote()`) | HTTP (`*.modal.run`) |
|--------|----------------------|---------------------|
| Serialization | Native Python (Modal handles) | JSON over HTTP |
| Auth | Modal token pair (SDK-level) | Additional HTTP auth layer |
| Latency | Lower (no HTTP overhead) | Higher (HTTP round-trip) |
| Error handling | Python exceptions | HTTP status codes |
| Gateway complexity | Direct function call | HTTP client setup |

**Consequences:**
- Simpler gateway code (no HTTP client, no URL management)
- Requires Modal SDK + tokens in gateway environment
- `MODAL_FUNCTION_INVOCATION` env var controls the mode (`auto`/`on`/`off`)
- Gateway has LRU-cached function lookups for performance

---

### ADR-004: Volume-Based Model Caching

| Attribute | Value |
|-----------|-------|
| Status | **Decided** |
| Date | 2025 |
| Context | Model weights need to persist across function invocations |

**Decision:** Use a Modal Volume (`embedding-models`) to cache model files.

**Rationale:**
- Modal containers are ephemeral — model downloads would repeat on every cold start without persistence
- Volume is created automatically (`create_if_missing=True`)
- fastembed accepts `cache_dir` parameter, pointed to Volume mount `/models`
- Eliminates ~30s model download on each cold start

**Consequences:**
- Cold start reduced from ~40s (download + load) to ~5-10s (load from Volume)
- Volume persists until manually deleted
- Volume is shared across all container instances (read-safe for inference)

---

### ADR-005: Per-Invocation Model Loading

| Attribute | Value |
|-----------|-------|
| Status | **Decided** |
| Date | 2025 |
| Context | Should the model be loaded once (container-level) or per-invocation? |

**Decision:** Load model per invocation via `load_runtime_model()`.

**Rationale:**
- Simple implementation — no container lifecycle hooks needed
- Warmup query (`model.embed(["warmup"])`) ensures model weights are in memory
- With fastembed + Volume cache, load time is acceptable (~1-2s)
- Avoids complexity of `@modal.enter()` / `@modal.cls` patterns

**Consequences:**
- Each invocation pays ~1-2s model load cost
- Future optimization: move to `@modal.cls` with `@modal.enter()` for container-level model loading if latency becomes critical
- Acceptable for current volume (50-500 invocations/day)

---

### ADR-006: Dual Field Names in Schemas

| Attribute | Value |
|-----------|-------|
| Status | **Decided** |
| Date | 2025 |
| Context | Gateway and legacy clients use different field names (`query`/`text`, `queries`/`texts`) |

**Decision:** Accept both field names in request schemas with `model_validator`.

**Rationale:**
- `query`/`queries` is the preferred field name (matches gateway conventions)
- `text`/`texts` is accepted for backward compatibility with older embedding service API
- Normalization happens at the schema level, service layer sees only canonical fields

**Consequences:**
- `POST /embed-batch` path alias also exists for gateway compat
- No migration burden on existing callers
- Slight schema complexity (two optional fields with validation)

## Pending

### PD-001: Container-Level Model Loading

| Attribute | Value |
|-----------|-------|
| Status | **Pending** |
| Context | Current per-invocation loading adds ~1-2s overhead |
| Options | `@modal.cls` with `@modal.enter()`, or `@modal.build()` for image-baked model |
| Trigger | When latency budget tightens or invocation volume increases significantly |

### PD-002: GPU Acceleration

| Attribute | Value |
|-----------|-------|
| Status | **Pending** |
| Context | Currently runs on default CPU, sufficient for current volume |
| Options | Add `gpu="T4"` to function decorator, switch to GPU-optimized model |
| Trigger | When batch sizes grow or latency requirements tighten |

See: [Dependencies](09-dependencies.md) | [Infrastructure Plan](12-infrastructure-plan.md) | [Modal Integration Plan](13-modal-integration-plan.md)
