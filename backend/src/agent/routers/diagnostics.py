"""Diagnostic endpoints for database and retrieval troubleshooting."""

from typing import Any

from fastapi import APIRouter

from .. import main as agent_main

router = APIRouter()


@router.get("/test-db-search")
def test_db_search(query: str = "community resources"):
    """Run a diagnostic retrieval flow and return debug metadata."""
    diagnostics: dict[str, Any] = {}

    try:
        agent_main.logger.info("Test DB Search: Query = '%s'", query)

        if agent_main.supabase is None:
            return {"error": "Supabase client not initialized"}

        try:
            table_result = (
                agent_main.supabase.table("document_chunks").select("*").limit(1).execute()
            )
            total_rows = (
                table_result.count
                if hasattr(table_result, "count")
                else len(table_result.data) if table_result.data else 0
            )
            diagnostics["table_exists"] = True
            diagnostics["total_rows"] = total_rows
            agent_main.logger.info("Test DB Search: Table has %s rows", total_rows)
        except Exception as exc:
            diagnostics["table_exists"] = False
            diagnostics["table_error"] = str(exc)
            agent_main.logger.error("Test DB Search: Table check failed: %s", exc)

        try:
            embedding_check = (
                agent_main.supabase.table("document_chunks")
                .select("id,embedding")
                .limit(5)
                .execute()
            )
            if embedding_check.data:
                embedding_rows: list[dict[str, Any]] = embedding_check.data  # type: ignore[assignment]
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
            rpc_test = agent_main.supabase.rpc(
                "search_similar_documents",
                {"query_embedding": test_embedding, "match_threshold": 0.0, "match_count": 1},
            ).execute()
            diagnostics["rpc_function_exists"] = True
            rpc_test_data: list[dict[str, Any]] = rpc_test.data or []  # type: ignore[assignment]
            diagnostics["rpc_test_results"] = len(rpc_test_data)
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

        result = agent_main.supabase.rpc(
            "search_similar_documents",
            {
                "query_embedding": question_embedding,
                "match_threshold": test_threshold,
                "match_count": 10,
            },
        ).execute()
        result_data: list[dict[str, Any]] = result.data or []  # type: ignore[assignment]

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
    if agent_main.supabase is None:
        return {"status": "error", "error": "Supabase client not initialized"}
    supabase_client = agent_main.supabase
    try:
        info: dict[str, Any] = {}

        try:
            count_result = supabase_client.table("document_chunks").select("id").limit(1).execute()
            info["total_rows"] = (
                count_result.count
                if hasattr(count_result, "count")
                else len(supabase_client.table("document_chunks").select("id").execute().data or [])
            )
        except Exception as exc:
            info["total_rows"] = f"error: {exc}"

        try:
            sample_result = (
                supabase_client.table("document_chunks")
                .select("id,source_url,chunk_index,embedding,content")
                .limit(3)
                .execute()
            )
            if sample_result.data:
                sample_rows: list[dict[str, Any]] = sample_result.data  # type: ignore[assignment]
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
            rpc_result = supabase_client.rpc(
                "search_similar_documents",
                {"query_embedding": test_embedding, "match_threshold": 0.0, "match_count": 1},
            ).execute()
            info["rpc_function_works"] = True
            rpc_data: list[dict[str, Any]] = rpc_result.data or []  # type: ignore[assignment]
            info["rpc_test_returned"] = len(rpc_data)
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
