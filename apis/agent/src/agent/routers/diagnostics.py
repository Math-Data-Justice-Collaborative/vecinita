"""Diagnostic endpoints for database and retrieval troubleshooting."""

import os
from typing import Any

from fastapi import APIRouter, Query

from .. import main as agent_main

try:
    import psycopg2
except Exception:  # pragma: no cover - optional in some environments
    psycopg2 = None  # type: ignore[assignment]

router = APIRouter()


def _database_url() -> str:
    return (os.getenv("DATABASE_URL") or "").strip()


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in values) + "]"


def _fetch_rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    database_url = _database_url()
    if not database_url or psycopg2 is None:
        raise RuntimeError("DATABASE_URL and psycopg2 are required for diagnostics")

    with psycopg2.connect(database_url, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if not cur.description:
                return []
            columns = [column[0] for column in cur.description]
            return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]


@router.get("/test-db-search")
def test_db_search(
    query: str = Query(
        default="community resources",
        min_length=1,
        max_length=10_000,
        description="Text used to build a diagnostic embedding and vector search probe.",
    ),
):
    """Run a diagnostic retrieval flow and return debug metadata."""
    diagnostics: dict[str, Any] = {}

    try:
        agent_main.logger.info("Test DB Search: Query = '%s'", query)

        if not _database_url() or psycopg2 is None:
            return {"error": "DATABASE_URL and psycopg2 are required"}

        try:
            table_rows = _fetch_rows("SELECT COUNT(*) AS total_rows FROM document_chunks")
            total_rows = int(table_rows[0]["total_rows"]) if table_rows else 0
            diagnostics["table_exists"] = True
            diagnostics["total_rows"] = total_rows
            agent_main.logger.info("Test DB Search: Table has %s rows", total_rows)
        except Exception as exc:
            diagnostics["table_exists"] = False
            diagnostics["table_error"] = str(exc)
            agent_main.logger.error("Test DB Search: Table check failed: %s", exc)

        try:
            embedding_rows = _fetch_rows("SELECT id, embedding FROM document_chunks LIMIT 5")
            if embedding_rows:
                non_null_embeddings = sum(
                    1 for row in embedding_rows if row.get("embedding") is not None
                )
                diagnostics["embeddings_exist"] = non_null_embeddings > 0
                diagnostics["sample_embedding_count"] = non_null_embeddings
                diagnostics["sample_size"] = len(embedding_rows)

                if non_null_embeddings > 0:
                    sample_embedding = next(
                        (row["embedding"] for row in embedding_rows if row.get("embedding")), None
                    )
                    if sample_embedding:
                        if isinstance(sample_embedding, list):
                            diagnostics["stored_embedding_dimension"] = len(sample_embedding)
                        elif isinstance(sample_embedding, str):
                            try:
                                parsed = agent_main.json.loads(sample_embedding)
                                diagnostics["stored_embedding_dimension"] = len(parsed)
                            except Exception:
                                diagnostics["stored_embedding_dimension"] = (
                                    "unknown (string format)"
                                )
                        else:
                            diagnostics["stored_embedding_dimension"] = (
                                f"unknown (type: {type(sample_embedding).__name__})"
                            )

                agent_main.logger.info(
                    "Test DB Search: %s/%s sample rows have embeddings",
                    non_null_embeddings,
                    len(embedding_rows),
                )
            else:
                diagnostics["embeddings_exist"] = False
                diagnostics["embedding_check_error"] = "No data returned"
        except Exception as exc:
            diagnostics["embeddings_exist"] = False
            diagnostics["embedding_check_error"] = str(exc)
            agent_main.logger.error("Test DB Search: Embedding check failed: %s", exc)

        try:
            test_embedding = [0.0] * 384
            rpc_test = _fetch_rows(
                "SELECT * FROM search_similar_documents(%s::vector, %s, %s)",
                (_vector_literal(test_embedding), 0.0, 1),
            )
            diagnostics["rpc_function_exists"] = True
            diagnostics["rpc_test_results"] = len(rpc_test)
            agent_main.logger.info(
                "Test DB Search: RPC function exists and returned %s results with test embedding",
                diagnostics["rpc_test_results"],
            )
        except Exception as exc:
            diagnostics["rpc_function_exists"] = False
            diagnostics["rpc_error"] = str(exc)
            agent_main.logger.error("Test DB Search: RPC function test failed: %s", exc)

        question_embedding = agent_main.embedding_model.embed_query(query)
        diagnostics["query_embedding_dimension"] = len(question_embedding)
        agent_main.logger.info(
            "Test DB Search: Generated embedding dimension = %s",
            len(question_embedding),
        )
        agent_main.logger.info("Test DB Search: First 5 values = %s", question_embedding[:5])

        test_threshold = 0.0
        agent_main.logger.info("Test DB Search: Searching with threshold = %s", test_threshold)

        result_data = _fetch_rows(
            "SELECT * FROM search_similar_documents(%s::vector, %s, %s)",
            (_vector_literal(question_embedding), test_threshold, 10),
        )

        agent_main.logger.info("Test DB Search: Found %s results", len(result_data))
        diagnostics["search_results_found"] = len(result_data)

        if result_data:
            similarities = [doc.get("similarity", 0) for doc in result_data]
            agent_main.logger.info("Test DB Search: Similarity scores = %s", similarities)

            return {
                "status": "success",
                "query": query,
                "diagnostics": diagnostics,
                "results_found": len(result_data),
                "similarity_range": {
                    "min": min(similarities),
                    "max": max(similarities),
                    "avg": sum(similarities) / len(similarities),
                },
                "sample_result": {
                    "content_preview": result_data[0].get("content", "")[:200],
                    "source_url": result_data[0].get("source_url", "N/A"),
                    "similarity": result_data[0].get("similarity", 0),
                },
                "all_similarities": similarities,
            }

        return {
            "status": "no_results",
            "query": query,
            "diagnostics": diagnostics,
            "message": "No results found. See diagnostics for details.",
            "recommendations": agent_main._get_recommendations(diagnostics),
        }

    except Exception as exc:
        agent_main.logger.error("Test DB Search Error: %s", exc)
        return {
            "status": "error",
            "query": query,
            "diagnostics": diagnostics,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }


