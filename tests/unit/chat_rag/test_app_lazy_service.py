"""Lazy ChatRagService initialization coverage."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import (
    create_app,
)
from vecinita_chat_rag_backend.config import ChatRagSettings

from tests.unit.chat_rag.conftest import (
    StubChatRagService,
    database_url,
)


def test_ask_lazy_inits_service() -> None:
    """Test ask lazy inits service."""
    settings = ChatRagSettings(
        database_url=database_url(),
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=10.0,
    )
    client = TestClient(create_app(settings=settings))
    with (
        patch("vecinita_chat_rag_backend.app.httpx.post"),
        patch(
            "vecinita_chat_rag_backend.app.ChatRagService.from_settings",
            return_value=StubChatRagService(),
        ) as mock_factory,
    ):
        response = client.post("/api/v1/ask", json={"question": "lazy init?"})
    assert response.status_code == HTTPStatus.OK
    mock_factory.assert_called_once()
