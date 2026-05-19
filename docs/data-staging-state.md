# Data Staging State

> **Project**: Vecinita  
> **Last updated**: 2026-05-19  
> **Source**: `docs/data-management-plan.md`, `docs/execution-plan.md`

Track asset staging before build tasks with Data Deps run.

| Asset | ID | Status | Verified | Notes |
|-------|-----|--------|----------|-------|
| Seed corpus EN | D1 | verified | 2026-05-19 | `data/fixtures/corpus/en/` |
| Seed corpus ES | D2 | verified | 2026-05-19 | `data/fixtures/corpus/es/` |
| Eval Q&A pairs | D3 | verified | 2026-05-19 | `data/fixtures/eval/qa_pairs.json` |
| Ingest HTML fixture | D4 | verified | 2026-05-19 | `data/fixtures/ingest/sample-page.html` |
| Alembic migrations | D5 | verified | 2026-05-19 | `apps/database/alembic/versions/20260519_0001` |
| FastEmbed weights | D6 | pending | — | Modal volume `embedding-models` |
| Qwen2.5-1.5B-Instruct | D7 | pending | — | Modal volume `llm-models`; 04-tech-plan |

**Gate:** Status must be `verified` before tasks listing the asset in Data Deps column start.
