"""
Security Middleware for Vecinita Gateway (Phase 7 - Hardening).

This module provides middleware for:
- API key validation without external auth hops
- Request tracking and rate limiting (per-endpoint configuration)
- Thread/conversation isolation
- Metadata header injection

Security Patterns:
- Auth handling is local to the gateway process
- Rate limiting tracks usage across multiple dimensions
- Thread isolation prevents cross-conversation access
"""

import logging
import os
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() in ["true", "1", "yes"]

# Rate limiting configuration
RATE_LIMIT_TOKENS_PER_DAY = int(os.getenv("RATE_LIMIT_TOKENS_PER_DAY", "1000"))
RATE_LIMIT_REQUESTS_PER_HOUR = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "100"))

# Per-endpoint rate limits (can be overridden)
ENDPOINT_RATE_LIMITS: dict[str, dict[str, int]] = {
    "/api/v1/ask": {"requests_per_hour": 60, "tokens_per_day": 1000},
    "/api/v1/scrape": {"requests_per_hour": 10, "tokens_per_day": 5000},
    "/api/v1/admin": {"requests_per_hour": 5, "tokens_per_day": 100},
    "/api/v1/embed": {"requests_per_hour": 100, "tokens_per_day": 10000},
}

PUBLIC_ENDPOINTS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/ask/config",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/redoc",
}

PUBLIC_PREFIXES = ("/api/v1/documents",)

