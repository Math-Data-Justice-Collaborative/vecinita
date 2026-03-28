"""
Supabase Edge Function Embedding Client

Replaces local embedding models with Supabase Edge Function calls.
Zero memory overhead, centralized model management.
"""

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from supabase import Client
else:
    Client = Any

logger = logging.getLogger(__name__)


class SupabaseEmbeddings:
    """LangChain-compatible embedding client using Supabase Edge Function."""

    def __init__(self, supabase_client: Client, function_name: str = "generate-embedding"):
        """
        Initialize the Supabase embedding client.

        Args:
            supabase_client: Authenticated Supabase client
            function_name: Name of the edge function (default: generate-embedding)
        """
        self.supabase = supabase_client
        self.function_name = function_name
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.dimension = 384

        logger.info(f"Initialized SupabaseEmbeddings with function '{function_name}'")

    def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            logger.debug(f"Generating embedding for query (length: {len(text)})")

            response = self.supabase.functions.invoke(
                self.function_name, invoke_options={"body": {"text": text}}
            )

            if response.status_code != 200:  # type: ignore[union-attr]
                raise RuntimeError(
                    f"Edge function returned status {response.status_code}: {response.data}"  # type: ignore[union-attr]
                )

            # Safely extract data from response (union type narrowing)
            if hasattr(response, "json") and callable(response.json):
                data = response.json()
            elif hasattr(response, "data"):
                data = response.data
            else:
                raise RuntimeError(f"Unexpected response type: {type(response)}")

            embedding = data.get("embedding") if isinstance(data, dict) else None

            if not embedding or not isinstance(embedding, list):
                raise ValueError(f"Invalid embedding response format: {data}")

            logger.debug(f"Generated embedding with dimension {len(embedding)}")
            return cast(list[float], embedding)

        except Exception as e:
            logger.error(f"Error generating embedding via edge function: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}") from e

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple documents (batch).

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            logger.debug(f"Generating embeddings for {len(texts)} documents")

            response = self.supabase.functions.invoke(
                self.function_name, invoke_options={"body": {"texts": texts}}
            )

            if response.status_code != 200:  # type: ignore[union-attr]
                raise RuntimeError(
                    f"Edge function returned status {response.status_code}: {response.data}"  # type: ignore[union-attr]
                )

            # Safely extract data from response (union type narrowing)
            if hasattr(response, "json") and callable(response.json):
                data = response.json()
            elif hasattr(response, "data"):
                data = response.data
            else:
                raise RuntimeError(f"Unexpected response type: {type(response)}")

            embeddings = data.get("embeddings") if isinstance(data, dict) else None

            if not embeddings or not isinstance(embeddings, list):
                raise ValueError(f"Invalid embeddings response format: {data}")

            logger.debug(f"Generated {len(embeddings)} embeddings")
            return cast(list[list[float]], embeddings)

        except Exception as e:
            logger.error(f"Error generating batch embeddings via edge function: {e}")
            # Fallback to individual calls if batch fails
            logger.warning("Falling back to individual embedding calls")
            return [self.embed_query(text) for text in texts]

    async def aembed_query(self, text: str) -> list[float]:
        """Async version of embed_query (delegates to sync for now)."""
        return self.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async version of embed_documents (delegates to sync for now)."""
        return self.embed_documents(texts)


def create_embedding_model(supabase_client: Client) -> SupabaseEmbeddings:
    """
    Factory function to create embedding model using Supabase Edge Function.

    Args:
        supabase_client: Authenticated Supabase client

    Returns:
        SupabaseEmbeddings instance
    """
    return SupabaseEmbeddings(supabase_client)
