"""LLM tag client HTTP contract tests (ADR-015 TP-014, EV-001 F20/F22)."""

from __future__ import annotations

import json
from typing import cast

import httpx
import pytest
from tests.helpers.json_response import json_str
from vecinita_llm_client import LlmClient
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_tagging.llm_client import LlmTagClient, LlmTagClientError

_VOCABULARY = ["housing", "legal", "benefits", "health"]


def test_infer_document_tags_parses_json_slugs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast(object, json.loads(request.content.decode())))
        assert request.url.path == "/generate"
        assert payload["max_tokens"] == 128
        assert "housing" in json_str(payload, "prompt")
        return httpx.Response(
            200,
            json={"text": '{"tags": ["housing", "legal"]}'},
        )

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    tags = client.infer_document_tags(
        title="Tenant rights",
        text="Information about eviction notice requirements.",
        language="en",
        vocabulary=_VOCABULARY,
    )
    assert tags == ["housing", "legal"]
    client.close()


def test_infer_document_tags_respects_max_tags_cap() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"text": '{"tags": ["housing", "legal", "benefits", "health"]}'},
        )

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    tags = client.infer_document_tags(
        title="Community resources",
        text="Multi-topic community guide.",
        language="en",
        vocabulary=_VOCABULARY,
        max_tags=2,
    )
    assert tags == ["housing", "legal"]
    client.close()


def test_infer_document_tags_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "gpu unavailable"})

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    with pytest.raises(LlmTagClientError, match="503"):
        client.infer_document_tags(
            title="Test",
            text="Body",
            language="en",
            vocabulary=_VOCABULARY,
        )
    client.close()


def test_infer_document_tags_raises_on_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "not-json"})

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    with pytest.raises(LlmTagClientError, match="JSON"):
        client.infer_document_tags(
            title="Test",
            text="Body",
            language="en",
            vocabulary=_VOCABULARY,
        )
    client.close()
