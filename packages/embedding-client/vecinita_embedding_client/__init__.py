"""HTTP client for Modal embeddings (384-dim, ADR-048 / F70)."""

from vecinita_embedding_client.client import (
    EMBEDDING_DIMENSION,
    EmbeddingClient,
    EmbeddingClientError,
)
from vecinita_embedding_client.prefixes import (
    apply_embed_prefix,
    assert_embedding_dimension,
    e5_prefixes_enabled,
    is_e5_family_model,
    resolve_embed_runtime,
)

__version__ = "0.1.0"

__all__ = [
    "EMBEDDING_DIMENSION",
    "EmbeddingClient",
    "EmbeddingClientError",
    "apply_embed_prefix",
    "assert_embedding_dimension",
    "e5_prefixes_enabled",
    "is_e5_family_model",
    "resolve_embed_runtime",
]
