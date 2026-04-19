"""
Unified API Gateway - Main FastAPI Application

Consolidates Q&A, scraping, embeddings, and admin endpoints into a single API.
Serves as the primary entry point for all backend services.

Port: 8004 (by default)
"""

# ruff: noqa: E402, I001

import os
import logging
import asyncio
import socket
import warnings
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# Suppress non-blocking transformers advisory on CPU-only environments.
# This warning appears when PyTorch/TensorFlow/Flax are not installed but
# doesn't prevent embedding service (HTTP-based) from functioning.
warnings.filterwarnings(
    "ignore",
    message=".*None of PyTorch.*TensorFlow.*Flax have been found.*",
    category=UserWarning,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Load environment with explicit precedence:
# runtime shell env > root .env > backend/.env defaults.
load_dotenv(_PROJECT_ROOT / ".env", override=False)
load_dotenv(_BACKEND_ROOT / ".env", override=False)

from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .middleware import (
    AuthenticationMiddleware,
    CorrelationIdMiddleware,
    RateLimitingMiddleware,
)
from .models import (
    GatewayConfig,
    GatewayPublicRootResponse,
    HealthCheck,
    IntegrationComponentStatus,
    IntegrationsStatus,
)
from .router_ask import router as ask_router
from .router_documents import router as documents_router
from .router_embed import router as embed_router
from .router_modal_jobs import router as modal_jobs_router

try:
    from .router_scrape import router as scrape_router
except ModuleNotFoundError as exc:
    # Scraper stack has optional dependencies (e.g. langchain_community).
    # Keep gateway importable for routes that do not depend on scraper features.
    logging.getLogger(__name__).warning(
        "Scrape router disabled because optional dependency is missing: %s",
        exc,
    )
    scrape_router = None

# ============================================================================
# Configuration
# ============================================================================


def _running_on_render() -> bool:
    return bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))


# Import normalized endpoints from central config (ensures consistency across services).
# config._normalize_internal_service_url() handles Render vs local-dev logic.
from src.config import EMBEDDING_SERVICE_URL
from src.services.modal.invoker import enforce_modal_function_policy_for_urls
from src.service_endpoints import (
    AGENT_SERVICE_URL,
    MODEL_ENDPOINT,
    SCRAPER_ENDPOINT,
    log_endpoint_summary as _log_ep_summary,
)
from src.utils.database_url import get_resolved_database_url

DATABASE_URL = get_resolved_database_url()

# CORS configuration - supports multiple origins separated by comma
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:4173"
).split(",")
ALLOWED_ORIGIN_REGEX = os.getenv("ALLOWED_ORIGIN_REGEX", "").strip() or None

