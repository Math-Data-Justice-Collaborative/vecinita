"""Unit tests for playground LLM list / ensure-ready helpers (eval-golden-sweep)."""

from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
from vecinita_eval.playground_setup import (
    PlaygroundSetupError,
    assert_no_legacy_ollama_url,
    ensure_model_ready,
    format_model_listing,
    make_playground_client,
    model_is_available,
    resolve_playground_base_url,
)
from vecinita_llm_client import LlmClient
from vecinita_shared_schemas.playground_models import (
    PlaygroundModelListResponse,
    PlaygroundModelSummary,
)

pytestmark = pytest.mark.unit


def test_assert_no_legacy_ollama_url_raises_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy Ollama URL must be unset (ADR-037)."""
    monkeypatch.setenv("VECINITA_MODAL_OLLAMA_URL", "http://legacy")
    with pytest.raises(PlaygroundSetupError, match="VECINITA_MODAL_OLLAMA_URL"):
        assert_no_legacy_ollama_url()


def test_resolve_playground_base_url_prefers_playground_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Playground URL wins over prod LLM URL for list/pull setup."""
    monkeypatch.setenv(
        "VECINITA_MODAL_LLM_PLAYGROUND_URL",
        "https://playground.example/",
    )
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "https://prod.example/")
    assert resolve_playground_base_url() == "https://playground.example"


def test_resolve_playground_base_url_falls_back_to_llm_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When playground URL is unset, fall back to prod LLM URL."""
    monkeypatch.delenv("VECINITA_MODAL_LLM_PLAYGROUND_URL", raising=False)
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "https://prod.example/")
    assert resolve_playground_base_url() == "https://prod.example"


def test_resolve_playground_base_url_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing base URL raises a clear setup error."""
    monkeypatch.delenv("VECINITA_MODAL_LLM_PLAYGROUND_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)
    with pytest.raises(PlaygroundSetupError, match="VECINITA_MODAL_LLM"):
        _ = resolve_playground_base_url()


def test_model_is_available_matches_id() -> None:
    """Availability lookup is by exact model_id."""
    listing = PlaygroundModelListResponse(
        items=[
            PlaygroundModelSummary(model_id="qwen2.5:1.5b-instruct", available=True),
            PlaygroundModelSummary(model_id="qwen3:8b", available=False),
        ]
    )
    assert model_is_available(listing, "qwen2.5:1.5b-instruct") is True
    assert model_is_available(listing, "qwen3:8b") is False
    assert model_is_available(listing, "missing:tag") is False


def test_format_model_listing_json_lines() -> None:
    """Listing formatter emits stable model_id + available rows."""
    listing = PlaygroundModelListResponse(
        items=[
            PlaygroundModelSummary(model_id="b:1", available=False),
            PlaygroundModelSummary(model_id="a:1", available=True),
        ]
    )
    text = format_model_listing(listing)
    assert "a:1\tavailable=true" in text
    assert "b:1\tavailable=false" in text


def test_ensure_model_ready_skips_pull_when_available() -> None:
    """Already-available models warm without calling pull."""
    calls: list[str] = []
    job_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.path == "/models/ollama":
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"model_id": "qwen3:8b", "available": True},
                    ]
                },
            )
        if request.url.path == "/warm":
            return httpx.Response(200, json={"status": "ok", "model_id": "qwen3:8b"})
        if request.url.path == "/models/ollama/pull":
            return httpx.Response(
                200,
                json={
                    "job_id": str(job_id),
                    "model_id": "qwen3:8b",
                    "status": "pulling",
                },
            )
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://playground.test",
        model_id="qwen3:8b",
        proxy_key="proxy",
        http_client=httpx.Client(
            transport=transport,
            base_url="http://playground.test",
        ),
    )
    result = ensure_model_ready(client, "qwen3:8b", warm=True)
    assert result.was_available is True
    assert result.pulled is False
    assert result.warmed is True
    assert result.available is True
    assert any(c.startswith("POST /warm") for c in calls)
    assert not any("pull" in c for c in calls)
    client.close()


def test_ensure_model_ready_pulls_and_waits_until_available() -> None:
    """Missing models enqueue pull and poll list until available."""
    list_hits = {"n": 0}
    ready_after_lists = 3  # initial + one pending poll + available
    job_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/models/ollama":
            list_hits["n"] += 1
            # 1: initial check; 2: first wait poll (still pulling); 3+: available
            available = list_hits["n"] >= ready_after_lists
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"model_id": "mistral:7b", "available": available},
                    ]
                },
            )
        if request.url.path == "/models/ollama/pull":
            return httpx.Response(
                200,
                json={
                    "job_id": str(job_id),
                    "model_id": "mistral:7b",
                    "status": "pulling",
                },
            )
        if request.url.path == "/warm":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(404, json={"detail": "not found"})

    sleeps: list[float] = []
    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://playground.test",
        model_id="mistral:7b",
        proxy_key="proxy",
        http_client=httpx.Client(
            transport=transport,
            base_url="http://playground.test",
        ),
    )
    result = ensure_model_ready(
        client,
        "mistral:7b",
        pull_if_missing=True,
        wait=True,
        warm=True,
        poll_interval_s=0.01,
        timeout_s=5.0,
        sleep=sleeps.append,
    )
    assert result.was_available is False
    assert result.pulled is True
    assert result.job_id == str(job_id)
    assert result.available is True
    assert result.warmed is True
    assert sleeps == [0.01]
    client.close()


def test_ensure_model_ready_raises_when_missing_and_pull_disabled() -> None:
    """Without --pull, missing models fail fast."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/models/ollama":
            return httpx.Response(200, json={"items": []})
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://playground.test",
        http_client=httpx.Client(
            transport=transport,
            base_url="http://playground.test",
        ),
    )
    with pytest.raises(PlaygroundSetupError, match="not available"):
        _ = ensure_model_ready(client, "missing:tag", pull_if_missing=False, warm=False)
    client.close()


def test_make_playground_client_uses_resolved_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Factory wires resolved playground URL + model_id for list/pull/warm."""
    monkeypatch.setenv("VECINITA_MODAL_LLM_PLAYGROUND_URL", "http://pg.test")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "secret")
    client = make_playground_client(model_id="qwen3:8b")
    assert client.default_model_id == "qwen3:8b"
    assert resolve_playground_base_url() == "http://pg.test"
    client.close()
