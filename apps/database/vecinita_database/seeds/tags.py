"""Load seed tag vocabulary and tagged corpus fixtures (EV-001, D8/D9)."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TAG_SEED_PATH = _REPO_ROOT / "data" / "fixtures" / "tags" / "seed_tags.json"
_TAGGED_ROOT = _REPO_ROOT / "data" / "fixtures" / "corpus" / "tagged"
_CHUNK_SIZE = 400


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database_url() -> str:
    return _normalize_database_url(
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        )
    )


def _chunk_text(body: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) + 1 <= _CHUNK_SIZE:
            buffer = f"{buffer}\n{paragraph}".strip() if buffer else paragraph
            continue
        if buffer:
            chunks.append(buffer)
        buffer = paragraph
    if buffer:
        chunks.append(buffer)
    return chunks


def load_seed_tags(*, database_url: str | None = None, seed_path: Path | None = None) -> int:
    """Insert bilingual starter tags from seed_tags.json."""
    path = seed_path or _TAG_SEED_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    tags = payload["tags"]
    engine = create_engine(database_url or _database_url())
    inserted = 0

    with engine.begin() as conn:
        for entry in tags:
            slug = entry["slug"]
            for language, label_key in (("en", "label_en"), ("es", "label_es")):
                label = entry[label_key]
                conn.execute(
                    text(
                        """
                        INSERT INTO tags (slug, label, language)
                        VALUES (:slug, :label, :language)
                        ON CONFLICT (slug, language) DO UPDATE
                        SET label = EXCLUDED.label
                        """
                    ),
                    {"slug": slug, "label": label, "language": language},
                )
                inserted += 1

    return inserted


def _resolve_tag_id(conn: Any, *, slug: str, language: str) -> Any:
    tag_id = conn.execute(
        text(
            """
            SELECT id FROM tags
            WHERE slug = :slug AND language = :language
            """
        ),
        {"slug": slug, "language": language},
    ).scalar_one_or_none()
    if tag_id is None:
        raise ValueError(f"Missing seed tag {slug!r} for language {language!r}")
    return tag_id


def load_tagged_corpus(*, database_url: str | None = None) -> dict[str, int]:
    """Load tagged fixture documents, chunks, and document tag assignments."""
    manifest_path = _TAGGED_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    engine = create_engine(database_url or _database_url())
    documents = 0
    chunks = 0
    document_tags = 0

    with engine.begin() as conn:
        for spec in manifest["documents"]:
            rel_path = Path(spec["path"])
            language = spec["language"]
            body_path = _TAGGED_ROOT / rel_path
            body = body_path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            title_line = next(
                (line.lstrip("# ").strip() for line in body.splitlines() if line.startswith("#")),
                body_path.stem,
            )
            url = f"fixture://corpus/tagged/{rel_path.as_posix()}"
            doc_id = conn.execute(
                text(
                    """
                    INSERT INTO documents (url, title, content_hash, language)
                    VALUES (:url, :title, :content_hash, :language)
                    ON CONFLICT (url) DO UPDATE
                    SET title = EXCLUDED.title,
                        content_hash = EXCLUDED.content_hash,
                        language = EXCLUDED.language,
                        updated_at = now()
                    RETURNING id
                    """
                ),
                {
                    "url": url,
                    "title": title_line,
                    "content_hash": content_hash,
                    "language": language,
                },
            ).scalar_one()
            documents += 1

            conn.execute(
                text("DELETE FROM chunks WHERE document_id = :document_id"),
                {"document_id": doc_id},
            )
            conn.execute(
                text("DELETE FROM document_tags WHERE document_id = :document_id"),
                {"document_id": doc_id},
            )
            for index, chunk in enumerate(_chunk_text(body)):
                conn.execute(
                    text(
                        """
                        INSERT INTO chunks (document_id, chunk_index, text, token_count)
                        VALUES (:document_id, :chunk_index, :text, NULL)
                        """
                    ),
                    {
                        "document_id": doc_id,
                        "chunk_index": index,
                        "text": chunk,
                    },
                )
                chunks += 1

            for slug in spec["tags"]:
                tag_id = _resolve_tag_id(conn, slug=slug, language=language)
                conn.execute(
                    text(
                        """
                        INSERT INTO document_tags (document_id, tag_id, source)
                        VALUES (:document_id, :tag_id, 'llm')
                        ON CONFLICT (document_id, tag_id) DO NOTHING
                        """
                    ),
                    {"document_id": doc_id, "tag_id": tag_id},
                )
                document_tags += 1

    return {
        "documents": documents,
        "chunks": chunks,
        "document_tags": document_tags,
    }
