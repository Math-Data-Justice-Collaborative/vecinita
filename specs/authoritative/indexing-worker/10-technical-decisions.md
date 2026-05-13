# Technical Decisions: Indexing Worker
> Auto-generated: 2026-05-12

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Embedding runtime | fastembed (ONNX) | sentence-transformers (PyTorch) | 2026-05-12 | Easy |
| TD-002 | Embedding model | BAAI/bge-small-en-v1.5 | all-MiniLM-L6-v2, bge-base-en-v1.5 | 2026-05-12 | Moderate (requires rebuild) |
| TD-003 | Chunking library | LlamaIndex SentenceSplitter | langchain text_splitter, custom | 2026-05-12 | Easy |
| TD-004 | Chunking strategy | Token-based with sentence awareness | Fixed character split, recursive | 2026-05-12 | Easy |
| TD-005 | Change detection | SHA-256 content hashing | Timestamp comparison, diff-based | 2026-05-12 | Easy |
| TD-006 | Batch execution | Modal spawn_map | Sequential loop, asyncio.gather | 2026-05-12 | Easy |
| TD-007 | Database driver | psycopg2-binary (sync) | asyncpg, SQLAlchemy | 2026-05-12 | Moderate |
| TD-008 | GPU type (default) | T4 | A10G, A100, L4 | 2026-05-12 | Easy |
| TD-009 | Deployment platform | Modal (serverless) | Render worker, self-hosted | 2026-05-12 | Hard |
| TD-010 | Vector index type | Deferred (see PTD-001) | — | — | — |

### TD-001: fastembed over sentence-transformers

**Context**: Need an embedding runtime for BAAI/bge-small-en-v1.5 on GPU. Two main options: fastembed (ONNX-based) and sentence-transformers (PyTorch-based).

**Decision**: Use fastembed via LlamaIndex adapter.

**Rationale**:
- ONNX runtime is ~2-3x faster than PyTorch for inference-only workloads
- Smaller memory footprint (~500MB vs ~2GB for PyTorch)
- Aligns with existing embedding-worker which already uses fastembed
- Simpler dependency tree (no full PyTorch installation)

**Consequences**: Cannot fine-tune models via fastembed (inference only). If fine-tuning is needed in the future, sentence-transformers would be required alongside fastembed.

**Alternatives considered**:
- **sentence-transformers**: Full PyTorch ecosystem, supports fine-tuning, larger community. Rejected due to heavier GPU memory footprint and slower inference for the read-only use case.

### TD-002: BAAI/bge-small-en-v1.5 Model

**Context**: Need to choose an embedding model. Must align with embedding-worker to produce compatible vectors.

**Decision**: BAAI/bge-small-en-v1.5 (384 dimensions).

**Rationale**:
- Already used by embedding-worker — vectors are directly compatible
- Shared model cache volume avoids duplicate downloads
- 384 dimensions is a good balance of quality vs. storage/search cost
- Strong MTEB benchmark performance for its size class

**Consequences**: Changing the model requires a full vector rebuild (`rebuild_all`). The 384-dim vector size is baked into the pgvector column definition.

**Alternatives considered**:
- **all-MiniLM-L6-v2**: Slightly faster, but lower quality on retrieval benchmarks.
- **bge-base-en-v1.5** (768 dims): Better quality but 2x storage and search cost. Overkill for current corpus size.

### TD-003: LlamaIndex SentenceSplitter

**Context**: Need a text chunking library that produces overlapping, token-aware chunks.

**Decision**: Use LlamaIndex `SentenceSplitter`.

**Rationale**:
- Sentence-boundary-aware splitting produces more semantically coherent chunks
- Token-based sizing aligns with embedding model's context window
- LlamaIndex is already a dependency for the embedding adapter
- Configurable `chunk_size` and `chunk_overlap` via environment variables

**Consequences**: Adds `llama-index-core` as a dependency. If LlamaIndex introduces breaking changes in text splitting, the chunker module isolates the impact.

**Alternatives considered**:
- **langchain text_splitter**: Similar capability, but would add langchain as a dependency alongside LlamaIndex.
- **Custom splitter**: Full control, but reinventing well-tested logic.

