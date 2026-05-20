# Config Validator (Vecinita)

Validates that settings and API payload fields in code match `docs/config-spec.md`.
Use when adding query/ingest parameters, defaults, validation rules, or admin config.

## State management

Read repo-root [`workflow-state.yaml`](../../workflow-state.yaml) §`template` and
§`stages.config-validator` before validating. After a validation pass invoked as part of
03-plan-tooling or evolve, set §`stages.config-validator.status` and log drift in `issue_log`.
Rules: [workflow-state-reference.md](../workflow-state-reference.md).

## Triggers

- New env var or settings field in `src/config.py`
- Query/ingest request body fields in `src/api/`
- Changing chunking or retrieval defaults

## Validation checks

### 1. Parameter existence

Every user-facing field must appear in `docs/config-spec.md`. Undocumented fields → `[Scope Drift]`.

### 2. Example RAG parameters (adjust to spec)

| Parameter | Spec type | Notes |
|-----------|-----------|-------|
| `collection_id` | str | Target corpus collection |
| `query` | str | User question |
| `top_k` | int | Retrieval count |
| `chunk_size` | int | Ingest chunk tokens/chars |
| `chunk_overlap` | int | Overlap between chunks |
| `embedding_model` | str | Must match DB vector dimension |
| `max_context_tokens` | int | Prompt budget |
| `include_sources` | bool | Return citations in response |

### 3. Defaults

Defaults in code must match config-spec. Mismatch → `[Contradiction]` with section cite.

### 4. Validation rules (typical)

- `top_k` >= 1
- `chunk_size` > `chunk_overlap` >= 0
- `query` non-empty for `/query`
- `collection_id` exists (or 404 at runtime)

### 5. Precedence

Document order in config-spec (e.g. request body > env defaults). Secrets only via env/platform — never in repo.

## Output

- **PASS** — types, defaults, rules aligned
- **FAIL** — list code vs spec per field

## References

- `docs/config-spec.md`
- `docs/api-contract.md`
- `docs/feature-list.md`