AUTH_BYPASS_PREFIXES = ("/api/v1/admin",)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to intercept requests and validate API keys locally.

    - Extracts API key from Authorization header
    - Performs local validation when auth is enabled
    - Tracks token usage
    - Adds metadata headers to responses
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle request authentication and tracking."""
        path = request.url.path

        # Skip auth for health checks and public endpoints
        if path in PUBLIC_ENDPOINTS:
            return await call_next(request)

        # Public document routes intentionally allow unauthenticated read access.
        if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            return await call_next(request)

        # Admin routes enforce auth at router-level via Supabase JWT admin checks.
        if any(path.startswith(prefix) for prefix in AUTH_BYPASS_PREFIXES):
            return await call_next(request)

        # Extract API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        api_key = self._extract_api_key(auth_header)

        # If auth is enabled, validate the API key
        if ENABLE_AUTH and not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Missing API key",
                    "detail": "Provide API key via 'Authorization: Bearer <api_key>' header",
                },
            )

        # Validate API key locally when auth is enabled
        if ENABLE_AUTH and api_key:
            is_valid = await self._validate_api_key(api_key)
            if not is_valid:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Invalid API key",
                        "detail": "API key validation failed",
                    },
                )

        # Call the actual endpoint
        try:
            start_time = time.time()
            response = await call_next(request)
            elapsed_time = time.time() - start_time

            # Track usage if auth is enabled
            if ENABLE_AUTH and api_key:
                # Estimate token usage based on response size
                content_length = response.headers.get("content-length", "0")
                try:
                    tokens_used = max(1, int(content_length) // 4)  # Rough estimate
                except ValueError:
                    tokens_used = 1

                await self._track_usage(api_key, tokens_used)

            # Add metadata headers to response
            headers = MutableHeaders(response.headers)
            headers["X-Request-Time"] = f"{elapsed_time:.3f}s"

            return response

        except Exception as e:
            logger.error(f"Error in authentication middleware: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
            )

    def _extract_api_key(self, auth_header: str) -> str | None:
        """Extract API key from Authorization header."""
        if not auth_header:
            return None

        # Support both "Bearer token" and "token" formats
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        elif len(parts) == 1:
            return parts[0]

        return None

    async def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key format locally without external network calls."""
        token = str(api_key or "").strip()
        if not token:
            return False

        # Keep validation permissive for existing integrations while still
        # rejecting empty/malformed placeholders.
        if token.lower() in {"none", "null", "undefined"}:
            return False

        return len(token) >= 8

    async def _track_usage(self, api_key: str, tokens: int) -> None:
        """Track token usage locally (best-effort logging only)."""
        try:
            logger.debug("api_usage_tracked key_len=%s tokens=%s", len(api_key), tokens)
        except Exception as e:
            logger.warning(f"Failed to track usage: {e}")


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with per-endpoint configuration.

    Tracks:
    - Requests per hour (per endpoint)
    - Tokens per day (global)

    Data structure:
    rate_limit_state[api_key] = {
        'token_count': int,
        'token_reset_time': datetime,
        'endpoint': {
            'path': {
                'request_count': int,
                'request_reset_time': datetime
            }
        }
    }

    TODO: Move to Redis for production/multi-instance deployment
    """

    def __init__(self, app):
        super().__init__(app)
        # In-memory rate limit tracking: api_key -> {tokens, requests_by_endpoint}
        self.rate_limit_state: dict[str, dict] = {}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Check rate limits before processing request.

        Returns 429 Too Many Requests if limits exceeded.
        """
        # Skip rate limiting for public endpoints
        if request.url.path in PUBLIC_ENDPOINTS:
            return await call_next(request)

        if any(request.url.path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            return await call_next(request)

        # Get API key from header
        auth_header = request.headers.get("Authorization", "")
        api_key = self._extract_api_key(auth_header)

        # Check rate limits if API key provided
        if api_key:
            rate_limit_info = self._check_and_update_rate_limits(
                api_key=api_key, endpoint=request.url.path, method=request.method
            )

            if rate_limit_info["exceeded"]:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": rate_limit_info["message"],
                        "limit_type": rate_limit_info["limit_type"],
                        "reset_at": rate_limit_info["reset_at"],
                    },
                    headers={
                        "Retry-After": str(rate_limit_info["retry_after_seconds"]),
                        "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                        "X-RateLimit-Remaining": str(max(0, rate_limit_info["remaining"])),
                        "X-RateLimit-Reset": rate_limit_info["reset_at"],
                    },
                )

        return await call_next(request)

    def _extract_api_key(self, auth_header: str) -> str | None:
        """Extract API key from Authorization header."""
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        elif len(parts) == 1:
            return parts[0]
        return None

    def _get_endpoint_limit(self, endpoint: str) -> dict[str, int]:
        """
        Get rate limit for specific endpoint.

        Returns:
            {'requests_per_hour': int, 'tokens_per_day': int}
        """
        # Check exact match first
        if endpoint in ENDPOINT_RATE_LIMITS:
            return ENDPOINT_RATE_LIMITS[endpoint]

        # Check path prefix matches
        for path_prefix, limits in ENDPOINT_RATE_LIMITS.items():
            if endpoint.startswith(path_prefix):
                return limits

        # Default limits for unknown endpoints
        return {
            "requests_per_hour": RATE_LIMIT_REQUESTS_PER_HOUR,
            "tokens_per_day": RATE_LIMIT_TOKENS_PER_DAY,
        }

    def _check_and_update_rate_limits(self, api_key: str, endpoint: str, method: str) -> dict:
        """
        Check and update rate limits for API key.

        Returns:
            {
                'exceeded': bool,
                'message': str,
                'limit_type': 'requests_per_hour' | 'tokens_per_day',
                'limit': int,
                'remaining': int,
                'reset_at': str (ISO format),
                'retry_after_seconds': int
            }
        """
        now = datetime.utcnow()

        # Initialize state for new API key
        if api_key not in self.rate_limit_state:
            self.rate_limit_state[api_key] = {
                "token_used": 0,
                "token_reset_time": now + timedelta(days=1),
                "endpoints": {},
            }

        state = self.rate_limit_state[api_key]

        # ===== Check tokens per day =====
        if now >= state["token_reset_time"]:
            # Reset daily tokens
            state["token_used"] = 0
            state["token_reset_time"] = now + timedelta(days=1)

        endpoint_limits = self._get_endpoint_limit(endpoint)
        tokens_per_day_limit = endpoint_limits["tokens_per_day"]

        if state["token_used"] >= tokens_per_day_limit:
            reset_at = state["token_reset_time"].isoformat()
            retry_after = int((state["token_reset_time"] - now).total_seconds())
            return {
                "exceeded": True,
                "message": f"Daily token limit ({tokens_per_day_limit}) exceeded",
                "limit_type": "tokens_per_day",
                "limit": tokens_per_day_limit,
                "remaining": max(0, tokens_per_day_limit - state["token_used"]),
                "reset_at": reset_at,
                "retry_after_seconds": max(1, retry_after),
            }

        # ===== Check requests per hour =====
        if endpoint not in state["endpoints"]:
            state["endpoints"][endpoint] = {
                "request_count": 0,
                "request_reset_time": now + timedelta(hours=1),
            }

        endpoint_state = state["endpoints"][endpoint]
        requests_per_hour_limit = endpoint_limits["requests_per_hour"]

        if now >= endpoint_state["request_reset_time"]:
            # Reset hourly requests
            endpoint_state["request_count"] = 0
            endpoint_state["request_reset_time"] = now + timedelta(hours=1)

        if endpoint_state["request_count"] >= requests_per_hour_limit:
            reset_at = endpoint_state["request_reset_time"].isoformat()
            retry_after = int((endpoint_state["request_reset_time"] - now).total_seconds())
            return {
                "exceeded": True,
                "message": f"Hourly request limit ({requests_per_hour_limit} req/hr) exceeded for {endpoint}",
                "limit_type": "requests_per_hour",
                "limit": requests_per_hour_limit,
                "remaining": max(0, requests_per_hour_limit - endpoint_state["request_count"]),
                "reset_at": reset_at,
                "retry_after_seconds": max(1, retry_after),
            }

        # ===== Update counters =====
        state["token_used"] += 1
        endpoint_state["request_count"] += 1

        # Return success with remaining limits
        return {
            "exceeded": False,
            "message": "Rate limits OK",
            "limit_type": "none",
            "limit": 0,
            "remaining": max(0, requests_per_hour_limit - endpoint_state["request_count"]),
            "reset_at": endpoint_state["request_reset_time"].isoformat(),
            "retry_after_seconds": 0,
        }


class ThreadIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for thread/conversation isolation in single-tenant mode.

    Tracks thread ownership and prevents cross-thread data access:
    - Maps thread_id -> session_id (API key or anonymous session)
    - Validates thread access on each request
    - Injects session context for downstream services

    In single-tenant mode, this provides conversation-level isolation
    without requiring full multi-tenancy infrastructure.
    """

    def __init__(self, app):
        super().__init__(app)
        # Thread registry: thread_id -> {session_id, created_at, last_accessed}
        self._thread_registry = {}
        # Session to threads: session_id -> [thread_ids]
        self._session_threads = {}
        # Thread timeout: remove threads after 24 hours of inactivity
        self._thread_ttl_seconds = 24 * 60 * 60

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Validate thread ownership and inject session context."""
        import time

        # Skip for public endpoints
        if request.url.path in ["/health", "/", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Extract thread_id from query params or headers
        thread_id = request.query_params.get("thread_id") or request.headers.get("X-Thread-ID")

        # Extract session identifier (API key or anonymous session)
        api_key = self._extract_api_key(request.headers.get("Authorization", ""))
        session_id = api_key or request.headers.get("X-Session-ID") or "anonymous"

        # If no thread_id provided, create a new one
        if not thread_id:
            import secrets

            thread_id = f"thread-{secrets.token_urlsafe(16)}"
            logger.info(f"Created new thread: {thread_id} for session: {session_id}")

        # Check thread ownership
        current_time = time.time()
        if thread_id in self._thread_registry:
            thread_info = self._thread_registry[thread_id]

            # Check if thread belongs to different session
            if thread_info["session_id"] != session_id:
                logger.warning(
                    f"Thread access denied: {thread_id} belongs to "
                    f"{thread_info['session_id']}, not {session_id}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Thread access denied",
                        "detail": "This conversation thread belongs to another session",
                    },
                )

            # Update last accessed time
            thread_info["last_accessed"] = current_time

            # Check if thread has expired
            age = current_time - thread_info["last_accessed"]
            if age > self._thread_ttl_seconds:
                logger.info(f"Thread expired: {thread_id} (age: {age / 3600:.1f} hours)")
                self._remove_thread(thread_id, session_id)
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": "Thread expired",
                        "detail": "This conversation thread has expired due to inactivity",
                    },
                )
        else:
            # Register new thread
            self._thread_registry[thread_id] = {
                "session_id": session_id,
                "created_at": current_time,
                "last_accessed": current_time,
            }

            # Add to session's thread list
            if session_id not in self._session_threads:
                self._session_threads[session_id] = []
            self._session_threads[session_id].append(thread_id)

            logger.info(f"Registered thread: {thread_id} for session: {session_id}")

        # Process request
        response = await call_next(request)

        # Add thread info to response headers
        response.headers["X-Thread-ID"] = thread_id
        response.headers["X-Thread-Session"] = session_id
        response.headers["X-Thread-Age"] = str(
            int(current_time - self._thread_registry[thread_id]["created_at"])
        )

        # Periodic cleanup of expired threads (every 100th request)
        if len(self._thread_registry) % 100 == 0:
            self._cleanup_expired_threads()

        return response

    def _extract_api_key(self, auth_header: str) -> str | None:
        """Extract API key from Authorization header."""
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        elif len(parts) == 1:
            return parts[0]
        return None

    def _remove_thread(self, thread_id: str, session_id: str):
        """Remove thread from registry."""
        if thread_id in self._thread_registry:
            del self._thread_registry[thread_id]

        if session_id in self._session_threads:
            if thread_id in self._session_threads[session_id]:
                self._session_threads[session_id].remove(thread_id)

            # Clean up empty session entries
            if not self._session_threads[session_id]:
                del self._session_threads[session_id]

    def _cleanup_expired_threads(self):
        """Remove expired threads from registry."""
        import time

        current_time = time.time()
        expired_threads = []

        for thread_id, info in self._thread_registry.items():
            age = current_time - info["last_accessed"]
            if age > self._thread_ttl_seconds:
                expired_threads.append((thread_id, info["session_id"]))

        for thread_id, session_id in expired_threads:
            logger.info(f"Cleaning up expired thread: {thread_id}")
            self._remove_thread(thread_id, session_id)

        if expired_threads:
            logger.info(f"Cleaned up {len(expired_threads)} expired threads")

    def get_session_threads(self, session_id: str) -> list[Any]:
        """Get all threads for a session (admin/debugging)."""
        threads = self._session_threads.get(session_id, [])
        return list(threads)

    def get_thread_info(self, thread_id: str) -> dict | None:
        """Get thread information (admin/debugging)."""
        return self._thread_registry.get(thread_id)

    def count_active_threads(self) -> int:
        """Count total active threads (monitoring)."""
        return len(self._thread_registry)

    def count_active_sessions(self) -> int:
        """Count total active sessions (monitoring)."""
        return len(self._session_threads)
