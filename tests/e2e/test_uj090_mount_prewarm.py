"""UJ-090 / TC-318-02: ChatRAG mount prewarm hits /api/v1/warm (not /health).

[Corpus: user-journeys.md §UJ-090] [Spec: docs/test-plan.md §TC-318-02]
"""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings

from tests.unit.chat_rag.conftest import StubChatRagService, database_url


@pytest.mark.e2e
def test_uj090_post_warm_returns_warming_and_schedules_modal_warm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mount prewarm contract: immediate warming; background uses Modal /warm paths."""
    monkeypatch.setenv("DATABASE_URL", database_url())
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "test-proxy-key")
    settings = ChatRagSettings(
        database_url=database_url(),
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=10.0,
        internal_write_url="http://write.test",
        internal_api_key="write-key",
    )
    client = TestClient(
        create_app(settings=settings, chat_service=StubChatRagService())  # type: ignore[arg-type]
    )
    with patch("vecinita_chat_rag_backend.app._warm_modal_services") as mock_warm:
        response = client.post("/api/v1/warm")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "warming"}
    mock_warm.assert_called_once_with(
        "http://embed.test",
        "http://llm.test",
        request_timeout_s=10.0,
        llm_proxy_key="test-proxy-key",
    )
