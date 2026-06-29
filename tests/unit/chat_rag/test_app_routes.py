"""Unit tests for ChatRAG FastAPI routes and helpers."""

from __future__ import annotations

import json
from http import HTTPStatus
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
from vecinita_chat_rag_backend.app import (
    _check_dependency,  # pyright: ignore[reportPrivateUsage]
    _fire_stats,  # pyright: ignore[reportPrivateUsage]
    _source_payload,  # pyright: ignore[reportPrivateUsage]
    _warm_modal_services,  # pyright: ignore[reportPrivateUsage]
    _warm_modal_url,  # pyright: ignore[reportPrivateUsage]
    create_app,
    parse_ask_body,
)
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_shared_schemas.chat_rag import Source
from vecinita_shared_schemas.json_types import (
    as_json_object,
)

from tests.helpers.json_response import (
    json_list,
    json_str,
    response_json_object,
)
from tests.unit.chat_rag.conftest import (
    StubChatRagService,
    database_url,
)

_WARM_SERVICE_COUNT = 2


@pytest.fixture
def client(chat_settings: ChatRagSettings) -> TestClient:
    """Client."""
    service = StubChatRagService()
    return TestClient(create_app(settings=chat_settings, chat_service=service))  # type: ignore[arg-type]


async def _request_with_body(body: object) -> Request:
    """Request with body."""
    payload = json.dumps(body).encode()

    async def receive() -> dict[str, object]:
        """Receive."""
        return {"type": "http.request", "body": payload, "more_body": False}

    scope: dict[str, object] = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/ask",
        "headers": [],
    }
    return Request(scope, receive)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_parse_ask_body_accepts_valid_question() -> None:
    """Test parse ask body accepts valid question."""
    request = await _request_with_body({"question": "Where is the clinic?"})
    body = await parse_ask_body(request)
    assert body.question == "Where is the clinic?"


@pytest.mark.asyncio
async def test_parse_ask_body_rejects_invalid_json() -> None:
    """Test parse ask body rejects invalid json."""
    scope: dict[str, object] = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/ask",
        "headers": [],
    }

    async def receive() -> dict[str, object]:
        """Receive."""
        return {"type": "http.request", "body": b"{not-json", "more_body": False}

    request = Request(scope, receive)  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as exc:
        await parse_ask_body(request)
    assert getattr(exc.value, "status_code", None) == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_parse_ask_body_rejects_non_object_json() -> None:
    """Test parse ask body rejects non object json."""
    request = await _request_with_body(["not", "an", "object"])
    with pytest.raises(HTTPException) as exc:
        await parse_ask_body(request)
    assert getattr(exc.value, "status_code", None) == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_parse_ask_body_rejects_identity_fields() -> None:
    """Test parse ask body rejects identity fields."""
    request = await _request_with_body({"question": "hi", "user_id": "abc"})
    with pytest.raises(HTTPException) as exc:
        await parse_ask_body(request)
    assert getattr(exc.value, "status_code", None) == HTTPStatus.BAD_REQUEST


def test_check_dependency_not_configured() -> None:
    """Test check dependency not configured."""
    assert _check_dependency(None) == "not_configured"


def test_check_dependency_ok() -> None:
    """Test check dependency ok."""
    with patch("vecinita_chat_rag_backend.app.httpx.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json={"status": "ok"})
        assert _check_dependency("http://embed.test") == "ok"


def test_check_dependency_error_on_http_failure() -> None:
    """Test check dependency error on http failure."""
    with patch("vecinita_chat_rag_backend.app.httpx.get") as mock_get:
        mock_get.side_effect = httpx.ConnectError("down")
        assert _check_dependency("http://embed.test") == "error"


def test_check_dependency_error_on_non_200() -> None:
    """Test check dependency error on non 200."""
    with patch("vecinita_chat_rag_backend.app.httpx.get") as mock_get:
        mock_get.return_value = httpx.Response(503)
        assert _check_dependency("http://embed.test") == "error"


def test_warm_modal_url_posts_to_warm_path() -> None:
    """Test warm modal url posts to warm path."""
    with patch("vecinita_chat_rag_backend.app.httpx.post") as mock_post:
        _warm_modal_url("http://llm.test", timeout_s=30.0)
    mock_post.assert_called_once_with("http://llm.test/warm", timeout=30.0)


def test_warm_modal_services_warms_embed_and_llm_in_parallel() -> None:
    """Test warm modal services warms embed and llm in parallel."""
    with patch("vecinita_chat_rag_backend.app._warm_modal_url") as mock_warm:
        _warm_modal_services(
            "http://embed.test",
            "http://llm.test",
            request_timeout_s=120.0,
        )
    assert mock_warm.call_count == _WARM_SERVICE_COUNT
    mock_warm.assert_any_call("http://embed.test", timeout_s=120.0)
    mock_warm.assert_any_call("http://llm.test", timeout_s=120.0)


def test_warm_modal_services_skips_when_urls_missing() -> None:
    """Test warm modal services skips when urls missing."""
    with patch("vecinita_chat_rag_backend.app._warm_modal_url") as mock_warm:
        _warm_modal_services(None, None, request_timeout_s=30.0)
    mock_warm.assert_not_called()


def test_warm_modal_services_warms_embed_only() -> None:
    """Test warm modal services warms embed only."""
    with patch("vecinita_chat_rag_backend.app._warm_modal_url") as mock_warm:
        _warm_modal_services("http://embed.test", None, request_timeout_s=30.0)
    mock_warm.assert_called_once_with("http://embed.test", timeout_s=30.0)


def test_warm_modal_services_warms_llm_only() -> None:
    """Test warm modal services warms llm only."""
    with patch("vecinita_chat_rag_backend.app._warm_modal_url") as mock_warm:
        _warm_modal_services(None, "http://llm.test", request_timeout_s=30.0)
    mock_warm.assert_called_once_with("http://llm.test", timeout_s=30.0)


def test_warm_modal_endpoint_schedules_background_warm(client: TestClient) -> None:
    """Test warm modal endpoint schedules background warm."""
    with patch("vecinita_chat_rag_backend.app._warm_modal_services") as mock_warm:
        response = client.post("/api/v1/warm")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "warming"}
    mock_warm.assert_called_once_with(
        "http://embed.test",
        "http://llm.test",
        request_timeout_s=10.0,
    )


