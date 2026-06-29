"""Shared CORS configuration for browser-facing FastAPI apps."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI


def parse_cors_origins(env_value: str | None = None) -> list[str]:
    """Parse comma-separated origins from VECINITA_CORS_ORIGINS."""
    raw = env_value if env_value is not None else os.environ.get("VECINITA_CORS_ORIGINS", "")
    return [part.strip() for part in raw.split(",") if part.strip()]


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
    return origins
