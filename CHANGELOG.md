# Changelog

## [0.3.0] — 2026-05-27

### EV-002: Admin Dashboard, Bulk Ops, Usage Stats, Audit Log (F23–F28)

**Features:**
- **M23–M28**: Admin UI overhaul (Tailwind + React Router), summary stats dashboard, system health aggregator, bulk corpus operations, serving statistics, audit log & document version history
- **Alembic** `20260526_0003`: `audit_log`, `document_versions`, `document_serving_stats`
- **Deploy** (TP-029): migration → internal-write-api → chat-rag-backend → admin frontend @ `0a2f813` (`evolve/EV-002-admin-overhaul`)

**Smoke validation (staging):**
- H1–H3b, T3 admin API (4/4), H4–H5 connectivity — all pass; Modal H4 waiver retained

## [0.2.0] — 2026-05-25

### EV-001: Corpus Tags, Community Browse, Admin Chunk/Tag Editing (F19–F22)

**Features:**
- **M15**: Tag schema & fixtures — Alembic migration (tags, document_tags, chunk_tags), seed tag vocabulary (D8), tagged corpus fixtures (D9)
- **M16**: Ingest tagging — LlmTagClient, ingest pipeline LLM tagging step, batch tag upsert, retag job worker
- **M17**: Public browse API — `GET /api/v1/documents`, `/api/v1/tags`, tag-filter RAG, ChatRAG frontend browse UI
- **M18**: Admin chunk viewer — tag editor PATCH routes, admin CORS preflight
- **M19**: Staging connectivity — browse smoke tests, EV-001 deploy scripts

**Fixes (deploy-time):**
- Tag inference prompt now uses Qwen2.5-Instruct chat template (was producing verbose text instead of JSON)
- Graceful fallback in `resolve_retrieval_tags` — tag inference failure no longer breaks ask route
- Retrieval fallback to unfiltered search when tag-filtered query yields empty results

**PRs:**
- [#39](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/39) M16 ingest tagging
- [#40](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/40) M17 browse + tag RAG
- [#41](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/41) M18 admin tags
- [#42](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/42) M19 deploy connectivity
- [#43](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/43) EV-001 merge to main

### Hotfixes (post-v1, pre-EV-001)

- Chat cold-start retry and warm-up UX (Modal LLM scale-to-zero transient failures)
- GET /jobs/{id} 404 — shared modal.Dict job store (#36)
- Starlette bump to 1.0.1 (PYSEC-2026-161)
- CI fixes: ripgrep, ruff SIM300/F401, pyright vllm kwargs

## [0.1.0] — 2026-05-20

Initial v1 deployment — bilingual community Q&A RAG + data management (5 apps, hybrid DO/Modal).
