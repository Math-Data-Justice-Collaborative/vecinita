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

from src.config import rewrite_deprecated_modal_embedding_host
from src.services.modal.invoker import modal_function_invocation_enabled

logger = logging.getLogger(__name__)


def _running_on_render() -> bool:
    """Return True when running in a Render environment."""
    return bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))


def _hostname_and_port(url: str) -> tuple[str, int | None]:
    parsed = urlparse(url)
    return (parsed.hostname or "", parsed.port)


def _safe_error_detail(exc: Exception) -> str:
    """Return concise error diagnostics for connection failures."""
    if isinstance(exc, httpx.HTTPStatusError):
        req = exc.request
        res = exc.response
        return (
            f"HTTPStatusError(method={req.method}, url={req.url}, "
            f"status={res.status_code}, reason={res.reason_phrase})"
        )
    if isinstance(exc, httpx.RequestError):
        req = exc.request
        return f"RequestError(method={req.method}, url={req.url}, detail={exc})"
    return f"{type(exc).__name__}: {exc}"


def _drop_headers(headers: dict[str, str], names: set[str]) -> dict[str, str]:
    """Return a copy of *headers* with case-insensitive names removed."""
    return {k: v for k, v in headers.items() if k.lower() not in names}


def _rewrite_deprecated_embedding_host(url: str) -> str | None:
    """Compatibility alias for :func:`rewrite_deprecated_modal_embedding_host`."""
    return rewrite_deprecated_modal_embedding_host(url)


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
            base_url:   Base URL of a **non-Modal** HTTP embedding microservice
                        (e.g. ``http://embedding:8001``). Do not use ``*.modal.run`` here;
                        use :func:`create_embedding_client` with ``MODAL_FUNCTION_INVOCATION``
                        enabled to call Modal ``embed_query`` / ``embed_batch`` functions.
            timeout:    HTTP request timeout in seconds (default: 30).
            auth_token: Shared-secret token sent as both
                        ``x-embedding-service-token`` and
                        ``Authorization: Bearer <token>`` headers.  If
                        omitted the following env vars are checked in order:
                        ``EMBEDDING_SERVICE_AUTH_TOKEN``,
                        ``MODAL_TOKEN_SECRET``,
                        ``MODAL_TOKEN_SECRET``.
        """
        self.base_url = base_url.rstrip("/")
        if "modal.run" in self.base_url.lower():
            if modal_function_invocation_enabled():
                raise ValueError(
                    "Do not point EmbeddingServiceClient at *.modal.run when "
                    "MODAL_FUNCTION_INVOCATION is enabled; use create_embedding_client(...) "
                    "which calls Modal functions instead of HTTP."
                )
            raise ValueError(
                "EmbeddingServiceClient cannot use *.modal.run without Modal function "
                "invocation; set MODAL_FUNCTION_INVOCATION=auto or 1 (with MODAL_TOKEN_*), "
                "or use http://localhost:8001 (or another non-Modal HTTP embedding service)."
            )
        self.timeout = timeout
        self.auth_token = (
            auth_token
            or os.getenv("EMBEDDING_SERVICE_AUTH_TOKEN")
            or os.getenv("MODAL_TOKEN_SECRET")
            or os.getenv("MODAL_TOKEN_SECRET")
        )
        headers = {}
        if self.auth_token:
            headers["x-embedding-service-token"] = self.auth_token
            headers["Authorization"] = f"Bearer {self.auth_token}"
        self.client = httpx.Client(timeout=timeout, headers=headers)
        logger.info("✅ Embedding Service Client initialized: %s", self.base_url)
        logger.info(
            "Embedding client auth/header profile: has_auth_token=%s running_on_render=%s",
            bool(self.auth_token),
            _running_on_render(),
        )

    def _is_local_embedding_url(self, base_url: str) -> bool:
        host, port = _hostname_and_port(base_url)
        return host in {"localhost", "127.0.0.1", "embedding-service"} and port == 8001

    def _headers_for_base_url(self, base_url: str) -> dict[str, str]:
        """Build per-target concrete headers so httpx never receives None values."""
        headers = dict(self.client.headers)

        if self._is_local_embedding_url(base_url):
            if self.auth_token:
                headers["x-embedding-service-token"] = self.auth_token
                headers["Authorization"] = f"Bearer {self.auth_token}"
            return headers

        # Fallback to client default headers for unknown endpoints.
        return headers

    def _candidate_base_urls(self) -> list[str]:
        """Return ordered base URLs to try for embedding requests."""
        parsed = urlparse(self.base_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        scheme = parsed.scheme or "http"

        # On Render, avoid localhost candidates because each service runs in its
        # own isolated container and localhost won't reach sibling services.
        if _running_on_render():
            local_candidates: list[str] = []
        else:
            local_candidates = [
                "http://localhost:8001",
                "http://127.0.0.1:8001",
            ]

        # In local dev, prioritize known-local service URLs before any stale
        # remote URL that may have been left in EMBEDDING_SERVICE_URL.
        local_first = (not _running_on_render()) and host not in {
            "",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "embedding-service",
        }

        candidates: list[str] = []
        if local_first:
            candidates.extend(local_candidates)
            candidates.append(self.base_url)
        else:
            candidates.append(self.base_url)
            candidates.extend(local_candidates)

        # Also include explicit endpoint env vars so one stale variable does not
        # block startup when another valid endpoint is configured.
        env_candidates = [
            os.getenv("EMBEDDING_UPSTREAM_URL", "").strip(),
        ]
        for candidate in env_candidates:
            if candidate:
                candidates.append(candidate.rstrip("/"))

        # Compatibility fallback for legacy embeddingservicecontainer host naming.
        rewritten_candidates: list[str] = []
        for candidate in candidates:
            rewritten = _rewrite_deprecated_embedding_host(candidate)
            if rewritten:
                rewritten_candidates.append(rewritten)
        candidates.extend(rewritten_candidates)

        discovered_cloud_run = self._discover_cloud_run_url()
        if discovered_cloud_run:
            candidates.append(discovered_cloud_run)

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
                response = self.client.post(
                    f"{base}{endpoint}",
                    json=payload,
                    headers=self._headers_for_base_url(base),
                )
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
        candidates = self._candidate_base_urls()
        logger.info("Embedding health validation candidates=%s", candidates)

        last_error: Exception | None = None
        for base in candidates:
            try:
                response = self.client.get(
                    f"{base}/health",
                    headers=self._headers_for_base_url(base),
                )
                response.raise_for_status()
                self.base_url = base
                logger.info(f"✅ Embedding service health check passed at {base}")
                return base
            except Exception as exc:
                last_error = exc

                status_code = (
                    exc.response.status_code
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None
                    else None
                )

                if status_code == 404:
                    try:
                        logger.warning(
                            "Embedding /health returned 404 at %s; retrying root path to detect "
                            "endpoint prefix mismatch.",
                            base,
                        )
                        fallback = self.client.get(
                            base,
                            headers=self._headers_for_base_url(base),
                        )
                        fallback.raise_for_status()
                        self.base_url = base
                        logger.info(
                            "✅ Embedding service root check passed at %s (no /health route)",
                            base,
                        )
                        return base
                    except Exception as root_exc:
                        last_error = root_exc

                logger.warning(
                    "Embedding service health check failed at %s: %s",
                    base,
                    _safe_error_detail(exc),
                )

        logger.error(
            "Embedding validation exhausted all candidates. configured_base_url=%s "
            "candidates=%s last_error=%s",
            self.base_url,
            candidates,
            _safe_error_detail(last_error) if last_error else "none",
        )

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
            response = self._post_with_fallback("/embed", {"text": text})
            payload = response.json()
            if isinstance(payload, dict):
                return cast(list[float], payload.get("embedding", []))
            return []
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 422:
                preview = (exc.response.text or "")[:800]
                logger.warning("Embedding /embed returned 422; body (truncated): %s", preview)
            logger.error("❌ Error calling embedding service: %s", exc)
            raise
        except Exception as e:
            logger.error("❌ Error calling embedding service: %s", e)
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
    embedding_service_url: str = "http://localhost:8001",
    validate_on_init: bool = False,
    auth_token: str | None = None,
) -> Embeddings:
    """
    Factory: HTTP embedding microservice, or Modal SDK when ``MODAL_FUNCTION_INVOCATION`` is on.

    When Modal function invocation is enabled, ``embedding_service_url`` is only used as a
    logical label (``ModalSdkEmbeddings.base_url``); vectors come from ``embed_query`` /
    ``embed_batch`` Modal functions, not ``*.modal.run`` HTTP.
    """
    if modal_function_invocation_enabled():
        from src.embedding_service.modal_embeddings import ModalSdkEmbeddings

        emb = ModalSdkEmbeddings(logical_url=embedding_service_url)
        if validate_on_init:
            emb.validate_connection()
        return emb

    client = EmbeddingServiceClient(base_url=embedding_service_url, auth_token=auth_token)
    if validate_on_init:
        client.validate_connection()
    return client
