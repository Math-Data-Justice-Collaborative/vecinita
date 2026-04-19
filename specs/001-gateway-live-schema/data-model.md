# Data model (conceptual): Render persistence + Modal payloads

Entities describe **logical** responsibilities after the architecture split. Field lists are
illustrative; implementation refines types in Pydantic models and OpenAPI components.

## Modal-side (ephemeral, no Postgres)

### `ModalEmbeddingBatchResult`

- `embeddings`: list of vectors or base64-encoded floats  
- `model`: string  
- `dimension`: int  
- `request_id`: optional correlation id  

### `ModalGenerationResult`

- `text` or structured chat payload  
- `finish_reason`, `usage` (tokens)  
- `request_id`  

### `ModalScraperChunkBatch`

- `job_id`: string  
- `chunks`: list of `{content, metadata, source_url, …}`  
- `cursor` / `done`: bool for pagination  
- `stats`: optional counters  

**Rule**: None of the above entities imply a DB connection on Modal; they are **transport DTOs**.

## Render-side (durable)

### `PersistedDocumentChunk`

- Maps from `ModalScraperChunkBatch.chunks` + ingestion policy  
- Surrogate keys, `document_id`, `chunk_index`, timestamps  

### `GatewayJobRecord` (scrape / modal-job registry)

- Existing job manager / registry tables as today; **only** mutated from Render code paths.

## Relationships

- `ModalScraperChunkBatch` **1—N**→ `PersistedDocumentChunk` (via gateway persist transaction)  
- `GatewayJobRecord` **updated** after Modal returns terminal status payload (no Modal DB read)

## Validation

- Idempotency: `(job_id, chunk_index)` or content hash prevents duplicate inserts on retries.  
- Max batch size enforced at gateway before DB write to protect Postgres.
