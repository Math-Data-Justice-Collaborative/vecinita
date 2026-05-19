"""HTTP client for Modal FastEmbed (384-dim)."""

from vecinita_embedding_client.client import (
    EMBEDDING_DIMENSION,
    EmbeddingClient,
    EmbeddingClientError,
)

__version__ = "0.1.0"

__all__ = [
    "EMBEDDING_DIMENSION",
    "EmbeddingClient",
    "EmbeddingClientError",
]
