"""Unit tests for production RAG config promote service (ADR-035 §10)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from vecinita_internal_write_api.rag_production_config_service import (
    RagConfigPromoteNotFoundError,
    _config_from_json,  # pyright: ignore[reportPrivateUsage]
    _resolve_promote_config,  # pyright: ignore[reportPrivateUsage]
    _row_datetime_optional,  # pyright: ignore[reportPrivateUsage]
    _row_uuid_optional,  # pyright: ignore[reportPrivateUsage]
    get_active_rag_config,
    promote_rag_config,
)
from vecinita_shared_schemas.eval_config import (
    EvalConfig,
    RagConfigPromoteRequest,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.unit

# eval_runs.corpus_profile is varchar(16) — keep fixture values within that limit.
_UNIT_PROMOTE_CORPUS = "unit-promote"

_PROMOTED_TOP_K = 8
_PRESET_TOP_K = 6
_RUN_TOP_K = 7
_SECOND_CONFIG_VERSION = 2


@pytest.fixture
def clean_rag_tables(engine: Engine) -> Iterator[None]:
    """Clear production config, presets, and eval runs touched by promote tests."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rag_production_config"))
        conn.execute(text("DELETE FROM audit_log WHERE event_type = 'rag.config.promoted'"))
        conn.execute(
            text("DELETE FROM eval_config_presets WHERE preset_name LIKE 'unit-promote-%'")
        )
        conn.execute(
            text("DELETE FROM eval_runs WHERE corpus_profile = :corpus"),
            {"corpus": _UNIT_PROMOTE_CORPUS},
        )
    yield
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rag_production_config"))
        conn.execute(text("DELETE FROM audit_log WHERE event_type = 'rag.config.promoted'"))
        conn.execute(
            text("DELETE FROM eval_config_presets WHERE preset_name LIKE 'unit-promote-%'")
        )
        conn.execute(
            text("DELETE FROM eval_runs WHERE corpus_profile = :corpus"),
            {"corpus": _UNIT_PROMOTE_CORPUS},
        )


def _sample_config(*, top_k: int) -> dict[str, object]:
    return EvalConfig(
        top_k=top_k,
        min_retrieval_score=0.3,
        system_prompt=f"Prompt top_k={top_k}",
        max_tokens=128,
        temperature=0.2,
        model_id="qwen2.5:1.5b-instruct",
    ).model_dump(mode="json")


def _insert_preset(engine: Engine, *, owner_id: UUID, top_k: int) -> UUID:
    preset_id = uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_config_presets (
                    id, preset_name, config, shared, owner_id, version
                )
                VALUES (
                    :id, :name, CAST(:config AS jsonb), false, :owner_id, 1
                )
                """
            ),
            {
                "id": preset_id,
                "name": f"unit-promote-{preset_id.hex[:8]}",
                "config": json.dumps(_sample_config(top_k=top_k)),
                "owner_id": owner_id,
            },
        )
    return preset_id


def _insert_eval_run(engine: Engine, *, top_k: int) -> UUID:
    run_id = uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_runs (
                    id, status, corpus_profile, mode, config_snapshot
                )
                VALUES (
                    :id, 'completed', :corpus, 'golden',
                    CAST(:config AS jsonb)
                )
                """
            ),
            {
                "id": run_id,
                "corpus": _UNIT_PROMOTE_CORPUS,
                "config": json.dumps(_sample_config(top_k=top_k)),
            },
        )
    return run_id


