"""SQLAlchemy engines sized for DO Managed Postgres connection limits."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import create_engine

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

# Staging DO Managed Postgres: max_connections=25, superuser_reserved=3 → ~22 usable.
# ChatRAG + internal-write-api + Alembic must share that budget (HF-alembic-do-db-ports).
APP_POOL_SIZE = 2
APP_MAX_OVERFLOW = 1
APP_POOL_RECYCLE_S = 300


def create_app_engine(database_url: str, *, application_name: str) -> Engine:
    """Create a small QueuePool engine with pre-ping and recycle."""
    return create_engine(
        database_url,
        pool_size=APP_POOL_SIZE,
        max_overflow=APP_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=APP_POOL_RECYCLE_S,
        connect_args={"application_name": application_name},
    )
