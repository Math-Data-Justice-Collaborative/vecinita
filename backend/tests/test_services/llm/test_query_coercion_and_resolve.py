"""Unit tests for LLM client query coercion (Pydantic/FastAPI-friendly URL handling).

Sentinel query strings like ``model=null`` must not be forwarded as literal model ids
to upstream chat APIs — see ``coerce_optional_query_str`` and ``resolve_request``.
"""

import pytest

from src.services.llm.client_manager import (
    LocalLLMClientManager,
    _ModalNativeChatClient,
    coerce_optional_query_str,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("null", None),
        ("NULL", None),
        ("None", None),
        ("undefined", None),
        ("  ollama  ", "ollama"),
        ("gemma3", "gemma3"),
    ],
)
def test_coerce_optional_query_str_sentinels_and_strip(raw, expected):
    assert coerce_optional_query_str(raw) == expected


def test_resolve_request_drops_null_string_model_for_default():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:10000/model",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "null")
    assert provider == "ollama"
    assert model == "gemma3"


def test_resolve_request_drops_control_characters_in_model():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:10000/model",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "bad\x00name")
    assert provider == "ollama"
    assert model == "gemma3"


def test_resolve_request_preserves_clean_explicit_model():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:10000/model",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "mistral")
    assert provider == "ollama"
    assert model == "mistral"


def test_resolve_request_unknown_model_falls_back_for_modal_native():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:10000/model",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "mistral:7b")
    assert provider == "ollama"
    assert model == "gemma3"


def test_resolve_request_unknown_model_allowed_for_direct_ollama_http():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:11434",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "mistral:7b")
    assert provider == "ollama"
    assert model == "mistral:7b"


def test_resolve_request_unknown_model_falls_back_for_modal_run_url():
    mgr = LocalLLMClientManager(
        base_url="https://vecinita--vecinita-model-api.modal.run",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "fuzzed-model-id")
    assert provider == "ollama"
    assert model == "gemma3"


def test_modal_native_chat_client_can_use_modal_function_invocation(monkeypatch):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    import src.services.llm.client_manager as client_manager

    monkeypatch.setattr(
        client_manager,
        "invoke_modal_model_chat",
        lambda **_kwargs: {"message": {"content": "hello from function"}},
    )

    client = _ModalNativeChatClient(
        base_url="https://example.modal.run",
        model="gemma3",
        headers={},
    )
    message = client.invoke([])
    assert message.content == "hello from function"


def test_validate_runtime_rejects_modal_run_when_invocation_disabled(monkeypatch):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    mgr = LocalLLMClientManager(
        base_url="https://example.modal.run",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    with pytest.raises(RuntimeError, match="Model base URL targets Modal"):
        mgr.validate_runtime()


def test_validate_runtime_accepts_modal_run_when_invocation_enabled(monkeypatch):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    mgr = LocalLLMClientManager(
        base_url="https://example.modal.run",
        default_model="gemma3",
        selection_file_path=None,
        locked=False,
    )
    mgr.validate_runtime()