@router.get("/db-info")
def get_db_info():
    """Return a compact snapshot of document-chunk and RPC state."""
    if not _database_url() or psycopg2 is None:
        return {"status": "error", "error": "DATABASE_URL and psycopg2 are required"}
    try:
        info: dict[str, Any] = {}

        try:
            count_rows = _fetch_rows("SELECT COUNT(*) AS total_rows FROM document_chunks")
            info["total_rows"] = int(count_rows[0]["total_rows"]) if count_rows else 0
        except Exception as exc:
            info["total_rows"] = f"error: {exc}"

        try:
            sample_rows = _fetch_rows(
                "SELECT id, source_url, chunk_index, embedding, content FROM document_chunks LIMIT 3"
            )
            if sample_rows:
                samples = []
                for row in sample_rows:
                    sample: dict[str, Any] = {
                        "id": row.get("id"),
                        "source_url": row.get("source_url"),
                        "chunk_index": row.get("chunk_index"),
                        "content_preview": (
                            row.get("content", "")[:100] + "..." if row.get("content") else None
                        ),
                        "has_embedding": row.get("embedding") is not None,
                    }

                    if row.get("embedding"):
                        embedding_value = row["embedding"]
                        if isinstance(embedding_value, list):
                            sample["embedding_dimension"] = len(embedding_value)
                            sample["embedding_type"] = "list"
                        elif isinstance(embedding_value, str):
                            sample["embedding_type"] = "string"
                            try:
                                parsed = agent_main.json.loads(embedding_value)
                                sample["embedding_dimension"] = len(parsed)
                            except Exception:
                                sample["embedding_dimension"] = "parse_failed"
                        else:
                            sample["embedding_type"] = type(embedding_value).__name__

                    samples.append(sample)

                info["sample_rows"] = samples
        except Exception as exc:
            info["sample_error"] = str(exc)

        try:
            test_embedding = [0.0] * 384
            rpc_result = _fetch_rows(
                "SELECT * FROM search_similar_documents(%s::vector, %s, %s)",
                (_vector_literal(test_embedding), 0.0, 1),
            )
            info["rpc_function_works"] = True
            info["rpc_test_returned"] = len(rpc_result)
        except Exception as exc:
            info["rpc_function_works"] = False
            info["rpc_error"] = str(exc)

        return {
            "status": "success",
            "database_info": info,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "expected_dimension": 384,
        }

    except Exception as exc:
        return {"status": "error", "error": str(exc), "error_type": type(exc).__name__}
