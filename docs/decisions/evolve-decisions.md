# Evolve decisions

## Cycle EV-012 — Scope (S013 / #116)

**Approved:** 2026-07-28  
**Session:** S013-unified-job-monitoring  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/116

### Scope summary

Admin Dashboard unified job monitoring (not ChatRAG). **Modal** owns lifecycle for all
long-running admin jobs (ingest/retag/eval/future) via Modal job queue; Admin Jobs list is
Modal `GET /jobs`. **DO Postgres** is SoT for storage including eval metrics; **Supabase =
auth only**. Detail at `/jobs/:id`; SSE + 4s poll fallback; admin-only full job CRUD; Modal
log affordances on failure. Extend F32/F36; no new Fn. See ADR-038, RD-173–RD-178.

### Decisions (intake + 01)

| ID | Topic | Choice |
|----|-------|--------|
| S013-D1 | S012 artifacts | Leave uncommitted |
| S013-D2 | Scope | v1 + full v2 |
| S013-D3 | Feature identity | Extend F32/F36; no new Fn |
| S013-D4 | Success | Issue #116 ACs as written |
| S013-D5 | v2 items | All: SoT alignment, Modal logs, cancel/retry (+ delete) |
| S013-D6 | Detail UX | `/jobs/:id` |
| S013-D7 | Eval row | Summary + link to eval drill-down |
| S013-D8 | List source | **Amended:** Modal `GET /jobs` primary (not FE dual-list merge) |
| S013-D9 | Out of scope | ChatRAG UI; Langfuse UI not in scope; all long-running admin jobs IN |
| S013-D10 | API risk | Compatible/additive |
| S013-D11 | Privacy | F32 limits; no PII |
| S013-D12 | Cycle size | One cycle EV-012 |
| S013-D13 | Apps | Admin FE + Modal DM + internal-write |
| S013-D14 | Env/secrets | Prefer none new |
| S013-D15 | CORS/VITE | Same Admin SPA |
| S013-D16 | UI preview | Yes — local non-deployed when useful |
| S013-D17 | Job updates | SSE + 4s poll fallback + SSE retry (RD-173) |
| S013-D18 | Acceptance | #116 ACs + extend UJ-023 |
| S013-D19 | E2E | API e2e + Vitest + Playwright T0-ui; live T3 after deploy |
| S013-D20 | Scope approval | Proceed |
| S013-D21 | Preset | Lean (superseded by D22) |
| S013-D22 | Routing | **Lean+build** |
| RD-174 | Job host | Modal for all long-running jobs incl. eval (amend ADR-033) |
| RD-175 | Storage/auth | DO Postgres storage SoT; Supabase auth-only |
| RD-176 | CRUD | Admin-only full job CRUD |

### Architecture amendment (01-requirements)

See ADR-038 and `docs/decisions.md` RD-173–RD-178.

### Close (2026-07-29)

| ID | Topic | Choice |
|----|-------|--------|
| S013-D23 | Merge #153 | Approved; merged @ `6940770` |
| S013-D24 | DO pins | Reset write-api + admin FE to `main` |
| S013-D25 | Close | Complete EV-012; skip optional 15-service-health |


## Cycle EV-014 — Scope (S016 / #87)

**Approved:** 2026-07-29  
**Session:** S016-chat-cold-start-ux  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/87  
**Feature:** F40

### Scope summary

ChatRAG cold-start / long-wait UX: rotating bilingual WRWC/Providence fun facts, soft donate
CTA, friendly consent banner + HTTP cookie opt-out before remembering seen facts in
localStorage. FE `/warm` via existing `prewarmChatServices` only — no Modal/backend work.

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| S016-D1 | Who/when | Community chat; cold-start retries |
| S016-D2 | Problem | Distract/inform with fun facts |
| S016-D3 | Success | Vitest + UI e2e for rotation/content |
| S016-D4 | Flow | Rotate ~4–5s; keep starting-up line |
| S016-D5 | Content | Static EN/ES i18n (no API) |
| S016-D6 | Triggers | Retry **or** slow stream >8s before first token |
| S016-D7 | N | 8 seconds |
| S016-D8 | Warm | FE `/warm` only (prewarmChatServices) |
| S016-D8b | Donate | Secondary CTA under fact → wrwc.org/donate |
| S016-D9 | Remember | localStorage seen-fact ids |
| S016-D9b | Consent | Banner + HTTP cookie opt-out; friendly no-tracking copy |
| S016-D10 | Apps | chat-rag-frontend; shared packages as needed |
| S016-D11 | Env | Optional VITE_WRWC_DONATE_URL w/ default |
| S016-D12 | CORS | None; external donate link; first-party cookie |
| S016-D13 | Timing | Keep retry policy; rotate 4–5s; no new p95 |
| S016-D14 | Acceptance | Facts + CTA + consent/opt-out; Vitest + UI e2e |
| S016-D15 | E2E | T0 Vitest UI e2e; live at 13 if easy |
| S016-D16 | Scope gate | Approve → allocate **F40** |
| S016-D17 | Routing | Lean+build (session open) |

### Docs to update (Phase A)

feature-list (done F40 stub), user-journeys, test-plan, acceptance-criteria, spec (delta),
config-spec if VITE_*, privacy/ADR if cookie consent, 01 seed.

## Cycle EV-015 — Scope (S017 / #167)

