# Indexing Worker

Document indexing pipeline running on Modal serverless infrastructure with GPU-accelerated embedding.

## Modes

| Mode | Function | Description |
|------|----------|-------------|
| **Single-doc** | `index_single_doc` | Index one document on demand — embed and upsert into pgvector |
| **Batch** | `index_batch` | Index multiple documents in parallel via `spawn_map` |
| **Selective** | `selective_reindex` | Re-index only changed documents using SHA-256 content hash comparison |
| **Full rebuild** | `full_rebuild` | Re-embed and re-index the entire corpus (used when the embedding model changes) |

## Runtime

- **Deploy target:** Modal serverless (T4 GPU for embedding)
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (configurable via `EMBEDDING_MODEL` env var)
- **Storage:** PostgreSQL with pgvector extension
- **Protocol:** Modal function invocation / Modal `.map()` for parallelism

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string with pgvector |
| `EMBEDDING_MODEL` | No | HuggingFace model name (default: `sentence-transformers/all-MiniLM-L6-v2`) |

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```
