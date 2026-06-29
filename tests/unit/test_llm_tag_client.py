"""LLM tag client HTTP contract tests (ADR-015 TP-014, EV-001 F20/F22)."""

from __future__ import annotations

import json
from typing import cast

import httpx
import pytest
from vecinita_llm_client import LlmClient
from vecinita_shared_schemas.json_types import (
    as_json_object,
)
from vecinita_tagging.llm_client import LlmTagClient, LlmTagClientError

from tests.helpers.json_response import (
    json_str,
)

_VOCABULARY = ["housing", "legal", "benefits", "health"]
_DEFAULT_TAG_MAX_TOKENS = 128


def test_infer_document_tags_parses_json_slugs() -> None:
    """Document tag inference parses JSON tag slugs from the LLM response."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        assert request.url.path == "/generate"
        assert payload["max_tokens"] == _DEFAULT_TAG_MAX_TOKENS
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
    """Document tag inference truncates results to the max_tags cap."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
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
    """Document tag inference raises on an HTTP error response."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
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
    """Document tag inference raises when the response text is not JSON."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
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


def test_infer_document_tags_parses_json_inside_markdown_fence() -> None:
    """Document tag inference parses JSON wrapped in a markdown code fence."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(
            200,
            json={"text": '```json\n{"tags": ["housing"]}\n```'},
        )

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    tags = client.infer_document_tags(
        title="Test",
        text="Body",
        language="en",
        vocabulary=_VOCABULARY,
    )
    assert tags == ["housing"]
    client.close()


def test_infer_document_tags_raises_when_tags_not_string_array() -> None:
    """Document tag inference raises when tags are not a string array."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"text": '{"tags": [1, 2]}'})

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    with pytest.raises(LlmTagClientError, match="string array"):
        client.infer_document_tags(
            title="Test",
            text="Body",
            language="en",
            vocabulary=_VOCABULARY,
        )
    client.close()


def test_infer_document_tags_raises_when_tags_field_not_a_list() -> None:
    """Document tag inference raises when the 'tags' field is not a list at all."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"text": '{"tags": "housing"}'})

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    with pytest.raises(LlmTagClientError, match="string array"):
        client.infer_document_tags(
            title="Test",
            text="Body",
            language="en",
            vocabulary=_VOCABULARY,
        )
    client.close()


def test_infer_document_tags_rejects_max_tags_below_one() -> None:
    """Document tag inference rejects a max_tags value below one."""
    transport = httpx.MockTransport(lambda _request: httpx.Response(500))
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm)
    with pytest.raises(LlmTagClientError, match="max_tags"):
        client.infer_document_tags(
            title="Test",
            text="Body",
            language="en",
            vocabulary=_VOCABULARY,
            max_tags=0,
        )
    client.close()


def test_infer_query_tags_delegates_to_document_inference() -> None:
    """Query tag inference reuses document inference with the question prompt."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        assert "Where can I get food?" in json_str(payload, "prompt")
        return httpx.Response(200, json={"text": '{"tags": ["benefits"]}'})

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm, tag_max_tokens=64)
    tags = client.infer_query_tags(
        question="Where can I get food?",
        vocabulary=_VOCABULARY,
    )
    assert tags == ["benefits"]
    client.close()


def test_llm_tag_client_uses_explicit_tag_max_tokens() -> None:
    """Tag client forwards the explicitly configured tag_max_tokens value."""
    seen_max_tokens: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        seen_max_tokens.append(int(json_str(payload, "max_tokens")))
        return httpx.Response(200, json={"text": '{"tags": ["housing"]}'})

    transport = httpx.MockTransport(handler)
    llm = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client = LlmTagClient(llm, tag_max_tokens=256)
    client.infer_document_tags(
        title="Test",
        text="Body",
        language="en",
        vocabulary=_VOCABULARY,
    )
    assert seen_max_tokens == [256]
    client.close()
