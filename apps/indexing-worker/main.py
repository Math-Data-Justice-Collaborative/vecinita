"""Indexing worker — document indexing pipeline on Modal.

Supports four modes:
- single_doc: Index one document on demand
- batch: Index multiple documents in parallel via spawn_map
- selective: Re-index only changed documents (content hash comparison)
- full_rebuild: Re-embed and re-index entire corpus
"""
import hashlib
import logging

import modal

app = modal.App("vecinita-indexing-worker")
logger = logging.getLogger(__name__)

indexing_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "llama-index-core",
        "llama-index-embeddings-huggingface",
        "psycopg2-binary",
        "pydantic>=2.0",
    )
)


def _content_hash(text: str) -> str:
    """Compute SHA-256 hash of document content for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _get_embed_model(model_name: str | None = None):
    """Get the configured embedding model."""
    import os
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    model = model_name or os.environ.get(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    return HuggingFaceEmbedding(model_name=model)


@app.function(image=indexing_image, gpu="T4", timeout=600)
def index_single_doc(
    doc_id: str,
    content: str,
    metadata: dict | None = None,
    database_url: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Index a single document: embed and store in pgvector.

    Returns dict with doc_id, content_hash, embedding_dim, and status.
    """
    import os

    db_url = database_url or os.environ.get("DATABASE_URL", "")
    embed_model = _get_embed_model(model_name)
    embedding = embed_model.get_text_embedding(content)
    content_hash = _content_hash(content)

    if db_url:
        _upsert_document(db_url, doc_id, content, embedding, content_hash, metadata)

    return {
        "doc_id": doc_id,
        "content_hash": content_hash,
        "embedding_dim": len(embedding),
        "status": "indexed",
    }


@app.function(image=indexing_image, gpu="T4", timeout=3600)
def index_batch(
    documents: list[dict],
    database_url: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Index multiple documents in parallel via spawn_map.

    Each document dict must have 'doc_id' and 'content' keys.
    Optional 'metadata' key for additional document metadata.

    Returns summary with total, succeeded, and failed counts.
    """
    results = list(
        index_single_doc.map(
            [d["doc_id"] for d in documents],
            [d["content"] for d in documents],
            [d.get("metadata") for d in documents],
            [database_url] * len(documents),
            [model_name] * len(documents),
        )
    )

    succeeded = sum(1 for r in results if r["status"] == "indexed")
    return {
        "total": len(documents),
        "succeeded": succeeded,
        "failed": len(documents) - succeeded,
        "results": results,
    }


@app.function(image=indexing_image, gpu="T4", timeout=3600)
def selective_reindex(
    documents: list[dict],
    database_url: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Re-index only documents whose content has changed.

    Compares content hash against stored hash to identify changed documents.
    Each document dict must have 'doc_id' and 'content' keys.
    """
    import os

    db_url = database_url or os.environ.get("DATABASE_URL", "")
    changed = []

    if db_url:
        stored_hashes = _get_stored_hashes(db_url, [d["doc_id"] for d in documents])
        for doc in documents:
            new_hash = _content_hash(doc["content"])
            if stored_hashes.get(doc["doc_id"]) != new_hash:
                changed.append(doc)
    else:
        changed = documents

    if not changed:
        return {"total": len(documents), "changed": 0, "reindexed": 0}

    result = index_batch.remote(changed, database_url, model_name)
    return {
        "total": len(documents),
        "changed": len(changed),
        "reindexed": result["succeeded"],
        "failed": result["failed"],
    }


@app.function(image=indexing_image, gpu="T4", timeout=7200)
def full_rebuild(
    database_url: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Re-embed and re-index the entire corpus.

    Used when the embedding model changes. Fetches all documents from the
    database, re-embeds them with the specified model, and replaces all
    existing embeddings.
    """
    import os

    db_url = database_url or os.environ.get("DATABASE_URL", "")
    if not db_url:
        return {"error": "DATABASE_URL not configured", "status": "failed"}

    documents = _fetch_all_documents(db_url)
    if not documents:
        return {"total": 0, "reindexed": 0, "status": "complete"}

    _clear_all_embeddings(db_url)
    result = index_batch.remote(documents, db_url, model_name)
    return {
        "total": len(documents),
        "reindexed": result["succeeded"],
        "failed": result["failed"],
        "status": "complete",
    }


def _upsert_document(
    database_url: str,
    doc_id: str,
    content: str,
    embedding: list[float],
    content_hash: str,
    metadata: dict | None = None,
) -> None:
    """Upsert a document with its embedding into pgvector."""
    import json
    import psycopg2

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                """INSERT INTO document_embeddings (doc_id, content, embedding, content_hash, metadata)
                VALUES (%s, %s, %s::vector, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    content_hash = EXCLUDED.content_hash,
                    metadata = EXCLUDED.metadata""",
                (doc_id, content, embedding, content_hash, json.dumps(metadata or {})),
            )
        conn.commit()
    finally:
        conn.close()


def _get_stored_hashes(database_url: str, doc_ids: list[str]) -> dict[str, str]:
    """Fetch stored content hashes for given document IDs."""
    import psycopg2

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT doc_id, content_hash FROM document_embeddings WHERE doc_id = ANY(%s)",
                (doc_ids,),
            )
            return dict(cur.fetchall())
    finally:
        conn.close()


def _fetch_all_documents(database_url: str) -> list[dict]:
    """Fetch all documents from the corpus for full rebuild."""
    import psycopg2

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT doc_id, content, metadata FROM document_embeddings")
            return [
                {"doc_id": row[0], "content": row[1], "metadata": row[2]}
                for row in cur.fetchall()
            ]
    finally:
        conn.close()


def _clear_all_embeddings(database_url: str) -> None:
    """Clear all embeddings for full rebuild."""
    import psycopg2

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE document_embeddings SET embedding = NULL")
        conn.commit()
    finally:
        conn.close()
