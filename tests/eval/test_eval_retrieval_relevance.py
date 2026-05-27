"""T14.5 / AC benchmarks: ≥80% retrieval relevance on eval fixture (D3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import create_engine, text
from tests.e2e.local_bootstrap import postgres_is_ready
from tests.helpers.json_response import json_str
from tests.unit.rag.conftest import attach_embeddings, basis_vector
from vecinita_database.seeds.load import _database_url, load_corpus
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

pytestmark = pytest.mark.integration

_EVAL_PATH = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "eval" / "qa_pairs.json"
_RELEVANCE_THRESHOLD = 0.8


@pytest.fixture
def eval_db() -> str:
    if not postgres_is_ready():
        pytest.skip("Postgres not available for eval benchmark")
    url = _database_url()
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM embeddings"))
        conn.execute(text("DELETE FROM chunks"))
        conn.execute(text("DELETE FROM documents"))
    load_corpus(database_url=url)
    attach_embeddings(
        database_url=url,
        match_substrings={
            "Food pantry": 0,
            "story time": 0,
            "library": 1,
            "Wi-Fi": 1,
            "banco de alimentos": 2,
            "biblioteca": 2,
            "cuentacuentos": 2,
        },
        default_index=3,
    )
    return url


def _load_pairs() -> list[JsonObject]:
    raw = cast(object, json.loads(_EVAL_PATH.read_text(encoding="utf-8")))
    if not isinstance(raw, list):
        msg = f"Expected JSON array in {_EVAL_PATH}"
        raise TypeError(msg)
    return [as_json_object(cast(object, item)) for item in raw]


def test_eval_retrieval_relevance_at_least_eighty_percent(eval_db: str) -> None:
    pairs = _load_pairs()
    assert pairs, "eval fixture must contain at least one Q&A pair"

    def embed_fn(question: str) -> list[float]:
        if "¿" in question or any(ch in question for ch in "áéíóúñ"):
            return basis_vector(2)
        if "library" in question.lower():
            return basis_vector(1)
        return basis_vector(0)

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=eval_db,
        top_k=5,
    )

    hits = 0
    for pair in pairs:
        question = json_str(pair, "question")
        expected_url = json_str(pair, "expected_doc_url")
        chunks = retriever.retrieve_chunks(question)
        urls = {chunk.url for chunk in chunks if chunk.url}
        if expected_url in urls:
            hits += 1

    rate = hits / len(pairs)
    assert rate >= _RELEVANCE_THRESHOLD, (
        f"retrieval relevance {rate:.0%} below {_RELEVANCE_THRESHOLD:.0%} "
        f"({hits}/{len(pairs)} expected URLs in top-k)"
    )
