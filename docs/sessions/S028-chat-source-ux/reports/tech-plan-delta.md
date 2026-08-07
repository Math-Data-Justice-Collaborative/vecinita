# 04-tech-plan delta — EV-026 / F72–F74 (TP locked)

> **Session:** S028-chat-source-ux · **Cycle:** EV-026 · **Date:** 2026-08-06  
> **Status:** **TP1–TP4 locked** (S028-D22) — awaiting plan approve / Gate B→C after 05  
> **Gate A→B:** PASS (S028-D20)

## TP1–TP4 (approved)

| ID | Topic | Choice |
|----|-------|--------|
| **TP1** | Phase / milestones | **Phase 29**: M123 F72 → M124 F73 → M125 F74 → M126 TC/docs gate |
| **TP2** | RD-321 ingest → `display_title` | **Defer** — DocumentAdmin + PATCH/bulk only; no job/upsert title→display |
| **TP3** | F72 URL helper | **`vecinita-frontend-ui`** (`packages/frontend-ui`) helper + export; chat-rag `SourceList` consumes; Vitest in package **and** SourceList |
| **TP4** | F73 + ADR + deps | Wire/verify `min_retrieval_score` on ask `sources[]` + synth (reuse rag `score_threshold`); no pad; CE threshold when on; **ADR-051**; **skip 06**; OpenAPI for PATCH + `display_title` DTO; CORS H0c for `PATCH /documents/{id}` |

## Carry locks (intake)

| ID | Value |
|----|--------|
| F72 | FE display filter only; backend may keep fixture/invalid URLs (RD-310) |
| F73 | `top_k` = max; filter below score; no pad; same set synth+UI (RD-311) |
| F74 | `display_title` + COALESCE; scrape updates `title` only (RD-312/320) |
| Tests | Vitest required; Playwright optional (RD-317) |
| Deploy | Prod-careful; AskQuestion before 12–13 (RD-318 / S028-D2) |
| 03 / 06 | Skipped (RD-319; TP4 reconfirm) |

## Existing stack (04 detect)

| Area | Finding |
|------|---------|
| `SourceList` | Links any truthy `url` — needs http(s) gate |
| RAG | `score_threshold` already on retriever; chat-rag passes `min_retrieval_score` — verify no pad + CE path |
| Write API | GET/DELETE `documents/{id}`; **no PATCH yet**; CORS already allows PATCH |
| Admin | `DocumentAdmin` + bulk metadata; need single-doc rename field |

## Milestones

| M | Focus | Fn | Issue |
|---|-------|-----|-------|
| M123 | Citation URL helper + SourceList | F72 | #222 |
| M124 | Relevance-gated sources (no pad) | F73 | #223 |
| M125 | `display_title` migration + PATCH + admin + packing | F74 | #224 |
| M126 | TC-242–251 + OpenAPI/docs gate | F72–F74 | #222–#224 |

## Artifacts

| Artifact | Path |
|----------|------|
| ADR-051 | `docs/adr/ADR-051-display-title-vs-lock-flag.md` (Accepted at M126 / T126.2) |
| Execution plan | Phase 29 in `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Roadmap | `docs/sessions/S028-chat-source-ux/roadmap.md` |
| This delta | `docs/sessions/S028-chat-source-ux/reports/tech-plan-delta.md` |

## Out of scope (this cycle)

- Ingest/job `title` → `display_title` (RD-321 deferred)
- New Playwright suite (optional only if DocumentAdmin cross-panel needs it)
- New npm/Python deps (06 stays skipped)
- New CORS origins / secrets
- #94 / #217 source-add curation

## Next

1. User **approve** Phase 29 plan (AskQuestion below in chat)
2. **05-verify-tech** (delta audit)
3. Gate **B→C** → **07-build** (06 skipped)
