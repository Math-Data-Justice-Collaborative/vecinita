# 01-requirements seed — S028 / EV-026 (#222 #223 #224)

**Purpose:** Handoff so **01-requirements** loads locked Phase 0–1 decisions and only
interviews **open questions** — not a greenfield re-litigation.

**Status:** Ready for 01-requirements  
**Session:** `S028-chat-source-ux`  
**Cycle:** EV-026 · Features **F72, F73, F74**  
**Mode:** `delta`  
**Sources:** [session-brief.md](../session-brief.md) · [evolve-decisions.md §EV-026](../../../decisions/evolve-decisions.md) · S028-D1–D17  
**Branch:** `feat/S028-chat-source-ux` @ `c81dbcc`

---

## How 01-requirements should use this

1. `read_context` → `active_session=S028-chat-source-ux`, stage `01-requirements`, mode delta.
2. Load this seed + EV-026 scope in `docs/decisions/evolve-decisions.md`.
3. **Confirm Locked decisions** in one AskQuestion (approve all / modify IDs).
4. Ask **only Open questions** below.
5. Allocate RD numbers starting at **RD-309** (after RD-308). New ADR only if 01 finds a
   multi-option architectural fork (candidate: ADR-051 display_title vs lock flag — already
   decided as separate column → likely RD-only).
6. Write **delta** sections to standing docs in the Document Manifest; session report
   `reports/01-requirements-chat-source-ux.md`.
7. Next routing stage: **02-verify-plan**.

---

## Locked decisions (confirm only)

| Seed ID | Session ID | Decision | Proposed RD |
|---------|------------|----------|-------------|
| S1 | S028-D4/D16 | Fn: **F72**=#222, **F73**=#223, **F74**=#224 | RD-309 |
| S2 | S028-D6 | F72: ChatRAG FE only — `<a href>` for valid absolute http(s); backend keeps URLs for tests; title shown without link when invalid | RD-310 |
| S3 | S028-D9 | F73: `top_k` = max; drop below `min_retrieval_score` (+ CE/rerank threshold if enabled); no pad; synthesis + UI same filtered `sources[]` | RD-311 |
| S4 | S028-D10 | F74: separate **`documents.display_title`**; scrape always updates raw **`title`** | RD-312 |
| S5 | S028-D11 | F74: DocumentAdmin **single-doc rename** + keep bulk metadata; chunks inherit display name; optional ingest title if cheap | RD-313 |
| S6 | S028-D8 | Curation in-cycle = F74 title edits only — **not** #94/#217 source-add | RD-314 |
| S7 | S028-D12/D15 | Compatible API preferred (`display_title` nullable; chat `sources[].title` = display string). If breaking unavoidable → **major version bump** | RD-315 |
| S8 | S028-D13 | Apps: chat-rag-frontend; packages/rag + chat-rag-backend; internal-write-api + migration; data-management-frontend. No new secrets/CORS expected | RD-316 |
| S9 | S028-D14 | Tests: Vitest URL; unit+e2e filtered sources; API+admin display_title; eval note few-strong vs many-weak; T0 smoke only if 12–13 approved | RD-317 |
| S10 | S028-D2/D7 | Prod-only careful; build+verify; **AskQuestion before 12–13** / corpus mutation | RD-318 |
| S11 | S028-D1/D17 | Feature preset routing; skip 03/06 unless tech plan finds need; Phase 1 impact approved | RD-319 |

---

## Document manifest (delta)

### Mandatory

| Document | Action | Sections |
|----------|--------|----------|
| `docs/feature-list.md` | Add F72–F74 | Summary rows + detail sections |
| `docs/user-journeys.md` | Add UJ-077–079 (proposed) | Citation URL display; dynamic sources; admin rename display title |
| `docs/test-plan.md` | Add TC-242+ | Map UJ ↔ Vitest / API e2e / integration |
| `docs/acceptance-criteria.md` | Add AC-SU* | Per-Fn AC |
| `docs/api-contract.md` | Delta | `display_title` on document DTOs; single-doc rename; bulk metadata; `sources[]` length 0…top_k semantics |
| `docs/config-spec.md` | Delta | `top_k` as max; filter vs `min_retrieval_score` |
| `docs/spec.md` | Delta | Schema column; citation packing display name |
| `docs/decisions.md` | Append | RD-309+ under EV-026 |

### Recommended

| Document | Action | Rationale |
|----------|--------|-----------|
| `docs/runbooks/corpus-operator-guide.md` | Delta | Operator rename / display_title |
| `docs/CORPUS.md` | Touch if new row needed | Only if new standing doc |
| OpenAPI yaml | Delta in 07 | Mirror api-contract |

### Excluded

| Document | Why |
|----------|-----|
| ADR-048 / embed docs | Unrelated |
| Full greenfield templates | Delta only |
| #94 / #217 data ingest epic | OOS (S028-D8) |

---

## Proposed journeys / tests (pre-filled)

| UJ | Feature | Layer |
|----|---------|-------|
| UJ-077 | F72 — citation shows link only for valid http(s) | Vitest `SourceList` (+ optional Playwright if shell interaction needed — prefer Vitest) |
| UJ-078 | F73 — ask returns 0…top_k sources by relevance; no pad | API e2e + unit retrieval filter |
| UJ-079 | F74 — admin sets `display_title`; ask/citation uses it | API integration + admin Vitest; Playwright if DocumentAdmin form ↔ list cross-panel |

| TC range (proposed) | Coverage |
|---------------------|----------|
| TC-242–244 | F72 valid/invalid/missing URL display |
| TC-245–247 | F73 filter / empty / max cap |
| TC-248–251 | F74 PATCH display_title, fallback, rescrape preserves display_title, citation |

---

## Open questions (01 interview only)

| OQ | Topic | Recommended |
|----|-------|-------------|
| OQ1 | F74 single-doc API | **New or extend** `PATCH /internal/v1/documents/{id}` with `{display_title}` (+ optional clear/reset); bulk keeps F27 path |
| OQ2 | F74 null `display_title` | Citations/admin use **`COALESCE(display_title, title)`** |
| OQ3 | F74 reset-to-scraped | Explicit **clear display_title** (null) → fall back to `title`; no separate “reset” endpoint required |
| OQ4 | F74 audit | Emit **`document.edited`** (or existing equivalent) with before/after including `display_title` |
| OQ5 | F72 validator | Absolute **`http:` / `https:`** only; reject relative, `javascript:`, `fixture://`, empty |
| OQ6 | F73 CE off | When CE/rerank disabled, filter is **`min_retrieval_score` only** (dense score) |
| OQ7 | F74 ingest title | **Include** optional `title`→`display_title` on job/upsert if low cost; else defer to 04 |
| OQ8 | Playwright | **Vitest required** for F72/F74 UI; Playwright only if DocumentAdmin rename is cross-component (list↔detail) — default **Vitest + API e2e**, Playwright optional |

---

## Explicitly out of interview scope

- Re-deciding F72 FE-only vs ingest rejection
- Adding #94/#217 source curation this cycle
- LLM-generated titles
- Community end-user title editing
- Prod deploy without AskQuestion
- Changing default `top_k=8` as a *target* (remains max)

---

## Next after 01

**02-verify-plan** (delta consistency pass on changed sections).
