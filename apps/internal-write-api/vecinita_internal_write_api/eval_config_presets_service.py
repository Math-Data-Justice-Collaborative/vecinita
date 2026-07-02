"""Per-user eval config preset CRUD (ADR-035 §7)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_str,
    row_uuid,
)
from vecinita_shared_schemas.eval_config import (
    EvalConfig,
    EvalConfigPresetCreateRequest,
    EvalConfigPresetListResponse,
    EvalConfigPresetResponse,
    EvalConfigPresetUpdateRequest,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.engine import Engine


class EvalConfigPresetAccessError(Exception):
    """Caller lacks permission for the requested preset operation."""


def list_eval_config_presets(
    engine: Engine,
    *,
    owner_id: UUID,
) -> EvalConfigPresetListResponse:
    """List presets owned by the caller plus shared presets from other admins."""
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                    SELECT id, preset_name, config, shared, owner_id, version,
                           created_at, updated_at
                    FROM eval_config_presets
                    WHERE owner_id = :owner_id OR shared = true
                    ORDER BY updated_at DESC
                    """
                ),
                {"owner_id": owner_id},
            )
            .mappings()
            .all()
        )
    return EvalConfigPresetListResponse(
        items=[_preset_from_row(mapping_row(row)) for row in rows],
    )


def create_eval_config_preset(
    engine: Engine,
    *,
    owner_id: UUID,
    body: EvalConfigPresetCreateRequest,
) -> EvalConfigPresetResponse:
    """Insert a new private or shared preset for the owner."""
    preset_id = uuid4()
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_config_presets (
                    id, preset_name, config, shared, owner_id, version,
                    created_at, updated_at
                )
                VALUES (
                    :id, :preset_name, CAST(:config AS jsonb), :shared, :owner_id, 1,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "id": preset_id,
                "preset_name": body.name,
                "config": json.dumps(body.config.model_dump(mode="json")),
                "shared": body.shared,
                "owner_id": owner_id,
                "created_at": now,
                "updated_at": now,
            },
        )
    return EvalConfigPresetResponse(
        preset_id=preset_id,
        version=1,
        name=body.name,
        config=body.config,
        shared=body.shared,
        owner_id=owner_id,
        created_at=now,
        updated_at=now,
    )


def get_eval_config_preset(
    engine: Engine,
    *,
    preset_id: UUID,
    requester_id: UUID,
) -> EvalConfigPresetResponse | None:
    """Fetch one preset when the requester is owner or preset is shared."""
    preset = _fetch_preset_row(engine, preset_id=preset_id)
    if preset is None:
        return None
    owner_id = row_uuid(preset, "owner_id")
    shared = bool(preset.get("shared"))
    if owner_id != requester_id and not shared:
        raise EvalConfigPresetAccessError
    return _preset_from_row(preset)


def update_eval_config_preset(
    engine: Engine,
    *,
    preset_id: UUID,
    owner_id: UUID,
    body: EvalConfigPresetUpdateRequest,
) -> EvalConfigPresetResponse | None:
    """Patch a preset; only the owner may update."""
    existing = _fetch_preset_row(engine, preset_id=preset_id)
    if existing is None:
        return None
    if row_uuid(existing, "owner_id") != owner_id:
        raise EvalConfigPresetAccessError
    current = _preset_from_row(existing)
    name = body.name if body.name is not None else current.name
    config = body.config if body.config is not None else current.config
    shared = body.shared if body.shared is not None else current.shared
    version = current.version + 1
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE eval_config_presets
                SET preset_name = :preset_name,
                    config = CAST(:config AS jsonb),
                    shared = :shared,
                    version = :version,
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {
                "id": preset_id,
                "preset_name": name,
                "config": json.dumps(config.model_dump(mode="json")),
                "shared": shared,
                "version": version,
                "updated_at": now,
            },
        )
    return EvalConfigPresetResponse(
        preset_id=preset_id,
        version=version,
        name=name,
        config=config,
        shared=shared,
        owner_id=owner_id,
        created_at=current.created_at,
        updated_at=now,
    )


def clone_eval_config_preset(
    engine: Engine,
    *,
    preset_id: UUID,
    cloner_id: UUID,
    name: str | None = None,
) -> EvalConfigPresetResponse:
    """Clone a shared preset (or own preset) into a new preset owned by the cloner."""
    source = get_eval_config_preset(engine, preset_id=preset_id, requester_id=cloner_id)
    if source is None:
        msg = "preset not found"
        raise LookupError(msg)
    clone_name = name or f"{source.name} (copy)"
    return create_eval_config_preset(
        engine,
        owner_id=cloner_id,
        body=EvalConfigPresetCreateRequest(
            name=clone_name,
            config=source.config,
            shared=False,
        ),
    )


def _fetch_preset_row(engine: Engine, *, preset_id: UUID) -> Mapping[str, object] | None:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT id, preset_name, config, shared, owner_id, version,
                           created_at, updated_at
                    FROM eval_config_presets
                    WHERE id = :id
                    """
                ),
                {"id": preset_id},
            )
            .mappings()
            .first()
        )
    if row is None:
        return None
    return mapping_row(row)


def _preset_from_row(row: Mapping[str, object]) -> EvalConfigPresetResponse:
    created = row.get("created_at")
    updated = row.get("updated_at")
    if not isinstance(created, datetime):
        created = datetime.now(UTC)
    if not isinstance(updated, datetime):
        updated = created
    config_raw = row.get("config")
    if isinstance(config_raw, str):
        config = EvalConfig.model_validate_json(config_raw)
    elif isinstance(config_raw, dict):
        config = EvalConfig.model_validate(config_raw)
    else:
        config = EvalConfig()
    return EvalConfigPresetResponse(
        preset_id=row_uuid(row, "id"),
        version=row_int(row, "version"),
        name=row_str(row, "preset_name"),
        config=config,
        shared=bool(row.get("shared")),
        owner_id=row_uuid(row, "owner_id"),
        created_at=created,
        updated_at=updated,
    )
