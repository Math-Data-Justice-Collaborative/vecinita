"""
FastAPI Dependencies for Authentication and Authorization.

Provides decorators and dependency functions for:
- Requiring API key authentication
- Requiring admin role
- Getting current API key
- Getting current user context
"""

import logging
import os
from functools import wraps

from fastapi import Depends, Header, HTTPException

logger = logging.getLogger(__name__)

# Configuration
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() in ["true", "1", "yes"]
ADMIN_API_KEYS = os.getenv("ADMIN_API_KEYS", "").split(",") if os.getenv("ADMIN_API_KEYS") else []
AUTH_FAIL_CLOSED = os.getenv("AUTH_FAIL_CLOSED", "true").lower() in ["true", "1", "yes"]


# ============================================================================
# Dependency Functions (for FastAPI Depends)
# ============================================================================


async def get_api_key(authorization: str | None = Header(None)) -> str | None:
    """
    Extract and validate API key from Authorization header.

    SECURITY: Implements fail-closed pattern when AUTH_FAIL_CLOSED=true

    Args:
        authorization: Authorization header (Bearer <token>)

    Returns:
        Validated API key

    Raises:
        HTTPException: 401 if missing/invalid, 403 if not admin-only endpoint
    """
    # If auth is disabled, accept missing header and avoid strict Bearer validation.
    # This keeps local/dev ergonomics while still allowing callers to pass a token.
    if not ENABLE_AUTH:
        if not authorization:
            return None
        parts = authorization.split(maxsplit=1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return authorization

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide 'Authorization: Bearer <api_key>' header",
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use 'Authorization: Bearer <api_key>'",
        )

    api_key = parts[1]

    # If auth is enabled, validate against admin keys for admin endpoints
    # (this is checked by require_admin_auth below)

    return api_key


async def require_admin_auth(api_key: str | None = Depends(get_api_key)) -> str | None:
    """
    Verify that API key belongs to an admin.

    Used as a dependency in admin endpoints to enforce authorization.

    Args:
        api_key: API key from get_api_key dependency

    Returns:
        admin API key

    Raises:
        HTTPException: 403 if not admin key
    """
    if not ENABLE_AUTH:
        # If auth disabled, dummy admin key works
        return api_key

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Admin API key required",
        )

    if api_key not in ADMIN_API_KEYS:
        logger.warning(f"Admin access attempt with non-admin API key: {api_key[:10]}***")
        raise HTTPException(
            status_code=403,
            detail="Admin access required for this endpoint",
        )

    return api_key


async def require_auth(api_key: str | None = Depends(get_api_key)) -> str | None:
    """
    Require valid API key for endpoint.

    Used for endpoints that require authentication.

    Args:
        api_key: API key from get_api_key dependency

    Returns:
        Validated API key

    Raises:
        HTTPException: 401 if missing/invalid
    """
    if ENABLE_AUTH and not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required for this endpoint",
        )

    return api_key


def public_endpoint():
    """
    Marker for endpoints that don't require authentication.

    Use: @app.get("/public", tags=["Public"])
    (just document that endpoint is public)
    """
    pass


# ============================================================================
# Decorator Functions (alternative to Depends)
# ============================================================================


def require_admin_api_key(func):
    """
    Decorator to require admin API key on function-based endpoints.

    Checks Authorization header for admin API key.
    Implements fail-closed pattern.

    Example:
        @app.get("/admin/cleanup")
        @require_admin_api_key
        async def cleanup_endpoint(request: Request):
            ...
    """

    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            if AUTH_FAIL_CLOSED:
                raise HTTPException(
                    status_code=401,
                    detail="Admin API key required",
                )
            return await func(request, *args, **kwargs)

        # Extract API key
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization format",
            )

        api_key = parts[1]

        # Verify admin status
        if api_key not in ADMIN_API_KEYS:
            logger.warning(f"Unauthorized admin access attempt: {api_key[:10]}***")
            raise HTTPException(
                status_code=403,
                detail="Admin credentials required",
            )

        return await func(request, *args, **kwargs)

    return wrapper


def require_valid_api_key(func):
    """
    Decorator to require valid API key on function-based endpoints.

    Example:
        @app.get("/protected")
        @require_valid_api_key
        async def protected_endpoint(request: Request):
            ...
    """

    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        if not ENABLE_AUTH:
            return await func(request, *args, **kwargs)

        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="API key required",
            )

        # Extract API key
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization format",
            )

        return await func(request, *args, **kwargs)

    return wrapper


# ============================================================================
# Context/Session Helpers
# ============================================================================


class RequestContext:
    """
    Context object for request-scoped data.

    Stores:
    - api_key: Authenticated API key
    - session_id: Session identifier
    - thread_id: Conversation thread ID
    - admin: Whether user is admin
    """

    def __init__(self):
        self.api_key: str | None = None
        self.session_id: str | None = None
        self.thread_id: str | None = None
        self.admin: bool = False

    def is_authenticated(self) -> bool:
        """Check if request is authenticated."""
        return self.api_key is not None

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.admin

    def __repr__(self):
        return f"RequestContext(api_key={self.api_key[:10] if self.api_key else None}***, admin={self.admin})"
