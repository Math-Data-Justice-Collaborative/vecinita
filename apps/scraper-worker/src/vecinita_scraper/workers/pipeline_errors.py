"""Stable ``error_category`` strings for worker → gateway persistence (FR-014 / US2)."""

from __future__ import annotations

# Align with ``backend/src/services/ingestion/pipeline_stage.py`` where applicable.
ERROR_CATEGORY_TRANSIENT = "transient"
ERROR_CATEGORY_PERMANENT = "permanent"
ERROR_CATEGORY_POLICY = "policy_blocked"
ERROR_CATEGORY_EMBEDDING = "embedding_failed"
ERROR_CATEGORY_EMBEDDING_PARTIAL = "embedding_failed_partial"
