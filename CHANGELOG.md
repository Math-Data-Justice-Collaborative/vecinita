# Changelog

## [Unreleased]

### EV-019: Ingest resilience (F47–F49) — S022 / #163 #166 #160

- **F47**: `content_hash` skip on unchanged URL re-ingest (`force` bypass)
- **F48**: Embed sub-batch + retry on transient Modal embed failures
- **F49**: HF tokenizer chunk overlap (default 32); ADR-044
- **Deploy:** PR [#179](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/179) → `main` @ `bd6bb00` (Path A H1–H5 PASS; Path B rechunk waived → follow-up)

### EV-018: Retrieval follow-on (F46 + F45 re-gate) — S021 / #83

- **F46**: Corpus DB guard against staging `basis_vector` wipe; Path B E0 restore on staging; UJ-061 non-empty retrieve
- **F45**: AC-BB9 CE ship gate **PASS** after F46; prod `VECINITA_RAG_RERANK_CE` remains **false** until separate approval
- **Deploy:** PR [#174](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/174) → `main` @ `9d1f10b` (Path A; H1–H5 PASS)
- **RET-001:** ADR-043 session handoff / safe-stops; RA-001–007 skill patches (fewer chats, digest + `HANDOFF.md`, state-update batching, CE metrics≠flag, BUG/14/07 ownership)

### EV-014: ChatRAG cold-start wait UX (F40) — S016 / #87

- Rotating bilingual fun-fact/info messages during cold-start / slow first token
- Soft donate CTA + cookie/localStorage consent (ADR-039)
- ChatRAG FE only (no Modal/backend change)
- **PR:** [#157](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/157) → `main` @ `82ad84e`

### EV-012: Unified Admin Jobs (F32/F36) — S013 / #116

- Modal-primary Jobs API: extras, admin cancel/retry/delete, `GET /jobs/events` SSE
- Eval enqueue bridge + soft-delete (`eval_runs.deleted_at`); Admin `/jobs` + `/jobs/:id`
- ADR-038 Modal lifecycle / DO storage split; Phase 19 M82–M85
- **PR:** [#153](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/153) → `main` @ `6940770`

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
