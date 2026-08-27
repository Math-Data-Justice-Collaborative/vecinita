"""Embedding client HTTP contract tests (ADR-008)."""

from __future__ import annotations

import json
from typing import cast

import httpx
import pytest
from vecinita_embedding_client import (
    EMBEDDING_DIMENSION,
    EmbeddingClient,
    EmbeddingClientError,
)
from vecinita_shared_schemas.json_types import (
    as_json_object,
)

_SAMPLE = [0.1] * EMBEDDING_DIMENSION
_EXPECTED_BATCH_COUNT = 2
_RETRY_ATTEMPTS_WITH_MAX_2 = 3
_TRANSIENT_THEN_OK_CALLS = 3
_SUB_BATCH_TOTAL = 5
_DEFAULT_BATCH_SIZE = 32
_TEXTS_ABOVE_DEFAULT_BATCH = 40
_TRANSPORT_RETRY_SUCCESS_CALLS = 2


def _no_sleep(_seconds: float) -> None:
    """No-op sleep for retry backoff in unit tests."""


def test_embed_single_returns_384_dimensions() -> None:
    """Embed returns a vector with the expected dimension for one text."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        assert request.method == "POST"
        assert request.url.path == "/embed"
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        assert payload == {"text": "hello world"}
        return httpx.Response(200, json={"embedding": _SAMPLE})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    vector = client.embed("hello world")
    assert len(vector) == EMBEDDING_DIMENSION
    client.close()


def test_embed_batch_returns_list_of_384_vectors() -> None:
    """Embed batch returns one vector per input text."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        assert request.url.path == "/embed/batch"
        assert payload == {"texts": ["a", "b"]}
        return httpx.Response(200, json={"embeddings": [_SAMPLE, _SAMPLE]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    vectors = client.embed_batch(["a", "b"])
    assert len(vectors) == _EXPECTED_BATCH_COUNT
    assert all(len(v) == EMBEDDING_DIMENSION for v in vectors)
    client.close()


def test_embed_raises_on_wrong_dimension() -> None:
    """Embed raises when the server returns a wrong-dimension vector."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"embedding": [0.1, 0.2]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    with pytest.raises(EmbeddingClientError, match="384"):
        _ = client.embed("x")
    client.close()


def test_embed_raises_on_http_error() -> None:
    """Embed raises when the server responds with an HTTP error status."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(503, json={"detail": "unavailable"})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    with pytest.raises(EmbeddingClientError, match="503"):
        _ = client.embed("x")
    client.close()


def test_embedding_client_requires_base_url_or_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Embedding client raises when neither base URL nor env var is set."""
    monkeypatch.delenv("VECINITA_MODAL_EMBED_URL", raising=False)

    with pytest.raises(EmbeddingClientError, match="VECINITA_MODAL_EMBED_URL"):
        _ = EmbeddingClient(base_url=None)


def test_embedding_client_context_manager_closes_owned_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Context manager closes the HTTP client it created itself."""
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"embedding": _SAMPLE})

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        """Client factory."""
        client = base_client(
            base_url=cast("httpx.URL | str", kwargs.get("base_url", "")),
            timeout=cast("float", kwargs.get("timeout", 30.0)),
            follow_redirects=cast("bool", kwargs.get("follow_redirects", True)),
            transport=httpx.MockTransport(handler),
        )
        original_close = client.close

        def tracked_close() -> None:
            """Tracked close."""
            closed.append(True)
            original_close()

        client.close = tracked_close
        return client

    monkeypatch.setattr(httpx, "Client", client_factory)

    with EmbeddingClient("http://embed.test") as client:
        assert client.embed("hello") == _SAMPLE

    assert closed == [True]


def test_embed_raises_when_embedding_field_missing() -> None:
    """Embed raises when the response is missing the embedding field."""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"unexpected": []}),
    )
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )

    with pytest.raises(EmbeddingClientError, match="embedding"):
        _ = client.embed("x")
    client.close()


