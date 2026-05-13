# Testing Plan: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker testing strategy will cover four layers: unit tests, integration tests, contract tests, and end-to-end tests. Since the service is **planned** (no existing code), this document defines the testing requirements and infrastructure needed.

## Testing Layers

| Layer | Scope | Tools | Location | CI |
|-------|-------|-------|----------|-----|
| Unit | Individual components (chunker, hasher, schemas) | pytest, pytest-mock | `apps/indexing-worker/tests/unit/` | Every push |
| Integration | Database operations, Modal function execution | pytest, psycopg2, modal | `apps/indexing-worker/tests/integration/` | Every push |
| Contract | Modal function signatures, input/output validation | pytest, pydantic | `apps/indexing-worker/tests/contract/` | Every push |
| End-to-end | Full pipeline: trigger → index → verify vectors | modal run, pytest | `apps/indexing-worker/tests/e2e/` | Pre-deploy |

## Unit Tests

### Chunker Tests (`test_chunker.py`)

| Test | Description | Input | Expected Output |
|------|-------------|-------|-----------------|
| `test_chunk_basic_document` | Chunk a simple document | 1000-token text | ~2 chunks with overlap |
| `test_chunk_empty_document` | Handle empty content | `""` | Empty list |
| `test_chunk_short_document` | Document smaller than chunk_size | 100-token text | 1 chunk |
| `test_chunk_respects_config` | Custom chunk_size and overlap | Text + config | Chunks match configured sizes |
| `test_chunk_preserves_metadata` | Metadata propagated to chunks | Document with metadata | Each chunk has parent metadata |
| `test_chunk_index_sequential` | chunk_index is 0-based sequential | Multi-chunk document | Indices 0, 1, 2, ... |
| `test_chunk_overlap_content` | Overlapping text between adjacent chunks | Long document | Shared tokens at boundaries |

### Hasher Tests (`test_hasher.py`)

| Test | Description | Input | Expected Output |
|------|-------------|-------|-----------------|
| `test_hash_deterministic` | Same content produces same hash | Identical strings | Identical SHA-256 hashes |
| `test_hash_different_content` | Different content produces different hash | Different strings | Different hashes |
| `test_hash_unicode_stable` | Unicode content hashes consistently | Unicode text | Consistent hash |
| `test_compare_changed` | Detect content change | Old hash + new content | `changed=True` |
| `test_compare_unchanged` | Detect no change | Matching hash + content | `changed=False` |
| `test_compare_no_stored_hash` | First-time document (no stored hash) | `None` + content | `changed=True` |

### Schema Tests (`test_schemas.py`)

| Test | Description |
|------|-------------|
| `test_index_document_request_valid` | Valid request passes validation |
| `test_index_batch_request_max_size` | Batch exceeding `INDEX_BATCH_SIZE` raises `ValidationError` |
| `test_rebuild_all_requires_confirm` | `confirm=False` is accepted (validated at function level) |
| `test_indexing_result_serialization` | `IndexingResult` serializes to dict correctly |
| `test_document_error_stages` | `stage` field accepts only valid values |

### Embedder Tests (`test_embedder.py`)

| Test | Description | Mock |
|------|-------------|------|
| `test_embed_returns_correct_dimensions` | Output vectors are 384-dim | Mock fastembed model |
| `test_embed_batch_matches_input_count` | Number of vectors matches number of inputs | Mock fastembed model |
| `test_embed_empty_input` | Empty input list returns empty output | Mock fastembed model |

## Integration Tests

### Database Tests (`test_db.py`)

Require a running PostgreSQL instance with pgvector extension.

| Test | Description |
|------|-------------|
| `test_read_document_by_id` | Read from `data_mgmt.documents` returns expected fields |
| `test_read_document_not_found` | Missing document returns None |
| `test_write_vectors` | Insert vector records into `agent.vectors` |
| `test_write_vectors_upsert` | Re-indexing replaces existing vectors |
| `test_delete_vectors_for_document` | Delete by document_id removes all chunk vectors |
| `test_delete_all_vectors` | Truncate `agent.vectors` for full rebuild |
| `test_upsert_content_hash` | Insert/update content hash record |
| `test_read_content_hashes` | Bulk read hashes for change detection |
| `test_create_indexing_job` | Insert job record with status tracking |
| `test_update_indexing_job` | Update job status and counters |

