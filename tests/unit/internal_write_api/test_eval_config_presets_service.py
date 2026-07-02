"""Unit tests for eval config preset CRUD service (ADR-035 §7)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from sqlalchemy import text
from vecinita_internal_write_api.eval_config_presets_service import (
    EvalConfigPresetAccessError,
    _preset_from_row,  # pyright: ignore[reportPrivateUsage]
    clone_eval_config_preset,
    create_eval_config_preset,
    get_eval_config_preset,
    list_eval_config_presets,
    update_eval_config_preset,
)
from vecinita_shared_schemas.eval_config import (
    EvalConfig,
    EvalConfigPresetCreateRequest,
    EvalConfigPresetUpdateRequest,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

_CUSTOM_TOP_K = 9
_EXPECTED_VERSION_AFTER_PATCH = 2


@pytest.fixture
def preset_owner_id() -> object:
    """Stable owner id for preset tests."""
    return uuid4()


@pytest.fixture
def created_preset_id(
    engine: Engine,
    preset_owner_id: object,
) -> Iterator[object]:
    """Create one private preset and delete it after the test."""
    created = create_eval_config_preset(
        engine,
        owner_id=preset_owner_id,  # type: ignore[arg-type]
        body=EvalConfigPresetCreateRequest(
            name=f"unit-{uuid4().hex[:8]}",
            config=EvalConfig(top_k=_CUSTOM_TOP_K),
            shared=False,
        ),
    )
    yield created.preset_id
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM eval_config_presets WHERE id = :id"),
            {"id": created.preset_id},
        )


def test_list_create_get_and_update_preset(
    engine: Engine,
    preset_owner_id: object,
    created_preset_id: object,
) -> None:
    """CRUD round-trip returns persisted preset fields."""
    listed = list_eval_config_presets(engine, owner_id=preset_owner_id)  # type: ignore[arg-type]
    assert any(item.preset_id == created_preset_id for item in listed.items)

    fetched = get_eval_config_preset(
        engine,
        preset_id=created_preset_id,  # type: ignore[arg-type]
        requester_id=preset_owner_id,  # type: ignore[arg-type]
    )
    assert fetched is not None
    assert fetched.config.top_k == _CUSTOM_TOP_K

    updated = update_eval_config_preset(
        engine,
        preset_id=created_preset_id,  # type: ignore[arg-type]
        owner_id=preset_owner_id,  # type: ignore[arg-type]
        body=EvalConfigPresetUpdateRequest(name="renamed"),
    )
    assert updated is not None
    assert updated.name == "renamed"
    assert updated.version == _EXPECTED_VERSION_AFTER_PATCH


def test_list_includes_shared_presets_from_other_owners(
    engine: Engine,
    preset_owner_id: object,
) -> None:
    """Shared presets owned by others appear in the caller listing."""
    other_owner = uuid4()
    shared = create_eval_config_preset(
        engine,
        owner_id=other_owner,
        body=EvalConfigPresetCreateRequest(
            name=f"shared-{uuid4().hex[:8]}",
            shared=True,
        ),
    )
    try:
        listed = list_eval_config_presets(engine, owner_id=preset_owner_id)  # type: ignore[arg-type]
        assert any(item.preset_id == shared.preset_id for item in listed.items)
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_config_presets WHERE id = :id"),
                {"id": shared.preset_id},
            )


def test_get_private_preset_denies_non_owner(
    engine: Engine,
    created_preset_id: object,
) -> None:
    """Private presets raise EvalConfigPresetAccessError for other admins."""
    with pytest.raises(EvalConfigPresetAccessError):
        get_eval_config_preset(
            engine,
            preset_id=created_preset_id,  # type: ignore[arg-type]
            requester_id=uuid4(),
        )


def test_get_shared_preset_allows_non_owner(
    engine: Engine,
    preset_owner_id: object,
) -> None:
    """Shared presets are readable by non-owners."""
    shared = create_eval_config_preset(
        engine,
        owner_id=preset_owner_id,  # type: ignore[arg-type]
        body=EvalConfigPresetCreateRequest(name="shared-read", shared=True),
    )
    try:
        fetched = get_eval_config_preset(
            engine,
            preset_id=shared.preset_id,
            requester_id=uuid4(),
        )
        assert fetched is not None
        assert fetched.shared is True
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_config_presets WHERE id = :id"),
                {"id": shared.preset_id},
            )


def test_get_and_update_return_none_for_missing_preset(
    engine: Engine,
    preset_owner_id: object,
) -> None:
    """Missing preset ids return None from get/update."""
    missing = uuid4()
    assert (
        get_eval_config_preset(
            engine,
            preset_id=missing,
            requester_id=preset_owner_id,  # type: ignore[arg-type]
        )
        is None
    )
    assert (
        update_eval_config_preset(
            engine,
            preset_id=missing,
            owner_id=preset_owner_id,  # type: ignore[arg-type]
            body=EvalConfigPresetUpdateRequest(shared=True),
        )
        is None
    )


def test_update_preset_denies_non_owner(
    engine: Engine,
    created_preset_id: object,
) -> None:
    """Only the owner may patch a preset."""
    with pytest.raises(EvalConfigPresetAccessError):
        update_eval_config_preset(
            engine,
            preset_id=created_preset_id,  # type: ignore[arg-type]
            owner_id=uuid4(),
            body=EvalConfigPresetUpdateRequest(name="stolen"),
        )


def test_clone_shared_preset_creates_private_copy(
    engine: Engine,
    preset_owner_id: object,
) -> None:
    """clone_eval_config_preset copies config under the cloner with shared=false."""
    source = create_eval_config_preset(
        engine,
        owner_id=preset_owner_id,  # type: ignore[arg-type]
        body=EvalConfigPresetCreateRequest(
            name="clone-me",
            config=EvalConfig(top_k=_CUSTOM_TOP_K),
            shared=True,
        ),
    )
    cloner_id = uuid4()
    try:
        cloned = clone_eval_config_preset(
            engine,
            preset_id=source.preset_id,
            cloner_id=cloner_id,
            name="my-copy",
        )
        assert cloned.name == "my-copy"
        assert cloned.shared is False
        assert cloned.owner_id == cloner_id
        assert cloned.config.top_k == _CUSTOM_TOP_K
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_config_presets WHERE id = :id"),
                {"id": source.preset_id},
            )
            conn.execute(
                text("DELETE FROM eval_config_presets WHERE owner_id = :owner_id"),
                {"owner_id": cloner_id},
            )


def test_clone_preset_uses_default_copy_name(
    engine: Engine,
    preset_owner_id: object,
) -> None:
    """clone_eval_config_preset appends (copy) when name is omitted."""
    source = create_eval_config_preset(
        engine,
        owner_id=preset_owner_id,  # type: ignore[arg-type]
        body=EvalConfigPresetCreateRequest(name="baseline", shared=True),
    )
    clone_id: object | None = None
    try:
        cloned = clone_eval_config_preset(
            engine,
            preset_id=source.preset_id,
            cloner_id=preset_owner_id,  # type: ignore[arg-type]
        )
        clone_id = cloned.preset_id
        assert cloned.name == "baseline (copy)"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM eval_config_presets WHERE id = :id"),
                {"id": source.preset_id},
            )
            if clone_id is not None:
                conn.execute(
                    text("DELETE FROM eval_config_presets WHERE id = :id"),
                    {"id": clone_id},
                )


def test_clone_missing_preset_raises_lookup_error(
    engine: Engine,
    preset_owner_id: object,
) -> None:
    """clone_eval_config_preset raises LookupError when the source id is unknown."""
    with pytest.raises(LookupError, match="preset not found"):
        clone_eval_config_preset(
            engine,
            preset_id=uuid4(),
            cloner_id=preset_owner_id,  # type: ignore[arg-type]
        )


def test_preset_from_row_parses_json_string_config() -> None:
    """_preset_from_row accepts JSON string config payloads."""
    preset_id = uuid4()
    owner_id = uuid4()
    parsed = _preset_from_row(
        {
            "id": preset_id,
            "preset_name": "json-string",
            "config": json.dumps({"top_k": _CUSTOM_TOP_K}),
            "shared": False,
            "owner_id": owner_id,
            "version": 1,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    )
    assert parsed.preset_id == preset_id
    assert parsed.config.top_k == _CUSTOM_TOP_K


def test_preset_from_row_parses_dict_config_and_timestamp_fallbacks() -> None:
    """_preset_from_row accepts dict config and substitutes missing datetimes."""
    parsed = _preset_from_row(
        {
            "id": uuid4(),
            "preset_name": "dict-config",
            "config": {"top_k": _CUSTOM_TOP_K},
            "shared": True,
            "owner_id": uuid4(),
            "version": 2,
            "created_at": "not-a-datetime",
            "updated_at": None,
        }
    )
    assert parsed.config.top_k == _CUSTOM_TOP_K
    assert parsed.created_at.tzinfo is UTC
    assert parsed.updated_at.tzinfo is UTC


def test_preset_from_row_defaults_config_when_unrecognized() -> None:
    """_preset_from_row falls back to EvalConfig() for unknown config shapes."""
    parsed = _preset_from_row(
        {
            "id": uuid4(),
            "preset_name": "bad-config",
            "config": 123,
            "shared": False,
            "owner_id": uuid4(),
            "version": 1,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    )
    assert parsed.config.top_k == EvalConfig().top_k
