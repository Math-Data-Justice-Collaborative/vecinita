# Feature Specification: vLLM + LlamaIndex RAG integration

**Spec ID**: 022  
**Feature Branch**: `022-vllm-llamaindex-integration`  
**Created**: 2026-05-13  
**Status**: Draft  
**Phase**: 3 (Integrate vLLM + LlamaIndex) — per `specs/monorepo-decomposition/09-migration-sequence.md`  
**Blocks**: None (can proceed in parallel with Phases 4–6 after completion)  
**Dependencies**: Spec 021 (agent must be extracted before RAG pipeline rewrite)  
**Risk**: Medium — new stack integration, need to validate inference quality  
**Effort**: L (4–5 days)

## Overview

Replace the current Modal `model-modal` and `embedding-modal` services with a vLLM + LlamaIndex stack. This introduces three Modal workers and rewrites the agent's inference pipeline:

1. **vLLM Inference** (`apps/vllm-inference/`) — A Modal app running vLLM with an OpenAI-compatible API, serving LLM inference on serverless GPU (H100/A100).
2. **Embedding Worker** (`apps/embedding-worker/`) — A Modal app running LlamaIndex's embedding pipeline for batch document embedding on GPU.
3. **Indexing Worker** (`apps/indexing-worker/`) — A Modal app for document indexing with four modes: single-doc, batch (via `spawn_map`), selective re-index, and full rebuild.

The agent (`apps/agent/`) is updated to use LlamaIndex as its RAG framework, connecting to vLLM's OpenAI-compatible endpoint via `llama-index-llms-vllm` for inference and to pgvector for vector search.

### Architecture After This Spec

```
chat-frontend → gateway → agent (LlamaIndex RAG)
                              ├── vLLM inference (Modal GPU) via OpenAI-compatible API
                              └── pgvector (PostgreSQL) for vector search

gateway ──Modal SDK──► embedding-worker (LlamaIndex embedding, Modal GPU)
gateway ──Modal SDK──► indexing-worker (LlamaIndex indexing, Modal GPU/CPU)
gateway ──Modal SDK──► scraper-worker (unchanged)
```

### What Gets Replaced

| Current Service | New Service | Change |
|----------------|------------|--------|
| `modal-apps/model-modal/` | `apps/vllm-inference/` | Full rewrite: custom inference → vLLM with OpenAI API |
| `modal-apps/embedding-modal/` | `apps/embedding-worker/` | Full rewrite: custom embedding → LlamaIndex embedding pipeline |
| (new) | `apps/indexing-worker/` | New service for document indexing pipeline |
| Agent's LLM calls | Agent's LlamaIndex pipeline | Rewrite: direct API calls → LlamaIndex with vLLM backend |

## User Scenarios & Testing

### User Story 1 — Self-hosted LLM inference via vLLM (Priority: P1)

**US-001**: As the agent service, I call vLLM's OpenAI-compatible API for LLM inference, so that the system runs its own model on GPU instead of depending on external LLM providers for primary inference.

**Why this priority**: Self-hosted inference via vLLM is the architectural foundation — the agent's RAG pipeline, the embedding worker, and the indexing worker all depend on reliable inference being available.

**Independent Test**: Deploy `apps/vllm-inference/` to Modal and call `POST /v1/chat/completions` with a test prompt — a coherent response is returned.

**Acceptance Scenarios**:

1. **Given** vLLM inference is deployed on Modal, **When** a client sends `POST /v1/chat/completions` with a valid chat message, **Then** vLLM returns a response conforming to the OpenAI chat completions schema.
2. **Given** vLLM inference is deployed, **When** a client sends `POST /v1/completions` with a text prompt, **Then** vLLM returns a text completion response.
3. **Given** vLLM inference is deployed, **When** the Modal function cold-starts, **Then** the model loads and serves the first request within the configured timeout (model-dependent, typically 60–120s for initial load).
4. **Given** vLLM inference is running, **When** multiple concurrent requests arrive, **Then** vLLM handles them via continuous batching without request failures.

---

### User Story 2 — LlamaIndex RAG pipeline in agent (Priority: P1)

**US-002**: As a developer, I use LlamaIndex in the agent service for RAG (retrieval-augmented generation), so that query processing, context retrieval, and response generation use a proven RAG framework.

**Why this priority**: LlamaIndex provides the orchestration layer that ties vLLM inference, vector search, and document retrieval into a coherent pipeline. Without it, the agent would need custom RAG logic.

