"""Embedding worker — LlamaIndex batch embedding on Modal GPU."""
import modal

app = modal.App("vecinita-embedding-worker")

embedding_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "llama-index-core",
        "llama-index-embeddings-huggingface",
        "psycopg2-binary",
        "pydantic>=2.0",
    )
)


@app.function(
    image=embedding_image,
    gpu="T4",
    timeout=1800,
)
def embed_documents(
    texts: list[str],
    model_name: str | None = None,
    database_url: str | None = None,
) -> list[list[float]]:
    """Embed a batch of text documents and optionally store in pgvector.

    Args:
        texts: List of text strings to embed.
        model_name: HuggingFace model name. Defaults to EMBEDDING_MODEL env var
                     or 'sentence-transformers/all-MiniLM-L6-v2'.
        database_url: PostgreSQL connection string for pgvector storage.
                      If None, embeddings are returned without storage.

    Returns:
        List of embedding vectors (one per input text).
    """
    import os
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    model = model_name or os.environ.get(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    embed_model = HuggingFaceEmbedding(model_name=model)
    embeddings = embed_model.get_text_embedding_batch(texts)

    if database_url:
        _store_embeddings(database_url, texts, embeddings)

    return embeddings


@app.function(
    image=embedding_image,
    gpu="T4",
    timeout=600,
)
def embed_query(
    query: str,
    model_name: str | None = None,
) -> list[float]:
    """Embed a single query for vector search."""
    import os
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    model = model_name or os.environ.get(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    embed_model = HuggingFaceEmbedding(model_name=model)
    return embed_model.get_query_embedding(query)


def _store_embeddings(
    database_url: str,
    texts: list[str],
    embeddings: list[list[float]],
) -> None:
    """Store embeddings in pgvector."""
    import psycopg2

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            for text, embedding in zip(texts, embeddings):
                cur.execute(
                    "INSERT INTO document_embeddings (content, embedding) "
                    "VALUES (%s, %s) "
                    "ON CONFLICT (content) DO UPDATE SET embedding = EXCLUDED.embedding",
                    (text, embedding),
                )
        conn.commit()
    finally:
        conn.close()
