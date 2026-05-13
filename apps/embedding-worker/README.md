# vecinita-embedding-worker

LlamaIndex document embedding worker deployed on [Modal](https://modal.com/) with GPU acceleration.

- **Embedding framework**: [LlamaIndex](https://www.llamaindex.ai/) with HuggingFace sentence-transformers
- **Default model**: `sentence-transformers/all-MiniLM-L6-v2` (configurable via `EMBEDDING_MODEL` env var)
- **Compute**: Modal serverless GPU (T4)
- **Storage**: Optional pgvector (PostgreSQL) for embedding persistence

## Functions

| Function | Description |
|----------|-------------|
| `embed_documents` | Batch-embed a list of texts, optionally storing results in pgvector |
| `embed_query` | Embed a single query string for vector search |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace model name |

## Local development

```bash
pip install -e ".[dev]"
```

## Quality checks

```bash
make lint
make test
```

## Deploy

```bash
make deploy
```

## Serve locally

```bash
make serve
```
