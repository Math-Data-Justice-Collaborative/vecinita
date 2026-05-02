"""
Database Query Security Helpers (Phase 7).

Provides utilities for secure database operations:
- SQL injection prevention (parameterized queries)
- Query logging and auditing
- Slow query detection
- Query plan analysis helpers
"""

import logging
import time
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)
slow_query_logger = logging.getLogger("vecinita.slow_queries")

# ============================================================================
# Configuration
# ============================================================================

SLOW_QUERY_THRESHOLD_SECONDS = 5.0  # Log queries slower than this
ENABLE_QUERY_LOGGING = True
ENABLE_SLOW_QUERY_DETECTION = True


# ============================================================================
# Query Validation Helpers
# ============================================================================


class QueryValidator:
    """
    Validates database queries for security and performance issues.
    """

    @staticmethod
    def validate_table_name(table_name: str) -> str:
        """
        Validate and sanitize table name.

        SECURITY: Prevents SQL injection through table names.
        Allows: alphanumeric, underscores, hyphens

        Args:
            table_name: Table name to validate

        Returns:
            Validated table name

        Raises:
            ValueError: If table name contains invalid characters
        """
        if not table_name:
            raise ValueError("Table name cannot be empty")

        # Allow alphanumeric, underscores, hyphens
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")

        if not all(c in valid_chars for c in table_name):
            raise ValueError(
                f"Invalid table name: {table_name}. Only alphanumeric, underscores, and hyphens allowed."
            )

        if len(table_name) > 100:
            raise ValueError(f"Table name too long: {table_name}")

        return table_name

    @staticmethod
    def validate_column_name(column_name: str) -> str:
        """
        Validate and sanitize column name.

        Args:
            column_name: Column name to validate

        Returns:
            Validated column name

        Raises:
            ValueError: If column name invalid
        """
        if not column_name:
            raise ValueError("Column name cannot be empty")

        # Allow alphanumeric, underscores, dots (for sub-fields)
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.")

        if not all(c in valid_chars for c in column_name):
            raise ValueError(f"Invalid column name: {column_name}")

        if len(column_name) > 200:
            raise ValueError(f"Column name too long: {column_name}")

        return column_name

    @staticmethod
    def validate_filter_value(value: Any) -> Any:
        """
        Validate filter value.

        SECURITY: Ensures type safety, prevents injection through values.
        Note: parameterized SQL execution should handle value binding.

        Args:
            value: Filter value

        Returns:
            Validated value

        Raises:
            ValueError: If value invalid type
        """
        # Allow: str, int, float, bool, None, list, dict
        if value is None:
            return value

        if isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, (list, tuple)):
            # Recursively validate list items
            return [QueryValidator.validate_filter_value(item) for item in value]

        if isinstance(value, dict):
            # Recursively validate dict values
            return {k: QueryValidator.validate_filter_value(v) for k, v in value.items()}

        raise ValueError(f"Invalid filter value type: {type(value)}")


# ============================================================================
# Query Logging & Auditing
# ============================================================================


