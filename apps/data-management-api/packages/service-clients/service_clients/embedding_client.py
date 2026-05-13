from httpx import AsyncClient, HTTPStatusError, RequestError

from service_clients import modal_invoker
from shared_schemas.embedding import EmbedRequest, EmbedResponse

_UPSTREAM_5XX_MESSAGE = (
    "Upstream embedding service returned an error; verify deployment health and "
    "EMBEDDING_SERVICE_BASE_URL."
)
_CLIENT_REJECTION_MESSAGE = "Embedding request was not accepted."
_UNREACHABLE_MESSAGE = "Embedding service unreachable; verify EMBEDDING_SERVICE_BASE_URL and network connectivity."


class EmbeddingUpstreamError(Exception):
    """Stable, client-safe failure from embedding HTTP calls (FR-002)."""

    def __init__(self, message: str, *, mapped_http_status: int | None = None) -> None:
        self.mapped_http_status = mapped_http_status
        super().__init__(message)


def _map_http_status_error(exc: HTTPStatusError) -> EmbeddingUpstreamError:
    resp = exc.response
    code = resp.status_code if resp is not None else None
    if code is not None and code >= 500:
        return EmbeddingUpstreamError(_UPSTREAM_5XX_MESSAGE, mapped_http_status=502)
    return EmbeddingUpstreamError(_CLIENT_REJECTION_MESSAGE, mapped_http_status=code)


class EmbeddingClient:
    """Async HTTP client for the Vecinita embedding-service."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def embed(self, text: str, model_version: str | None = None) -> EmbedResponse:
        """Send an embedding request to embedding-service."""
        if modal_invoker.modal_function_invocation_enabled():
            try:
                raw = await modal_invoker.embedding_embed_single_modal(text, model_version)
                return EmbedResponse.model_validate(raw)
            except EmbeddingUpstreamError:
                raise
            except Exception as exc:
                raise EmbeddingUpstreamError(
                    "Embedding Modal embed_query failed; verify MODAL_EMBEDDING_* env and credentials.",
                    mapped_http_status=503,
                ) from exc
        payload = EmbedRequest(text=text, model_version=model_version)
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embed",
                    content=payload.model_dump_json(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return EmbedResponse.model_validate(response.json())
        except HTTPStatusError as exc:
            raise _map_http_status_error(exc) from exc
        except RequestError as exc:
            raise EmbeddingUpstreamError(
                _UNREACHABLE_MESSAGE, mapped_http_status=503
            ) from exc

    async def health(self) -> dict:
        """Check embedding-service health."""
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except HTTPStatusError as exc:
            raise _map_http_status_error(exc) from exc
        except RequestError as exc:
            raise EmbeddingUpstreamError(
                _UNREACHABLE_MESSAGE, mapped_http_status=503
            ) from exc
