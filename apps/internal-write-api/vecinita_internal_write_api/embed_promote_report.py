"""F71 embed-promote advisory report (UJ-076 / TC-235-236 / AC-ME3-ME4).

Builds EN/ES Hy1 relevancy + faithfulness vs E0 baseline from linked F36 eval
runs when present; otherwise returns a scaffold with null metric columns so
operators can still open the report after a shadow rebuild.

[Corpus: feature-list.md §F71]
[Spec: docs/acceptance-criteria.md §AC-ME3]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from sqlalchemy import text
from vecinita_embedding_client.modal_pins import (
    DEFAULT_EMBEDDING_MODEL_ID,
    LEGACY_E0_EMBEDDING_MODEL_ID,
)
from vecinita_shared_schemas.db_mapping import mapping_row, row_str_optional
from vecinita_shared_schemas.internal_write import (
    EmbedPromoteHy1Metrics,
    EmbedPromoteLanguageMetrics,
    EmbedPromoteReportResponse,
)
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Connection, Engine

_Lang = Literal["en", "es"]
_LANGS: tuple[_Lang, ...] = ("en", "es")


class EmbedPromoteReportNotFoundError(LookupError):
    """Raised when rebuild_run_id does not exist."""


def _empty_hy1() -> EmbedPromoteHy1Metrics:
    return EmbedPromoteHy1Metrics(
        answer_relevancy=None,
        faithfulness=None,
        hit_at_k=None,
        mean_rank=None,
    )


def _scaffold_language() -> EmbedPromoteLanguageMetrics:
    return EmbedPromoteLanguageMetrics(
        answer_relevancy=None,
        faithfulness=None,
        hit_at_k=None,
        mean_rank=None,
        baseline_e0=_empty_hy1(),
    )


def scaffold_embed_promote_report(
    *,
    rebuild_run_id: UUID,
    candidate_embedding_model_id: str,
    baseline_embedding_model_id: str = LEGACY_E0_EMBEDDING_MODEL_ID,
    dense_available: bool = False,
) -> EmbedPromoteReportResponse:
    """Return EN/ES column scaffold (null metrics) for a rebuild run stamp."""
    by_language: dict[_Lang, EmbedPromoteLanguageMetrics] = {
        lang: _scaffold_language() for lang in _LANGS
    }
    return EmbedPromoteReportResponse(
        rebuild_run_id=rebuild_run_id,
        candidate_embedding_model_id=candidate_embedding_model_id,
        baseline_embedding_model_id=baseline_embedding_model_id,
        dense_available=dense_available,
        by_language=by_language,
    )


def _optional_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _aggregate_locale_metrics(
    items: list[dict[str, object]],
) -> dict[_Lang, EmbedPromoteHy1Metrics]:
    """Average faithfulness / answer_relevancy (+ dense) per locale."""
    buckets: dict[_Lang, dict[str, list[float]]] = {
        lang: {
            "answer_relevancy": [],
            "faithfulness": [],
            "hit_at_k": [],
            "mean_rank": [],
        }
        for lang in _LANGS
    }
    for item in items:
        locale_raw = str(item.get("locale") or "").lower()
        if locale_raw not in {"en", "es"}:
            continue
        locale: _Lang = "en" if locale_raw == "en" else "es"
        metrics_raw = item.get("metrics")
        metrics = (
            as_json_object(cast("object", metrics_raw)) if isinstance(metrics_raw, dict) else {}
        )
        for key in ("answer_relevancy", "faithfulness"):
            score = _optional_float(metrics.get(key))
            if score is not None:
                buckets[locale][key].append(score)
        custom_raw = metrics.get("custom_scores")
        custom = as_json_object(cast("object", custom_raw)) if isinstance(custom_raw, dict) else {}
        for key in ("hit_at_k", "mean_rank"):
            score = _optional_float(custom.get(key))
            if score is None:
                score = _optional_float(metrics.get(key))
            if score is not None:
                buckets[locale][key].append(score)
    return {
        lang: EmbedPromoteHy1Metrics(
            answer_relevancy=_mean(buckets[lang]["answer_relevancy"]),
            faithfulness=_mean(buckets[lang]["faithfulness"]),
            hit_at_k=_mean(buckets[lang]["hit_at_k"]),
            mean_rank=_mean(buckets[lang]["mean_rank"]),
        )
        for lang in _LANGS
    }


def _has_dense(metrics: EmbedPromoteHy1Metrics) -> bool:
    return metrics.hit_at_k is not None or metrics.mean_rank is not None


def _merge_candidate_baseline(
    *,
    candidate: dict[_Lang, EmbedPromoteHy1Metrics],
    baseline: dict[_Lang, EmbedPromoteHy1Metrics],
) -> tuple[dict[_Lang, EmbedPromoteLanguageMetrics], bool]:
    dense = any(
        _has_dense(candidate.get(lang, _empty_hy1()))
        or _has_dense(baseline.get(lang, _empty_hy1()))
        for lang in _LANGS
    )
    by_language: dict[_Lang, EmbedPromoteLanguageMetrics] = {}
    for lang in _LANGS:
        cand = candidate.get(lang, _empty_hy1())
        base = baseline.get(lang, _empty_hy1())
        by_language[lang] = EmbedPromoteLanguageMetrics(
            answer_relevancy=cand.answer_relevancy,
            faithfulness=cand.faithfulness,
            hit_at_k=cand.hit_at_k if dense else None,
            mean_rank=cand.mean_rank if dense else None,
            baseline_e0=EmbedPromoteHy1Metrics(
                answer_relevancy=base.answer_relevancy,
                faithfulness=base.faithfulness,
                hit_at_k=base.hit_at_k if dense else None,
                mean_rank=base.mean_rank if dense else None,
            ),
        )
    return by_language, dense


def aggregate_locale_metrics(
    items: list[dict[str, object]],
) -> dict[_Lang, EmbedPromoteHy1Metrics]:
    """Public wrapper for unit tests - average Hy1 (+ dense) per locale."""
    return _aggregate_locale_metrics(items)


def merge_candidate_baseline(
    *,
    candidate: dict[_Lang, EmbedPromoteHy1Metrics],
    baseline: dict[_Lang, EmbedPromoteHy1Metrics],
) -> tuple[dict[_Lang, EmbedPromoteLanguageMetrics], bool]:
    """Public wrapper for unit tests - nest E0 baseline under each language."""
    return _merge_candidate_baseline(candidate=candidate, baseline=baseline)


def _load_eval_items_for_rebuild(
    conn: Connection,
    *,
    rebuild_run_id: UUID,
) -> list[dict[str, object]]:
    """Items from completed eval runs whose config_snapshot.rebuild_run_id matches."""
    rows = (
        conn.execute(
            text(
                """
                SELECT i.locale, i.metrics
                FROM eval_run_items i
                JOIN eval_runs r ON r.id = i.run_id
                WHERE r.deleted_at IS NULL
                  AND r.status = 'completed'
                  AND (r.config_snapshot->>'rebuild_run_id') = :rebuild_run_id
                """
            ),
            {"rebuild_run_id": str(rebuild_run_id)},
        )
        .mappings()
        .all()
    )
    return [dict(mapping_row(row)) for row in rows]


def _load_baseline_eval_items(conn: Connection) -> list[dict[str, object]]:
    """Latest completed live (non-shadow) golden items for E0 compare."""
    rows = (
        conn.execute(
            text(
                """
                SELECT i.locale, i.metrics
                FROM eval_run_items i
                JOIN eval_runs r ON r.id = i.run_id
                WHERE r.deleted_at IS NULL
                  AND r.status = 'completed'
                  AND (
                    r.config_snapshot->>'rebuild_run_id' IS NULL
                    OR r.config_snapshot->>'rebuild_run_id' = ''
                  )
                ORDER BY r.completed_at DESC NULLS LAST, r.created_at DESC
                LIMIT 500
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(mapping_row(row)) for row in rows]


