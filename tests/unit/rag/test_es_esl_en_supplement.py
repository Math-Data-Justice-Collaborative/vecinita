"""EV-029 / #217 R6 — Spanish ESL queries supplement EN corpus retrieval."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.es_esl_supplement import (
    merge_es_esl_retrieval_for_r6,
    merge_retrieved_chunks_by_score,
    should_supplement_en_for_es_esl_query,
)
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest

pytestmark = pytest.mark.unit

_ESL_QUESTION = "¿Dónde puedo encontrar clases gratis de inglés en Providence?"
_NUEVAS_VOCES = "¿Qué es Nuevas Voces?"
_BLEND_TOP_K = 4
_MERGE_TOP_K = 3
_DUP_EN_SCORE = 0.95
_MID_EN_SCORE = 0.8
_LOW_ES_SCORE = 0.5


def _chunk(
    *,
    score: float,
    language: str | None,
    url: str,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="body",
        score=score,
        title="Title",
        url=url,
        language=language,
    )


def test_should_supplement_es_question_with_ingles_keyword() -> None:
    """Spanish ESL question triggers EN supplement (EV-029 R6)."""
    assert should_supplement_en_for_es_esl_query(
        language="es",
        question=_ESL_QUESTION,
        tag_slugs=None,
    )


def test_should_supplement_es_question_with_esl_tag() -> None:
    """Explicit esl tag triggers EN supplement even without inglés keyword."""
    assert should_supplement_en_for_es_esl_query(
        language="es",
        question="clases en Providence",
        tag_slugs=["esl"],
    )


def test_should_not_supplement_pure_spanish_community_question() -> None:
    """Non-ESL Spanish queries stay ES-filtered only."""
    assert not should_supplement_en_for_es_esl_query(
        language="es",
        question=_NUEVAS_VOCES,
        tag_slugs=None,
    )


def test_should_not_supplement_english_locale() -> None:
    """EN locale does not trigger cross-language supplement."""
    assert not should_supplement_en_for_es_esl_query(
        language="en",
        question=_ESL_QUESTION,
        tag_slugs=None,
    )


def test_merge_es_esl_retrieval_caps_spanish_hits() -> None:
    """Spanish ESL blend keeps EN program pages in the merged top_k."""
    es_chunks = [
        _chunk(score=0.99, language="es", url="https://vecina.wrwc.org/es/education/"),
        _chunk(score=0.98, language="es", url="https://vecina.wrwc.org/es/conocenos/"),
        _chunk(score=0.97, language="es", url="https://childrensfriendri.org/head-start-espanol/"),
    ]
    en_chunks = [
        _chunk(
            score=0.6,
            language="en",
            url="https://provlib.org/education/adults/ri-family-literacy-initiative/",
        ),
        _chunk(
            score=0.55,
            language="en",
            url="https://clpvd.org/learn/spotlight/adult-education/esol/",
        ),
    ]
    merged = merge_es_esl_retrieval_for_r6(es_chunks, en_chunks, top_k=_BLEND_TOP_K)
    urls = [chunk.url for chunk in merged]
    assert len(merged) == _BLEND_TOP_K
    assert urls.count("https://vecina.wrwc.org/es/education/") == 1
    assert "https://provlib.org/education/adults/ri-family-literacy-initiative/" in urls
    assert "https://clpvd.org/learn/spotlight/adult-education/esol/" in urls


def test_merge_retrieved_chunks_by_score_dedupes_and_ranks() -> None:
    """Merged retrieve keeps highest-scoring unique chunks up to top_k."""
    shared_id = uuid4()
    primary = [
        _chunk(
            score=_LOW_ES_SCORE,
            language="es",
            url="https://vecina.wrwc.org/es/education/",
        ),
        RetrievedChunk(
            chunk_id=shared_id,
            document_id=uuid4(),
            text="dup",
            score=0.4,
            title="dup",
            url="https://vecina.wrwc.org/es/education/",
            language="es",
        ),
    ]
    supplemental = [
        RetrievedChunk(
            chunk_id=shared_id,
            document_id=uuid4(),
            text="dup-en",
            score=_DUP_EN_SCORE,
            title="dup-en",
            url="https://provlib.org/education/adults/ri-family-literacy-initiative/",
            language="en",
        ),
        _chunk(
            score=_MID_EN_SCORE,
            language="en",
            url="https://clpvd.org/learn/spotlight/adult-education/esol/",
        ),
    ]
    merged = merge_retrieved_chunks_by_score(primary, supplemental, top_k=_MERGE_TOP_K)
    assert len(merged) == _MERGE_TOP_K
    assert merged[0].score == _DUP_EN_SCORE
    assert merged[0].url == "https://provlib.org/education/adults/ri-family-literacy-initiative/"
    assert merged[1].score == _MID_EN_SCORE
    assert merged[2].score == _LOW_ES_SCORE


class _LangAwareStubRetriever:
    def __init__(self) -> None:
        self.languages: list[str | None] = []

    def retrieve_chunks(
        self,
        _question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = None,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> list[RetrievedChunk]:
        _ = (tag_slugs, top_k, score_threshold)
        self.languages.append(language)
        if language == "es":
            return [
                _chunk(
                    score=0.7,
                    language="es",
                    url="https://vecina.wrwc.org/es/education/",
                ),
            ]
        if language == "en":
            return [
                _chunk(
                    score=0.9,
                    language="en",
                    url="https://provlib.org/education/adults/ri-family-literacy-initiative/",
                ),
                _chunk(
                    score=0.85,
                    language="en",
                    url="https://clpvd.org/learn/spotlight/adult-education/esol/",
                ),
            ]
        return []


class _StubLlm:
    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        return "Programas de inglés en Providence."

    def generate_stream(self, prompt: str, **kwargs: object) -> list[str]:
        _ = (prompt, kwargs)
        return ["Programas"]

    def close(self) -> None:
        return


def test_chat_service_supplements_en_chunks_for_spanish_esl_question() -> None:
    """Service retrieve_sources merges EN ESL hits when language=es (EV-029 R6)."""
    retriever = _LangAwareStubRetriever()
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=_StubLlm(),  # type: ignore[arg-type]
    )
    sources = service.retrieve_sources(
        AskRequest(question=_ESL_QUESTION, language="es"),
    )
    urls = {source.url for source in sources if source.url is not None}
    assert "https://provlib.org/education/adults/ri-family-literacy-initiative/" in urls
    assert "es" in retriever.languages
    assert "en" in retriever.languages