**Independent Test**: Send a RAG query to the agent — it retrieves relevant documents from pgvector, sends them with the query to vLLM via LlamaIndex, and returns a grounded response with source citations.

**Acceptance Scenarios**:

1. **Given** the agent is running with LlamaIndex configured, **When** a query is sent to `POST /agent/query`, **Then** the agent retrieves context from pgvector, augments the prompt, sends it to vLLM, and returns a response with source references.
2. **Given** the agent uses `llama-index-llms-vllm`, **When** the agent processes a query, **Then** LlamaIndex connects to vLLM's OpenAI-compatible endpoint (not a third-party LLM provider) for inference.
3. **Given** the agent has conversation memory, **When** a follow-up query references prior context, **Then** LlamaIndex includes conversation history in the RAG pipeline.
4. **Given** vLLM is temporarily unavailable, **When** the agent receives a query, **Then** it returns a structured error indicating LLM backend unavailability — not an unhandled exception.

---

### User Story 3 — Document embedding via LlamaIndex (Priority: P1)

**US-003**: As the gateway, I trigger batch document embedding through the embedding-worker on Modal, so that new documents are embedded and stored in pgvector for RAG retrieval.

**Why this priority**: Documents must be embedded before they can be retrieved by the RAG pipeline. The embedding worker is the ingestion path that feeds the agent's vector search.

**Independent Test**: Trigger the embedding-worker with a set of test documents — embeddings are generated and stored in pgvector, and subsequent RAG queries can retrieve them.

**Acceptance Scenarios**:

1. **Given** the embedding-worker is deployed on Modal, **When** the gateway triggers it with a batch of documents, **Then** embeddings are generated using LlamaIndex's embedding pipeline and stored in pgvector.
2. **Given** documents have been embedded, **When** the agent performs a RAG query, **Then** the vector search returns relevant documents based on semantic similarity.
3. **Given** a document is updated, **When** the embedding-worker re-embeds it, **Then** the new embedding replaces the old one in pgvector.

---

### User Story 4 — Document indexing pipeline (Priority: P2)

**US-004**: As the gateway, I trigger document indexing through the indexing-worker on Modal with support for single-doc, batch, selective re-index, and full rebuild modes, so that the corpus stays current and can be rebuilt when the embedding model changes.

**Why this priority**: The indexing worker is the operational backbone for keeping the RAG corpus up-to-date. Full rebuild capability is essential for embedding model upgrades.

**Independent Test**: Trigger each indexing mode and verify documents are indexed (or re-indexed) in pgvector.

**Acceptance Scenarios**:

1. **Given** a single new document, **When** the gateway triggers indexing-worker in single-doc mode, **Then** the document is embedded and indexed in pgvector.
2. **Given** a batch of 100 documents, **When** the gateway triggers indexing-worker in batch mode (via `spawn_map`), **Then** all documents are embedded in parallel across Modal workers and indexed in pgvector.
3. **Given** 10 documents have changed since last indexing, **When** the gateway triggers selective re-index mode, **Then** only the changed documents are re-embedded and re-indexed.
4. **Given** a new embedding model is deployed, **When** the gateway triggers full rebuild mode, **Then** all documents in the corpus are re-embedded with the new model and the old embeddings are replaced.

---

### User Story 5 — End-to-end RAG validation (Priority: P1)

**US-005**: As a developer, I can run an end-to-end RAG test that validates the full pipeline from query to response, so that integration between all components is verified.

**Why this priority**: Individual component tests do not catch integration failures between vLLM, LlamaIndex, pgvector, and the agent. The end-to-end test is the definitive quality gate.

**Independent Test**: Ingest test documents → embed them → query the agent → verify the response is grounded in the ingested documents.

**Acceptance Scenarios**:

1. **Given** test documents are ingested and embedded, **When** a query relevant to those documents is sent to the agent via the gateway, **Then** the response references information from the test documents and includes source citations.
2. **Given** the full pipeline is running, **When** a query about a topic not in the corpus is sent, **Then** the agent either responds with a disclaimer about limited context or uses its general knowledge — it does not hallucinate corpus content.
3. **Given** the full pipeline is running, **When** 10 sequential queries are sent, **Then** all return within acceptable latency (< 30s for synchronous, first token < 5s for streaming) and none fail with unhandled errors.

---

### Edge Cases