def test_embed_batch_raises_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Embed batch raises when retries are exhausted on HTTP 5xx (AC-IR4 / TC-190)."""
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "2")
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "0")
    monkeypatch.setattr("vecinita_embedding_client.client.time.sleep", _no_sleep)
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(502, json={})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )

    with pytest.raises(EmbeddingClientError, match="502"):
        _ = client.embed_batch(["a"])
    assert calls["n"] == _RETRY_ATTEMPTS_WITH_MAX_2  # initial + 2 retries
    client.close()


def test_embed_batch_retries_transient_5xx_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-IR3 / TC-189: sub-batch recovers after transient 5xx."""
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "3")
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "0")
    monkeypatch.setenv("VECINITA_EMBED_BATCH_SIZE", "32")
    monkeypatch.setattr("vecinita_embedding_client.client.time.sleep", _no_sleep)
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < _TRANSIENT_THEN_OK_CALLS:
            return httpx.Response(503, json={"detail": "cold"})
        return httpx.Response(200, json={"embeddings": [_SAMPLE]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    vectors = client.embed_batch(["only"])
    assert len(vectors) == 1
    assert calls["n"] == _TRANSIENT_THEN_OK_CALLS
    client.close()


def test_embed_batch_sub_batches_large_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F48: texts longer than VECINITA_EMBED_BATCH_SIZE split into sub-calls."""
    monkeypatch.setenv("VECINITA_EMBED_BATCH_SIZE", "2")
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "0")
    seen_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        texts_obj = payload["texts"]
        assert isinstance(texts_obj, list)
        texts = cast("list[object]", texts_obj)
        seen_sizes.append(len(texts))
        return httpx.Response(
            200,
            json={"embeddings": [_SAMPLE for _ in texts]},
        )

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    vectors = client.embed_batch(["a", "b", "c", "d", "e"])
    assert len(vectors) == _SUB_BATCH_TOTAL
    assert seen_sizes == [2, 2, 1]
    client.close()


def test_embed_batch_dim_mismatch_does_not_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-IR4: wrong embedding dim hard-fails without retry."""
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "3")
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "0")
    monkeypatch.setattr("vecinita_embedding_client.client.time.sleep", _no_sleep)
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    with pytest.raises(EmbeddingClientError, match="384"):
        _ = client.embed_batch(["a"])
    assert calls["n"] == 1
    client.close()


def test_embed_batch_raises_when_embeddings_field_missing() -> None:
    """Embed batch raises when the response is missing the embeddings field."""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"unexpected": []}),
    )
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )

    with pytest.raises(EmbeddingClientError, match="embeddings"):
        _ = client.embed_batch(["a"])
    client.close()


def test_embed_raises_on_non_numeric_value() -> None:
    """Embed raises when a correctly-sized vector contains a non-numeric value."""
    bad_vector: list[object] = [0.1] * (EMBEDDING_DIMENSION - 1)
    bad_vector.append("not-a-number")
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"embedding": bad_vector}),
    )
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )

    with pytest.raises(EmbeddingClientError, match="numeric"):
        _ = client.embed("x")
    client.close()


def test_embedding_client_does_not_close_injected_http_client() -> None:
    """Closing the client must not close an externally injected HTTP client."""
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"embedding": _SAMPLE})

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, base_url="http://embed.test")
    original_close = http.close

    def tracked_close() -> None:
        """Tracked close."""
        closed.append(True)
        original_close()

    http.close = tracked_close
    client = EmbeddingClient("http://embed.test", http_client=http)
    client.close()

    assert closed == []


def test_embed_batch_empty_returns_empty_list() -> None:
    """Empty input short-circuits without calling the embed service."""
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"embeddings": []})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    assert client.embed_batch([]) == []
    assert calls["n"] == 0
    client.close()


def test_env_batch_size_invalid_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-integer VECINITA_EMBED_BATCH_SIZE uses the default (32)."""
    monkeypatch.setenv("VECINITA_EMBED_BATCH_SIZE", "not-an-int")
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "0")
    seen_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        texts_obj = payload["texts"]
        assert isinstance(texts_obj, list)
        seen_sizes.append(len(cast("list[object]", texts_obj)))
        return httpx.Response(
            200,
            json={"embeddings": [_SAMPLE for _ in cast("list[object]", texts_obj)]},
        )

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    texts = [f"t{i}" for i in range(_TEXTS_ABOVE_DEFAULT_BATCH)]
    assert len(client.embed_batch(texts)) == _TEXTS_ABOVE_DEFAULT_BATCH
    assert seen_sizes == [_DEFAULT_BATCH_SIZE, 8]
    client.close()


def test_env_retry_backoff_invalid_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-float VECINITA_EMBED_RETRY_BACKOFF_S uses the default without crashing."""
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "bad-float")
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "1")
    sleeps: list[float] = []

    def capture_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("vecinita_embedding_client.client.time.sleep", capture_sleep)
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={})
        return httpx.Response(200, json={"embeddings": [_SAMPLE]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    assert len(client.embed_batch(["a"])) == 1
    assert sleeps == [0.5]
    client.close()


def test_embed_batch_retries_transport_error_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Transport errors retry with backoff then succeed (F48)."""
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "2")
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "0")
    monkeypatch.setattr("vecinita_embedding_client.client.time.sleep", _no_sleep)
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            msg = "connection refused"
            raise httpx.ConnectError(msg)
        return httpx.Response(200, json={"embeddings": [_SAMPLE]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    assert len(client.embed_batch(["a"])) == 1
    assert calls["n"] == _TRANSPORT_RETRY_SUCCESS_CALLS
    client.close()


def test_embed_batch_transport_error_exhausts_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exhausted transport retries raise EmbeddingClientError."""
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "1")
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "0")
    monkeypatch.setattr("vecinita_embedding_client.client.time.sleep", _no_sleep)

    def handler(_request: httpx.Request) -> httpx.Response:
        msg = "timed out"
        raise httpx.ReadTimeout(msg)

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    with pytest.raises(EmbeddingClientError, match="transport error"):
        _ = client.embed_batch(["a"])
    client.close()
