"""UJ-027 / TC-080: public sign-up disabled — invite-only registration."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast

import pytest

pytestmark = pytest.mark.e2e

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "supabase" / "config.toml"


def test_supabase_config_disables_public_signup() -> None:
    """Canonical Supabase project config rejects self-registration (TP-S004-07)."""
    with _CONFIG_PATH.open("rb") as handle:
        config = tomllib.load(handle)

    auth = cast("dict[str, object]", config["auth"])
    email = cast("dict[str, object]", auth["email"])
    sms = cast("dict[str, object]", auth["sms"])
    assert auth["enable_signup"] is False
    assert auth["enable_anonymous_sign_ins"] is False
    # Email provider must stay on so invited operators can sign in (signup gated by [auth]).
    assert email["enable_signup"] is True
    assert sms["enable_signup"] is False
