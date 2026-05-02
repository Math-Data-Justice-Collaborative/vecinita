"""Unit tests for retrieval ranking tool."""

import json

from src.agent.tools.rank_retrieval import create_rank_retrieval_tool


def test_rank_retrieval_reorders_by_lexical_overlap():
    tool = create_rank_retrieval_tool()
    docs = [
        {
            "content": "General neighborhood information and updates",
            "source_url": "https://example.com/general",
            "similarity": 0.94,
        },
        {
            "content": "Housing assistance and rental support program details",
            "source_url": "https://example.com/housing",
            "similarity": 0.72,
        },
    ]

    ranked_json = tool.invoke(
        {
            "query": "housing assistance",
            "results_json": json.dumps(docs),
            "top_k": 2,
        }
    )

    ranked = json.loads(ranked_json)
    assert ranked[0]["source_url"] == "https://example.com/housing"


def test_rank_retrieval_handles_invalid_input():
    tool = create_rank_retrieval_tool()
    ranked_json = tool.invoke(
        {
            "query": "housing",
            "results_json": "not-json",
            "top_k": 2,
        }
    )
    assert ranked_json == "[]"
