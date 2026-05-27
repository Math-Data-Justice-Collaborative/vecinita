"""Public corpus browse queries (F19)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Connection, Engine
from vecinita_shared_schemas.chat_rag import (
    DocumentBrowseDetail,
    DocumentBrowseItem,
    DocumentBrowsePage,
    TagFacet,
    TagListResponse,
    TagSummary,
)
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_str,
    row_str_optional,
    row_uuid,
    scalar_int,
    sqlalchemy_scalar_one,
)

_TAG_SQL = text(
    """
    SELECT t.slug, t.label
    FROM document_tags dt
    JOIN tags t ON t.id = dt.tag_id
    JOIN documents d ON d.id = dt.document_id
    WHERE dt.document_id = :document_id
      AND t.language = COALESCE(d.language, 'en')
    ORDER BY t.slug
    """
)


def _tag_summaries(conn: Connection, document_id: UUID) -> list[TagSummary]:
    tag_rows = conn.execute(_TAG_SQL, {"document_id": document_id}).mappings().all()
    return [
        TagSummary(
            slug=row_str(mapping_row(tag), "slug"),
            label=row_str(mapping_row(tag), "label"),
        )
        for tag in tag_rows
    ]


def list_documents(
    engine: Engine,
    *,
    tags: list[str] | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> DocumentBrowsePage:
    """Paginated public document browse with optional tag and text filters."""
    filters: list[str] = []
    params: dict[str, object] = {
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }

    if tags:
        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM document_tags dt
                JOIN tags t ON t.id = dt.tag_id
                WHERE dt.document_id = d.id
                  AND t.slug IN :tag_slugs
            )
            """
        )
        params["tag_slugs"] = tuple(tags)

    if q:
        filters.append("(d.title ILIKE :q_pattern OR d.url ILIKE :q_pattern)")
        params["q_pattern"] = f"%{q.strip()}%"

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    count_sql = text(f"SELECT COUNT(*) FROM documents d {where_clause}")
    list_sql = text(
        f"""
        SELECT d.id, d.title, d.url, d.language
        FROM documents d
        {where_clause}
        ORDER BY d.created_at DESC, d.url
        LIMIT :limit OFFSET :offset
        """
    )

    if tags:
        count_sql = count_sql.bindparams(bindparam("tag_slugs", expanding=True))
        list_sql = list_sql.bindparams(bindparam("tag_slugs", expanding=True))

    with engine.connect() as conn:
        total = scalar_int(sqlalchemy_scalar_one(conn.execute(count_sql, params)))
        rows = conn.execute(list_sql, params).mappings().all()
        items: list[DocumentBrowseItem] = []
        for raw_row in rows:
            row = mapping_row(raw_row)
            doc_id = row_uuid(row, "id")
            items.append(
                DocumentBrowseItem(
                    document_id=doc_id,
                    title=row_str_optional(row, "title"),
                    url=row_str(row, "url"),
                    language=row_str_optional(row, "language"),
                    tags=_tag_summaries(conn, doc_id),
                )
            )

    return DocumentBrowsePage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


def get_document(engine: Engine, document_id: UUID) -> DocumentBrowseDetail | None:
    """Fetch one document for public browse detail."""
    doc_sql = text(
        """
        SELECT id, title, url, language
        FROM documents
        WHERE id = :document_id
        """
    )
    with engine.connect() as conn:
        raw_row = conn.execute(doc_sql, {"document_id": document_id}).mappings().one_or_none()
        if raw_row is None:
            return None
        row = mapping_row(raw_row)
        return DocumentBrowseDetail(
            document_id=row_uuid(row, "id"),
            title=row_str_optional(row, "title"),
            url=row_str(row, "url"),
            language=row_str_optional(row, "language"),
            tags=_tag_summaries(conn, document_id),
        )


def list_tag_facets(engine: Engine) -> TagListResponse:
    """Distinct tag facets with document counts for browse and chat filters."""
    sql = text(
        """
        SELECT
            t.slug,
            t.label,
            t.language,
            COUNT(DISTINCT dt.document_id) AS document_count
        FROM tags t
        LEFT JOIN document_tags dt ON dt.tag_id = t.id
        GROUP BY t.slug, t.label, t.language
        HAVING COUNT(DISTINCT dt.document_id) > 0
        ORDER BY t.slug, t.language
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return TagListResponse(
        tags=[
            TagFacet(
                slug=row_str(mapping_row(row), "slug"),
                label=row_str(mapping_row(row), "label"),
                language=row_str(mapping_row(row), "language"),
                document_count=row_int(mapping_row(row), "document_count"),
            )
            for row in rows
        ]
    )


def engine_from_url(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for browse queries."""
    return create_engine(database_url)