### TD-004: Token-Based Chunking with Sentence Awareness

**Context**: Choose between character-based and token-based chunk sizing.

**Decision**: Token-based chunks (512 tokens, 50-token overlap).

**Rationale**:
- Embedding models have token-based context windows, not character-based
- Token-based sizing ensures chunks fit within model limits
- 512 tokens provides sufficient context for retrieval without diluting relevance
- 50-token overlap (~10%) ensures continuity across chunk boundaries

**Consequences**: Token counting adds minor overhead per chunk. Chunk sizes in characters will vary based on content.

### TD-005: SHA-256 Content Hashing for Change Detection

**Context**: Need to detect which documents have changed to avoid re-indexing unchanged content.

**Decision**: SHA-256 hash of document content, stored in `agent.content_hashes`.

**Rationale**:
- Deterministic: same content always produces same hash
- Fast: SHA-256 is CPU-efficient even for large documents
- Storage-efficient: 64-byte hex string per document
- Resistant to false positives (collision probability negligible)

**Consequences**: Any whitespace or formatting change triggers a re-index. This is intentional — formatting changes can affect chunk boundaries and thus embedding quality.

**Alternatives considered**:
- **Timestamp comparison**: Simpler but unreliable — `updated_at` may change without content change (e.g., metadata-only updates).
- **Diff-based**: Would allow partial re-indexing of changed chunks, but dramatically more complex for marginal benefit.

### TD-006: Modal spawn_map for Batch Parallelism

**Context**: Need to parallelize indexing across multiple documents.

**Decision**: Use Modal's `spawn_map` (or `.map()`) to distribute work across GPU containers.

**Rationale**:
- Modal handles container provisioning and scaling automatically
- Each document gets its own GPU container — no contention
- Built-in failure isolation: one document's failure doesn't affect others
- Aligns with scraper-worker pattern (`vecinita-scraper` uses similar approach)

**Consequences**: Higher container count during batch operations increases cost. Mitigated by `INDEX_BATCH_SIZE` limit (default 100).

### TD-007: psycopg2-binary (Sync) Driver

**Context**: Need PostgreSQL connectivity for reading documents and writing vectors.

**Decision**: Use psycopg2-binary with synchronous connections.

**Rationale**:
- Modal functions are invoked synchronously — no event loop to block
- Simpler connection management: one connection per function invocation
- psycopg2 is battle-tested, well-documented, and widely used
- Binary package avoids libpq build dependency in Modal containers

**Consequences**: Cannot share a connection pool across invocations (each container has its own). Acceptable for serverless model where containers are ephemeral.

### TD-008: T4 GPU Default

**Context**: Choose GPU type for embedding generation.

**Decision**: NVIDIA T4 as default GPU.

**Rationale**:
- Most cost-effective GPU on Modal for inference workloads
- 16GB VRAM is more than sufficient for bge-small-en-v1.5 (~500MB)
- Good availability on Modal platform
- Sufficient FP16 performance for ONNX inference

**Consequences**: If a larger model is adopted in the future, T4 may be insufficient. GPU type is configurable at deployment time.

### TD-009: Modal over Render Worker

**Context**: Choose deployment platform for GPU-accelerated indexing.

**Decision**: Deploy on Modal (serverless GPU).

**Rationale**:
- GPU access: Modal provides on-demand GPU provisioning; Render does not offer GPU instances
- Cost: Pay-per-invocation model is efficient for bursty indexing workloads
- Scale-to-zero: No cost when idle, unlike a persistent GPU worker
- Consistency: Aligns with embedding-worker and scraper-worker (both on Modal)

**Consequences**: Adds Modal as a platform dependency. Gateway must use Modal SDK for invocation (no direct HTTP).

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | pgvector index type | IVFFlat, HNSW | Query performance | Medium — acceptable without index at small scale | HNSW |
| PTD-002 | Connection pooling | Per-invocation, pgBouncer, internal pool | Connection overhead | Low — per-invocation is acceptable for serverless | Per-invocation (defer) |
| PTD-003 | Chunk size optimization | 256, 512, 1024 tokens | Retrieval quality | Low — 512 is a safe default | 512 (current), benchmark later |
| PTD-004 | Error recovery for partial rebuilds | Resume from checkpoint, restart from scratch | Rebuild reliability | Medium — affects long rebuilds | Checkpoint-based resume |

