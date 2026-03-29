"""
Embedding Service Client - HTTP client for calling the embedding microservice.

Provides a LangChain-compatible embeddings class that calls the dedicated
embedding service instead of loading models locally.
"""

import logging
import os
import subprocess
from typing import cast
from urllib.parse import urlparse, urlunparse

import httpx
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class EmbeddingServiceClient(Embeddings):
    """
    LangChain-compatible embeddings using HTTP calls to embedding microservice.

    This allows the agent to be lightweight (no embedding models) while delegating
    embedding generation to a separate Render service.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: int = 30,
        auth_token: str | None = None,
    ):
        """
        Initialize embedding service client.

        Args:
            base_url:   Base URL of the embedding service.  On Render this
                        should be the modal-proxy embedding prefix, e.g.
                        ``http://vecinita-modal-proxy-v1:10000/embedding``
                        (default: ``http://localhost:8001``).
            timeout:    HTTP request timeout in seconds (default: 30).
            auth_token: Shared-secret token sent as both
                        ``x-embedding-service-token`` and
                        ``Authorization: Bearer <token>`` headers.  If
                        omitted the following env vars are checked in order:
                        ``EMBEDDING_SERVICE_AUTH_TOKEN``,
                        ``MODAL_API_PROXY_SECRET``, ``MODAL_API_KEY``,
                        ``MODAL_TOKEN_SECRET``,
                        ``MODAL_API_TOKEN_SECRET``.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auth_token = (
            auth_token
            or os.getenv("EMBEDDING_SERVICE_AUTH_TOKEN")
            or os.getenv("MODAL_API_PROXY_SECRET")
            or os.getenv("MODAL_API_KEY")
            or os.getenv("MODAL_TOKEN_SECRET")
            or os.getenv("MODAL_API_TOKEN_SECRET")
        )
        self.modal_proxy_key = (
            os.getenv("MODAL_API_KEY")
            or os.getenv("MODAL_API_TOKEN_ID")
            or os.getenv("MODAL_TOKEN_ID")
        )
        self.modal_proxy_secret = os.getenv("MODAL_API_PROXY_SECRET") or os.getenv(
            "MODAL_TOKEN_SECRET"
        )
        self.proxy_auth_token = (
            os.getenv("PROXY_AUTH_TOKEN")
            or os.getenv("MODAL_PROXY_AUTH_TOKEN")
            or os.getenv("X_PROXY_TOKEN")
        )
        headers = {}
        if self.auth_token:
            headers["x-embedding-service-token"] = self.auth_token
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if self.proxy_auth_token:
            headers["X-Proxy-Token"] = self.proxy_auth_token
        if self.modal_proxy_key and self.modal_proxy_secret:
            headers["Modal-Key"] = self.modal_proxy_key
            headers["Modal-Secret"] = self.modal_proxy_secret
        self.client = httpx.Client(timeout=timeout, headers=headers)
        self._single_embed_field = "text"
        logger.info(f"✅ Embedding Service Client initialized: {self.base_url}")

    def _candidate_base_urls(self) -> list[str]:
        """Return ordered base URLs to try for embedding requests."""
        candidates = [self.base_url]

        discovered_cloud_run = self._discover_cloud_run_url()
        if discovered_cloud_run:
            candidates.append(discovered_cloud_run)

        parsed = urlparse(self.base_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        scheme = parsed.scheme or "http"

        # Local development safety net: if docker hostname isn't resolvable,
        # try localhost/127.0.0.1 on same port.
        if host == "embedding-service":
            for fallback_host in ("localhost", "127.0.0.1"):
                fallback = urlunparse(
                    (
                        scheme,
                        f"{fallback_host}:{port}",
                        "",
                        "",
                        "",
                        "",
                    )
                ).rstrip("/")
                candidates.append(fallback)

        # De-duplicate while preserving order.
        return list(dict.fromkeys(candidates))

    def _discover_cloud_run_url(self) -> str | None:
        """Discover embedding service URL from Cloud Run via gcloud CLI.

        Activated only when enough context is present via environment variables.
        """
        service_name = os.getenv("EMBEDDING_CLOUD_RUN_SERVICE") or os.getenv(
            "CLOUD_RUN_EMBED_SERVICE"
        )
        project = os.getenv("GCP_PROJECT_ID") or os.getenv("PROJECT_ID")
        region = os.getenv("GCP_REGION") or os.getenv("REGION")

        if not service_name or not project or not region:
            return None

        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "run",
                    "services",
                    "describe",
                    service_name,
                    "--region",
                    region,
                    "--project",
                    project,
                    "--format=value(status.url)",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=8,
            )
            url = (result.stdout or "").strip().rstrip("/")
            if result.returncode == 0 and url.startswith("https://"):
                logger.info("Discovered Cloud Run embedding URL via gcloud: %s", url)
                return url
            stderr = (result.stderr or "").strip()
            if stderr:
                logger.warning("Cloud Run URL discovery failed: %s", stderr)
        except Exception as exc:
            logger.warning("Cloud Run URL discovery raised error: %s", exc)

        return None

    def _post_with_fallback(
        self,
        endpoint: str,
        payload: dict,
        suppress_status_log: set[int] | None = None,
    ):
        """POST to embedding service, trying fallback URLs when needed."""
        last_error: Exception | None = None
        for base in self._candidate_base_urls():
            try:
                response = self.client.post(f"{base}{endpoint}", json=payload)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                status_code = (
                    exc.response.status_code
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None
                    else None
                )
                if suppress_status_log and status_code in suppress_status_log:
                    logger.debug(
                        "Embedding service call returned expected status %s at %s%s",
                        status_code,
                        base,
                        endpoint,
                    )
                else:
                    logger.warning(f"Embedding service call failed at {base}{endpoint}: {exc}")

        if last_error is not None:
            raise last_error
        raise RuntimeError("Embedding service request failed without an explicit error")

    def validate_connection(self) -> str:
        """Validate embedding service availability and bind client to first healthy base URL.

        Returns:
            The active base URL selected after health check.

        Raises:
            RuntimeError if no candidate URL is reachable.
        """
        last_error: Exception | None = None
        for base in self._candidate_base_urls():
            try:
                response = self.client.get(f"{base}/health")
                response.raise_for_status()
                self.base_url = base
                logger.info(f"✅ Embedding service health check passed at {base}")
                return base
            except Exception as exc:
                last_error = exc
                logger.warning(f"Embedding service health check failed at {base}: {exc}")

        raise RuntimeError(
            "Embedding service is unavailable at all configured endpoints. "
            "Ensure EMBEDDING_SERVICE_URL is reachable and the embedding service is running."
        ) from last_error

    def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            try:
                response = self._post_with_fallback(
                    "/embed",
                    {self._single_embed_field: text},
                    suppress_status_log={422},
                )
            except httpx.HTTPStatusError as exc:
                # Some deployed Modal embedding endpoints still expect `query` instead of `text`.
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code == 422:
                    self._single_embed_field = "query"
                    response = self._post_with_fallback("/embed", {"query": text})
                else:
                    raise
            payload = response.json()
            if isinstance(payload, dict):
                return cast(list[float], payload.get("embedding", []))
            return []
        except Exception as e:
            logger.error(f"❌ Error calling embedding service: {e}")
            raise

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple documents (batch).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            try:
                response = self._post_with_fallback("/embed-batch", {"texts": texts})
            except Exception:
                response = self._post_with_fallback("/embed/batch", {"texts": texts})
            payload = response.json()
            if isinstance(payload, dict):
                return cast(list[list[float]], payload.get("embeddings", []))
            return []
        except Exception as e:
            logger.error(f"❌ Error calling embedding service: {e}")
            raise

    async def aembed_query(self, text: str) -> list[float]:
        """Async version of embed_query (delegates to sync for now)."""
        return self.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
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
    validate_on_init: bool = False,
    auth_token: str | None = None,
) -> EmbeddingServiceClient:
    """
    Factory function to create embedding service client.

    Args:
        embedding_service_url: URL of embedding service
                              (default: http://embedding-service:8001 for Docker)

    Returns:
        EmbeddingServiceClient instance
    """
    client = EmbeddingServiceClient(base_url=embedding_service_url, auth_token=auth_token)
    if validate_on_init:
        client.validate_connection()
    return client
