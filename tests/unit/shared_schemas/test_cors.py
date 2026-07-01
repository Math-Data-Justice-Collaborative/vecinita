"""Unit tests for vecinita_shared_schemas.cors."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.testclient import TestClient
from vecinita_shared_schemas.cors import (
    configure_cors,
    parse_cors_origins,
)

if TYPE_CHECKING:
    import pytest

ADMIN_ORIGIN = "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app"


def test_parse_cors_origins_splits_and_trims() -> None:
    """Test parse cors origins splits and trims."""
    assert parse_cors_origins("https://a.test, https://b.test ,") == [
        "https://a.test",
        "https://b.test",
    ]


def test_parse_cors_origins_reads_env_when_value_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test parse cors origins reads env when value not provided."""
    monkeypatch.setenv("VECINITA_CORS_ORIGINS", "https://env.test")

    assert parse_cors_origins() == ["https://env.test"]


def test_configure_cors_returns_empty_when_no_origins() -> None:
    """Test configure cors returns empty when no origins."""
    app = FastAPI()

    assert configure_cors(app, env_value="") == []


def test_configure_cors_adds_middleware_and_extra_headers() -> None:
    """Test configure cors adds middleware and extra headers."""
    app = FastAPI()

    origins = configure_cors(
        app,
        env_value="https://frontend.test",
        extra_allow_headers=["X-Custom"],
    )

    assert origins == ["https://frontend.test"]
    assert app.user_middleware


def test_unhandled_exception_includes_cors_headers() -> None:
    """500 responses include Access-Control-Allow-Origin so browsers surface HTTP errors."""
    app = FastAPI()
    configure_cors(app, env_value=ADMIN_ORIGIN)

    @app.get("/boom")
    def boom() -> None:  # pyright: ignore[reportUnusedFunction]
        msg = "simulated failure"
        raise RuntimeError(msg)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/boom", headers={"Origin": ADMIN_ORIGIN})
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
