# Data Models Diagram: Embedding Worker
> Auto-generated: 2026-05-12

## Pydantic Schema Relationships

```mermaid
erDiagram
    QueryRequest {
        string query "Primary text field (optional)"
        string text "Alias field (optional)"
        string model "Override model (optional)"
    }

    BatchQueryRequest {
        list_string queries "List of queries (optional)"
        list_string texts "Alias list (optional)"
        string model "Override model (optional)"
    }

    EmbeddingResponse {
        list_float embedding "384-dim vector"
        string model "Model used"
        int dimensions "Vector length (384)"
    }

    BatchEmbeddingResponse {
        list_list_float embeddings "List of 384-dim vectors"
        string model "Model used"
        int dimensions "Vector length (384)"
    }

    EmbeddingServiceRootResponse {
        string status "ok"
        string model "Default model"
    }

    EmbeddingLivenessResponse {
        string status "ok"
    }

    QueryRequest ||--|| EmbeddingResponse : "POST /embed"
    BatchQueryRequest ||--|| BatchEmbeddingResponse : "POST /embed/batch"
```

## Modal Function I/O (Dict-Based)

```mermaid
erDiagram
    EmbedQueryInput {
        string query "Text to embed"
    }

    EmbedQueryOutput {
        list_float embedding "384-dim vector"
        string model "BAAI/bge-small-en-v1.5"
        int dimension "384"
    }

    EmbedBatchInput {
        list_string queries "Texts to embed"
    }

    EmbedBatchOutput {
        list_list_float embeddings "List of 384-dim vectors"
        string model "BAAI/bge-small-en-v1.5"
        int dimension "384"
    }

    EmbedQueryInput ||--|| EmbedQueryOutput : "embed_query.remote()"
    EmbedBatchInput ||--|| EmbedBatchOutput : "embed_batch.remote()"
```

## Service Layer Types

```mermaid
classDiagram
    class Embedder {
        <<Protocol>>
        +embed(texts: Sequence[str]) Any
    }

    class EmbeddingService {
        -_embedder: Embedder
        -_default_model: str
        +embed_query(query, model) EmbeddingResponse
        +embed_batch(queries, model) BatchEmbeddingResponse
        -_to_vector(raw) list~float~
    }

    class EmptyQueryError {
        <<ValueError>>
    }

    class EmbeddingExecutionError {
        <<RuntimeError>>
    }

    class TextEmbedding {
        +embed(texts) Iterable~ndarray~
    }

    Embedder <|.. TextEmbedding : implements
    EmbeddingService --> Embedder : uses
    EmbeddingService ..> EmptyQueryError : raises
    EmbeddingService ..> EmbeddingExecutionError : raises
```

See: [Data Models](../02-data-models.md)
