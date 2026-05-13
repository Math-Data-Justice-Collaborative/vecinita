"""FastAPI application factory with Modal ASGI integration."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vecinita_scraper.api.routes import router as jobs_router
from vecinita_scraper.core.config import get_config
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import ScraperHealthResponse

logger = get_logger(__name__)
_PUBLIC_PATHS = {"/", "/health", "/openapi.json", "/docs", "/redoc"}


def _is_public_path(path: str) -> bool:
    if path in _PUBLIC_PATHS:
        return True
    return path.startswith("/docs/") or path.startswith("/redoc/")


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def _token_fingerprint(token: str) -> str:
    if len(token) <= 8:
        return token
    return f"{token[:4]}...{token[-4:]}"


def _allowed_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    config = get_config()
    allowed_origins = _allowed_origins()

    app = FastAPI(
        title="Vecinita Scraper",
        description="Serverless web scraping pipeline with job queue management",
        version="0.1.0",
    )

    @app.middleware("http")
    async def auth_guard(request: Request, call_next: Any) -> Any:
        """Enforce API key auth for protected routes."""
        if request.method == "OPTIONS" or _is_public_path(request.url.path):
            return await call_next(request)

        if config.auth.debug_bypass_auth:
            logger.warning(
                "Auth bypass enabled for request",
                method=request.method,
                path=request.url.path,
                environment=config.environment,
            )
            return await call_next(request)

        token = _extract_bearer_token(request.headers.get("Authorization"))
        if token is None:
            logger.warning(
                "Missing or invalid Authorization header",
                method=request.method,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        if token not in config.auth.api_keys:
            logger.warning(
                "Rejected API key",
                method=request.method,
                path=request.url.path,
                api_key_fingerprint=_token_fingerprint(token),
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key"},
            )

        request.state.api_key_fingerprint = _token_fingerprint(token)
        return await call_next(request)

    # Register CORS after auth so CORS wraps auth: auth_guard JSONResponses still get ACAO headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allowed_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any) -> Any:
        """Log HTTP requests."""
        logger.info("HTTP request", method=request.method, path=request.url.path)
        response = await call_next(request)
        logger.info(
            "HTTP response",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response

    @app.get("/", tags=["meta"], summary="Service index")
    async def root() -> dict[str, str]:
        """Public landing; job routes still need ``Authorization: Bearer``."""
        return {
            "service": "vecinita-scraper",
            "health": "/health",
            "openapi": "/openapi.json",
            "documentation": "/docs",
            "note": "Job and scrape endpoints require a valid SCRAPER_API_KEYS bearer token.",
        }

    @app.get("/health", response_model=ScraperHealthResponse, tags=["health"])
    async def health() -> ScraperHealthResponse:
        """Health check endpoint."""
        return ScraperHealthResponse(status="ok", service="vecinita-scraper")

    app.include_router(jobs_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions."""
        logger.exception("Unhandled exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app
