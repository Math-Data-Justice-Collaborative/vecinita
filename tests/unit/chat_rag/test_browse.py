"""Unit tests for public corpus browse queries."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import text
from vecinita_chat_rag_backend.browse import (
    engine_from_url,
    get_document,
    list_documents,
    list_tag_facets,
)

from tests.unit.chat_rag.conftest import database_url

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def test_engine_from_url_creates_engine() -> None:
    engine = engine_from_url(database_url())
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    finally:
        engine.dispose()


def test_list_documents_returns_page(
    engine: Engine,
    browse_document: tuple[UUID, str],
) -> None:
    _doc_id, doc_url = browse_document
    page = list_documents(engine, page=1, page_size=10)
    assert page.total >= 1
    assert any(item.url == doc_url for item in page.items)


def test_list_documents_filters_by_tag(
    engine: Engine,
    browse_document: tuple[UUID, str],
) -> None:
    doc_id, _doc_url = browse_document
    page = list_documents(engine, tags=["housing"], page=1, page_size=20)
    assert any(item.document_id == doc_id for item in page.items)


def test_list_documents_filters_by_query(
    engine: Engine,
    browse_document: tuple[UUID, str],
) -> None:
    _doc_id, _doc_url = browse_document
    page = list_documents(engine, q="Browse fixture", page=1, page_size=20)
    assert page.total >= 1
    assert any(item.title == "Browse fixture" for item in page.items)


def test_get_document_returns_detail(
    engine: Engine,
    browse_document: tuple[UUID, str],
) -> None:
    doc_id, doc_url = browse_document
    detail = get_document(engine, doc_id)
    assert detail is not None
    assert detail.url == doc_url
    assert detail.tags[0].slug == "housing"


def test_get_document_returns_none_for_missing(engine: Engine) -> None:
    assert get_document(engine, uuid.uuid4()) is None


def test_list_tag_facets_includes_housing(
    engine: Engine,
    browse_document: tuple[UUID, str],
) -> None:
    _doc_id, _doc_url = browse_document
    response = list_tag_facets(engine)
    assert any(tag.slug == "housing" for tag in response.tags)
