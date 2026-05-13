# Sequence Flows Diagram: Embedding Worker
> Auto-generated: 2026-05-12

## Single Embedding Request

```mermaid
sequenceDiagram
    participant U as End User
    participant GW as Gateway
    participant INV as invoker.py
    participant M as Modal Runtime
    participant EW as embed_query
    participant FE as fastembed
    participant VOL as Volume (/models)

    U->>GW: GET /api/v1/ask?question=...
    GW->>INV: invoke_modal_embedding_single(text)
    INV->>INV: _lookup_function("vecinita-embedding", "embed_query")
    Note over INV: LRU cached after first call
    INV->>M: fn.remote(text)
    M->>EW: embed_query(query)
    EW->>EW: load_runtime_model()
    EW->>FE: TextEmbedding(model_name, cache_dir="/models")
    FE->>VOL: Load cached model
    VOL-->>FE: Model weights
    EW->>FE: model.embed(["warmup"])
    FE-->>EW: warmup vector
    EW->>FE: model.embed([query])
    FE-->>EW: ndarray (384-dim)
    EW->>EW: vector.tolist()
    EW-->>M: {"embedding": [...], "model": "...", "dimension": 384}
    M-->>INV: dict result
    INV-->>GW: dict result
    GW->>GW: Query PostgreSQL for nearest neighbors
    GW-->>U: Answer with sources
```

## Batch Embedding Request

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant INV as invoker.py
    participant M as Modal Runtime
    participant EW as embed_batch
    participant FE as fastembed
    participant VOL as Volume (/models)

    GW->>INV: invoke_modal_embedding_batch(texts)
    INV->>INV: _lookup_function("vecinita-embedding", "embed_batch")
    INV->>M: fn.remote(texts)
    M->>EW: embed_batch(queries)
    EW->>EW: load_runtime_model()
    EW->>FE: TextEmbedding(model_name, cache_dir="/models")
    FE->>VOL: Load cached model
    VOL-->>FE: Model weights
    EW->>FE: model.embed(["warmup"])
    FE-->>EW: warmup vector
    EW->>FE: model.embed(queries)
    FE-->>EW: list[ndarray] (N x 384-dim)
    EW->>EW: [v.tolist() for v in vectors]
    EW-->>M: {"embeddings": [[...], ...], "model": "...", "dimension": 384}
    M-->>INV: dict result
    INV-->>GW: dict result
    GW->>GW: Batch INSERT into agent.vectors
```

## Cold Start Sequence

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant M as Modal Runtime
    participant C as Container
    participant EW as embed_query
    participant FE as fastembed
    participant VOL as Volume
    participant HF as HuggingFace Hub

    GW->>M: fn.remote(text)
    Note over M: No warm container available
    M->>C: Provision new container
    Note over C: debian_slim + Python 3.11 + fastembed
    C->>C: Mount Volume at /models
    M->>EW: embed_query(query)
    EW->>FE: TextEmbedding(model_name, cache_dir="/models")

    alt Model cached on Volume
        FE->>VOL: Load from /models
        VOL-->>FE: Model files (~100MB)
        Note over FE: ~1-5s load time
    else First-ever invocation
        FE->>HF: Download BAAI/bge-small-en-v1.5
        HF-->>FE: Model files (~100MB)
        FE->>VOL: Cache to /models
        Note over FE: ~30s download + save
    end

    EW->>FE: model.embed(["warmup"])
    FE-->>EW: Warmup complete
    EW->>FE: model.embed([query])
    FE-->>EW: ndarray (384-dim)
    EW-->>M: Result dict
    M-->>GW: Result dict
```

## Error Handling Sequence

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant INV as invoker.py
    participant M as Modal Runtime
    participant EW as embed_query/batch

    alt Empty query
        GW->>INV: invoke_modal_embedding_single("")
        INV->>M: fn.remote("")
        M->>EW: embed_query("")
        EW->>EW: EmptyQueryError raised
        EW-->>M: Exception propagated
        M-->>INV: Exception raised
        INV-->>GW: EmptyQueryError
    end

    alt Backend failure
        GW->>INV: invoke_modal_embedding_single(text)
        INV->>M: fn.remote(text)
        M->>EW: embed_query(text)
        EW->>EW: fastembed fails internally
        EW->>EW: EmbeddingExecutionError wraps cause
        EW-->>M: Exception propagated
        M-->>INV: Exception raised
        INV-->>GW: EmbeddingExecutionError
    end

    alt Timeout
        GW->>INV: invoke_modal_embedding_single(text)
        INV->>M: fn.remote(text)
        M->>EW: embed_query(text)
        Note over EW: Processing exceeds 600s
        M-->>INV: TimeoutError
        INV-->>GW: TimeoutError
    end
```

## HTTP API Sequence (Development)

```mermaid
sequenceDiagram
    participant DEV as Developer
    participant API as FastAPI (api.py)
    participant SVC as EmbeddingService
    participant EMB as Embedder (FakeEmbedder in tests)

    DEV->>API: POST /embed {"query": "test"}
    API->>API: Parse QueryRequest
    API->>SVC: service.embed_query("test", model=None)
    SVC->>SVC: Validate non-empty
    SVC->>EMB: embedder.embed(["test"])
    EMB-->>SVC: [ndarray]
    SVC->>SVC: _to_vector(raw) → list[float]
    SVC-->>API: EmbeddingResponse(embedding, model, dimensions)
    API-->>DEV: 200 {"embedding": [...], "model": "...", "dimensions": 384}
```

See: [User Journeys](../05-user-journeys.md) | [Data Flow](../06-data-flow.md) | [API Contract](../08-api-contract.md)
