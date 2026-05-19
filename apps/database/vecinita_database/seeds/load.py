"""Load committed corpus fixtures into Postgres (no embeddings)."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from sqlalchemy import create_engine, text

_REPO_ROOT = Path(__file__).resolve().parents[4]
_CORPUS_ROOT = _REPO_ROOT / "data" / "fixtures" / "corpus"
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


def _fixture_url(language: str, path: Path) -> str:
    rel = path.relative_to(_CORPUS_ROOT / language)
    return f"fixture://corpus/{language}/{rel.as_posix()}"


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


def load_corpus(*, database_url: str | None = None) -> dict[str, int]:
    """Insert seed documents and chunks for each language directory."""
    engine = create_engine(database_url or _database_url())
    documents = 0
    chunks = 0

    with engine.begin() as conn:
        for language_dir in sorted(_CORPUS_ROOT.iterdir()):
            if not language_dir.is_dir():
                continue
            language = language_dir.name
            for path in sorted(language_dir.glob("**/*")):
                if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                    continue
                body = path.read_text(encoding="utf-8")
                content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
                title_line = next(
                    (
                        line.lstrip("# ").strip()
                        for line in body.splitlines()
                        if line.startswith("#")
                    ),
                    path.stem,
                )
                url = _fixture_url(language, path)
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

    return {"documents": documents, "chunks": chunks}


def main() -> None:
    counts = load_corpus()
    print(f"Seeded {counts['documents']} documents, {counts['chunks']} chunks")


if __name__ == "__main__":
    main()