MAX_URLS_PER_REQUEST = int(os.getenv("MAX_URLS_PER_REQUEST", "100"))
JOB_RETENTION_HOURS = int(os.getenv("JOB_RETENTION_HOURS", "24"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


async def _probe_http_health(base_url: str, timeout_seconds: float = 2.0) -> str:
    """Probe a dependency health endpoint and return a simple status string."""
    if not base_url:
        return "not_configured"

    health_url = f"{base_url.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(health_url)
        return "ok" if response.status_code == 200 else "error"
    except Exception:
        return "error"


async def _probe_database_socket(database_url: str, timeout_seconds: float = 2.0) -> str:
    """Probe database reachability by opening a TCP socket to host/port from DATABASE_URL."""
    if not database_url:
        return "not_configured"

    try:
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = int(parsed.port or 5432)
        if not host:
            return "error"

        connection = await asyncio.wait_for(
            asyncio.open_connection(host=host, port=port),
            timeout=timeout_seconds,
        )
        _, writer = connection
        writer.close()
        await writer.wait_closed()
        return "ok"
    except (socket.gaierror, OSError, TimeoutError, ValueError):
        return "error"
    except Exception:
        return "error"


async def _probe_http_dependency(
    name: str,
    base_url: str,
    *,
    timeout_seconds: float = 2.0,
    critical: bool = False,
) -> IntegrationComponentStatus:
    """Probe an HTTP dependency and return operator-friendly health details."""
    if not base_url:
        return IntegrationComponentStatus(
            status="not_configured",
            configured=False,
            critical=critical,
            endpoint=None,
            health_url=None,
            detail=f"{name} is not configured",
        )

    health_url = f"{base_url.rstrip('/')}/health"
    started_at = asyncio.get_running_loop().time()
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(health_url)
        elapsed_ms = int((asyncio.get_running_loop().time() - started_at) * 1000)
        status = "ok" if response.status_code == 200 else "error"
        return IntegrationComponentStatus(
            status=status,
            configured=True,
            critical=critical,
            endpoint=base_url,
            health_url=health_url,
            response_time_ms=elapsed_ms,
            detail=f"health endpoint returned {response.status_code}",
        )
    except Exception as exc:
        elapsed_ms = int((asyncio.get_running_loop().time() - started_at) * 1000)
        return IntegrationComponentStatus(
            status="error",
            configured=True,
            critical=critical,
            endpoint=base_url,
            health_url=health_url,
            response_time_ms=elapsed_ms,
            detail=f"{name} probe failed: {exc}",
        )


async def _probe_database_dependency(
    database_url: str,
    *,
    timeout_seconds: float = 2.0,
    critical: bool = True,
) -> IntegrationComponentStatus:
    """Probe Postgres reachability and return a structured status payload."""
    if not database_url:
        return IntegrationComponentStatus(
            status="not_configured",
            configured=False,
            critical=critical,
            endpoint=None,
            health_url=None,
            detail="database is not configured",
        )

    try:
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = int(parsed.port or 5432)
        endpoint = f"{host}:{port}" if host else None
    except Exception:
        endpoint = None

    started_at = asyncio.get_running_loop().time()
    status = await _probe_database_socket(database_url, timeout_seconds=timeout_seconds)
    elapsed_ms = int((asyncio.get_running_loop().time() - started_at) * 1000)

    return IntegrationComponentStatus(
        status=status,
        configured=True,
        critical=critical,
        endpoint=endpoint,
        health_url=None,
        response_time_ms=elapsed_ms,
        detail=(
            "database socket probe succeeded" if status == "ok" else "database socket probe failed"
        ),
    )


async def _build_integrations_status() -> IntegrationsStatus:
    """Build an aggregated integrations status payload for operators and deploy checks."""
    agent_status, database_status = await asyncio.gather(
        _probe_http_dependency("agent", AGENT_SERVICE_URL, critical=True),
        _probe_database_dependency(DATABASE_URL, critical=True),
    )

    # Modal worker-backed services are invoked by application calls, not continuously
    # probed over HTTP, to avoid keeping endpoint-style health checks as a cost driver.
    embedding_status = IntegrationComponentStatus(
        status="not_configured",
        configured=False,
        critical=False,
        endpoint=None,
        health_url=None,
        detail="embedding service health probe disabled (function-invoked dependency)",
    )
    scraper_status = IntegrationComponentStatus(
        status="not_configured",
        configured=False,
        critical=False,
        endpoint=None,
        health_url=None,
        detail="scraper service health probe disabled (function-invoked dependency)",
    )
    model_status = IntegrationComponentStatus(
        status="not_configured",
        configured=False,
        critical=False,
        endpoint=None,
        health_url=None,
        detail="model service health probe disabled (function-invoked dependency)",
    )

    components = {
        "agent": agent_status,
        "embedding_service": embedding_status,
        "database": database_status,
        "scraper": scraper_status,
        "model": model_status,
    }

    degraded_integrations = [
        name
        for name, component in components.items()
        if component.configured and component.status != "ok"
    ]
    active_integrations = [
        name
        for name, component in components.items()
        if component.configured and component.status == "ok"
    ]

    overall_status = "ok"
    if any(component.critical and component.status != "ok" for component in components.values()):
        overall_status = "degraded"

    return IntegrationsStatus(
        status=overall_status,
        gateway=IntegrationComponentStatus(
            status="ok",
            configured=True,
            critical=True,
            endpoint=os.getenv("RENDER_SERVICE_NAME") or "vecinita-gateway",
            health_url=None,
            response_time_ms=0,
            detail="gateway process is running",
        ),
        components=components,
        active_integrations=active_integrations,
        degraded_integrations=degraded_integrations,
        timestamp=datetime.now(timezone.utc),
    )


# ============================================================================
# FastAPI Application
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan: startup and shutdown events.

    Startup: Initialize resources when the application starts.
    Shutdown: Clean up resources when the application stops.
    """
    # ========== STARTUP ==========
    _log_ep_summary(logging.getLogger(__name__))
    enforce_modal_function_policy_for_urls(
        {
            "MODEL_ENDPOINT": MODEL_ENDPOINT,
            "EMBEDDING_SERVICE_URL": EMBEDDING_SERVICE_URL,
            "SCRAPER_ENDPOINT": SCRAPER_ENDPOINT,
            "REINDEX_SERVICE_URL": os.getenv("REINDEX_SERVICE_URL", "").strip() or None,
        }
    )
    print("[Gateway] Starting Vecinita Unified API Gateway")
    print(f"[Gateway] Agent Service: {AGENT_SERVICE_URL}")
    print(f"[Gateway] Embedding Service: {EMBEDDING_SERVICE_URL}")
    print(f"[Gateway] Database: {'configured' if DATABASE_URL else 'not configured'}")
    print(f"[Gateway] Embedding Model: {EMBEDDING_MODEL}")

    # TODO: Initialize service clients
    # - Agent service HTTP client
    # - Embedding service HTTP client
    # - Database connection pool
    # - Cache layer (if needed)

    yield

    # ========== SHUTDOWN ==========
    print("[Gateway] Shutting down Vecinita Unified API Gateway")

    # TODO: Cleanup
    # - Close HTTP clients
    # - Close database connections
    # - Cleanup any running background tasks


app = FastAPI(
    title="Vecinita Unified API Gateway",
    description="Consolidated API for Q&A, document scraping, embeddings, and administration",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/docs/openapi.json",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)


def custom_openapi():
    """Attach Bearer security scheme documentation for Schemathesis and API clients."""
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {})
    schemes = components.setdefault("securitySchemes", {})
    schemes["GatewayBearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "description": (
            "When ENABLE_AUTH is true, send your API key as a Bearer token. "
            "Public routes (health, parts of /api/v1/documents, ask/config, etc.) "
            "are listed in middleware.PUBLIC_ENDPOINTS."
        ),
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.get("/api/v1/openapi.json", include_in_schema=False)
async def openapi_json_legacy_alias():
    """Same schema as ``GET /api/v1/docs/openapi.json`` (older path kept for compatibility)."""
    return JSONResponse(app.openapi())


# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Correlation-ID"],
)

# Add rate limiting middleware (before auth to catch limits early)
app.add_middleware(RateLimitingMiddleware)

# Add authentication middleware (validates API keys)
app.add_middleware(AuthenticationMiddleware)

# Outermost on request path: stable correlation id for operators + Modal submit payloads (**FR-006**)
app.add_middleware(CorrelationIdMiddleware)

# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/", tags=["Health"])
async def root(request: Request):
    """
    Gateway root endpoint.

    Returns service info and available endpoints.
    - For browsers (Accept: text/html): serves frontend index.html if available
    - For API clients (Accept: application/json): returns JSON service info
    """
    # Check if frontend is built and available
    frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    frontend_available = frontend_dist.exists() and (frontend_dist / "index.html").exists()

    # Check Accept header to determine response type
    accept_header = request.headers.get("accept", "").lower()

    # If it's a browser request (accepts text/html) and frontend is available, serve it
    if "text/html" in accept_header and frontend_available:
        return FileResponse(str(frontend_dist / "index.html"))

    # Otherwise return JSON service info (for API clients or when frontend unavailable)
    if frontend_available:
        front_message = " | Frontend available at /"
    else:
        front_message = " | Frontend not built (use: npm run build in frontend/)"

    return GatewayPublicRootResponse(
        service="Vecinita Unified API Gateway",
        version="1.0.0",
        description="Consolidated API for Q&A, document viewing, scraping, and embeddings"
        + front_message,
        api_base="/api/v1",
        endpoints={
            "Q&A": {
                "ask": "GET /api/v1/ask?question=...",
                "ask_stream": "GET /api/v1/ask/stream?question=...",
                "config": "GET /api/v1/ask/config",
            },
            "Scraping": {
                "submit": "POST /api/v1/scrape",
                "status": "GET /api/v1/scrape/{job_id}",
                "history": "GET /api/v1/scrape/history",
                "cancel": "POST /api/v1/scrape/{job_id}/cancel",
                "stats": "GET /api/v1/scrape/stats",
            },
            "Embeddings": {
                "single": "POST /api/v1/embed",
                "batch": "POST /api/v1/embed/batch",
                "similarity": "POST /api/v1/embed/similarity",
                "config": "GET /api/v1/embed/config",
                "update_config": "POST /api/v1/embed/config",
            },
            "Documents": {
                "overview": "GET /api/v1/documents/overview",
                "preview": "GET /api/v1/documents/preview",
                "tags": "GET /api/v1/documents/tags",
            },
            "Operations": {
                "health": "GET /health",
                "integrations": "GET /api/v1/integrations/status",
            },
            "Documentation": {
                "docs": "GET /api/v1/docs (OpenAPI/Swagger)",
                "openapi": "GET /api/v1/docs/openapi.json",
            },
        },
        environment={
            "agent_service": AGENT_SERVICE_URL,
            "embedding_service": EMBEDDING_SERVICE_URL,
            "database_configured": bool(DATABASE_URL),
        },
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint - kept at root for backward compatibility.

    Returns:
        Service health status
    """
    integrations = await _build_integrations_status()
    agent_status = integrations.components["agent"].status
    embedding_status = integrations.components["embedding_service"].status
    database_status = integrations.components["database"].status

    return HealthCheck(
        status=integrations.status,
        agent_service=agent_status,
        embedding_service=embedding_status,
        database=database_status,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/api/v1/health", response_model=HealthCheck, include_in_schema=False)
async def health_check_v1_alias():
    """Versioned alias used by smoke/live checks and legacy clients."""
    return await health_check()


@app.get("/integrations/status", response_model=IntegrationsStatus)
async def integrations_status():
    """Detailed integration health for deploy checks and operator diagnostics."""
    return await _build_integrations_status()


@app.get("/api/v1/integrations/status", response_model=IntegrationsStatus, include_in_schema=False)
async def integrations_status_v1_alias():
    """Versioned alias for integration health checks."""
    return await integrations_status()


@app.get("/config", response_model=GatewayConfig)
async def get_gateway_config():
    """
    Get gateway configuration - kept at root for backward compatibility.
    Also available at /api/v1/admin/config
    Returns:
        Current configuration
    """
    return GatewayConfig(
        agent_url=AGENT_SERVICE_URL,
        embedding_service_url=EMBEDDING_SERVICE_URL,
        database_url=DATABASE_URL if DATABASE_URL else None,
        max_urls_per_request=MAX_URLS_PER_REQUEST,
        job_retention_hours=JOB_RETENTION_HOURS,
        embedding_model=EMBEDDING_MODEL,
    )


# ============================================================================
# Include Routers - API v1
# ============================================================================

# Create a version router that will hold all v1 endpoints
v1_router = APIRouter(prefix="/api/v1")

# Include sub-routers (they already have their own prefixes: /ask, /scrape, /embed)
v1_router.include_router(ask_router)
if scrape_router is not None:
    v1_router.include_router(scrape_router)
v1_router.include_router(embed_router)
v1_router.include_router(modal_jobs_router)
v1_router.include_router(documents_router)  # public, no auth

# Include the version router in the main app
app.include_router(v1_router)

# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with standard response format."""
    cid = getattr(request.state, "correlation_id", None)
    detail = exc.detail
    if isinstance(detail, str):
        error: Any = detail or "An error occurred"
    elif isinstance(detail, (dict, list)):
        # Preserve structured errors (e.g. upstream 422 JSON from embedding proxy).
        error = detail
    else:
        error = str(detail) if detail is not None else "An error occurred"
    content: dict[str, Any] = {
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if cid:
        content["correlation_id"] = cid
    headers = {"X-Correlation-ID": cid} if cid else {}
    return JSONResponse(status_code=exc.status_code, content=content, headers=headers)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    cid = getattr(request.state, "correlation_id", None)
    content: dict[str, Any] = {
        "error": "Internal server error",
        "detail": str(exc) if app.debug else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if cid:
        content["correlation_id"] = cid
    headers = {"X-Correlation-ID": cid} if cid else {}
    return JSONResponse(status_code=500, content=content, headers=headers)


# ============================================================================
# Static File Serving - Frontend
# ============================================================================

# Mount frontend distribution files at root if they exist
frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    print(f"[Gateway] Frontend detected at {frontend_dist}")
    try:
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
        print("[Gateway] Frontend mounted at /")
    except Exception as e:
        print(f"[Gateway] Warning: Could not mount frontend: {e}")
else:
    print(f"[Gateway] Frontend not found at {frontend_dist}")
    print("[Gateway] To generate frontend: cd frontend && npm install && npm run build")


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GATEWAY_PORT", "8004"))
    reload = os.getenv("RELOAD", "False").lower() == "true"

    print(f"Starting gateway on port {port} ({'with' if reload else 'without'} reload)...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info",
    )