def build_embed_promote_report(
    engine: Engine,
    *,
    rebuild_run_id: UUID,
) -> EmbedPromoteReportResponse:
    """Load rebuild stamps + optional F36 aggregates into the promote report."""
    with engine.connect() as conn:
        run_row = (
            conn.execute(
                text(
                    """
                    SELECT id, embedding_model_id
                    FROM rebuild_runs
                    WHERE id = :id
                    """
                ),
                {"id": rebuild_run_id},
            )
            .mappings()
            .first()
        )
        if run_row is None:
            msg = f"rebuild run not found: {rebuild_run_id}"
            raise EmbedPromoteReportNotFoundError(msg)
        run = mapping_row(run_row)
        candidate = row_str_optional(run, "embedding_model_id") or DEFAULT_EMBEDDING_MODEL_ID
        candidate_items = _load_eval_items_for_rebuild(conn, rebuild_run_id=rebuild_run_id)
        baseline_items = _load_baseline_eval_items(conn)

    if not candidate_items and not baseline_items:
        return scaffold_embed_promote_report(
            rebuild_run_id=rebuild_run_id,
            candidate_embedding_model_id=candidate,
        )

    candidate_metrics = _aggregate_locale_metrics(candidate_items)
    baseline_metrics = _aggregate_locale_metrics(baseline_items)
    by_language, dense = _merge_candidate_baseline(
        candidate=candidate_metrics,
        baseline=baseline_metrics,
    )
    return EmbedPromoteReportResponse(
        rebuild_run_id=rebuild_run_id,
        candidate_embedding_model_id=candidate,
        baseline_embedding_model_id=LEGACY_E0_EMBEDDING_MODEL_ID,
        dense_available=dense,
        by_language=by_language,
    )
