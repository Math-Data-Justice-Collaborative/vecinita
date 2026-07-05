# Data Staging State

> **Project**: Vecinita  
> **Last updated**: 2026-06-30  
> **Source**: `docs/data-management-plan.md`, `docs/sessions/S000-internal-docs-archive/execution-plan.md`

Track asset staging before build tasks with Data Deps run.

| Asset | ID | Status | Verified | Notes |
|-------|-----|--------|----------|-------|
| Seed corpus EN | D1 | verified | 2026-05-19 | `data/fixtures/corpus/en/` |
| Seed corpus ES | D2 | verified | 2026-05-19 | `data/fixtures/corpus/es/` |
| Eval Q&A pairs | D3 | verified | 2026-05-19 | `data/fixtures/eval/qa_pairs.json` |
| Ingest HTML fixture | D4 | verified | 2026-05-19 | `data/fixtures/ingest/sample-page.html` |
| Alembic migrations | D5 | verified | 2026-05-24 | `apps/database/alembic/versions/` incl. `20260524_0002` |
| Seed tag vocabulary | D8 | verified | 2026-05-24 | `data/fixtures/tags/seed_tags.json` |
| Tagged corpus fixtures | D9 | verified | 2026-05-24 | `data/fixtures/corpus/tagged/` |
| FastEmbed weights | D6 | verified | 2026-06-30 | **`vecinita`** workspace; volume `embedding-models`; URL `https://vecinita--vecinita-embedding-embedding-api.modal.run`; smoke 384-dim PASS (QA-S006-002 remediation) |
| Qwen2.5-1.5B-Instruct | D7 | verified | 2026-06-30 | **`vecinita`** workspace; deployed `vecinita-llm`; `/health` OK + `test_modal_weights_staged.py` PASS (QA-S006-002 remediation) |

**Gate:** Status must be `verified` before tasks listing the asset in Data Deps column start.

## Modal model volumes (D6, D7)

Operator procedure (QA-003):

1. Authenticate: `modal token new` (or `modal token info` to confirm).
2. **Workspace:** `modal profile activate vecinita` (deploy scripts enforce this automatically).
3. From repo root: `./scripts/stage_modal_weights.sh`
   - Deploys `vecinita-embedding` and `vecinita-llm` unless `VECINITA_STAGE_MODAL_DEPLOY=0`.
   - Runs `modal run …::stage_embedding_weights` and `modal run …::stage_llm_weights` to populate volumes and `commit()` caches.
   - Set `VECINITA_STAGE_SKIP_LLM=1` to stage D6 only.
3. Set `VECINITA_MODAL_EMBED_URL` / `VECINITA_MODAL_LLM_URL` from Modal deploy output (must use **`vecinita--`** prefix, not `fontface--`).
4. Verify: `curl` health + embed length 384; or `uv run pytest tests/smoke/test_modal_weights_staged.py -v`.
5. When live checks pass, set D6/D7 status to `verified` and fill **Verified** date.

See also `infra/modal/README.md`.