def test_source_payload_stringifies_uuid_fields() -> None:
    """Test source payload stringifies uuid fields."""
    chunk_id = uuid4()
    document_id = uuid4()
    payload = _source_payload(
        [
            Source(
                chunk_id=chunk_id,
                document_id=document_id,
                title="Doc",
                url="https://example.com",
                score=0.5,
            )
        ]
    )
    assert payload[0]["chunk_id"] == str(chunk_id)
    assert payload[0]["document_id"] == str(document_id)


def test_source_payload_stringifies_uuid_when_encoder_returns_uuid() -> None:
    """Test source payload stringifies uuid when encoder returns uuid."""
    chunk_id = uuid4()
    document_id = uuid4()
    source = Source(
        chunk_id=chunk_id,
        document_id=document_id,
        title="Doc",
        url="https://example.com",
        score=0.5,
    )
    with patch("vecinita_chat_rag_backend.app.jsonable_encoder") as mock_encoder:
        mock_encoder.return_value = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "title": "Doc",
            "url": "https://example.com",
            "score": 0.5,
        }
        payload = _source_payload([source])
    assert payload[0]["chunk_id"] == str(chunk_id)
    assert payload[0]["document_id"] == str(document_id)


def test_fire_stats_posts_document_ids() -> None:
    """Test fire stats posts document ids."""
    document_id = uuid4()
    with patch("vecinita_chat_rag_backend.app.httpx.post") as mock_post:
        _fire_stats(
            [
                Source(
                    chunk_id=uuid4(),
                    document_id=document_id,
                    title="Doc",
                    url="https://example.com",
                    score=0.5,
                )
            ],
            "http://write.test",
            "secret-key",
        )
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-key"