def test_get_active_rag_config_returns_none_when_empty(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """No active row yields None."""
    _ = clean_rag_tables
    assert get_active_rag_config(engine) is None


def test_promote_from_preset_activates_config_and_increments_version(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """Promoting a preset inserts an active row with audit metadata."""
    _ = clean_rag_tables
    owner_id = uuid4()
    promoter_id = uuid4()
    preset_id = _insert_preset(engine, owner_id=owner_id, top_k=_PRESET_TOP_K)
    response = promote_rag_config(
        engine,
        promoted_by=promoter_id,
        body=RagConfigPromoteRequest(source="preset", preset_id=preset_id),
    )
    assert response.config_version == 1
    assert response.promoted_by == promoter_id
    assert isinstance(response.promoted_at, datetime)

    active = get_active_rag_config(engine)
    assert active is not None
    assert active.config.top_k == _PRESET_TOP_K
    assert active.config_version == 1
    assert active.promoted_by == promoter_id


def test_promote_from_run_uses_config_snapshot(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """Promoting an eval run copies its config_snapshot."""
    _ = clean_rag_tables
    run_id = _insert_eval_run(engine, top_k=_RUN_TOP_K)
    response = promote_rag_config(
        engine,
        promoted_by=uuid4(),
        body=RagConfigPromoteRequest(source="run", run_id=run_id),
    )
    assert response.config_version == 1
    active = get_active_rag_config(engine)
    assert active is not None
    assert active.config.top_k == _RUN_TOP_K


def test_promote_second_time_increments_config_version(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """Second promote deactivates prior row and bumps version."""
    _ = clean_rag_tables
    owner_id = uuid4()
    first_preset = _insert_preset(engine, owner_id=owner_id, top_k=_PRESET_TOP_K)
    second_preset = _insert_preset(engine, owner_id=owner_id, top_k=_PROMOTED_TOP_K)
    promote_rag_config(
        engine,
        promoted_by=uuid4(),
        body=RagConfigPromoteRequest(source="preset", preset_id=first_preset),
    )
    second = promote_rag_config(
        engine,
        promoted_by=uuid4(),
        body=RagConfigPromoteRequest(source="preset", preset_id=second_preset),
    )
    assert second.config_version == _SECOND_CONFIG_VERSION
    active = get_active_rag_config(engine)
    assert active is not None
    assert active.config.top_k == _PROMOTED_TOP_K
    assert active.config_version == _SECOND_CONFIG_VERSION


def test_promote_preset_not_found_raises(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """Unknown preset id raises RagConfigPromoteNotFoundError."""
    _ = clean_rag_tables
    with pytest.raises(RagConfigPromoteNotFoundError, match="preset not found"):
        promote_rag_config(
            engine,
            promoted_by=uuid4(),
            body=RagConfigPromoteRequest(source="preset", preset_id=uuid4()),
        )


def test_promote_run_not_found_raises(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """Unknown run id raises RagConfigPromoteNotFoundError."""
    _ = clean_rag_tables
    with pytest.raises(RagConfigPromoteNotFoundError, match="run not found"):
        promote_rag_config(
            engine,
            promoted_by=uuid4(),
            body=RagConfigPromoteRequest(source="run", run_id=uuid4()),
        )


def test_get_active_rag_config_parses_promoted_at_timestamp(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """Active row maps promoted_at from the database."""
    _ = clean_rag_tables
    preset_id = _insert_preset(engine, owner_id=uuid4(), top_k=_PRESET_TOP_K)
    promote_rag_config(
        engine,
        promoted_by=uuid4(),
        body=RagConfigPromoteRequest(source="preset", preset_id=preset_id),
        request_id=uuid4(),
    )
    active = get_active_rag_config(engine)
    assert active is not None
    assert active.promoted_at is not None
    assert active.promoted_at.tzinfo is not None


def test_config_from_json_parses_string_dict_and_defaults() -> None:
    """_config_from_json accepts JSON text, dict payloads, and falls back to defaults."""
    sample = _sample_config(top_k=_PRESET_TOP_K)
    parsed = EvalConfig.model_validate(sample)
    assert _config_from_json(parsed.model_dump_json()).top_k == _PRESET_TOP_K
    assert _config_from_json(parsed.model_dump()).top_k == _PRESET_TOP_K
    assert _config_from_json(None).top_k == EvalConfig().top_k


def test_row_datetime_optional_handles_none_datetime_and_invalid() -> None:
    """Row datetime helper returns None, datetime values, or raises on bad types."""
    assert _row_datetime_optional({"promoted_at": None}, "promoted_at") is None
    promoted_at = datetime.now(UTC)
    assert _row_datetime_optional({"promoted_at": promoted_at}, "promoted_at") == promoted_at
    with pytest.raises(TypeError, match="Expected datetime"):
        _row_datetime_optional({"promoted_at": "not-a-datetime"}, "promoted_at")


def test_row_uuid_optional_handles_none_and_uuid() -> None:
    """Row UUID helper returns None or parses UUID columns."""
    assert _row_uuid_optional({"promoted_by": None}, "promoted_by") is None
    owner_id = uuid4()
    assert _row_uuid_optional({"promoted_by": owner_id}, "promoted_by") == owner_id


def test_resolve_promote_config_requires_source_ids(
    engine: Engine,
    clean_rag_tables: None,
) -> None:
    """Service-level guard rejects promote requests missing preset_id or run_id."""
    _ = clean_rag_tables
    with pytest.raises(ValueError, match="preset_id is required"):
        _resolve_promote_config(
            engine,
            body=RagConfigPromoteRequest.model_construct(source="preset", preset_id=None),
        )
    with pytest.raises(ValueError, match="run_id is required"):
        _resolve_promote_config(
            engine,
            body=RagConfigPromoteRequest.model_construct(source="run", run_id=None),
        )
