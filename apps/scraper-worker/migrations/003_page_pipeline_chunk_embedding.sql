-- Feature 012: traceable chunk text (**FR-005**) + idempotent embeddings per chunk+model (**data-model** idempotency).

ALTER TABLE chunks ADD COLUMN IF NOT EXISTS raw_text TEXT;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS enriched_text TEXT;

UPDATE chunks SET raw_text = chunk_text WHERE raw_text IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_embeddings_chunk_id_model_name
    ON embeddings (chunk_id, model_name);