def test_health_reports_dependencies(client: TestClient) -> None:
    """Test health reports dependencies."""
    with patch("vecinita_chat_rag_backend.app.httpx.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json={"status": "ok"})
        response = client.get("/health")
    body = response_json_object(response)
    deps = as_json_object(body["dependencies"])
    assert json_str(deps, "postgres") == "ok"
    assert json_str(deps, "modal_embed") == "ok"


def test_health_marks_postgres_error(chat_settings: ChatRagSettings) -> None:
    """Test health marks postgres error."""
    broken = ChatRagSettings(
        database_url="postgresql+psycopg://invalid:invalid@127.0.0.1:1/nodb",
        top_k=chat_settings.top_k,
        embed_url=chat_settings.embed_url,
        llm_url=chat_settings.llm_url,
        request_timeout_s=chat_settings.request_timeout_s,
    )
    client = TestClient(create_app(settings=broken))
    with patch("vecinita_chat_rag_backend.app.httpx.get") as mock_get:
        mock_get.return_value = httpx.Response(200)
        response = client.get("/health")
    deps = as_json_object(response_json_object(response)["dependencies"])
    assert json_str(deps, "postgres") == "error"


def test_ask_returns_stub_answer(client: TestClient) -> None:
    """Test ask returns stub answer."""
    response = client.post("/api/v1/ask", json={"question": "Where is the clinic?"})
    assert response.status_code == HTTPStatus.OK
    assert json_str(response_json_object(response), "answer") == "Stub answer"


def test_ask_returns_503_when_service_fails(chat_settings: ChatRagSettings) -> None:
    """Test ask returns 503 when service fails."""
    service = StubChatRagService(ask_error=RuntimeError("upstream down"))
    client = TestClient(create_app(settings=chat_settings, chat_service=service))  # type: ignore[arg-type]
    response = client.post("/api/v1/ask", json={"question": "fail?"})
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_ask_stream_emits_sse_tokens(chat_settings: ChatRagSettings) -> None:
    """Test ask stream emits sse tokens."""
    service = StubChatRagService(stream_tokens=["Hi", " there"])
    client = TestClient(create_app(settings=chat_settings, chat_service=service))  # type: ignore[arg-type]
    with client.stream("POST", "/api/v1/ask/stream", json={"question": "hello"}) as response:
        assert response.status_code == HTTPStatus.OK
        body = "".join(response.iter_text())
    assert "data:" in body
    assert "Hi" in body
    assert '"done": true' in body


def test_ask_stream_empty_sources_falls_back_to_ask(chat_settings: ChatRagSettings) -> None:
    """Test ask stream empty sources falls back to ask."""
    service = StubChatRagService(sources=[])
    client = TestClient(create_app(settings=chat_settings, chat_service=service))  # type: ignore[arg-type]
    with client.stream("POST", "/api/v1/ask/stream", json={"question": "empty"}) as response:
        body = "".join(response.iter_text())
    assert "Stub answer" in body
    assert '"sources": []' in body


def test_ask_stream_returns_503_when_retrieval_fails(chat_settings: ChatRagSettings) -> None:
    """Test ask stream returns 503 when retrieval fails."""
    service = StubChatRagService(retrieve_error=RuntimeError("retrieval failed"))
    client = TestClient(create_app(settings=chat_settings, chat_service=service))  # type: ignore[arg-type]
    response = client.post("/api/v1/ask/stream", json={"question": "fail"})
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_list_documents_route(
    client: TestClient,
    browse_document: tuple[UUID, str],
) -> None:
    """Test list documents route."""
    _doc_id, doc_url = browse_document
    response = client.get("/api/v1/documents")
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    items = json_list(body, "items")
    assert any(json_str(as_json_object(item), "url") == doc_url for item in items)


def test_get_document_route(
    client: TestClient,
    browse_document: tuple[UUID, str],
) -> None:
    """Test get document route."""
    doc_id, doc_url = browse_document
    response = client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == HTTPStatus.OK
    assert json_str(response_json_object(response), "url") == doc_url


def test_get_document_route_404(client: TestClient) -> None:
    """Test get document route 404."""
    response = client.get(f"/api/v1/documents/{uuid4()}")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_list_tags_route(
    client: TestClient,
    browse_document: tuple[UUID, str],
) -> None:
    """Test list tags route."""
    _doc_id, _doc_url = browse_document
    response = client.get("/api/v1/tags")
    assert response.status_code == HTTPStatus.OK
    tags = json_list(response_json_object(response), "tags")
    assert any(json_str(as_json_object(tag), "slug") == "housing" for tag in tags)


def test_fire_stats_noops_when_disabled() -> None:
    """Test fire stats noops when disabled."""
    with patch("vecinita_chat_rag_backend.app.httpx.post") as mock_post:
        _fire_stats(
            [
                Source(
                    chunk_id=uuid4(),
                    document_id=uuid4(),
                    title="Doc",
                    url="https://example.com",
                    score=0.5,
                )
            ],
            "http://write.test",
            "secret-key",
            stats_enabled=False,
        )
    mock_post.assert_not_called()


def test_fire_stats_noops_when_no_sources() -> None:
    """Test fire stats noops when no sources."""
    with patch("vecinita_chat_rag_backend.app.httpx.post") as mock_post:
        _fire_stats([], "http://write.test", "secret-key")
    mock_post.assert_not_called()


def test_fire_stats_noops_when_sources_lack_document_id() -> None:
    """Test fire stats noops when sources lack document id."""
    source_without_doc = Source.model_construct(
        chunk_id=uuid4(),
        document_id=None,
        title="Doc",
        url="https://example.com",
        score=0.5,
    )
    with patch("vecinita_chat_rag_backend.app.httpx.post") as mock_post:
        _fire_stats([source_without_doc], "http://write.test", "secret-key")
    mock_post.assert_not_called()


def test_source_payload_leaves_string_ids_unchanged() -> None:
    """Test source payload leaves string ids unchanged."""
    payload = _source_payload(
        [
            Source(
                chunk_id=uuid4(),
                document_id=uuid4(),
                title="Doc",
                url="https://example.com",
                score=0.5,
            )
        ]
    )
    first = payload[0]
    assert isinstance(first["chunk_id"], str)
    assert isinstance(first["document_id"], str)


def test_create_app_lazy_loads_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test create app lazy loads settings."""
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_MODAL_EMBED_URL", "http://embed.test")
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")
    client = TestClient(create_app())
    with patch("vecinita_chat_rag_backend.app.httpx.get") as mock_get:
        mock_get.return_value = httpx.Response(200)
        response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
