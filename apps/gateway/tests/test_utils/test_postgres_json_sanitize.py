"""Tests for ``src.utils.postgres_json_sanitize``."""

from __future__ import annotations

from collections import UserDict

from src.utils.postgres_json_sanitize import sanitize_postgres_json_payload, sanitize_postgres_text


def test_sanitize_postgres_text_strips_nul() -> None:
    assert sanitize_postgres_text("a\u0000b") == "ab"
    assert sanitize_postgres_text("ok") == "ok"


def test_sanitize_postgres_json_payload_nested_strings_and_keys() -> None:
    raw = {"a\u0000b": {"x\u0000": ["y\u0000z", 1, None]}, "n": 2}
    out = sanitize_postgres_json_payload(raw)
    assert out == {"ab": {"x": ["yz", 1, None]}, "n": 2}


def test_sanitize_postgres_json_payload_tuple() -> None:
    assert sanitize_postgres_json_payload(("a\u0000",)) == ("a",)


def test_sanitize_postgres_json_payload_userdict() -> None:
    raw = UserDict({"k\u0000": ["v\u0000"]})
    out = sanitize_postgres_json_payload(raw)
    assert out == {"k": ["v"]}
