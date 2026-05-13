# Vecinita Agent — Technical Decisions

> Auto-generated: 2026-05-12

## Overview

Key architectural and technical decisions for the agent service, including both resolved decisions and pending choices requiring attention during the `apis/agent/` → `apps/agent/` restructuring.

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | RAG pipeline style | Deterministic (hand-orchestrated) | Autonomous LangGraph agent loop | 2025 | moderate |
| TD-002 | LLM provider routing | Single Ollama-compatible endpoint | Multi-provider (OpenAI, Groq, DeepSeek) | 2025 | easy |
| TD-003 | Embedding strategy | External HTTP service (384-dim all-MiniLM-L6-v2) | Local sentence-transformers in-process | 2025 | easy |
| TD-004 | Vector database | PostgreSQL + pgvector (direct psycopg2) | Dedicated vector DB (Pinecone, Weaviate, Qdrant) | 2025 | hard |
| TD-005 | Guardrails approach | Local regex + optional Guardrails AI Hub | Custom ML classifiers, LLM-based moderation | 2025 | easy |
| TD-006 | Streaming protocol | Server-Sent Events (SSE) | WebSocket, HTTP/2 server push | 2025 | moderate |
| TD-007 | Bilingual support | Auto-detection with `langdetect` + Spanish heuristics | User-selected language only | 2025 | easy |

### TD-001: Deterministic RAG Pipeline Over Autonomous Agent

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2025 |
| Context | LangGraph StateGraph and ToolNode are imported and configured in `main.py`, but the production `/ask` and `/ask-stream` endpoints use a hand-orchestrated flow: classify intent → invoke db_search → build prompt → call LLM → return. |
| Decision | Use deterministic RAG with explicit tool invocation rather than letting the LLM decide which tools to call |
| Rationale | Predictable latency, consistent behavior, easier debugging. Autonomous agent loops risk unbounded tool calls and hallucinated tool use. |
| Consequences | Cannot dynamically chain tools (e.g., search → rewrite → search again) without explicit code paths. Less flexible for complex multi-step queries. |
| Alternatives considered | Autonomous LangGraph agent loop — rejected due to latency unpredictability and hallucination risk with small models |

### TD-002: Single Ollama-Compatible LLM Endpoint

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2025 |
| Context | The codebase retains import stubs for OpenAI, Groq, and DeepSeek providers, but `LocalLLMClientManager` enforces `provider == "ollama"` and rejects all others. |
| Decision | Route all LLM traffic through a single Ollama-compatible endpoint (Modal vLLM in production, local Ollama in dev) |
| Rationale | Simplifies provider management; Modal vLLM exposes an Ollama-compatible API, unifying the interface. |
| Consequences | Cannot fail over to cloud LLM providers (OpenAI, Groq) if Modal is down. Dead code for other providers adds confusion. |
| Alternatives considered | Multi-provider with failover — rejected to reduce complexity and API key management |

### TD-003: External Embedding Service

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2025 |
| Context | The Dockerfile explicitly avoids installing embedding models ("zero local embedding models") to keep the image small for Render's starter plan. |
| Decision | Delegate all embedding to an external HTTP service; maintain HuggingFace local fallback as emergency backup |
| Rationale | Saves ~50MB+ memory on the agent container; allows embedding service to scale independently |
| Consequences | Network dependency for every query; embedding service outage blocks retrieval |
| Alternatives considered | In-process sentence-transformers — rejected due to memory constraints on Render starter plan |

### TD-004: PostgreSQL + pgvector Over Dedicated Vector DB

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2025 |
| Context | The project uses the shared `vecinita-postgres` database for all services. Vector search is done via raw psycopg2 SQL with `<=>` cosine distance operator. |
| Decision | Use pgvector extension in the shared PostgreSQL instance rather than a dedicated vector database |
| Rationale | Fewer infrastructure components; transactional consistency with other data; Render provides managed PostgreSQL. |
| Consequences | Limited to pgvector's performance characteristics; no built-in ANN indexing optimization (IVFFlat/HNSW must be explicitly created); shared database contention |
| Alternatives considered | Pinecone, Weaviate, Qdrant — rejected to minimize infrastructure and cost |

### TD-005: Hybrid Guardrails (Local Regex + Optional Hub)

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2025 |
| Context | Guardrails AI Hub SDK is optionally installed; local regex patterns are always active. On Render, local guardrails can be disabled via `RENDER_DISABLE_LOCAL_GUARDRAILS` when upstream enforcement is expected. |
| Decision | Layer local regex checks (always available) with optional Hub SDK validators |
| Rationale | Ensures baseline safety without external dependencies; Hub adds ML-based PII detection when available |
| Consequences | Local regex is less accurate than ML-based detection; dual system adds complexity |
| Alternatives considered | Hub-only — rejected due to SDK installation reliability issues; LLM-based moderation — rejected due to latency |

