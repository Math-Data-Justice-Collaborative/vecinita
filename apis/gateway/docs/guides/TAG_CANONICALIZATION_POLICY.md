# Tag Canonicalization Policy

This policy defines how Vecinita canonicalizes bilingual metadata tags and how to migrate existing records safely.

## Goals

- Keep a **single canonical tag value** per concept for search/filter consistency.
- Accept English and Spanish tag aliases during ingestion/admin updates.
- Normalize historical tags without changing chunk embeddings.

## Canonicalization Rules

Implemented in `src/utils/tags.py`:

1. Lowercase and trim
2. Strip accents (e.g., `educación` -> `educacion`)
3. Collapse whitespace
4. Map aliases to canonical values via controlled dictionary
   - Examples:
     - `ri` -> `rhode island`
     - `pvd` -> `providence`
     - `inmigracion` -> `immigration`
     - `vivienda` -> `housing`
5. De-duplicate, limit count and length

Canonical output is intentionally stable and language-agnostic (currently English-controlled terms).

## Migration Script

Use `scripts/canonicalize_tags.py`.

### Dry run

```bash
uv run python scripts/canonicalize_tags.py --dry-run
```

### Apply changes

```bash
uv run python scripts/canonicalize_tags.py --apply
```

### Notes

- Sources are updated via `upsert_source`.
- Chunks are updated with **metadata-only updates** (`collection.update`) so embeddings/documents are preserved.
- Affected fields: `tags`, `location_tags`, `subject_tags`, `service_tags`, `content_type_tags`, `organization_tags`, `audience_tags`.

## Reindex Policy

Reindexing is **not required** when only canonicalizing tags because embeddings are unchanged.

Reindex only if:

- You materially changed source text/content,
- You changed chunking strategy,
- You changed embedding model/provider.

## Recommended Rollout

1. Run dry-run in staging and review summary counts.
2. Run apply in staging and validate admin/documents tag filters.
3. Run apply in production during low-traffic window.
4. Spot-check `/api/v1/admin/tags` and `/api/v1/documents/tags` results.
