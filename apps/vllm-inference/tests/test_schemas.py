"""Unit tests for Pydantic request/response schemas."""

import pytest
from pydantic import ValidationError

from vecinita.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Message,
    StreamChunk,
)
from vecinita.config import settings

# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------


class TestMessage:
    def test_valid_roles(self):
        for role in ("user", "assistant", "system"):
            msg = Message(role=role, content="hello")
            assert msg.role == role

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            Message(role="bot", content="hello")

    def test_content_required(self):
        with pytest.raises(ValidationError):
            Message(role="user")


# ---------------------------------------------------------------------------
# ChatRequest
# ---------------------------------------------------------------------------


class TestChatRequest:
    def test_defaults(self):
        req = ChatRequest(messages=[Message(role="user", content="hi")])
        assert req.model == settings.default_model
        assert req.temperature == 0.7
        assert req.max_tokens is None

    def test_custom_values(self):
        req = ChatRequest(
            model="mistral",
            messages=[Message(role="user", content="hi")],
            temperature=0.1,
            max_tokens=256,
        )
        assert req.model == "mistral"
        assert req.temperature == 0.1
        assert req.max_tokens == 256

    def test_empty_messages_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(messages=[])

    def test_temperature_bounds(self):
        with pytest.raises(ValidationError):
            ChatRequest(
                messages=[Message(role="user", content="hi")],
                temperature=3.0,
            )
        with pytest.raises(ValidationError):
            ChatRequest(
                messages=[Message(role="user", content="hi")],
                temperature=-0.1,
            )

    def test_max_tokens_must_be_positive(self):
        with pytest.raises(ValidationError):
            ChatRequest(
                messages=[Message(role="user", content="hi")],
                max_tokens=0,
            )


# ---------------------------------------------------------------------------
# ChatResponse
# ---------------------------------------------------------------------------


class TestChatResponse:
    def test_done_default(self):
        resp = ChatResponse(
            model="llama3.2",
            message=Message(role="assistant", content="Hello!"),
        )
        assert resp.done is True

    def test_serialisation_round_trip(self):
        resp = ChatResponse(
            model="phi3",
            message=Message(role="assistant", content="Hi"),
        )
        assert ChatResponse.model_validate(resp.model_dump()) == resp


# ---------------------------------------------------------------------------
# HealthResponse
# ---------------------------------------------------------------------------


class TestHealthResponse:
    def test_ok_status(self):
        h = HealthResponse(status="ok", models=["llama3.2"])
        assert h.status == "ok"
        assert "llama3.2" in h.models

    def test_error_status(self):
        h = HealthResponse(status="error")
        assert h.status == "error"
        assert h.models == []

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            HealthResponse(status="unknown")


# ---------------------------------------------------------------------------
# StreamChunk
# ---------------------------------------------------------------------------


class TestStreamChunk:
    def test_fields(self):
        chunk = StreamChunk(model="mistral", content="token", done=False)
        assert chunk.model == "mistral"
        assert chunk.content == "token"
        assert chunk.done is False

    def test_json_serialisable(self):
        chunk = StreamChunk(model="mistral", content="hi", done=True)
        data = chunk.model_dump_json()
        assert '"done":true' in data