### Modal Function Tests

| Test | Description | Environment |
|------|-------------|-------------|
| `test_index_document_local` | Run `index_document` locally with `modal run` | Local + test DB |
| `test_health_check_local` | Run `health_check` locally | Local + test DB |

## Contract Tests

Validate that Modal function inputs/outputs match the documented API contract ([08-api-contract.md](08-api-contract.md)).

| Test | Description |
|------|-------------|
| `test_index_document_contract` | Verify return shape matches `IndexingResult` schema |
| `test_index_batch_contract` | Verify batch return includes per-document errors |
| `test_reindex_changed_contract` | Verify skipped_documents count is present |
| `test_rebuild_all_safety_flag` | Verify `confirm=False` produces rejection |
| `test_health_check_contract` | Verify health response shape |

## End-to-End Tests

Run the full pipeline from trigger through vector verification.

| Test | Description | Prerequisites |
|------|-------------|---------------|
| `test_e2e_single_document` | Index one document, verify vectors exist in DB | Test DB with sample document |
| `test_e2e_batch_indexing` | Index 10 documents, verify all vectors | Test DB with 10 documents |
| `test_e2e_selective_reindex` | Change 1 of 5 documents, verify only 1 re-indexed | Test DB with 5 documents + hashes |
| `test_e2e_no_changes` | Run re-index with no changes, verify zero processing | Test DB with up-to-date hashes |
| `test_e2e_full_rebuild` | Rebuild all vectors, verify count matches document count | Test DB with documents |

## Test Infrastructure

### Test Database

```yaml
services:
  test-postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: vecinita_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
```

### Test Fixtures

| Fixture | Purpose |
|---------|---------|
| `sample_document` | A document with known content for deterministic testing |
| `sample_documents_batch` | 10 documents for batch testing |
| `test_db_connection` | PostgreSQL connection to test database with pgvector |
| `seeded_vectors` | Pre-populated vectors for deletion/update tests |
| `seeded_content_hashes` | Pre-populated hashes for change detection tests |
| `mock_embedder` | Mock embedding model returning fixed-dimension vectors |

## CI Integration (Planned)

### GitHub Actions Workflow

```yaml
name: indexing-worker-ci
on:
  push:
    paths:
      - "apps/indexing-worker/**"
  pull_request:
    paths:
      - "apps/indexing-worker/**"

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: vecinita_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
        working-directory: apps/indexing-worker
      - run: pytest tests/unit/ tests/contract/ -v
        working-directory: apps/indexing-worker
      - run: pytest tests/integration/ -v
        working-directory: apps/indexing-worker
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/vecinita_test
```

## Coverage Goals

| Layer | Target | Rationale |
|-------|--------|-----------|
| Unit (chunker, hasher, schemas) | 90%+ | Pure logic, easy to test |
| Unit (embedder) | 80%+ | Mocked model, focus on interface |
| Integration (database) | 80%+ | Critical data integrity |
| Contract | 100% of documented functions | Must match API contract |
| E2E | All happy paths + key failure modes | Confidence for deployment |

## Known Testing Challenges

| Challenge | Mitigation |
|-----------|-----------|
| GPU not available in CI | Mock embedding model in unit tests; use `modal run` for local GPU tests |
| pgvector not in standard Postgres image | Use `pgvector/pgvector:pg16` Docker image in CI |
| Modal function testing | Unit test business logic separately; integration test with `modal run` locally |
| Large batch tests are slow | Limit CI batch tests to 10 documents; larger batches in nightly runs |

## Cross-References

- API contract (test targets): [08-api-contract.md](08-api-contract.md)
- Data models (test fixtures): [02-data-models.md](02-data-models.md)
- Architecture (component boundaries): [07-architecture.md](07-architecture.md)
