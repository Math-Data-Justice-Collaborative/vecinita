"""Unit tests for LLM client query coercion (Pydantic/FastAPI-friendly URL handling).

Sentinel query strings like ``model=null`` must not be forwarded as literal model ids
to upstream chat APIs — see ``coerce_optional_query_str`` and ``resolve_request``.
"""

import pytest

from src.services.llm.client_manager import LocalLLMClientManager, coerce_optional_query_str

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
        ("llama3.1:8b", "llama3.1:8b"),
    ],
)
def test_coerce_optional_query_str_sentinels_and_strip(raw, expected):
    assert coerce_optional_query_str(raw) == expected


def test_resolve_request_drops_null_string_model_for_default():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:10000/model",
        default_model="llama3.1:8b",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "null")
    assert provider == "ollama"
    assert model == "llama3.1:8b"


def test_resolve_request_drops_control_characters_in_model():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:10000/model",
        default_model="llama3.1:8b",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "bad\x00name")
    assert provider == "ollama"
    assert model == "llama3.1:8b"


def test_resolve_request_preserves_clean_explicit_model():
    mgr = LocalLLMClientManager(
        base_url="http://127.0.0.1:10000/model",
        default_model="llama3.1:8b",
        selection_file_path=None,
        locked=False,
    )
    provider, model = mgr.resolve_request(None, "mistral:7b")
    assert provider == "ollama"
    assert model == "mistral:7b"
