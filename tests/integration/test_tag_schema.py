"""Tag schema FK constraints and Alembic head verification (EV-001)."""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration

_DATABASE_DIR = Path(__file__).resolve().parents[2] / "apps" / "database"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def test_alembic_history_includes_tag_schema() -> None:
    """Tag migration revision is applied (present in Alembic history)."""
    env = {**os.environ, "DATABASE_URL": _database_url()}
    history = subprocess.run(
        ["uv", "run", "alembic", "history"],
        cwd=_DATABASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "20260524_0002" in history.stdout


def test_document_tags_foreign_key_enforced() -> None:
    """document_tags rejects unknown document_id."""
    engine = create_engine(_database_url())
    bogus_document = uuid.uuid4()
    with engine.begin() as conn:
        tag_id = conn.execute(
            text(
                """
                INSERT INTO tags (slug, label, language)
                VALUES ('fk-test-doc', 'FK Test', 'en')
                RETURNING id
                """
            )
        ).scalar_one()
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO document_tags (document_id, tag_id, source)
                    VALUES (:document_id, :tag_id, 'llm')
                    """
                ),
                {"document_id": bogus_document, "tag_id": tag_id},
            )


def test_chunk_tags_foreign_key_enforced() -> None:
    """chunk_tags rejects unknown chunk_id."""
    engine = create_engine(_database_url())
    bogus_chunk = uuid.uuid4()
    with engine.begin() as conn:
        tag_id = conn.execute(
            text(
                """
                INSERT INTO tags (slug, label, language)
                VALUES ('fk-test-chunk', 'FK Test Chunk', 'en')
                RETURNING id
                """
            )
        ).scalar_one()
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO chunk_tags (chunk_id, tag_id, source)
                    VALUES (:chunk_id, :tag_id, 'human')
                    """
                ),
                {"chunk_id": bogus_chunk, "tag_id": tag_id},
            )
