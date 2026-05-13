# Data Flow Diagrams: Indexing Worker
> Auto-generated: 2026-05-12

## Single-Document Indexing Pipeline

```mermaid
flowchart TD
    A[Caller<br/>Gateway / Scraper] -->|"index_document(doc_id)"| B[Indexing Worker]
    B -->|"SELECT content FROM data_mgmt.documents"| C[(PostgreSQL)]
    C -->|"Document content + metadata"| B
    B -->|"SentenceSplitter(512, 50)"| D[Chunker]
    D -->|"N text chunks"| E[Embedder]
    E -->|"fastembed on GPU"| F[384-dim vectors]
    F -->|"DELETE old vectors"| G[(agent.vectors)]
    F -->|"INSERT new vectors"| G
    B -->|"UPSERT content hash"| H[(agent.content_hashes)]
    B -->|"UPDATE job status"| I[(agent.indexing_jobs)]
    B -->|"IndexingResult"| A
```

## Batch Indexing Flow

```mermaid
flowchart TD
    A[Gateway] -->|"index_batch(doc_ids)"| B[Orchestrator<br/>CPU only]
    B -->|"Validate batch size ≤ 100"| B
    B -->|"CREATE indexing_jobs record"| DB[(PostgreSQL)]
    B -->|"spawn_map"| C1[index_document<br/>GPU Container 1]
    B -->|"spawn_map"| C2[index_document<br/>GPU Container 2]
    B -->|"spawn_map"| CN[index_document<br/>GPU Container N]

    C1 -->|"vectors"| DB
    C2 -->|"vectors"| DB
    CN -->|"vectors"| DB

    C1 -->|"result"| B
    C2 -->|"result"| B
    CN -->|"result"| B

    B -->|"Aggregate results"| B
    B -->|"UPDATE indexing_jobs"| DB
    B -->|"IndexingResult"| A
```

## Selective Re-Indexing Flow

```mermaid
flowchart TD
    A[Gateway] -->|"reindex_changed(source_id)"| B[Orchestrator]
    B -->|"SELECT documents WHERE source_id"| C[(data_mgmt.documents)]
    B -->|"SELECT content_hashes"| D[(agent.content_hashes)]

    C -->|"Document list"| E{Compare Hashes}
    D -->|"Stored hashes"| E

    E -->|"SHA-256 current content"| E
    E -->|"Changed docs"| F[spawn_map<br/>index_document]
    E -->|"Unchanged docs"| G[Skip<br/>skipped_documents++]

    F -->|"New vectors"| H[(agent.vectors)]
    F -->|"Updated hashes"| D

    B -->|"IndexingResult<br/>processed + skipped"| A
```

## Full Rebuild Flow

```mermaid
flowchart TD
    A[Operator via Gateway] -->|"rebuild_all(reason, confirm=True)"| B[Orchestrator]
    B -->|"Check confirm=True"| C{Safety Check}
    C -->|"confirm=False"| REJECT[Reject]
    C -->|"confirm=True"| D{Concurrent Check}
    D -->|"Another rebuild running"| REJECT
    D -->|"No concurrent rebuild"| E[Proceed]

    E -->|"DELETE ALL FROM agent.vectors"| F[(PostgreSQL)]
    E -->|"DELETE ALL FROM agent.content_hashes"| F
    E -->|"SELECT ALL FROM data_mgmt.documents"| F

    F -->|"All documents"| G[Batch Loop]
    G -->|"Batch 1 (100 docs)"| H1[spawn_map → GPU]
    G -->|"Batch 2 (100 docs)"| H2[spawn_map → GPU]
    G -->|"Batch N"| HN[spawn_map → GPU]

    H1 -->|"vectors"| F
    H2 -->|"vectors"| F
    HN -->|"vectors"| F

    G -->|"Aggregate all results"| I[IndexingResult]
    I -->|"Return"| A
```

## Document-to-Vector Transformation Detail

```mermaid
flowchart LR
    subgraph "Input"
        DOC["Document<br/>~5000 tokens<br/>(markdown text)"]
    end

    subgraph "Stage 1: Chunk"
        DOC --> S1["SentenceSplitter<br/>chunk_size=512<br/>overlap=50"]
        S1 --> C1["Chunk 0<br/>512 tokens"]
        S1 --> C2["Chunk 1<br/>512 tokens"]
        S1 --> C3["..."]
        S1 --> CN["Chunk N<br/>≤512 tokens"]
    end

    subgraph "Stage 2: Embed"
        C1 --> E1["vector(384)"]
        C2 --> E2["vector(384)"]
        CN --> EN["vector(384)"]
    end

    subgraph "Stage 3: Store"
        E1 --> DB[(agent.vectors<br/>pgvector)]
        E2 --> DB
        EN --> DB
    end
```