class QueryAudit:
    """
    Audit trail for database queries.

    Tracks:
    - Query execution time
    - Success/failure
    - User/API key
    - Affected rows
    """

    @staticmethod
    def log_query(
        query_type: str,
        table_name: str,
        duration_seconds: float,
        success: bool,
        affected_rows: int = 0,
        error: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """
        Log query execution for auditing.

        Args:
            query_type: 'select', 'insert', 'update', 'delete'
            table_name: Target table
            duration_seconds: Query execution time
            success: Whether query succeeded
            affected_rows: Number of rows affected
            error: Error message if failed
            user_id: User/API key who executed query
        """
        level = "INFO" if success else "ERROR"
        status = "OK" if success else "FAIL"

        message = (
            f"[{level}] Query: {query_type} on {table_name} | "
            f"Duration: {duration_seconds:.3f}s | "
            f"Status: {status}"
        )

        if affected_rows > 0:
            message += f" | Rows: {affected_rows}"

        if error:
            message += f" | Error: {error}"

        if user_id:
            message += f" | User: {user_id[:10]}***"

        # Detect slow queries
        if ENABLE_SLOW_QUERY_DETECTION and duration_seconds > SLOW_QUERY_THRESHOLD_SECONDS:
            slow_query_logger.warning(
                f"SLOW QUERY: {query_type} {table_name} took {duration_seconds:.3f}s"
            )

        if ENABLE_QUERY_LOGGING:
            if success:
                logger.info(message)
            else:
                logger.error(message)


# ============================================================================
# Query Timing Decorator
# ============================================================================


def track_query_time(query_type: str, table_name: str):
    """
    Decorator to automatically track query execution time.

    Usage:
        @track_query_time("select", "documents")
        async def get_documents(db, limit=10):
            return db.table("documents").select("*").limit(limit).execute()

    Args:
        query_type: Type of query ('select', 'insert', 'update', 'delete')
        table_name: Table being queried
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                QueryAudit.log_query(query_type, table_name, duration, True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                QueryAudit.log_query(query_type, table_name, duration, False, error=str(e))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                QueryAudit.log_query(query_type, table_name, duration, True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                QueryAudit.log_query(query_type, table_name, duration, False, error=str(e))
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# Common Query Patterns (Security-Hardened)
# ============================================================================


async def get_document_by_id(
    db,
    document_id: str,
    session_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Securely get document by ID with optional session filtering.

    SECURITY:
    - Uses parameterized query execution
    - Validates column/table names
    - Enforces session isolation
    - Timeouts enforced at connection level

    Args:
        db: Database client or query adapter
        document_id: Document ID (parameterized)
        session_id: Session ID for isolation (parameterized)

    Returns:
        Document record or None

    Raises:
        ValueError: If validation fails
        Exception: If query fails
    """
    table_name = QueryValidator.validate_table_name("documents")
    column_name = QueryValidator.validate_column_name("id")

    try:
        query = db.table(table_name).select("*").eq(column_name, document_id)

        # Add session filtering if provided
        if session_id:
            query = query.eq("session_id", session_id)

        result = query.single().execute()
        return result.data if result else None

    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}")
        raise


async def delete_documents_by_filter(
    db,
    table_name: str = "documents",
    filter_field: str | None = None,
    filter_value: Any | None = None,
    session_id: str | None = None,
) -> int:
    """
    Securely delete documents with filters.

    SECURITY:
    - Validates table/column names
    - Parameterizes filter values
    - Enforces session isolation
    - Logs audit trail

    Args:
        db: Database client or query adapter
        table_name: Table to delete from
        filter_field: Field to filter on (parameterized)
        filter_value: Value to match (parameterized)
        session_id: Session ID for isolation

    Returns:
        Number of deleted rows

    Raises:
        ValueError: If validation fails
    """
    table_name = QueryValidator.validate_table_name(table_name)

    try:
        query = db.table(table_name).delete()

        # Apply filters
        if filter_field:
            filter_field = QueryValidator.validate_column_name(filter_field)
            filter_value = QueryValidator.validate_filter_value(filter_value)
            query = query.eq(filter_field, filter_value)

        # Enforce session isolation
        if session_id:
            session_id = QueryValidator.validate_filter_value(session_id)
            query = query.eq("session_id", session_id)

        result = query.execute()
        deleted_count = len(result.data) if result.data else 0

        logger.info(f"Deleted {deleted_count} records from {table_name}")
        return deleted_count

    except Exception as e:
        logger.error(f"Failed to delete records from {table_name}: {e}")
        raise


# ============================================================================
# Query Plan Analysis (for optimization)
# ============================================================================


def suggest_indexes(slow_query_log: list[str]) -> list[str]:
    """
    Analyze slow query log and suggest indexes.

    Args:
        slow_query_log: List of slow query names/descriptions

    Returns:
        List of index suggestions
    """
    suggestions = []

    # Analyze patterns
    query_counts: dict[str, int] = {}
    for query in slow_query_log:
        query_counts[query] = query_counts.get(query, 0) + 1

    # Suggest indexes for frequently slow queries
    for query, count in query_counts.items():
        if count > 10:  # More than 10 slow executions
            suggestions.append(f"Consider adding index for: {query}")

    return suggestions


# Need to import asyncio for the decorator
import asyncio
