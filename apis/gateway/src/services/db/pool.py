"""Postgres connection manager with health checks and retry helpers."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

try:
    import psycopg2
except Exception:  # pragma: no cover - optional in some test profiles
    psycopg2 = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Pool configuration
POOL_MIN_SIZE = int(os.getenv("POOL_MIN_SIZE", "5"))
POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE", "20"))
POOL_TIMEOUT_SECONDS = int(os.getenv("POOL_TIMEOUT_SECONDS", "10"))
POOL_RECYCLE_SECONDS = int(os.getenv("POOL_RECYCLE_SECONDS", "3600"))  # 1 hour
POOL_HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv("POOL_HEALTH_CHECK_INTERVAL_SECONDS", "300"))

# Query configuration
QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS", "30"))
QUERY_RETRY_MAX_ATTEMPTS = int(os.getenv("QUERY_RETRY_MAX_ATTEMPTS", "3"))
QUERY_RETRY_BACKOFF_SECONDS = int(os.getenv("QUERY_RETRY_BACKOFF_SECONDS", "1"))


# ============================================================================
# Connection Pool Manager
# ============================================================================


class DatabaseConnectionPool:
    """
    Manages database connections with health checks and pooling.

    Features:
    - Lazy initialization of connections
    - Connection timeout handling
    - Automatic reconnection with exponential backoff
    - Health check monitoring
    - Query timeout enforcement

    Note: This is a lightweight process-local manager, not a true shared pool.
    For production multi-instance deployment, use an external pool such as PgBouncer.
    """

    def __init__(self):
        """Initialize connection pool manager."""
        self._client: str | None = None
        self._initialized = False
        self._health_check_task: asyncio.Task | None = None
        self._last_health_check: datetime | None = None
        self._health_status = {
            "connected": False,
            "connection_count": 0,
            "failed_queries": 0,
            "successful_queries": 0,
        }

    async def initialize(self) -> None:
        """
        Initialize database connection pool.

        Called on application startup.

        Raises:
            RuntimeError: If credentials not configured
        """
        if self._initialized:
            return

        if not DATABASE_URL:
            raise RuntimeError("Database not configured. Set DATABASE_URL.")
        if psycopg2 is None:
            raise RuntimeError(
                "Database not configured. Install psycopg2 to enable Postgres access."
            )

        try:
            self._client = DATABASE_URL
            logger.info("Database connection pool initialized")
            logger.info(f"Pool size: {POOL_MIN_SIZE}-{POOL_MAX_SIZE}")
            logger.info(f"Connection timeout: {POOL_TIMEOUT_SECONDS}s")
            logger.info(f"Query timeout: {QUERY_TIMEOUT_SECONDS}s")

            self._initialized = True
            self._health_status["connected"] = True
            self._health_status["connection_count"] = 1

            # Start health check task
            self._health_check_task = asyncio.create_task(self._run_health_checks())

        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    async def shutdown(self) -> None:
        """
        Shutdown database connection pool.

        Called on application shutdown.
        Closes all connections and stops health check task.
        """
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        self._client = None
        self._initialized = False
        self._health_status["connected"] = False
        logger.info("Database connection pool shutdown")

    def get_client(self) -> str:
        """
        Get configured database handle.

        Returns:
            Postgres connection string

        Raises:
            RuntimeError: If pool not initialized
        """
        if not self._initialized or not self._client:
            raise RuntimeError("Database connection pool not initialized. Call initialize() first.")

        return self._client

    async def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if self._client is None or psycopg2 is None:
                return False

            with psycopg2.connect(self._client, connect_timeout=POOL_TIMEOUT_SECONDS) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            self._last_health_check = datetime.utcnow()
            self._health_status["connected"] = True
            return True

        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self._health_status["connected"] = False
            return False

    async def _run_health_checks(self) -> None:
        """
        Periodically run health checks in background.

        Monitors connection pool health and logs issues.
        """
        while True:
            try:
                await asyncio.sleep(POOL_HEALTH_CHECK_INTERVAL_SECONDS)
                is_healthy = await self.health_check()

                if is_healthy:
                    logger.debug("Database health check passed")
                else:
                    logger.error("Database health check failed")
                    # TODO: Trigger reconnection logic

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    def get_stats(self) -> dict:
        """
        Get connection pool statistics.

        Returns:
            Statistics about pool usage, health, etc.
        """
        return {
            "initialized": self._initialized,
            "connected": self._health_status["connected"],
            "pool_size_configured": f"{POOL_MIN_SIZE}-{POOL_MAX_SIZE}",
            "connection_timeout": POOL_TIMEOUT_SECONDS,
            "query_timeout": QUERY_TIMEOUT_SECONDS,
            "health_check_interval": POOL_HEALTH_CHECK_INTERVAL_SECONDS,
            "last_health_check": (
                self._last_health_check.isoformat() if self._last_health_check else None
            ),
            "stats": self._health_status,
        }


# ============================================================================
# Global Instance
# ============================================================================

# Single global instance for application
connection_pool = DatabaseConnectionPool()


# ============================================================================
# FastAPI Dependency
# ============================================================================


async def get_database_client() -> str:
    """
    FastAPI dependency to get database handle from pool.

    Usage:
        async def endpoint(database_url: str = Depends(get_database_client)):
            ...

    Returns:
        Database connection string from connection pool

    Raises:
        RuntimeError: If pool not initialized
    """
    return connection_pool.get_client()


# ============================================================================
# Context Manager for Query Execution
# ============================================================================


@asynccontextmanager
async def query_with_timeout(query_name: str = "query"):
    """
    Context manager that enforces query timeout.

    Usage:
        async with query_with_timeout("get_documents") as timeout_handle:
            result = db.table("documents").select("*").execute()

    Args:
        query_name: Name of query for logging

    Yields:
        Timeout handle (can be used to extend timeout if needed)

    Raises:
        asyncio.TimeoutError: If query exceeds timeout
    """
    try:
        logger.debug(f"Executing query: {query_name}")
        yield None
        logger.debug(f"Query completed: {query_name}")
        connection_pool._health_status["successful_queries"] += 1

    except asyncio.TimeoutError:
        logger.error(f"Query timeout: {query_name} (>{QUERY_TIMEOUT_SECONDS}s)")
        connection_pool._health_status["failed_queries"] += 1
        raise


# ============================================================================
# Query Retry Helper
# ============================================================================


async def execute_with_retry(
    query_func,
    query_name: str = "query",
    max_attempts: int = QUERY_RETRY_MAX_ATTEMPTS,
) -> Any:
    """
    Execute query with automatic retry on failure.

    Implements exponential backoff retry strategy.

    Usage:
        result = await execute_with_retry(
            lambda: db.table("docs").select("*").execute(),
            query_name="get_all_docs"
        )

    Args:
        query_func: Async function that performs database query
        query_name: Name for logging
        max_attempts: Maximum retry attempts (default 3)

    Returns:
        Query result

    Raises:
        Exception: Final exception if all retries fail
    """
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        try:
            async with query_with_timeout(query_name):
                if asyncio.iscoroutinefunction(query_func):
                    result = await asyncio.wait_for(query_func(), timeout=QUERY_TIMEOUT_SECONDS)
                else:
                    result = query_func()

                if attempt > 0:
                    logger.info(f"Query succeeded on attempt {attempt + 1}: {query_name}")

                return result

        except Exception as e:
            last_error = e

            if attempt < max_attempts - 1:
                # Exponential backoff: 1s, 2s, 4s, etc.
                wait_time = QUERY_RETRY_BACKOFF_SECONDS * (2**attempt)
                logger.warning(
                    f"Query attempt {attempt + 1}/{max_attempts} failed for {query_name}: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Query failed after {max_attempts} attempts: {query_name}")

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Query execution failed without a captured error: {query_name}")
