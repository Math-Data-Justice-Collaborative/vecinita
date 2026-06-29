"""BUG-2026-06-05 / issue #54: language-aware corpus filtering for bilingual retrieval.

Staging symptom: English questions against a Spanish-only corpus return no-context answers
because retrieval is not filtered by selected corpus language.

Expected (issue #54 + EV-005 #57): AskRequest.language filters documents.language and
routes query/response language together.
"""

from __future__ import annotations

import inspect
import os
from pathlib import Path

import pytest
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_shared_schemas.chat_rag import AskRequest

from tests.unit.rag.conftest import basis_vector, seed_spanish_only_corpus

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]
CHAT_SERVICE = REPO_ROOT / "apps" / "chat-rag-backend" / "vecinita_chat_rag_backend" / "service.py"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def spanish_only_corpus_db() -> str:
    """Corpus with only Spanish documents (staging-like)."""
    url = _database_url()
    seed_spanish_only_corpus(database_url=url)
    return url


def test_ask_request_accepts_language_field() -> None:
    """API contract must carry explicit corpus/query language (EV-005)."""
    request = AskRequest(question="When is the food pantry open?", language="en")
    assert request.language == "en"


def test_retrieve_chunks_supports_language_filter(spanish_only_corpus_db: str) -> None:
    """Spanish-only corpus: language=es returns ES chunks; language=en returns none."""
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=spanish_only_corpus_db,
        top_k=3,
    )
    sig = inspect.signature(retriever.retrieve_chunks)
    assert "language" in sig.parameters, "retrieve_chunks must accept language= filter"

    es_chunks = retriever.retrieve_chunks(
        "¿Cuándo publica horarios el banco de alimentos?",
        language="es",
    )
    en_chunks = retriever.retrieve_chunks(
        "When is the food pantry open?",
        language="en",
    )

    assert es_chunks, "Spanish query with language=es should hit Spanish-only corpus"
    assert all(chunk.language == "es" for chunk in es_chunks)
    assert en_chunks == [], "language=en on Spanish-only corpus must not return ES chunks"


def test_chat_service_passes_request_language_to_retriever() -> None:
    """ChatRagService must resolve and forward language into retrieval."""
    text_body = CHAT_SERVICE.read_text(encoding="utf-8")
    assert "_effective_language" in text_body
    assert "language=language" in text_body