### PTD-001: pgvector Index Type

**Context**: `agent.vectors` will need an approximate nearest neighbor (ANN) index for search performance. pgvector supports IVFFlat and HNSW.

**Why it matters**: Without an index, vector search degrades linearly with row count. At 10K+ vectors, query latency becomes unacceptable for real-time RAG.

**Options researched**:
- **IVFFlat**: Faster build time, lower memory. Requires choosing `lists` parameter. Recall decreases as corpus grows unless re-tuned. Effort: low.
- **HNSW**: Better recall out of the box, no tuning required for most corpus sizes. Slower to build, higher memory. Effort: low.

**Recommendation**: HNSW for better recall without tuning. Build time is less critical since vectors are written incrementally.

**Risk of continued deferral**: Acceptable at small scale (<5K vectors). Must decide before corpus exceeds ~10K vectors.

**Decision deadline**: Before first production deployment with real corpus.

### PTD-002: Connection Pooling Strategy

**Context**: Each Modal function invocation will open a fresh PostgreSQL connection. This is simple but creates overhead.

**Why it matters**: At high batch concurrency (e.g., 100 parallel `index_document` calls), each opens its own connection. Render Postgres may have a 97-connection limit.

**Options researched**:
- **Per-invocation (current plan)**: Simple, no shared state. Risk of hitting connection limit during large batches. Effort: none.
- **pgBouncer**: External connection pooler, handles multiplexing. Requires infrastructure setup. Effort: medium.
- **Internal pool (per-container)**: Pool within each Modal container. Limited benefit since containers are ephemeral. Effort: low.

**Recommendation**: Start with per-invocation. Add pgBouncer if connection limits are hit during batch operations.

**Risk of continued deferral**: Low at current scale. Becomes medium-high when running batches of 50+ concurrent documents.

**Decision deadline**: After first batch indexing load test.

### PTD-003: Chunk Size Optimization

**Context**: Default chunk size is 512 tokens with 50-token overlap. This is an industry standard but may not be optimal for the specific corpus.

**Why it matters**: Chunk size directly impacts retrieval quality and storage cost. Too small = noisy retrieval. Too large = diluted relevance.

**Options researched**:
- **256 tokens**: More precise retrieval, but higher chunk count (2x storage, 2x embedding cost).
- **512 tokens (current)**: Good balance, widely used default for general-purpose RAG.
- **1024 tokens**: Richer context per chunk, but may retrieve irrelevant content alongside relevant content.

**Recommendation**: Start with 512. After initial deployment, run retrieval quality benchmarks with 256 and 1024 to compare.

**Risk of continued deferral**: Low — 512 is a safe default. Optimization is a quality-of-life improvement, not a blocker.

**Decision deadline**: After first retrieval quality evaluation.

### PTD-004: Error Recovery for Partial Rebuilds

**Context**: `rebuild_all` can take up to 3600s. If it fails midway (timeout, crash), the vector store is in an inconsistent state (some old vectors deleted, some new ones written).

**Why it matters**: A failed rebuild leaves the RAG system with incomplete or mixed-model vectors, degrading search quality.

**Options researched**:
- **Restart from scratch**: Delete all vectors and retry. Simple but wasteful — re-does already-completed work. Effort: none (current behavior).
- **Checkpoint-based resume**: Track progress in `indexing_jobs`, resume from last completed document. Effort: medium.
- **Shadow table**: Write new vectors to a staging table, swap atomically on completion. Effort: high.

**Recommendation**: Checkpoint-based resume. Track `last_processed_document_id` in the job record and support a `resume` parameter on `rebuild_all`.

**Risk of continued deferral**: Medium — a failed 1-hour rebuild is expensive to restart. Becomes critical as corpus grows.

**Decision deadline**: Before corpus exceeds 1,000 documents.

## Cross-References

- Dependencies: [09-dependencies.md](09-dependencies.md)
- Architecture: [07-architecture.md](07-architecture.md)
- Modal integration: [13-modal-integration-plan.md](13-modal-integration-plan.md)
