# Indexing Worker — Sequence Flow Diagrams
> Auto-generated: 2026-05-12

## Single Document Indexing

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant IW as Indexing Worker
    participant DB as PostgreSQL
    participant PGV as pgvector

    GW->>IW: index_document.remote(document_id)
    IW->>DB: SELECT FROM data_mgmt.documents WHERE id = document_id
    DB-->>IW: document record (content, metadata)
    IW->>IW: Chunk text (LlamaIndex TextSplitter)
    IW->>IW: Generate embeddings (fastembed / LlamaIndex)
    IW->>IW: Compute content_hash (SHA-256)
    IW->>PGV: UPSERT agent.vectors[] (doc_id, chunk_idx, embedding, hash)
    PGV-->>IW: rows affected
    IW-->>GW: {status: "complete", chunks: N, vectors: N}
```

## Batch Indexing via spawn_map

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant IW as Indexing Worker
    participant IW_N as Indexing Worker (N instances)
    participant DB as PostgreSQL
    participant PGV as pgvector

    GW->>IW: index_batch.remote(document_ids[])
    IW->>DB: SELECT FROM data_mgmt.documents WHERE id IN (...)
    DB-->>IW: document records[]
    IW->>IW_N: index_document.spawn_map(document_ids[])
    Note over IW_N: Modal spawns N parallel workers
    par Worker 1
        IW_N->>IW_N: Chunk + embed doc 1
        IW_N->>PGV: UPSERT vectors for doc 1
    and Worker 2
        IW_N->>IW_N: Chunk + embed doc 2
        IW_N->>PGV: UPSERT vectors for doc 2
    and Worker N
        IW_N->>IW_N: Chunk + embed doc N
        IW_N->>PGV: UPSERT vectors for doc N
    end
    IW_N-->>IW: results[]
    IW-->>GW: {status: "complete", total_docs: N, total_vectors: M}
```

## Selective Re-Indexing (Changed Content)

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant IW as Indexing Worker
    participant DB as PostgreSQL
    participant PGV as pgvector

    GW->>IW: reindex_changed.remote(scope_filter)
    IW->>DB: SELECT id, content FROM data_mgmt.documents WHERE scope_filter
    DB-->>IW: documents[]
    IW->>PGV: SELECT document_id, content_hash FROM agent.vectors
    PGV-->>IW: existing hashes[]
    IW->>IW: Compare SHA-256 hashes
    Note over IW: Only documents with changed content proceed
    IW->>IW: Chunk changed documents
    IW->>IW: Generate new embeddings
    IW->>PGV: DELETE old vectors for changed docs
    IW->>PGV: INSERT new vectors with updated hashes
    IW-->>GW: {changed: X, unchanged: Y, total_reindexed: X}
```

## Full Rebuild (Model Change)

```mermaid
sequenceDiagram
    participant Op as Operator
    participant GW as Gateway
    participant IW as Indexing Worker
    participant DB as PostgreSQL
    participant PGV as pgvector

    Op->>GW: POST /trigger rebuild_all
    GW->>IW: rebuild_all.remote(new_model_name)
    IW->>DB: SELECT * FROM data_mgmt.documents
    DB-->>IW: all documents[]
    IW->>PGV: TRUNCATE agent.vectors (or batch delete)
    Note over IW: Process in batches of INDEX_BATCH_SIZE
    loop For each batch
        IW->>IW: Chunk batch documents
        IW->>IW: Generate embeddings with new model
        IW->>PGV: INSERT agent.vectors[] (new model vectors)
    end
    IW-->>GW: {status: "complete", model: new_model_name, total_docs: N, total_vectors: M}
    GW-->>Op: Rebuild complete
```

## Scraper-Triggered Indexing (Post-Scrape)

```mermaid
sequenceDiagram
    participant SW as Scraper Worker
    participant IW as Indexing Worker
    participant DB as PostgreSQL
    participant PGV as pgvector

    Note over SW: Scrape job completes, documents stored
    SW->>IW: index_document.spawn(document_id)
    activate IW
    IW->>DB: SELECT FROM data_mgmt.documents WHERE id = document_id
    DB-->>IW: document record
    IW->>IW: Chunk + embed
    IW->>PGV: UPSERT vectors
    IW-->>SW: {status: "indexed"}
    deactivate IW
```

## Health Check

```mermaid
sequenceDiagram
    participant Monitor as Monitoring
    participant IW as Indexing Worker
    participant DB as PostgreSQL
    participant PGV as pgvector

    Monitor->>IW: health_check.remote()
    IW->>DB: SELECT 1 (data_mgmt connection)
    DB-->>IW: OK
    IW->>PGV: SELECT count(*) FROM agent.vectors
    PGV-->>IW: vector_count
    IW-->>Monitor: {status: "healthy", db: "connected", vector_count: N, model: "BAAI/bge-small-en-v1.5"}
```
