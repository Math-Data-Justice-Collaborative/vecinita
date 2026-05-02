"""Consumer Pact: gateway → embedding microservice over HTTP when Modal RPC is off.

``LOCAL_EMBEDDING_SERVICE_URL`` points at the mock provider; interaction mirrors
:meth:`src.api.router_embed._post_single_embedding` / batch first-attempt payloads.

Writes ``backend/pacts/vecinita-gateway-vecinita-embedding-http.json`` (gitignored).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pact import Pact

pytestmark = [pytest.mark.integration, pytest.mark.contract]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _pact_output_dir() -> Path:
    return _repo_root() / "backend" / "pacts"


def _embed_http_fallback_client(mock_base: str, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.setenv("LOCAL_EMBEDDING_SERVICE_URL", mock_base)

    from src.api.router_embed import router as embed_router

    app = FastAPI()
    app.include_router(embed_router, prefix="/api/v1")
    return TestClient(app)


def test_gateway_writes_embedding_http_consumer_pact(monkeypatch: pytest.MonkeyPatch) -> None:
    pact = Pact("vecinita-gateway", "vecinita-embedding-http").with_specification("V4")

    (
        pact.upon_receiving("single embed via HTTP when Modal function RPC is disabled")
        .with_request("POST", "/embed")
        .with_body({"query": "hello via http"}, content_type="application/json", part="Request")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json", part="Response")
        .with_body(
            {
                "embedding": [0.1, 0.2, 0.3, 0.4],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 4,
            },
            content_type="application/json",
            part="Response",
        )
    )

    (
        pact.upon_receiving("batch embed via HTTP when Modal function RPC is disabled")
        .with_request("POST", "/embed/batch")
        .with_body({"queries": ["a", "b"]}, content_type="application/json", part="Request")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json", part="Response")
        .with_body(
            {
                "embeddings": [[0.0, 1.0], [1.0, 0.0]],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 2,
            },
            content_type="application/json",
            part="Response",
        )
    )

    with pact.serve(raises=True, verbose=False) as mock_upstream:
        with _embed_http_fallback_client(mock_upstream.url, monkeypatch) as gateway_client:
            single = gateway_client.post("/api/v1/embed", json={"text": "hello via http"})
            assert single.status_code == 200
            payload = single.json()
            assert payload["dimension"] == 4
            assert len(payload["embedding"]) == 4

            batch = gateway_client.post("/api/v1/embed/batch", json={"texts": ["a", "b"]})
            assert batch.status_code == 200
            b_json = batch.json()
            assert b_json["dimension"] == 2
            assert len(b_json["embeddings"]) == 2

    pact.write_file(_pact_output_dir(), overwrite=True)