**Approved:** 2026-07-30  
**Session:** S017-corpus-reembed-migration  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/167  
**Feature:** F41

### Scope summary

Implement a **safe, repeatable corpus rebuild** (re-embed only; re-chunk + re-embed; full
re-scrape) via Admin Jobs UI + Modal job with a **force** flag (bypass content_hash skip).
Staging dry-run + F36 eval gate; **prod cutover = runbook only** this cycle (no live prod
rebuild). Expands #167 beyond investigation-only (S017-D3). Write boundary: Modal →
internal-write → Postgres (ADR-007).

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| S017-D1 | Session type | `feature` → 16-evolve |
| S017-D2 | Routing | Standard+build (`01→02→04→07→08→09→10→11→12→13`; skip 03, 05, 06) |
| S017-D3 | #167 scope | Expand from investigation-only → **implement** rebuild |
| S017-D4 | Rebuild modes | All three: re-embed / re-chunk+re-embed / full re-scrape |
| S017-D5 | Operator UX | Admin Jobs UI + Modal job + **force** flag |
| S017-D6 | Prod cutover | Staging + F36 gate; prod = runbook only |
| S017-D7 | Fn | Allocate **F41** |
| S017-D8 | Phase gate | Proceed to Phase A (01-requirements) |
| S017-D9 | Mode ops | All three modes in API; **staging runs store-backed** (no live scrape unless rescrape) |
| S017-D10 | Job typing | `job_type=rebuild` + `mode` enum |
| S017-D11 | Dry-run | Shadow dual-write + promote |
| S017-D12 | Scope | Whole corpus default + optional `document_ids` |
| S017-D13 | Versioning | Version stamps + track across revisions; dim dual-write → #159 |
| S017-D14 | Retag | Separate retag job only |
| S017-D15 | Progress UX | Jobs SSE + `/jobs/:id` only |
| S017-D16 | Document store | Postgres `body_text` + `document_revisions` (ADR-040) |
| S017-D17 | Fn packing | Document store folded into **F41** |
| S017-D19 / **TP-S017-01** | Build vs ops (ISS-006) | **Option 2** (2026-07-30): **BUILD** keeps full shadow dual-write + promote + F36-on-shadow in F41 (RD-191 / ADR-040 §3 / 02 M2 / UJ-054 / Admin promote / TC-164–169); **OPS** = live same-settings rebuild as equivalence test. **Amended by TP-S017-07 / S017-D25:** staging this cycle **REQUIRES** full shadow→F36→promote (shadow path exercised, not deferred-unused) **in addition to** live equivalence. Q3 backfill prefer rescrape (reconstruct-from-chunks only w/ operator ack). Specs drafting as 04 artifacts now. |
| S017-D20 / **TP-S017-02** | Shadow schema (Q5) | **Option 1** (2026-07-30): Dedicated `shadow_chunks` + `shadow_embeddings` + `rebuild_runs` table |
| S017-D21 / **TP-S017-03** | Promote cutover (Q6) | **Option 1** (2026-07-30): Transactional copy shadow → live on promote |
| S017-D22 / **TP-S017-04** | F36-on-shadow wire (Q7) | **Option 1** (2026-07-30): Eval enqueue accepts optional `rebuild_run_id` for F36-on-shadow |
| S017-D23 / **TP-S017-05** | Milestone shape (Q8) | **Option 1** (2026-07-30): **Phase 20** with **M86–M90** (store+migration → ingest+backfill → rebuild job → promote+Admin UI → tests/docs) |
| S017-D24 / **TP-S017-06** | Promote OpenAPI (Q9) | **Option 1** (2026-07-30): `POST /internal/v1/rebuild/{id}/promote` → `{promoted, rebuild_run_id, chunks_promoted, documents_promoted}`; Admin FE via corpus API proxy (admin JWT) |
| S017-D25 / **TP-S017-07** | Staging ops (Q10) | **Option 2** (2026-07-30): Staging this cycle **REQUIRES** full shadow→F36→promote (in addition to live same-settings equivalence from TP-S017-01). Ops note: shadow path exercised on staging, not deferred-unused. Amends S017-D19. |
| S017-D26 / **TP-S017-08** | Backfill path (Q11) | **Option 1** (2026-07-30): Backfill via rebuild/job path + Admin control; prefer rescrape; reconstruct-from-chunks only with operator ack |
| S017-D27 / **TP-S017-09** | Dependency policy (Q12) | **Option 2** (2026-07-30): Allow minor deps in 07 if needed; flag in dependency-inventory |

### 02-verify-plan verdicts (2026-07-30)

| ID | Verdict | Decision |
|----|---------|----------|
| M1 | Approve fix | TC-166 mapped under UJ-053 |
| M2 | Lock | F36 against shadow **before** promote |
| M3 | Modify | Admin UI **promote** + **full build this session** |
| M4 | Approve | One-time corpus **backfill** in F41 |
| M5 | Defer | deployment-integration / data-flow → **04-tech-plan** |
| M6 | Approve | Promote auth = **`admin`** (enqueue parity) |

### Docs to update (Phase A)

feature-list (F41), user-journeys (UJ-053–054), test-plan (TC-161–169), acceptance-criteria
(AC-RB*), spec/api-contract/config-spec delta, ADR-040, runbook outline, decisions RD-188+.
