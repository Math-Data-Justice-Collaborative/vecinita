from httpx import AsyncClient, HTTPStatusError, RequestError

from service_clients import modal_invoker
from shared_schemas.model import PredictRequest, PredictResponse

_UPSTREAM_5XX_MESSAGE = "Upstream model service returned an error; verify deployment health and MODEL_SERVICE_BASE_URL."
_CLIENT_REJECTION_MESSAGE = "Model prediction request was not accepted."
_UNREACHABLE_MESSAGE = (
    "Model service unreachable; verify MODEL_SERVICE_BASE_URL and network connectivity."
)


class ModelUpstreamError(Exception):
    """Stable, client-safe failure from model HTTP calls (FR-002)."""

    def __init__(self, message: str, *, mapped_http_status: int | None = None) -> None:
        self.mapped_http_status = mapped_http_status
        super().__init__(message)


def _map_http_status_error(exc: HTTPStatusError) -> ModelUpstreamError:
    resp = exc.response
    code = resp.status_code if resp is not None else None
    if code is not None and code >= 500:
        return ModelUpstreamError(_UPSTREAM_5XX_MESSAGE, mapped_http_status=502)
    return ModelUpstreamError(_CLIENT_REJECTION_MESSAGE, mapped_http_status=code)


class ModelClient:
    """Async HTTP client for the Vecinita model-service."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def predict(
        self, text: str, model_version: str | None = None
    ) -> PredictResponse:
        """Send a prediction request to model-service."""
        if modal_invoker.modal_function_invocation_enabled():
            try:
                raw = await modal_invoker.model_predict_modal(text, model_version)
                return PredictResponse.model_validate(raw)
            except ModelUpstreamError:
                raise
            except Exception as exc:
                raise ModelUpstreamError(
                    "Model Modal predict RPC failed; verify MODAL_MODEL_APP_NAME, "
                    "MODAL_MODEL_PREDICT_FUNCTION, and Modal credentials.",
                    mapped_http_status=503,
                ) from exc
        payload = PredictRequest(text=text, model_version=model_version)
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/predict",
                    content=payload.model_dump_json(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return PredictResponse.model_validate(response.json())
        except HTTPStatusError as exc:
            raise _map_http_status_error(exc) from exc
        except RequestError as exc:
            raise ModelUpstreamError(
                _UNREACHABLE_MESSAGE, mapped_http_status=503
            ) from exc

    async def health(self) -> dict:
        """Check model-service health."""
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except HTTPStatusError as exc:
            raise _map_http_status_error(exc) from exc
        except RequestError as exc:
            raise ModelUpstreamError(
                _UNREACHABLE_MESSAGE, mapped_http_status=503
            ) from exc
