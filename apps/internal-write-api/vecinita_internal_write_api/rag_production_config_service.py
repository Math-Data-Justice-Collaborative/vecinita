"""Production RAG config promote + active read (ADR-035 §10)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_uuid,
    row_value,
    scalar_int,
    sqlalchemy_scalar_one,
)
from vecinita_shared_schemas.eval_config import (
    EvalConfig,
    RagConfigActiveResponse,
    RagConfigPromoteRequest,
    RagConfigPromoteResponse,
)

from vecinita_internal_write_api.audit import emit_audit_event

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.engine import Engine


class RagConfigPromoteNotFoundError(Exception):
    """Promote source preset or run was not found."""


def _row_datetime_optional(row: Mapping[str, object], key: str) -> datetime | None:
    value = row_value(row, key)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    msg = f"Expected datetime for {key!r}, got {type(value).__name__}"
    raise TypeError(msg)


def _row_uuid_optional(row: Mapping[str, object], key: str) -> UUID | None:
    value = row_value(row, key)
    if value is None:
        return None
    return row_uuid(row, key)


def _config_from_json(value: object) -> EvalConfig:
    if isinstance(value, str):
        return EvalConfig.model_validate_json(value)
    if isinstance(value, dict):
        return EvalConfig.model_validate(value)
    return EvalConfig()


def _active_row_from_mapping(row: Mapping[str, object]) -> RagConfigActiveResponse:
    return RagConfigActiveResponse(
        config=_config_from_json(row.get("config")),
        config_version=row_int(row, "config_version"),
        promoted_at=_row_datetime_optional(row, "promoted_at"),
        promoted_by=_row_uuid_optional(row, "promoted_by"),
    )


def get_active_rag_config(engine: Engine) -> RagConfigActiveResponse | None:
    """Return the active production config row, if any."""
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT config, config_version, promoted_at, promoted_by
                    FROM rag_production_config
                    WHERE is_active = true
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .first()
        )
    if row is None:
        return None
    return _active_row_from_mapping(mapping_row(row))


def _resolve_promote_config(
    engine: Engine,
    *,
    body: RagConfigPromoteRequest,
) -> EvalConfig:
    if body.source == "preset":
        preset_id = body.preset_id
        if preset_id is None:
            msg = "preset_id is required when source is preset"
            raise ValueError(msg)
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text(
                        """
                        SELECT config
                        FROM eval_config_presets
                        WHERE id = :preset_id
                        """
                    ),
                    {"preset_id": preset_id},
                )
                .mappings()
                .first()
            )
        if row is None:
            msg = "preset not found"
            raise RagConfigPromoteNotFoundError(msg)
        return _config_from_json(mapping_row(row).get("config"))

    run_id = body.run_id
    if run_id is None:
        msg = "run_id is required when source is run"
        raise ValueError(msg)
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT config_snapshot
                    FROM eval_runs
                    WHERE id = :run_id
                    """
                ),
                {"run_id": run_id},
            )
            .mappings()
            .first()
        )
    if row is None:
        msg = "run not found"
        raise RagConfigPromoteNotFoundError(msg)
    mapped = mapping_row(row)
    return _config_from_json(mapped.get("config_snapshot"))


def promote_rag_config(
    engine: Engine,
    *,
    promoted_by: UUID,
    body: RagConfigPromoteRequest,
    request_id: UUID | None = None,
) -> RagConfigPromoteResponse:
    """Upsert the active production RAG config from a preset or eval run snapshot."""
    config = _resolve_promote_config(engine, body=body)
    promoted_at = datetime.now(UTC)
    config_row_id = uuid4()
    audit_request_id = request_id or uuid4()

    with engine.begin() as conn:
        next_version = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text("SELECT COALESCE(MAX(config_version), 0) + 1 FROM rag_production_config")
                )
            )
        )
        conn.execute(
            text(
                """
                UPDATE rag_production_config
                SET is_active = false
                WHERE is_active = true
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO rag_production_config (
                    id, config, config_version, is_active, promoted_at, promoted_by
                )
                VALUES (
                    :id,
                    CAST(:config AS jsonb),
                    :config_version,
                    true,
                    :promoted_at,
                    :promoted_by
                )
                """
            ),
            {
                "id": config_row_id,
                "config": json.dumps(config.model_dump(mode="json")),
                "config_version": next_version,
                "promoted_at": promoted_at,
                "promoted_by": promoted_by,
            },
        )
        emit_audit_event(
            conn,
            event_type="rag.config.promoted",
            entity_type="rag_production_config",
            entity_id=config_row_id,
            request_id=audit_request_id,
            payload={
                "config_version": next_version,
                "source": body.source,
                "preset_id": str(body.preset_id) if body.preset_id is not None else None,
                "run_id": str(body.run_id) if body.run_id is not None else None,
            },
            actor_id=promoted_by,
            actor_role="super-admin",
        )

    return RagConfigPromoteResponse(
        config_version=next_version,
        promoted_at=promoted_at,
        promoted_by=promoted_by,
    )
