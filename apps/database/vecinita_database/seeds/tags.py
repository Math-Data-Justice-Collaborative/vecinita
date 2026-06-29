"""Load seed tag vocabulary and tagged corpus fixtures (EV-001, D8/D9)."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, cast

from sqlalchemy import create_engine, text
from vecinita_shared_schemas.db_mapping import scalar_uuid
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Connection

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
    payload = as_json_object(cast("object", json.loads(path.read_text(encoding="utf-8"))))
    tags_raw = payload.get("tags")
    if not isinstance(tags_raw, list):
        msg = "seed_tags.json must contain a 'tags' array"
        raise ValueError(msg)  # noqa: TRY004  # seed JSON shape validation
    tags_list: list[object] = cast("list[object]", tags_raw)
    engine = create_engine(database_url or _database_url())
    inserted = 0

    with engine.begin() as conn:
        for raw_entry in tags_list:
            entry = as_json_object(raw_entry)
            slug = str(entry["slug"])
            for language, label_key in (("en", "label_en"), ("es", "label_es")):
                label = str(entry[label_key])
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


def _resolve_tag_id(conn: Connection, *, slug: str, language: str) -> UUID:
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
        msg = f"Missing seed tag {slug!r} for language {language!r}"
        raise ValueError(msg)
    return scalar_uuid(cast("object", tag_id))


def load_tagged_corpus(*, database_url: str | None = None) -> dict[str, int]:
    """Load tagged fixture documents, chunks, and document tag assignments."""
    manifest_path = _TAGGED_ROOT / "manifest.json"
    manifest = as_json_object(cast("object", json.loads(manifest_path.read_text(encoding="utf-8"))))
    documents_raw = manifest.get("documents")
    if not isinstance(documents_raw, list):
        msg = "tagged corpus manifest must contain a 'documents' array"
        raise ValueError(msg)  # noqa: TRY004  # manifest JSON shape validation
    documents_list: list[object] = cast("list[object]", documents_raw)
    engine = create_engine(database_url or _database_url())
    documents = 0
    chunks = 0
    document_tags = 0

    with engine.begin() as conn:
        for raw_spec in documents_list:
            spec = as_json_object(raw_spec)
            rel_path = Path(str(spec["path"]))
            language = str(spec["language"])
            body_path = _TAGGED_ROOT / rel_path
            body = body_path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            title_line = next(
                (line.lstrip("# ").strip() for line in body.splitlines() if line.startswith("#")),
                body_path.stem,
            )
            url = f"fixture://corpus/tagged/{rel_path.as_posix()}"
            doc_id = scalar_uuid(
                cast(
                    "object",
                    conn.execute(
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
                    ).scalar_one(),
                )
            )
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

            tags_raw = spec.get("tags")
            if not isinstance(tags_raw, list):
                msg = f"document spec {rel_path} must contain a 'tags' array"
                raise ValueError(msg)  # noqa: TRY004  # document spec JSON shape validation
            tags_list: list[object] = cast("list[object]", tags_raw)
            for raw_slug in tags_list:
                slug = str(raw_slug)
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