### TD-006: SSE for Streaming

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2025 |
| Context | The `/ask-stream` endpoint uses `StreamingResponse` with `text/event-stream` media type. |
| Decision | Use Server-Sent Events for real-time progress and answer streaming |
| Rationale | SSE is simpler than WebSocket for unidirectional streaming; native browser support; works through standard HTTP proxies |
| Consequences | Unidirectional only (server → client); cannot receive mid-stream user input; connection may timeout on slow LLM responses |
| Alternatives considered | WebSocket — rejected as overkill for one-way streaming |

### TD-007: Auto-Detection Bilingual Support

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2025 |
| Context | The agent serves a Providence, RI community with significant Spanish-speaking population. |
| Decision | Auto-detect language via `langdetect` with Spanish character/marker heuristics; respond in detected language |
| Rationale | Reduces friction for Spanish speakers; heuristics handle mixed-language edge cases better than pure ML detection |
| Consequences | Detection errors possible with very short queries; only en/es supported |
| Alternatives considered | User-selected language only — rejected as too much friction for community members |

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | pgvector index strategy | IVFFlat, HNSW, none | Query performance at scale | Degrading search latency as corpus grows | HNSW |
| PTD-002 | Conversation memory persistence | In-process MemorySaver, PostgreSQL, Redis | Multi-turn quality, stateless scaling | No conversation continuity across restarts | PostgreSQL |
| PTD-003 | Dead provider code cleanup | Remove, feature-flag, keep | Maintainability | Growing confusion about supported providers | Remove |
| PTD-004 | Autonomous agent loop activation | Enable LangGraph loop, keep deterministic | Flexibility vs. predictability | No impact if deterministic path is sufficient | Keep deterministic; revisit with larger models |

### PTD-001: pgvector Index Strategy

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | No `CREATE INDEX ... USING hnsw` or `ivfflat` found in codebase; vector search uses sequential scan via `<=>` operator |
| Impact | Query latency increases linearly with corpus size; currently manageable with small corpus |
| Decision deadline | Before corpus exceeds ~100K chunks |

**Options researched:**

**Option A: HNSW index**
- How it works: Create approximate nearest neighbor index using HNSW algorithm
- Pros: Fast recall, good accuracy, no training required
- Cons: Higher memory usage, slower builds
- Effort: S
- Reversibility: easy
- Ecosystem fit: pgvector natively supports HNSW

**Option B: IVFFlat index**
- How it works: Create inverted file index with flat quantization
- Pros: Lower memory usage, faster builds
- Cons: Requires periodic retraining; lower recall than HNSW
- Effort: S
- Reversibility: easy
- Ecosystem fit: pgvector natively supports IVFFlat

**Recommendation:** HNSW — better recall without training overhead, standard recommendation for pgvector workloads.
**Risk of continued deferral:** Search latency will degrade as the document corpus grows, impacting user experience.

### PTD-002: Conversation Memory Persistence

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | `MemorySaver` from `langgraph.checkpoint.memory` is imported but the deterministic path uses `context_answer` parameter for follow-ups rather than persistent memory. Thread IDs are passed but not used for retrieval of prior conversation state. |
| Impact | No true multi-turn conversations; follow-ups require the frontend to pass prior answer context |
| Decision deadline | Before implementing multi-turn conversation features |

**Options researched:**

**Option A: PostgreSQL-backed checkpointer**
- How it works: Use `langgraph-checkpoint-postgres` to persist conversation state in the existing database
- Pros: Uses existing infrastructure; transactional; survives restarts
- Cons: Additional table; slightly higher latency per turn
- Effort: M
- Reversibility: easy

**Option B: Redis-backed checkpointer**
- How it works: Use Redis for fast conversation state storage with TTL
- Pros: Very fast reads/writes; natural TTL expiry
- Cons: New infrastructure dependency; data loss on eviction
- Effort: L (new infra)
- Reversibility: moderate

**Recommendation:** PostgreSQL — avoids new infrastructure; conversation state naturally belongs with the rest of the data.
**Risk of continued deferral:** Users cannot have true multi-turn conversations; frontend must manage context, limiting conversation depth.

### PTD-003: Dead Provider Code Cleanup

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | Import stubs for `ChatGroq`, `ChatOpenAI`, `GROQ_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_*` exist in `main.py` and `client_manager.py` but `LocalLLMClientManager` rejects all non-ollama providers. Dead env vars (`GROQ_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_*`) are declared in `render.yaml`. |
| Impact | Maintainability; new developers may think multiple providers are supported |
| Decision deadline | During `apis/agent/` → `apps/agent/` restructuring |

**Recommendation:** Remove dead provider code and env var declarations during restructuring.
**Risk of continued deferral:** Confusion, larger attack surface from unused API key env vars.

### PTD-004: Autonomous Agent Loop Activation

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | LangGraph `StateGraph`, `ToolNode`, `MemorySaver` are imported and a graph is constructed in `main.py`, but all production endpoints bypass it in favor of the deterministic path. |
| Impact | Flexibility — autonomous loop could chain tools (search → rewrite → re-search) for complex queries |
| Decision deadline | Not urgent; revisit when using larger models that reliably follow tool-calling instructions |

**Recommendation:** Keep deterministic path as default; revisit autonomous loop when model quality supports reliable multi-step tool calling.
**Risk of continued deferral:** Low risk; deterministic path is more predictable and debuggable.

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
