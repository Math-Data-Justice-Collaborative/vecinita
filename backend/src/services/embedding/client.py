"""
Embedding Service Client - HTTP client for calling the embedding microservice.

Provides a LangChain-compatible embeddings class that calls the dedicated
embedding service instead of loading models locally.
"""

import logging
from typing import List

import httpx
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class EmbeddingServiceClient(Embeddings):
    """
    LangChain-compatible embeddings using HTTP calls to embedding microservice.

    This allows the agent to be lightweight (no embedding models) while delegating
    embedding generation to a separate Render service.
    """

    def __init__(self, base_url: str = "http://localhost:8001", timeout: int = 30):
        """
        Initialize embedding service client.

        Args:
            base_url: URL of embedding service (default: http://localhost:8001)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        logger.info(f"✅ Embedding Service Client initialized: {self.base_url}")

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.post(
                f"{self.base_url}/embed", json={"text": text}
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"❌ Error calling embedding service: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents (batch).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.post(
                f"{self.base_url}/embed-batch", json={"texts": texts}
            )
            response.raise_for_status()
            return response.json()["embeddings"]
        except Exception as e:
            logger.error(f"❌ Error calling embedding service: {e}")
            raise

    async def aembed_query(self, text: str) -> List[float]:
        """Async version of embed_query (delegates to sync for now)."""
        return self.embed_query(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async version of embed_documents (delegates to sync for now)."""
        return self.embed_documents(texts)

    def __del__(self):
        """Cleanup client on deletion."""
        try:
            self.client.close()
        except Exception:
            pass


def create_embedding_client(
    embedding_service_url: str = "http://embedding-service:8001",
) -> EmbeddingServiceClient:
    """
    Factory function to create embedding service client.

    Args:
        embedding_service_url: URL of embedding service
                              (default: http://embedding-service:8001 for Docker)

    Returns:
        EmbeddingServiceClient instance
    """
    return EmbeddingServiceClient(base_url=embedding_service_url)
