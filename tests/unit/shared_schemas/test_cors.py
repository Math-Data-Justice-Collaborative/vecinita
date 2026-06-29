"""Unit tests for vecinita_shared_schemas.cors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from vecinita_shared_schemas.cors import configure_cors, parse_cors_origins

if TYPE_CHECKING:
    import pytest


def test_parse_cors_origins_splits_and_trims() -> None:
    assert parse_cors_origins("https://a.test, https://b.test ,") == [
        "https://a.test",
        "https://b.test",
    ]


def test_parse_cors_origins_reads_env_when_value_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VECINITA_CORS_ORIGINS", "https://env.test")

    assert parse_cors_origins() == ["https://env.test"]


def test_configure_cors_returns_empty_when_no_origins() -> None:
    app = FastAPI()

    assert configure_cors(app, env_value="") == []


def test_configure_cors_adds_middleware_and_extra_headers() -> None:
    app = FastAPI()

    origins = configure_cors(
        app,
        env_value="https://frontend.test",
        extra_allow_headers=["X-Custom"],
    )

    assert origins == ["https://frontend.test"]
    assert app.user_middleware
