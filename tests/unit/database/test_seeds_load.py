"""Unit tests for corpus seed loader helpers and CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from vecinita_database.seeds.load import (
    _chunk_text,  # pyright: ignore[reportPrivateUsage]
    _database_url,  # pyright: ignore[reportPrivateUsage]
    _fixture_url,  # pyright: ignore[reportPrivateUsage]
    _normalize_database_url,  # pyright: ignore[reportPrivateUsage]
    load_corpus,
    main,
)

from tests.unit.database.conftest import (
    database_url,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_MIN_CHUNK_COUNT = 2
_OVERSIZED_PARA_LEN = 500


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    """Test normalize database url upgrades postgresql scheme."""
    assert (
        _normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_fixture_url_builds_fixture_scheme(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test fixture url builds fixture scheme."""
    corpus_root = tmp_path / "corpus"
    monkeypatch.setattr("vecinita_database.seeds.load._CORPUS_ROOT", corpus_root)
    path = corpus_root / "en" / "sample.md"
    assert _fixture_url("en", path) == "fixture://corpus/en/sample.md"


def test_chunk_text_splits_long_paragraphs() -> None:
    """Test chunk text splits long paragraphs."""
    long_para = "word " * 120
    body = f"Intro\n\n{long_para.strip()}\n\nTail paragraph"
    chunks = _chunk_text(body)
    assert len(chunks) >= _MIN_CHUNK_COUNT
    assert any("Tail paragraph" in chunk for chunk in chunks)


def test_normalize_database_url_leaves_psycopg_unchanged() -> None:
    """Test normalize database url leaves psycopg unchanged."""
    url = "postgresql+psycopg://user:pass@host/db"
    assert _normalize_database_url(url) == url


def test_chunk_text_handles_single_oversized_paragraph() -> None:
    """Test chunk text handles single oversized paragraph."""
    body = "x" * _OVERSIZED_PARA_LEN
    chunks = _chunk_text(body)
    assert len(chunks) == 1
    assert len(chunks[0]) == _OVERSIZED_PARA_LEN


def test_chunk_text_merges_short_paragraphs() -> None:
    """Test chunk text merges short paragraphs."""
    body = "First short para.\n\nSecond short para."
    chunks = _chunk_text(body)
    assert len(chunks) == 1
    assert "First short para." in chunks[0]
    assert "Second short para." in chunks[0]


def test_load_corpus_skips_unsupported_language(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test load corpus skips unsupported language."""
    corpus_root = tmp_path / "corpus"
    (corpus_root / "fr").mkdir(parents=True)
    (corpus_root / "fr" / "doc.md").write_text("# French\n\nBody", encoding="utf-8")
    monkeypatch.setattr("vecinita_database.seeds.load._CORPUS_ROOT", corpus_root)

    counts = load_corpus(database_url=database_url())

    assert counts == {"documents": 0, "chunks": 0}


def test_load_corpus_skips_non_markdown_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test load corpus skips non markdown files."""
    corpus_root = tmp_path / "corpus"
    en_dir = corpus_root / "en"
    en_dir.mkdir(parents=True)
    (en_dir / "notes.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr("vecinita_database.seeds.load._CORPUS_ROOT", corpus_root)

    counts = load_corpus(database_url=database_url())

    assert counts == {"documents": 0, "chunks": 0}


def test_load_corpus_inserts_fixture_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test load corpus inserts fixture document."""
    corpus_root = tmp_path / "corpus"
    en_dir = corpus_root / "en"
    en_dir.mkdir(parents=True)
    (en_dir / "seed-doc.md").write_text("# Seed title\n\nSeed body paragraph.", encoding="utf-8")
    monkeypatch.setattr("vecinita_database.seeds.load._CORPUS_ROOT", corpus_root)

    counts = load_corpus(database_url=database_url())

    assert counts["documents"] == 1
    assert counts["chunks"] >= 1


def test_database_url_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test database url reads env."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    assert _database_url().startswith("postgresql+psycopg://")


def test_load_corpus_skips_non_directory_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test load corpus skips non directory entries."""
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    (corpus_root / "readme.txt").write_text("skip me", encoding="utf-8")
    en_dir = corpus_root / "en"
    en_dir.mkdir()
    (en_dir / "valid.md").write_text("# Valid\n\nBody", encoding="utf-8")
    monkeypatch.setattr("vecinita_database.seeds.load._CORPUS_ROOT", corpus_root)

    counts = load_corpus(database_url=database_url())

    assert counts["documents"] == 1


def test_chunk_text_empty_body_returns_empty_list() -> None:
    """Test chunk text empty body returns empty list."""
    assert _chunk_text("   \n\n  ") == []


def test_main_prints_seed_counts(capsys: pytest.CaptureFixture[str]) -> None:
    """Test main prints seed counts."""
    with patch(
        "vecinita_database.seeds.load.load_corpus", return_value={"documents": 2, "chunks": 5}
    ):
        main()
    captured = capsys.readouterr()
    assert "Seeded 2 documents, 5 chunks" in captured.out
