"""Sync-message pact payloads: scraper ``EmbeddingClient`` ↔ Modal embedding functions (tests only).

Mirrors ``vecinita_scraper.clients.embedding_client.EmbeddingClient._modal_request``:

- ``GET /`` → ``embed_query.remote.aio("health")`` (model root metadata).
- ``POST /embed/batch`` → ``embed_batch.remote.aio(queries)``.
"""

from __future__ import annotations

SCRAPER_EMBEDDING_MODAL_REQUESTS: dict[str, dict] = {
    "scraper_modal_embed_config_probe": {
        "fn": "embed_query",
        "call": {"kind": "single_text", "text": "health"},
    },
    "scraper_modal_embed_batch": {
        "fn": "embed_batch",
        "call": {"kind": "queries", "queries": ["chunk-a", "chunk-b"]},
    },
}

SCRAPER_EMBEDDING_MODAL_RESPONSES: dict[str, dict] = {
    "scraper_modal_embed_config_probe": {
        "model": "BAAI/bge-small-en-v1.5",
        "dimension": 384,
        "embedding_dimensions": 384,
        "max_tokens": 1024,
        "batch_size": 100,
    },
    "scraper_modal_embed_batch": {
        "embeddings": [[0.1, 0.2], [0.3, 0.4]],
        "model": "BAAI/bge-small-en-v1.5",
        "dimension": 384,
        "dimensions": 384,
    },
}
