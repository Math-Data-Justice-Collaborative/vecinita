"""
Unified API Gateway - Main FastAPI Application

Consolidates Q&A, scraping, embeddings, and admin endpoints into a single API.
Serves as the primary entry point for all backend services.

Port: 8004 (by default)
"""

# ruff: noqa: E402, I001

import os
import logging
import warnings
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

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

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .middleware import AuthenticationMiddleware, RateLimitingMiddleware
from .models import GatewayConfig, HealthCheck
from .router_ask import router as ask_router
from .router_documents import router as documents_router
from .router_embed import router as embed_router

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


AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")

# Import normalized endpoints from central config (ensures consistency across services).
# config._normalize_internal_service_url() handles Render vs local-dev logic.
from src.config import EMBEDDING_SERVICE_URL
from src.service_endpoints import log_endpoint_summary as _log_ep_summary

DATABASE_URL = os.getenv("DATABASE_URL", "")

# CORS configuration - supports multiple origins separated by comma
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:4173"
).split(",")
ALLOWED_ORIGIN_REGEX = os.getenv("ALLOWED_ORIGIN_REGEX", "").strip() or None

MAX_URLS_PER_REQUEST = int(os.getenv("MAX_URLS_PER_REQUEST", "100"))
JOB_RETENTION_HOURS = int(os.getenv("JOB_RETENTION_HOURS", "24"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

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
    openapi_url="/api/v1/openapi.json",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# Add rate limiting middleware (before auth to catch limits early)
app.add_middleware(RateLimitingMiddleware)

# Add authentication middleware (validates API keys)
app.add_middleware(AuthenticationMiddleware)

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

    return {
        "service": "Vecinita Unified API Gateway",
        "version": "1.0.0",
        "description": "Consolidated API for Q&A, document viewing, scraping, and embeddings"
        + front_message,
        "api_base": "/api/v1",
        "endpoints": {
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
            "Documentation": {
                "docs": "GET /api/v1/docs (OpenAPI/Swagger)",
                "openapi": "GET /api/v1/openapi.json",
            },
        },
        "environment": {
            "agent_service": AGENT_SERVICE_URL,
            "embedding_service": EMBEDDING_SERVICE_URL,
            "database_configured": bool(DATABASE_URL),
        },
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint - kept at root for backward compatibility.

    Returns:
        Service health status
    """
    # TODO: Check actual service connectivity
    return HealthCheck(
        status="ok",
        agent_service="ok",  # Should ping AGENT_SERVICE_URL
        embedding_service="ok",  # Should ping EMBEDDING_SERVICE_URL
        database="ok",  # Should test DATABASE_URL connection
        timestamp=datetime.now(timezone.utc),
    )


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
v1_router.include_router(documents_router)  # public, no auth

# Include the version router in the main app
app.include_router(v1_router)

# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler with standard response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail or "An error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


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