- vLLM cold-start latency on Modal may exceed typical HTTP timeouts; the agent must handle this with retries or extended timeouts.
- Embedding model mismatch: if the embedding model used for indexing differs from the model used for query embedding, retrieval quality degrades silently. The system must enforce model consistency.
- Large documents may exceed vLLM's context window; the agent must chunk documents appropriately via LlamaIndex's node parsing.
- Modal `spawn_map` for batch indexing may encounter partial failures; the indexing-worker must track and report per-document success/failure.
- GPU memory limits on Modal may constrain model size; the vLLM config must match the provisioned GPU type (H100 80GB vs A100 40GB).
- LlamaIndex version compatibility with `llama-index-llms-vllm` must be verified — these are separate packages with potentially mismatched release cycles.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST create `apps/vllm-inference/main.py` as a Modal app that runs vLLM with an OpenAI-compatible API, exposing `/v1/completions` and `/v1/chat/completions` endpoints on serverless GPU (H100 or A100, configurable).
- **FR-002**: The system MUST create `apps/embedding-worker/main.py` as a Modal app that runs LlamaIndex's embedding pipeline for batch document embedding, storing results in pgvector.
- **FR-003**: The system MUST create `apps/indexing-worker/main.py` as a Modal app for document indexing, supporting four modes:
  - **Single-doc**: Index one document on demand.
  - **Batch**: Index multiple documents in parallel via Modal `spawn_map`.
  - **Selective re-index**: Re-index only documents that have changed since last indexing (based on content hash or timestamp).
  - **Full rebuild**: Re-embed and re-index the entire corpus (used when embedding model changes).
- **FR-004**: The system MUST update `apps/agent/` to use LlamaIndex as its RAG framework, replacing the current custom RAG logic. The agent's `pyproject.toml` MUST include `llama-index`, `llama-index-llms-vllm`, `llama-index-vector-stores-postgres` (or equivalent pgvector integration), and `llama-index-embeddings-huggingface` (or the chosen embedding provider).
- **FR-005**: The agent MUST connect to vLLM's OpenAI-compatible endpoint for inference via LlamaIndex's `llama-index-llms-vllm` integration. The vLLM endpoint URL MUST be configurable via environment variable (`VLLM_API_BASE` or similar).
- **FR-006**: LlamaIndex MUST handle embedding model management in the embedding-worker, including model loading, batching, and dimension configuration. The embedding model MUST be configurable via environment variable.
- **FR-007**: The indexing-worker MUST support all 4 modes defined in FR-003. Batch mode MUST use Modal's `spawn_map` for parallel execution. Selective re-index MUST compare content hashes to identify changed documents.
- **FR-008**: The existing Modal services (`modal-apps/model-modal/` and `modal-apps/embedding-modal/`) MUST be fully replaced by the new workers. No code from the old services may remain in active use after this spec.
- **FR-009**: The gateway's Modal SDK calls MUST be updated to invoke the new worker function names. Modal function references in `apps/gateway/src/services/modal/` MUST point to `apps/vllm-inference/`, `apps/embedding-worker/`, `apps/indexing-worker/`, and `apps/scraper-worker/`.
- **FR-010**: An end-to-end RAG pipeline test MUST exist that validates: query → gateway → agent → LlamaIndex (retrieval from pgvector + inference via vLLM) → response with sources. This test MUST be runnable in CI with appropriate Modal and database configuration.

### Key Entities

- **vLLM inference service**: A Modal app exposing OpenAI-compatible API for LLM inference on GPU.
- **Embedding worker**: A Modal app running LlamaIndex embedding pipeline for batch document embedding.
- **Indexing worker**: A Modal app managing the document indexing lifecycle (single, batch, selective, rebuild).
- **LlamaIndex RAG pipeline**: The agent's query processing framework — retrieval, augmentation, generation.
- **pgvector**: PostgreSQL extension for vector similarity search, storing document embeddings.
- **OpenAI-compatible API**: The REST API contract (`/v1/completions`, `/v1/chat/completions`) that vLLM exposes and LlamaIndex consumes.
- **Modal `spawn_map`**: Modal's parallel execution primitive for distributing work across multiple containers.

## Acceptance Scenarios

