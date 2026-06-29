"""Unit tests for tag seed loader helpers and fixtures."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from vecinita_database.seeds.tags import (
    _chunk_text,
    _normalize_database_url,
    _resolve_tag_id,
    load_seed_tags,
    load_tagged_corpus,
)

from tests.unit.database.conftest import database_url


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    assert (
        _normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_normalize_database_url_leaves_psycopg_unchanged() -> None:
    url = "postgresql+psycopg://user:pass@host/db"
    assert _normalize_database_url(url) == url


def test_chunk_text_handles_single_oversized_paragraph() -> None:
    chunks = _chunk_text("y" * 500)
    assert len(chunks) == 1


def test_chunk_text_flushes_existing_buffer_before_overflow() -> None:
    chunks = _chunk_text(f"{'a' * 300}\n\n{'b' * 200}")
    assert len(chunks) >= 2


def test_chunk_text_flushes_buffer_on_overflow() -> None:
    body = textwrap.dedent(
        """
        Short intro.

        """
        + ("x" * 500)
        + """

        Final bit.
        """
    )
    chunks = _chunk_text(body)
    assert len(chunks) >= 2


def test_load_seed_tags_rejects_invalid_payload(tmp_path: Path) -> None:
    bad_path = tmp_path / "seed_tags.json"
    bad_path.write_text(json.dumps({"not_tags": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="tags"):
        load_seed_tags(database_url=database_url(), seed_path=bad_path)


def test_load_seed_tags_inserts_bilingual_rows() -> None:
    inserted = load_seed_tags(database_url=database_url())
    assert inserted == 16


def test_resolve_tag_id_raises_for_missing_tag() -> None:
    engine = create_engine(database_url())
    with engine.begin() as conn, pytest.raises(ValueError, match="Missing seed tag"):
        _resolve_tag_id(conn, slug="does-not-exist", language="en")


def test_load_tagged_corpus_rejects_invalid_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tagged_root = tmp_path / "tagged"
    tagged_root.mkdir()
    (tagged_root / "manifest.json").write_text(json.dumps({"documents": "bad"}), encoding="utf-8")
    monkeypatch.setattr("vecinita_database.seeds.tags._TAGGED_ROOT", tagged_root)

    with pytest.raises(ValueError, match="documents"):
        load_tagged_corpus(database_url=database_url())


def test_load_tagged_corpus_rejects_document_without_tags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tagged_root = tmp_path / "tagged"
    doc_path = Path("en/missing-tags.md")
    (tagged_root / doc_path).parent.mkdir(parents=True)
    (tagged_root / doc_path).write_text("# Doc\n\nBody", encoding="utf-8")
    manifest = {
        "documents": [
            {"path": doc_path.as_posix(), "language": "en", "tags": "not-a-list"},
        ]
    }
    (tagged_root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr("vecinita_database.seeds.tags._TAGGED_ROOT", tagged_root)
    load_seed_tags(database_url=database_url())

    with pytest.raises(ValueError, match="must contain a 'tags' array"):
        load_tagged_corpus(database_url=database_url())


def test_chunk_text_empty_body_returns_empty_list() -> None:
    assert _chunk_text("   \n\n  ") == []


def test_database_url_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from vecinita_database.seeds.tags import _database_url

    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    assert _database_url().startswith("postgresql+psycopg://")


def test_load_tagged_corpus_loads_manifest_documents() -> None:
    load_seed_tags(database_url=database_url())
    counts = load_tagged_corpus(database_url=database_url())
    assert counts["documents"] >= 1
    assert counts["document_tags"] >= 1
