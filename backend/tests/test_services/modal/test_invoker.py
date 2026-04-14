"""Tests for Modal Function.from_name invocation helpers."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def clear_lookup_cache():
    from src.services.modal import invoker

    invoker._lookup_function.cache_clear()
    yield
    invoker._lookup_function.cache_clear()


def test_modal_function_invocation_unset_off_even_with_tokens(monkeypatch):
    from src.services.modal.invoker import modal_function_invocation_enabled

    monkeypatch.delenv("MODAL_FUNCTION_INVOCATION", raising=False)
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    assert modal_function_invocation_enabled() is False


def test_modal_function_invocation_auto_off_without_tokens(monkeypatch):
    from src.services.modal.invoker import modal_function_invocation_enabled

    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "auto")
    for key in (
        "MODAL_TOKEN_ID",
        "MODAL_TOKEN_SECRET",
        "MODAL_API_TOKEN_ID",
        "MODAL_API_TOKEN_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    assert modal_function_invocation_enabled() is False


def test_modal_function_invocation_auto_on_with_canonical_tokens(monkeypatch):
    from src.services.modal.invoker import modal_function_invocation_enabled

    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "auto")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.delenv("MODAL_API_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_API_TOKEN_SECRET", raising=False)
    assert modal_function_invocation_enabled() is True


def test_modal_function_invocation_auto_on_with_legacy_api_tokens(monkeypatch):
    from src.services.modal.invoker import modal_function_invocation_enabled

    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "auto")
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    monkeypatch.setenv("MODAL_API_TOKEN_ID", "ak-legacy")
    monkeypatch.setenv("MODAL_API_TOKEN_SECRET", "as-legacy")
    assert modal_function_invocation_enabled() is True


def test_modal_function_invocation_explicit_http_disables_despite_tokens(monkeypatch):
    from src.services.modal.invoker import modal_function_invocation_enabled

    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "http")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    assert modal_function_invocation_enabled() is False


def test_modal_function_invocation_explicit_auto_uses_token_gate(monkeypatch):
    from src.services.modal.invoker import modal_function_invocation_enabled

    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "auto")
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    monkeypatch.delenv("MODAL_API_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_API_TOKEN_SECRET", raising=False)
    assert modal_function_invocation_enabled() is False


def test_modal_function_invocation_explicit_true_without_tokens(monkeypatch):
    from src.services.modal.invoker import modal_function_invocation_enabled

    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    assert modal_function_invocation_enabled() is True


def test_invoke_modal_scraper_reindex_uses_spawn_and_get(monkeypatch):
    from src.services.modal import invoker

    class _Call:
        def get(self, timeout=None):
            assert timeout == 45.0
            return {"status": "accepted", "mode": "spawn"}

    class _Fn:
        def spawn(self, *, clean, stream, verbose):
            assert clean is True and stream is False and verbose is True
            return _Call()

    monkeypatch.setenv("MODAL_SCRAPER_APP_NAME", "app-scraper")
    monkeypatch.setenv("MODAL_SCRAPER_REINDEX_FUNCTION", "trigger_reindex")
    monkeypatch.setenv("MODAL_SCRAPER_REINDEX_FUNCTION_TIMEOUT", "45")

    monkeypatch.setattr(invoker, "_lookup_function", lambda *a, **k: _Fn())
    out = invoker.invoke_modal_scraper_reindex(True, False, True)
    assert out == {"status": "accepted", "mode": "spawn"}
