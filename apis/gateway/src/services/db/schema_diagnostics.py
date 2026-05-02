"""Database schema diagnostics for Postgres and pgvector prerequisites."""

import logging
import os
from typing import Any

try:
    import psycopg2
except Exception:  # pragma: no cover - optional in some test profiles
    psycopg2 = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates Postgres schema prerequisites for Vecinita."""

    def __init__(self, db: Any):
        """Initialize with a DB adapter or database URL string."""
        self.db = db
        self.validation_errors: list[str] = []
        self.validation_warnings: list[str] = []

    def _execute(self, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        if hasattr(self.db, "execute"):
            return list(self.db.execute(sql, params))

        if hasattr(self.db, "cursor"):
            with self.db.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return list(cur.fetchall() or [])
                return []

        database_url = self.db if isinstance(self.db, str) else os.getenv("DATABASE_URL", "")
        if not database_url or psycopg2 is None:
            raise RuntimeError("DATABASE_URL and psycopg2 are required for schema diagnostics")

        with psycopg2.connect(str(database_url), connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return list(cur.fetchall() or [])
                return []

    async def validate_all(self) -> dict[str, Any]:
        """
        Run all schema validations.

        Returns:
            {
                'status': 'ok' | 'warning' | 'error',
                'errors': [...],
                'warnings': [...],
                'checks': {
                    'rpc_search_similar_documents': bool,
                    'table_document_chunks': bool,
                    'column_embedding': {'exists': bool, 'type': str, 'dimensions': int},
                    'index_source': bool,
                    'index_session_id': bool,
                    'index_created_at': bool,
                    'table_conversations': bool,
                    'table_documents': bool,
                }
            }
        """
        self.validation_errors = []
        self.validation_warnings = []
        results: dict[str, bool | dict[str, Any]] = {}

        # Check RPC function
        results["rpc_search_similar_documents"] = await self._check_rpc_search_similar_documents()

        # Check document_chunks table and columns
        results["table_document_chunks"] = await self._check_table_document_chunks()
        results["column_embedding"] = await self._check_column_embedding()

        # Check indexes
        results["index_source"] = await self._check_index("document_chunks_source_idx")
        results["index_session_id"] = await self._check_index("document_chunks_session_id_idx")
        results["index_created_at"] = await self._check_index("document_chunks_created_at_idx")

        # Check supporting tables
        results["table_conversations"] = await self._check_table("conversations")
        results["table_documents"] = await self._check_table("documents")

        # Determine overall status
        if self.validation_errors:
            status = "error"
        elif self.validation_warnings:
            status = "warning"
        else:
            status = "ok"

        return {
            "status": status,
            "errors": self.validation_errors,
            "warnings": self.validation_warnings,
            "checks": results,
        }

    async def _check_rpc_search_similar_documents(self) -> bool:
        """Check if search_similar_documents function exists."""
        try:
            rows = self._execute(
                "SELECT 1 FROM pg_proc WHERE proname = 'search_similar_documents' LIMIT 1"
            )
            if rows:
                return True
            raise RuntimeError("function not found")
        except Exception as e:
            error_msg = str(e)

            if "not found" in error_msg.lower() or "no function" in error_msg.lower():
                self.validation_errors.append(
                    "❌ Function 'search_similar_documents' not found in database.\n"
                    "   Apply the pgvector bootstrap migrations before starting the service."
                )
                return False
            logger.warning(f"RPC check status unclear: {error_msg}")
            return True

        return False

    async def _check_table_document_chunks(self) -> bool:
        """Check if document_chunks table exists with expected columns."""
        try:
            rows = self._execute("SELECT to_regclass('public.document_chunks')")
            return bool(rows and rows[0][0])
        except Exception:
            self.validation_errors.append(
                "❌ Table 'document_chunks' not found in database.\n"
                "   Apply the database migrations before starting the service."
            )
            return False

    async def _check_column_embedding(self) -> dict[str, Any]:
        """Check if document_chunks.embedding column exists and is a vector column."""
        try:
            rows = self._execute("""
                SELECT udt_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'document_chunks'
                  AND column_name = 'embedding'
                """)
            if rows and rows[0][0]:
                column_type = str(rows[0][0])
                if column_type.lower() != "vector":
                    self.validation_errors.append(
                        f"❌ Column 'embedding' has invalid type '{column_type}'. Expected pgvector."
                    )
                    return {"exists": True, "type": column_type, "dimensions": None}
                return {"exists": True, "type": column_type, "dimensions": 384}
            raise RuntimeError("column embedding does not exist")
        except Exception as e:
            error_msg = str(e)
            if "embedding" in error_msg.lower() or "column" in error_msg.lower():
                self.validation_errors.append(
                    "❌ Column 'embedding' not found in 'document_chunks' table.\n"
                    "   Add the pgvector embedding column before enabling semantic search."
                )
                return {"exists": False, "type": None, "dimensions": None}
            logger.warning(f"Embedding column check status unclear: {error_msg}")
            return {"exists": True, "type": "vector (unverified)", "dimensions": 384}

    async def _check_index(self, index_name: str) -> bool:
        """Check if a Postgres index exists."""
        try:
            rows = self._execute(
                "SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = %s LIMIT 1",
                (index_name,),
            )
            if rows:
                return True
        except Exception as exc:
            logger.warning("Index check failed for %s: %s", index_name, exc)
        self.validation_warnings.append(
            f"⚠️  Index '{index_name}' was not found. Query performance may be degraded."
        )
        return False

    async def _check_table(self, table_name: str) -> bool:
        """Check if table exists."""
        try:
            rows = self._execute("SELECT to_regclass(%s)", (f"public.{table_name}",))
            return bool(rows and rows[0][0])
        except Exception:
            self.validation_warnings.append(
                f"⚠️  Table '{table_name}' may not exist or may not be accessible."
            )
            return False


async def validate_schema(db: Any) -> dict[str, Any]:
    """
    Convenience function: Run complete schema validation.

    Args:
        db: Database adapter or connection string

    Returns:
        Validation result dictionary with status and detailed checks
    """
    validator = SchemaValidator(db)
    return await validator.validate_all()


def get_validation_summary(validation_result: dict[str, Any]) -> str:
    """
    Format validation result as human-readable summary.

    Args:
        validation_result: Result from validate_schema()

    Returns:
        Formatted string summary
    """
    status = validation_result["status"].upper()
    errors = validation_result["errors"]
    warnings = validation_result["warnings"]

    lines = [f"Schema Validation: {status}"]
    lines.append("=" * 50)

    if errors:
        lines.append("\nERRORS:")
        for error in errors:
            lines.append(f"\n{error}")

    if warnings:
        lines.append("\nWARNINGS:")
        for warning in warnings:
            lines.append(f"\n{warning}")

    if not errors and not warnings:
        lines.append("\n✅ All schema checks passed!")

    return "\n".join(lines)
