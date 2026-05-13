from httpx import AsyncClient, HTTPStatusError, RequestError, Response
from pydantic import HttpUrl

from service_clients import modal_invoker
from shared_schemas.scraper import ScrapeRequest, ScrapeResult

_UPSTREAM_5XX_MESSAGE = "Upstream scraper service returned an error; verify scraper health and SCRAPER_SERVICE_BASE_URL."
_CLIENT_REJECTION_MESSAGE = "Scraper rejected the request."
_UNREACHABLE_MESSAGE = "Scraper service unreachable; verify SCRAPER_SERVICE_BASE_URL and network connectivity."


class ScraperUpstreamError(Exception):
    """Stable, client-safe failure from scraper HTTP calls (see FR-002 in platform spec)."""

    def __init__(self, message: str, *, mapped_http_status: int | None = None) -> None:
        self.mapped_http_status = mapped_http_status
        super().__init__(message)


def _map_http_status_error(exc: HTTPStatusError) -> ScraperUpstreamError:
    resp = exc.response
    code = resp.status_code if resp is not None else None
    if code is not None and code >= 500:
        return ScraperUpstreamError(_UPSTREAM_5XX_MESSAGE, mapped_http_status=502)
    return ScraperUpstreamError(_CLIENT_REJECTION_MESSAGE, mapped_http_status=code)


class ScraperClient:
    """Async HTTP client for the Vecinita scraper-service."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def scrape(self, url: str, depth: int = 1) -> ScrapeResult:
        """Send a scrape request to scraper-service."""
        payload = ScrapeRequest(url=HttpUrl(url), depth=depth)
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/scrape",
                    content=payload.model_dump_json(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return ScrapeResult.model_validate(response.json())
        except HTTPStatusError as exc:
            raise _map_http_status_error(exc) from exc
        except RequestError as exc:
            raise ScraperUpstreamError(
                _UNREACHABLE_MESSAGE, mapped_http_status=503
            ) from exc

    async def health(self) -> dict:
        """Check scraper-service health."""
        if modal_invoker.modal_function_invocation_enabled():
            try:
                return await modal_invoker.scraper_health_modal()
            except ScraperUpstreamError:
                raise
            except Exception as exc:
                raise ScraperUpstreamError(
                    "Scraper Modal health_check failed; verify MODAL_SCRAPER_APP_NAME, "
                    "MODAL_SCRAPER_HEALTH_FUNCTION, and Modal credentials.",
                    mapped_http_status=503,
                ) from exc
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except HTTPStatusError as exc:
            raise _map_http_status_error(exc) from exc
        except RequestError as exc:
            raise ScraperUpstreamError(
                _UNREACHABLE_MESSAGE, mapped_http_status=503
            ) from exc

    async def forward_jobs(
        self,
        method: str,
        subpath: str,
        *,
        query: str = "",
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Forward HTTP to the scraper ``/jobs`` subtree (same ``base_url`` host).

        Used by the data-management API app to proxy operator job CRUD without exposing a
        separate scraper hostname to browsers (**FR-001**). Does not raise on 4xx/5xx so the
        caller can mirror upstream status codes and bodies.
        """
        subpath = (subpath or "").strip("/")
        url = f"{self.base_url}/jobs" + (f"/{subpath}" if subpath else "")
        if query:
            url = f"{url}?{query}"
        hdrs: dict[str, str] = {"User-Agent": "vecinita-dm-api-jobs-proxy/1.0"}
        if headers:
            hdrs.update(headers)
        if content is not None and "content-type" not in {k.lower() for k in hdrs}:
            hdrs["Content-Type"] = "application/json"
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                return await client.request(method.upper(), url, content=content, headers=hdrs)
        except RequestError as exc:
            raise ScraperUpstreamError(
                _UNREACHABLE_MESSAGE, mapped_http_status=503
            ) from exc
