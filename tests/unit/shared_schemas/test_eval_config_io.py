"""Unit tests for eval config JSON column parsing."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from vecinita_shared_schemas.db_mapping import row_datetime_optional
from vecinita_shared_schemas.eval_config import EvalConfig, eval_config_from_json

_PRESET_TOP_K = 12


def test_eval_config_from_json_parses_string_dict_and_defaults() -> None:
    """eval_config_from_json accepts JSON text, dict payloads, and falls back to defaults."""
    parsed = EvalConfig(top_k=_PRESET_TOP_K)
    assert eval_config_from_json(parsed.model_dump_json()).top_k == _PRESET_TOP_K
    assert eval_config_from_json(parsed.model_dump()).top_k == _PRESET_TOP_K
    assert eval_config_from_json(None).top_k == EvalConfig().top_k


def test_row_datetime_optional_reexported_via_db_mapping() -> None:
    """Datetime row helpers live in db_mapping for shared use."""
    assert row_datetime_optional({"promoted_at": None}, "promoted_at") is None
    promoted_at = datetime.now(UTC)
    assert row_datetime_optional({"promoted_at": promoted_at}, "promoted_at") == promoted_at
    with pytest.raises(TypeError, match="Expected datetime"):
        row_datetime_optional({"promoted_at": "not-a-datetime"}, "promoted_at")
