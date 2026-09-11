"""Shared CORS configuration for browser-facing FastAPI apps."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import FastAPI

_LOGGER = logging.getLogger(__name__)


def parse_cors_origins(env_value: str | None = None) -> list[str]:
    """Parse comma-separated origins from VECINITA_CORS_ORIGINS."""
    raw = env_value if env_value is not None else os.environ.get("VECINITA_CORS_ORIGINS", "")
    return [part.strip() for part in raw.split(",") if part.strip()]


def prod_cors_origins_cover_frontends(
    origins: list[str],
    *,
    frontend_origins: tuple[str, ...] | list[str],
) -> bool:
    """Return True when every frontend origin is present in the CORS allow-list.

    Used to catch ADR-054 drift where staging FE origins were synced onto prod
    APIs (BUG-2026-09-10).
    """
    allowed = {origin.rstrip("/") for origin in origins}
    required = [origin.rstrip("/") for origin in frontend_origins if origin.strip()]
    if not required:
        return False
    return all(origin in allowed for origin in required)


def cors_origins_contain_staging_hosts(origins: list[str]) -> bool:
    """Return True when any origin host looks like a staging Vecinita frontend.

    Prod API CORS must not include staging FE hosts (ADR-054 isolation;
    BUG-2026-09-10 follow-up).
    """
    for origin in origins:
        host = origin.rstrip("/").removeprefix("https://").removeprefix("http://").split("/")[0]
        if "vecinita-staging-" in host.lower():
            return True
    return False


def cors_headers_for_request(request: Request, origins: list[str]) -> dict[str, str]:
    """Return Access-Control-* headers when the request Origin is allowed."""
    origin = request.headers.get("origin")
    if origin and origin in origins:
        return {"Access-Control-Allow-Origin": origin}
    return {}


def install_cors_exception_handlers(app: FastAPI, origins: list[str]) -> None:
    """Ensure unhandled 500 responses include CORS headers for browser clients."""
    if not origins:
        return

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        _LOGGER.exception("Unhandled exception on %s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
            headers=cors_headers_for_request(request, origins),
        )


def configure_cors(
    app: FastAPI,
    *,
    extra_allow_headers: list[str] | None = None,
    env_value: str | None = None,
) -> list[str]:
    """Attach CORSMiddleware when origins are configured. Returns allowed origins."""
    origins = parse_cors_origins(env_value)
    if not origins:
        return []
    headers = ["Content-Type", "Authorization"]
    if extra_allow_headers:
        headers.extend(extra_allow_headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=headers,
    )
    install_cors_exception_handlers(app, origins)
    return origins
