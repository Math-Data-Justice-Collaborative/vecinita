"""Contract sync tests for backend chat payloads vs model service schemas."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from src.services.llm.client_manager import _ModalNativeChatClient

pytestmark = pytest.mark.unit


def _load_model_service_schemas_module():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / "services" / "model-modal" / "src" / "vecinita" / "api" / "schemas.py"

    spec = importlib.util.spec_from_file_location("model_modal_schemas", module_path)
    assert spec and spec.loader, f"Unable to load service schemas from {module_path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_modal_native_client_payload_matches_model_service_chat_schema(monkeypatch):
    captured: dict[str, object] = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "ok"}}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json, headers):
            captured["url"] = url
            captured["payload"] = json
            captured["headers"] = headers
            return _FakeResponse()

    monkeypatch.setattr("src.services.llm.client_manager.httpx.Client", _FakeClient)

    client = _ModalNativeChatClient(
        base_url="http://vecinita-modal-proxy-v1:10000/model",
        model="llama3.2",
        headers={"X-Proxy-Token": "secret"},
        temperature=0.2,
    )

    response = client.invoke(
        [SystemMessage(content="You are helpful."), HumanMessage(content="Hola")]
    )

    assert response.content == "ok"
    assert str(captured["url"]).endswith("/chat")

    schemas = _load_model_service_schemas_module()
    parsed = schemas.ChatRequest.model_validate(captured["payload"])

    assert parsed.model == "llama3.2"
    assert len(parsed.messages) == 2
    assert parsed.messages[0].role == "system"
    assert parsed.messages[1].role == "user"
