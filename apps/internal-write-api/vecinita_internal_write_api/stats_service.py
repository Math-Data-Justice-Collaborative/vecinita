"""Corpus statistics queries for admin dashboard."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, cast

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_str,
    row_str_optional,
    row_uuid,
    scalar_int,
)
from vecinita_shared_schemas.internal_write import (
    ParityGaps,
    RecentActivity,
    StatsServedRequest,
    StatsServedResponse,
    StatsSummaryResponse,
    TagCount,
    TopServedItem,
    TopServedResponse,
)

from vecinita_internal_write_api.deps import row_datetime, row_datetime_optional

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def fetch_stats_summary(*, engine: Engine) -> StatsSummaryResponse:
    """Aggregate corpus counts, tag distribution, and recent activity."""
    with engine.connect() as conn:
        total_docs = scalar_int(
            cast("object", conn.execute(text("SELECT COUNT(*) FROM documents")).scalar_one())
        )

        total_chunks = scalar_int(
            cast("object", conn.execute(text("SELECT COUNT(*) FROM chunks")).scalar_one())
        )

        tag_rows = (
            conn.execute(
                text(
                    """
                    SELECT t.slug, t.label, COUNT(dt.document_id) AS doc_count
                    FROM tags t
                    JOIN document_tags dt ON dt.tag_id = t.id
                    GROUP BY t.slug, t.label
                    ORDER BY doc_count DESC LIMIT 50
                    """
                )
            )
            .mappings()
            .all()
        )

        lang_rows = (
            conn.execute(
                text(
                    """
                    SELECT COALESCE(language, 'unknown') AS lang, COUNT(*) AS cnt
                    FROM documents GROUP BY language
                    """
                )
            )
            .mappings()
            .all()
        )

        chunk_lang_rows = (
            conn.execute(
                text(
                    """
                    SELECT COALESCE(d.language, 'unknown') AS lang, COUNT(*) AS cnt
                    FROM chunks c
                    JOIN documents d ON d.id = c.document_id
                    GROUP BY d.language
                    """
                )
            )
            .mappings()
            .all()
        )

        en_only = scalar_int(
            cast(
                "object",
                conn.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM documents
                        WHERE language = 'en'
                        AND publish_status = 'published'
                        AND paired_document_id IS NULL
                        """
                    )
                ).scalar_one(),
            )
        )

        es_only = scalar_int(
            cast(
                "object",
                conn.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM documents
                        WHERE language = 'es'
                        AND publish_status = 'published'
                        AND paired_document_id IS NULL
                        """
                    )
                ).scalar_one(),
            )
        )

        recent_rows = (
            conn.execute(
                text(
                    """
                    SELECT event_type, entity_id, created_at
                    FROM audit_log ORDER BY created_at DESC LIMIT 20
                    """
                )
            )
            .mappings()
            .all()
        )

        top_rows = (
            conn.execute(
                text(
                    """
                    SELECT s.document_id, d.title, d.url,
                           s.served_count, s.last_served_at
                    FROM document_serving_stats s
                    LEFT JOIN documents d ON d.id = s.document_id
                    ORDER BY s.served_count DESC LIMIT 10
                    """
                )
            )
            .mappings()
            .all()
        )

    return StatsSummaryResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        tag_distribution=[
            TagCount(
                slug=row_str(mapping_row(row), "slug"),
                label=row_str(mapping_row(row), "label"),
                document_count=row_int(mapping_row(row), "doc_count"),
            )
            for row in tag_rows
        ],
        language_breakdown={
            row_str(mapping_row(row), "lang"): row_int(mapping_row(row), "cnt") for row in lang_rows
        },
        chunk_language_breakdown={
            row_str(mapping_row(row), "lang"): row_int(mapping_row(row), "cnt")
            for row in chunk_lang_rows
        },
        parity_gaps=ParityGaps(en_only=en_only, es_only=es_only),
        recent_activity=[
            RecentActivity(
                event_type=row_str(mapping_row(row), "event_type"),
                entity_id=row_uuid(mapping_row(row), "entity_id"),
                created_at=row_datetime(mapping_row(row), "created_at"),
            )
            for row in recent_rows
        ],
        top_served=[
            TopServedItem(
                document_id=row_uuid(mapping_row(row), "document_id"),
                title=row_str_optional(mapping_row(row), "title"),
                url=row_str_optional(mapping_row(row), "url"),
                served_count=row_int(mapping_row(row), "served_count"),
                last_served_at=row_datetime_optional(mapping_row(row), "last_served_at"),
            )
            for row in top_rows
        ],
    )


def record_documents_served(*, engine: Engine, body: StatsServedRequest) -> StatsServedResponse:
    """Increment served counters for cited documents."""
    for doc_id in body.document_ids:
        with contextlib.suppress(Exception), engine.begin() as conn:
            _ = conn.execute(
                text(
                    """
                    INSERT INTO document_serving_stats
                    (document_id, served_count, last_served_at)
                    VALUES (:doc_id, 1, now())
                    ON CONFLICT (document_id) DO UPDATE
                    SET served_count = document_serving_stats.served_count + 1,
                        last_served_at = now()
                    """
                ),
                {"doc_id": doc_id},
            )
    return StatsServedResponse()


def fetch_top_served(*, engine: Engine, limit: int) -> TopServedResponse:
    """Return top served documents by count."""
    limit = min(max(1, limit), 100)
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                    SELECT s.document_id, d.title, d.url,
                           s.served_count, s.last_served_at
                    FROM document_serving_stats s
                    LEFT JOIN documents d ON d.id = s.document_id
                    ORDER BY s.served_count DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            )
            .mappings()
            .all()
        )
    return TopServedResponse(
        items=[
            TopServedItem(
                document_id=row_uuid(mapping_row(row), "document_id"),
                title=row_str_optional(mapping_row(row), "title"),
                url=row_str_optional(mapping_row(row), "url"),
                served_count=row_int(mapping_row(row), "served_count"),
                last_served_at=row_datetime_optional(mapping_row(row), "last_served_at"),
            )
            for row in rows
        ]
    )
