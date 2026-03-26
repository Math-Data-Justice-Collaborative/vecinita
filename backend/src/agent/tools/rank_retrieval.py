"""Retrieval ranking tool for Vecinita agent.

Provides deterministic lightweight reranking for db_search results.
"""

import json
import re
from typing import Any

from langchain_core.tools import tool


def _tokenize_for_rerank(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) > 1}


def _rerank_results(query: str, docs: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    """Lightweight lexical reranker to improve top-ordering relevance."""
    query_terms = _tokenize_for_rerank(query)
    if not query_terms:
        return docs[:top_k]

    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in docs:
        content_terms = _tokenize_for_rerank(str(doc.get("content", "")))
        overlap = len(query_terms & content_terms)
        recall = overlap / max(1, len(query_terms))
        base_similarity = float(doc.get("similarity", 0.0) or 0.0)
        combined = (0.75 * base_similarity) + (0.25 * recall)
        scored.append((combined, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def create_rank_retrieval_tool():
    """Create ranking tool for retrieval result ordering."""

    @tool
    def rank_retrieval_results(query: str, results_json: str, top_k: int = 5) -> str:
        """Rerank retrieval results based on lexical-query relevance and similarity.

        Args:
            query: Original user query.
            results_json: JSON list returned by db_search.
            top_k: Maximum results to return after reranking.

        Returns:
            JSON string of reranked retrieval documents.
        """
        try:
            docs = json.loads(results_json) if isinstance(results_json, str) else []
            if not isinstance(docs, list):
                return "[]"

            safe_docs = [doc for doc in docs if isinstance(doc, dict)]
            safe_top_k = max(1, min(int(top_k or 5), 50))
            ranked = _rerank_results(query, safe_docs, safe_top_k)
            return json.dumps(ranked, ensure_ascii=False)
        except Exception:
            return "[]"

    return rank_retrieval_results
