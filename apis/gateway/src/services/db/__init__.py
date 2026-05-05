"""
Database service module (Phase 7 - Security Hardening).

Provides:
- Connection pooling with health checks
- Query execution with retry logic and timeouts
- Security helpers for parameterized queries
- Slow query detection and auditing
"""

from .pool import (
    connection_pool,
    execute_with_retry,
    get_database_client,
    query_with_timeout,
)
from .security import (
    QueryAudit,
    QueryValidator,
    delete_documents_by_filter,
    get_document_by_id,
    suggest_indexes,
    track_query_time,
)

__all__ = [
    # Pool
    "connection_pool",
    "get_database_client",
    "execute_with_retry",
    "query_with_timeout",
    # Security
    "QueryValidator",
    "QueryAudit",
    "track_query_time",
    "get_document_by_id",
    "delete_documents_by_filter",
    "suggest_indexes",
]