- **AS-001**: **Given** `apps/vllm-inference/main.py` exists, **When** it is deployed to Modal, **Then** `POST /v1/chat/completions` returns a valid chat completion response.
- **AS-002**: **Given** `apps/embedding-worker/main.py` exists, **When** it is invoked with a list of text documents, **Then** it returns embedding vectors and stores them in pgvector.
- **AS-003**: **Given** `apps/indexing-worker/main.py` exists, **When** it is invoked in single-doc mode with one document, **Then** that document is embedded and indexed.
- **AS-004**: **Given** the indexing-worker in batch mode, **When** invoked with 50 documents, **Then** Modal `spawn_map` processes them in parallel and all 50 are indexed.
- **AS-005**: **Given** 5 of 100 documents have changed, **When** selective re-index is triggered, **Then** only the 5 changed documents are re-embedded and re-indexed.
- **AS-006**: **Given** a new embedding model is configured, **When** full rebuild is triggered, **Then** all documents in the corpus are re-embedded with the new model.
- **AS-007**: **Given** the agent uses LlamaIndex, **When** a RAG query is processed, **Then** the agent retrieves context from pgvector and generates a response via vLLM.
- **AS-008**: **Given** the agent's `pyproject.toml`, **When** dependencies are inspected, **Then** `llama-index`, `llama-index-llms-vllm`, and pgvector-related LlamaIndex packages are listed.
- **AS-009**: **Given** the gateway's Modal service calls, **When** `grep -r "model-modal\|embedding-modal" apps/gateway/` is run, **Then** zero matches are found (old worker names fully replaced).
- **AS-010**: **Given** the full pipeline is running, **When** test documents are ingested, embedded, and queried, **Then** the agent's response is grounded in the test documents and includes source citations.

## Success Criteria

- **SC-001**: vLLM inference deploys on Modal and responds to `/v1/chat/completions` with valid completions. Verified by a successful Modal deployment and a test API call.
- **SC-002**: Embedding worker generates embeddings and stores them in pgvector. Verified by invoking the worker with test documents and querying pgvector for the resulting vectors.
- **SC-003**: Indexing worker successfully executes all 4 modes (single-doc, batch, selective re-index, full rebuild). Verified by triggering each mode and inspecting pgvector state.
- **SC-004**: Agent processes RAG queries via LlamaIndex and vLLM. Verified by an end-to-end test: query → agent → LlamaIndex retrieval → vLLM inference → response with sources.
- **SC-005**: No references to `model-modal` or `embedding-modal` remain in the active codebase. Verified by `grep -r` across the repository.
- **SC-006**: Gateway's Modal SDK calls successfully invoke the new worker functions. Verified by triggering each worker type from the gateway and confirming execution.
- **SC-007**: End-to-end RAG pipeline test passes: ingest → embed → query → grounded response. Verified by the test defined in FR-010.
- **SC-008**: Latency is acceptable: synchronous RAG queries complete in < 30s, streaming queries deliver first token in < 5s (excluding cold-start). Verified by timing 10 sequential test queries.

## Assumptions

- Spec 021 (gateway/agent extraction) is complete — the agent is an independent service at `apps/agent/`.
- Modal account and GPU access (H100 or A100) are available for vLLM deployment.
- PostgreSQL with pgvector extension is available and accessible by the agent and workers.
- The LLM model to run on vLLM is decided at deployment time (per TD-009, deferred). The architecture supports model swapping via environment variable.
- The embedding model is decided at deployment time (per TD-008, deferred). LlamaIndex supports multiple embedding providers.
- `llama-index-llms-vllm` supports connecting to a remote vLLM endpoint (not just local). The vLLM endpoint URL is passed via environment variable.
- The existing scraper-worker (`apps/scraper-worker/`) is unchanged by this spec — only `model-modal` and `embedding-modal` are replaced.
- Modal `spawn_map` is available in the current Modal SDK version and supports the batch sizes expected (100+ documents).

## Technical References

- `specs/monorepo-decomposition/08-recommended-boundaries.md` — vLLM inference, embedding worker, indexing worker service definitions
- `specs/monorepo-decomposition/09-migration-sequence.md` — Phase 3 details
- `specs/monorepo-decomposition/02-app-inventory.md` — GPU worker inventory and current→target mapping
- `specs/authoritative/vllm-inference/` — vLLM architecture documentation
- `specs/.technical-decisions-log.json` — TD-008 (LLM provider strategy), TD-009 (model selection)
- `specs/021-gateway-agent-extraction/spec.md` — prerequisite spec
- [vLLM OpenAI-compatible API docs](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html)
- [LlamaIndex vLLM integration](https://docs.llamaindex.ai/en/stable/examples/llm/vllm/)
- [Modal spawn_map docs](https://modal.com/docs/reference/modal.Function#spawn_map)
