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

## Cycle EV-016 — Scope (S019 / Batch A retrieval)

**Approved (session open):** 2026-07-31  
**Session:** S019-retrieval-quality  
**Issues:** #158, #161, #165, #162 (investigation); #83 parent if rerank ships  
**Feature:** F42 (deferred until F36 spike picks winner)

### Scope summary

**Investigate → ship:** Run F36 ablations across top_k (#158), rerank (#161→#83), context
packing (#165), and soft language filter (#162). Pick winners; allocate **one Fn (F42)**;
ship **at most one** change on `packages/rag` + ChatRAG prompt assembly. If rerank wins,
ship a **cheap** slice only; leave full #83 open. Do not pull #82 / #84 / full #76.

### Decisions (session open)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D1 | Session type | `feature` → 16-evolve |
| S019-D2 | Routing | **Standard** (`01→02→04→07→08→09→10→11→12→13`; skip 03, 05, 06) |
| S019-D3 | #162 | Include in investigation set |
| S019-D4 | Shape | Spike F36 first → recommend → allocate F42 → build |
| S019-D5 | Rerank win | Cheap slice this cycle; #83 remains parent |

### Decisions (Phase 0 intake lock — 2026-07-31)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D6 | Success | F36 golden lift vs dense-only baseline + **Admin playground promote-path smoke** |
| S019-D7 | Spike env | Local / unit+eval fixtures first; staging F36 job only if local lift unclear |
| S019-D8 | Cost/latency | Prefer config/prompt/heuristic; new models self-hosted (ADR-009) + Modal cost in report; **cross-encoder on Modal OK if F36 lift clear** (A+C) |
| S019-D9 | Lock scope → spike plan → F36 baseline |
| S019-D10 | Unblock A0 via **staging** F36 / staging corpus (option B; local Docker deferred) |
| S019-D11 | Next = A2 packing now; ISS-008 Admin staging fixture = F42 ship prereq |
| S019-D12 | Continue spike — A4 cheap rerank (R1/R2); F42 deferred (relevancy still low; P1 > P3) |

### Phase 0 status

A0–A4(+R3) + A3 complete. R3 rejected. F42 still deferred. **Model sweep:** Tiny + S1/S2
AWQ all tied @ relevancy 0.23; **S019-D20** playground **A100-80GB** for non-AWQ / larger
MoE (S3+). ISS-008 remains open (F42 ship prereq).
See session `model-sweep-plan.md` / `model-sweep-tracker.md`.

### Model sweep extension (2026-07-31)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D15 | Extend Phase 0 | Add ordered open-LLM ladder (Tiny→Large); track in session; **F42 not allocated** until ship lock |
| S019-D16 | Fixed RAG cell (Gate A=1) | Staging golden + **R0** + **P1** packing + control **`qwen2.5:1.5b-instruct`** |
| S019-D17 | Hosting policy (Gate B=4) | Self-host everything in order via Modal; fail/skip per model with cost logged (**no API**). Playground **T4** today — Tiny first; larger models attempt then skip on OOM/pull failure |
| S019-D18 | Queue confirm (Gate C=1) | Approve deduplicated queue **T1→L4** as in `model-sweep-tracker` |
| S019-D19 | Playground GPU + AWQ (Option B / ask 3) | Playground-only **A10** (~$1.10/hr) + **AWQ 4-bit** for Small+; S1 re-verify tag **`qwen3.6:27b-awq`** → `QuantTrio/Qwen3.6-27B-AWQ`; prod `vecinita-llm` stays **T4**; prior S1 T4 metrics **invalid**; F42 not allocated. **Risk:** image pins `vllm>=0.8.5,<0.9`; QuantTrio recommends ≥0.19 for Qwen3.6 — warm may fail → bump playground image or fall back to A100-80 |
| S019-D20 | Playground GPU upsize (ask C) | After S1/S2 AWQ ties: playground → **A100-80GB** (~$2.50/hr) for **non-AWQ** dense 27B + larger MoE (S3+); prod stays T4; F42 still not allocated. Note: BF16 35B-A3B ~70GB — may need FP8/AWQ even on A100-80 |

### Phase 0 extension — batch 1 lock (2026-07-31)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D21 | Model lock | Keep synthesizer **`qwen2.5:1.5b-instruct`** (prod pin); **stop model sweep** — skip M1+ (all Tiny–S3 tied @ relevancy 0.23) |
| S019-D22 | F42 allocation | **F42 = P1 packing** (#165) now; Standard build path for packing ship |
| S019-D23 | Harness timing | Caching / LangGraph harness = **separate Phase 0 spike** (may become F43 later); does not block F42 packing allocation |
| S019-D24 | LangGraph intent | **Intend to ship LangGraph into ChatRAG** — requires **ADR-006 amendment** (+ ADR-004 check for checkpoints). Spike first under eval/playground; ship only after amend + Phase A specs |
| S019-D25 | Caching spike primary | Test **A** (retrieval/embed cache + prompt/KV reuse) **and B** (ephemeral LangGraph checkpoint / short-term memory, sessionless) **plus pre-cached answers**; run **≥6 named configs** in harness matrix (see `spike-harness-cache.md`) |
| S019-D26 | Playground GPU | Drop playground back to **T4** (enough for 1.5B lock); prod stays T4 |
| S019-D27 | ADR-006 path | **Spike H0–H9 first** (eval-only); **defer ADR-006 amend** until data justifies LangGraph ship (softens rush on D24) |
| S019-D28 | Harness matrix expand | Bump to **10 configs (H0–H9)**; add intent classification, sub-agents, answer classification; **distinct LangGraph state schemas S0–S8** (see `spike-harness-cache.md` idea catalog + matrix) |

### Phase 0 status (post D21–D28)

Model sweep **closed**. **F42 = P1 packing** allocated (ISS-008 gates promote smoke). Harness spike expanded to **H0–H9** (cache + intent/answer class + sub-agent workflows, schemas S0–S8) — eval-only; ADR amend deferred (D27). Playground → T4.

### Phase 0 hybrid iterate (2026-08-01)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D29 | Hybrid option | **A — Measure then ship**: run Hy0–Hy4 (+ HyLang0 L0+P1, HyK8 top_k=8+P1); freeze F42 after results; F43 cache later unless dual approved |
| S019-D30 | Hybrid metrics | Add **EN/ES locale breakdown**, **answer_lang_match_rate**, **mean_cross_lang_share**, context chars / docs; Spanish-aware H7 rewrites |
| S019-D31 | Hybrid result → F42 | Sweep `20260801T002819Z`: **F42 = H7+P1** (relevancy 0.31 / faith 0.91); drop R1; P3 not default; HyK8 no lift; es_rel=0 (n=2) follow-on; `phase0_approved` still pending AskQuestion |
| S019-D32 | No-prompt baselines | Re-open Phase 0 measure: per-model **bare** (empty system prompt) vs pack/prompt/H7 lifts; default models = control + Tiny (T4); judges pinned 1.5B; `phase0_approved` still false |

Plan: session `reports/spike-hybrid-plan.md` · runners `spike_hybrid_sweep.py`, `spike_model_prompt_baseline.py`.

### Phase 0 expansion — path 2+3+4 (2026-08-01)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D33 | Phase 0 expand before `phase0_approved` | **2+3+4**: (2) fix **ISS-008** Admin staging golden; (3) expand **Spanish golden + judge** coverage; (4) spike **#159 multilingual embeddings** + staging re-embed via F41. `phase0_approved` stays false until 2–4 land evidence. F42 = H7+P1 still the ship candidate; embed swap may amend F42 / add Fn if lift clears. |

**Order:** ISS-008 → ES golden/judge → #159 embed spike (prefer **384-d** FastEmbed candidates to avoid dim migration) → re-AskQuestion `phase0_approved`.

| ID | Topic | Choice |
|----|-------|--------|
| S019-D34 | ES + embed spike params | **A+B**: ingest more `vecina.wrwc.org/es/*` into staging, then expand ES golden (≥6 scored). **E0+E1+E2**: measure `bge-small-en-v1.5` vs `multilingual-e5-small` vs `paraphrase-multilingual-MiniLM-L12-v2` (all 384-d); defer bge-m3 / dim change. |
| S019-D35 | #159 spike result | Offline hit@5: E0=E1=1.00, E2=0.87 (reject E2). E1 better rank@1 (0.73 vs 0.60). **Do not fold embed swap into F42**; keep F42=H7+P1 on E0. Keep #159 open for optional F41 shadow + F36 LLM on E1. ES A+B ingest+golden **keep**. |
| S019-D36 | E1 F36 before Phase A | User chose path **2**: run **E1 F41 shadow + Hy1 F36 LLM** vs E0 live **before** `phase0_approved`. F42 default stays H7+P1/E0 unless E1 clears relevancy lift without EN regression. |
| S019-D37 | E1 F36 result + `phase0_approved` | Shadow `1fa1dec9…` + `20260801T130441Z_e1-shadow-f36.json`: E1_Hy1 relevancy **0.11** vs E0_Hy1 **0.28** (EN −0.27, ES flat). ES retrieval ↑ but **no ship**. F42 remains **H7+P1 on E0**; #159 stays open (not F42). **User approved Phase 0 (option 1)** → Phase A `01-requirements`; ISS-008 deploy remains ship-path prereq. |

### Phase 0 closed — Phase A entry (2026-08-01)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D37 (lock) | `phase0_approved` | **Yes** → `01-requirements` for **F42 = H7+P1 on E0**. Do **not** ship E1/F41. Rebuild `1fa1dec9…` not promoted. Prod embed pin `BAAI/bge-small-en-v1.5` unchanged. |

**Ship scope (locked):** P1 context packing (#165) + thin H7 multi-query fan-out; no LangGraph / ADR-006; R1/CE/#162/cache out of F42.

### Phase A — 01-requirements (2026-08-01)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D38 | Document Manifest | Mandatory + Config Spec + Acceptance Criteria; skip API Contract |
| S019-D39 | F42 Feature List / Spec | H7 default on; P3 non-default (`p3` packer); E0 embed; shared `packages/rag` |
| S019-D40 | Journeys / tests / AC | UJ-055/056; TC-170–175; AC-RQ1–RQ7; Hy1 ship floor 0.28/0.91 |
| S019-D41 | Config knobs | `VECINITA_RAG_MULTI_QUERY` (+ count), `VECINITA_RAG_PACKER`, `VECINITA_RAG_CONTEXT_MAX_CHARS` |
| S019-D42 | 02 M1–M3 | H7 = cheap heuristic rewrites (not LLM); Hy1 0.28/0.91 staging ship gate; p95 &lt;15s unchanged |

### Phase B — 04-tech-plan (2026-08-01)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D43 | Tech plan shape | Phase 21 **M91–M93**; skip dep inventory / data-mgmt / new deploy topology |
| S019-D44 | ADR-041 | Heuristic H7 + P1 packing; no LangGraph / ADR-006 amend; E0 pin unchanged |

### Phase D — 12-verify-deploy (2026-08-01)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D48 | 12 failure mitigations | **Approve all** (option 1) — build/CI, Modal URL verify, ISS-008-before-Hy1, H7 kill switch, H4–H5, hold on Hy1 miss |
| S019-D49 | 12 rollback plan | **Approve** (option 1) — `VECINITA_RAG_MULTI_QUERY=false` and/or redeploy prior DO SHA (`a6c39e5`); no embed rollback |

**12 complete:** checklist **ready** → `docs/sessions/S019-retrieval-quality/reports/deploy-checklist.md`. Next: **13-deploy-smoke** (ISS-008 + Hy1 AC-RQ6).

### Phase D — 13-deploy-smoke AC-RQ6 (2026-08-01)

| ID | Topic | Choice |
|----|-------|--------|
| S019-D50 | AC-RQ6 disposition | **Investigate/fix** (option 1) — not waive / not rollback |
| S019-D51 | Hy1 false zeros | Direct YES/NO answer-relevancy judge (mirror faithfulness); H7 ES rewrite + spike→`packages/rag` parity |
| S019-D52 | Hy1 re-gate | **PASS** — relevancy **0.833** / faith **0.938** (`20260802T022836Z`); Path A @ `5693422` |

**13 status:** Path A + H1–H5 + AC-RQ6 PASS — **closed**.

| ID | Topic | Choice |
|----|-------|--------|
| S019-D53 | Session close | **Close now** (option 1) — skip optional 15-service-health; write evolve-summary + evolve-report-EV-016; archive S019; leave out-of-scope Modal/LLM dirty files alone |

**Closeout:** PR [#172](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/172) merged @ `b08ec30` (2026-08-02). Session `S019-retrieval-quality` archived; cycle EV-016 completed.

## Cycle EV-017 — Scope (S020 / Retrieval Batch B)

**Approved (session open):** 2026-08-02  
**Session:** S020-retrieval-batch-b  
**Predecessor:** S019 / EV-016 (F42 LIVE)  
**Issues:** #83, #161 (CE spike), #162 (soft language); **F43** answer/retrieval cache  
**Branch:** `evolve/EV-017-retrieval-batch-b`

### Scope summary

**Batch B — multi-track:** Ship **F43** answer/retrieval cache (H1/H9 cost win; no LangGraph).
Keep **#83 / #161** CE rerank as spike-gated track (prior R3 failed lift). Include **#162**
soft language filter in the same cycle (optional / empty-hit; not proven on staging golden).

### Decisions (session open)

| ID | Topic | Choice |
|----|-------|--------|
| S020-D1 | Session | Open **S020-retrieval-batch-b** (do not reopen S019) |
| S020-D2 | Scope | **All three** tracks in one cycle (F43 + CE spike + #162) |
| S020-D3 | Routing | **Standard** (`01→02→04→07→08→09→10→11→12→13`; skip 03, 05, 06, 15) |

### Decisions (Phase 0 intake batch 1 — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S020-D4 | F43 cache tiers | **Full H1 cascade** — exact → semantic answer → retrieve-result → generate |
| S020-D5 | #83 / #161 CE | **Spike + ship gate** — no prod CE unless gate passes |
| S020-D6 | #162 soft language | **Config-gated L1** (default off) + empty-hit fixture |
| S020-D7 | Fn ids | **Pre-allocate F43** (cache) + **F44** (#162) + **F45** (CE) as Planned |

| S020-D8 | Proceed gate | **Allocate F43–F45 + finalize impact + start 01-requirements** |

### Decisions (01 Phase 0C — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S020-D9 | Locked L1–L12 | **Approve all** |
| S020-D10 | Semantic cache | **Conservative** cosine; miss → retrieve; log hits; quality ≥ H0 |
| S020-D11 | CE spike model | **`BAAI/bge-reranker-v2-m3`** on Modal T4 |
| S020-D12 | CE ship floors | Relevancy ≥ **0.28** and faith ≥ **0.91** (Hy1 staging floors) |
| S020-D13 | Deploy | Staging **Path A** (write-api + chat-rag) |
| S020-D14 | Cache lifecycle | **TTL + size cap**; bust on corpus version / F41 rebuild |

### Decisions (02-verify-plan medium closeout — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S020-D15 | Medium M1–M4 | **Approve all** — semantic threshold **0.92**; cache TTL=**3600s** / max_entries=**1024**; CE spike ephemeral Modal T4 (ChatRAG never playground URL); OpenAPI `cache_hit` in **07-build** |

### Decisions (Phase A checkpoint + 04-tech-plan — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S020-D16 | Phase A checkpoint | **Continue to Phase B** / start 04-tech-plan |
| S020-D17 | Tech plan TP1–TP7 | **Approve all** — Phase 22 M94–M98; ADR-042; reuse query embed; CE ephemeral T4 + mock CI; F43→F44→F45; no new ChatRAG deps; skip topology rewrite |

### Phase A / B status

Phase 0 **approved**. 01 locked (D9–D14). 02 **completed** (D15). Gate A→B **passed** (D16).  
04-tech-plan artifacts drafted (D17). Next: **Gate B→C** → 07-build.

---

## Cycle EV-018 — Scope (S021 / Retrieval follow-on)

**Approved (session open + Phase 0 Fn lock):** 2026-08-02  
**Session:** S021-retrieval-follow-on  
**Predecessor:** S020 / EV-017 (F43/F44 LIVE; F45 spike-only @ `f24a620`)  
**Issues:** empty retrieve pools (staging); #83 / #161 (CE re-gate); AC-BB9 / UJ-060 / TC-184  
**Features:** **F46** (retrieve reliability) + **F45** (CE re-gate extension)  
**Branch:** `evolve/EV-018-retrieval-follow-on`

### Scope summary

Fix staging **empty retrieve pools** (`pool=0` / empty `sources`) that invalidated the EV-017
CE ship gate, then **re-run** AC-BB9 / UJ-060 with non-empty context. Ship #83 / enable prod CE
only if floors pass; otherwise keep spike-only.

### Decisions (session open — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S021-D1 | Session | Open **S021-retrieval-follow-on** (do not reopen S020) |
| S021-D2 | Scope | **Empty retrieve + CE re-gate** in one cycle |
| S021-D3 | Routing | **Standard** (skip 03, 05, 06, 15) |
| S021-D4 | 00-context | **Scoped delta** |
| S021-D5 | EV-018 | Allocated in Phase 0 (not at 00 open) |
| S021-D6 | CE floors | Relevancy ≥ **0.28**, faith ≥ **0.91** (carry S020-D12) |
| S021-D7 | Prod CE flag | Stay **false** until re-gate + deploy approval |

### Decisions (Phase 0 Fn allocation — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S021-D8 | Fn ids | **F46** retrieve reliability + **extend F45** CE re-gate |
| S021-D9 | Ordering | **F46 first**, then F45 re-gate (same cycle; two milestones) |
| S021-D10 | Shape | Planned Fn work in evolve (not nested 14-hotfix) unless root cause is trivial one-liner |
| S021-D11 | Deploy default | Staging **Path A**; escalate to Path B only if corpus rebuild required |
| S021-D12 | Proceed gate | Create EV-018 + impact → start **01-requirements** after user confirm |

### Decisions (01 Phase 0C — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S021-D13 | Root cause in specs | **Outcome-based** ACs; diagnose in 04/07 |
| S021-D14 | Bug report | **Defer** BUG file until 07 code repro |
| S021-D15 | Test IDs | **UJ-061** + **TC-185/186** + **AC-FO1–FO5**; amend UJ-060 prereq |
| S021-D16 | Locked L1–L14 | **Approve all** |
| S021-D9–D12 | Phase 0 proceed | **Approved** — start 01 (user option 1) |

### Decisions (02-verify-plan — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S021-D17 | Gate A→B / M1–M4 | **Approve all** — M1 representative pools; M2 `min_retrieval_score`; M3 CE model lock prose; M4 root cause stays 04/07 |
| S021-D18 | 04 TP1–TP6 | **Approve all** — Phase 23 M99→M100; no new ADR; diagnose order; Path A; no CORS churn |
| S021-D19 | Gate B→C | **Pass** — start 07-build at T99.1 |
| S021-D20 | F46 root cause (initial) | Live vectors uncorrelated with Modal E0; Path B recommended |
| S021-D21 | Promote history | **Not a failed E0 promote of bad shadow** — shadow E0 still matches Modal (cos=1). Live wiped 2026-08-02 02:45 with test `basis_vector` one-hots; E0 promote only covered 2/49 docs |
| S021-D22 | T99.3 fix path | **Path B** full E0 re-embed all docs + promote; file `BUG-2026-08-02-staging-basis-vector-wipe`; harden `attach_embeddings` / DELETE helpers with corpus DB guard (user approved 2026-08-02) |
| S021-D23 | T99.4 local Docker | **Skip Docker Desktop** — waive local TC-185; fixture TC-185 remains CI-gated / skip-without-Postgres; local closeout = TC-186 + bug PASS + staging Path B AC-FO1 (user 2026-08-02) |
| S021-D24 | T100.1 CE re-gate | AC-BB9 / TC-184 **PASS** (`ship_gate_pass=true`; CE+P1 relevancy 0.778 / faith 0.938). Keep prod `VECINITA_RAG_RERANK_CE` **false** until 12/13 Path A approval (AC-FO4); #83 open until flag flip |
| S021-D25 | 11-verify-impl | **Approve F46 + F45** → 12-verify-deploy (user option 1, 2026-08-02) |
| S021-D26 | 12 Phase 2+3 | **Approve both** failure mitigations + rollback → 13 Path A with `VECINITA_RAG_RERANK_CE=false` (user option 1, 2026-08-02) |

### Decisions (13-deploy-smoke — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S021-D27 | Path A execute | **Full Path A** — push/PR/merge/redeploy/H1–H5; CE stays false (user option 1) |
| S021-D28 | Cycle close | **17-retrospective** (user option 4, 2026-08-02) |

### Phase 0–D / deploy status

EV-018 **completed** 2026-08-02. PR [#174](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/174) @ `9d1f10b`; Path A PASS; CE flag still default-off.
Next: **17-retrospective** (S021-D28). CE flag flip remains a separate approval.

## Cycle EV-019 — Scope (S022 / Ingest resilience)

**Approved (session open + Phase 0 Fn lock):** 2026-08-02  
**Session:** S022-ingest-resilience  
**Predecessor:** S021 / EV-018 (completed; pipeline idle on `main`)  
**Issues:** #163 (content_hash skip), #166 (embed sub-batch/retry), #160 (chunk overlap)  
**Features:** **F47**, **F48**, **F49**  
**Branch:** `evolve/EV-019-ingest-resilience`

### Scope summary

Investigate then ship ingest resilience on the shared write/embed path: skip no-op
re-embeds when `content_hash` is unchanged, sub-batch + retry transient embed failures,
and add configurable chunk overlap with sizing clarity.

### Decisions (session open — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S022-D1 | Session | Open **S022-ingest-resilience** |
| S022-D2 | Scope | Bundle A: **#163 + #166 + #160** |
| S022-D3 | Routing | **Standard** (skip 03, 05, 06, 15) |
| S022-D4 | 00-context | **Scoped** |
| S022-D5 | Posture | **Investigate → ship** in one cycle |
| S022-D6 | #160 | **Include** this cycle |
| S022-D7 | Continue | Open → Phase 0 → **01-requirements** |

### Decisions (Phase 0 Fn allocation — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S022-D8 | Fn ids | **F47** (#163), **F48** (#166), **F49** (#160) |
| S022-D9 | Ordering | **F47 + F48** first, then **F49** |
| S022-D10 | Deploy | Staging **Path A** default |
| S022-D11 | Boundary | Shared write/embed path only — no ChatRAG redesign |
| S022-D12 | Embed vs tags | Tags ADR-023 fail-open; embeds **retry then fail job** (no silent holes) |
| S022-D13 | Proceed gate | Create EV-019 + impact → start **01-requirements** (user `1,1,1,1`) |

### Phase 0 status

EV-019 **in_progress**. Next: **01-requirements** (delta; load 01-requirements-seed).

### Decisions (01 Phase 0C — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S022-D14 | Phase 0C answers | Q0–Q5 = `1,1,1,2,2,1` — approve locked; metadata refresh on skip; fail URL on embed exhaust; **overlap default 32**; **HF tokenizer**; extend UJ + TC |
| S022-D15 | F49 overlap | Prod default **`chunk_overlap_tokens=32`** (overrides seed rec. default 0) |
| S022-D16 | F49 tokenizer | **HF tokenizer** for `BAAI/bge-small-en-v1.5` (ADR-044) |
| S022-D17 | Tests / journeys | Extend UJ-002; add **UJ-062**; TC-187–192; AC-IR1–IR7 |
| S022-D18 | RD range | RD-219–RD-228 recorded in `docs/decisions.md` |
| S022-D19 | 01 complete | Spec deltas + session report → **02-verify-plan** |
| S022-D20 | Gate A→B / M1–M6 | **Approve all** — embed defaults; metrics→04; OpenAPI gaps→04/07; AC-RB4 rebuild vs IR; FE optional; data-flow renumber |
| S022-D21 | 04 TP1–TP6 | **Approve all** — Phase 24 M101–M104; no new ADR; OpenAPI/metrics; API e2e; Path A; no new CORS/UI |
| S022-D22 | Gate B→C | **PASS** — start 07-build at T101.1 (05/06 skipped) |

### Phase A status

01-requirements **completed** 2026-08-02.  
02-verify-plan **completed** 2026-08-02 — Gate A→B **PASS** (S022-D20).

### Phase B status

04-tech-plan **completed** 2026-08-02 — TP1–TP6 (S022-D21); Gate B→C **PASS** (S022-D22).  
Next: **07-build** Phase 24 @ T101.1.

---

## Cycle EV-020 — Scope (S023 / #158 #165)

**Approved (Phase 0):** 2026-08-02  
**Session:** S023-retrieval-topk-packing  
**Predecessor:** S022 / EV-019 (Path A PASS @ `bd6bb00`; Path B waived)  
**Issues:** #158 (top_k), #165 (P3 packing residual)  
**Features:** **F50**, **F51**  
**Branch:** `evolve/EV-020-retrieval-topk-packing`

### Scope summary

Residual retrieval ship after F42: promote prod **`top_k` 5→8** and default packer
**`p1`→`p3`**. Reuse S019 A1/A2 evidence; close #158/#165 after ship.

### Decisions (session open + Phase 0 — 2026-08-02)

| ID | Topic | Choice |
|----|-------|--------|
| S023-D1 | Session | Open **S023-retrieval-topk-packing** after S022 close |
| S023-D2 | Routing | **Standard** (skip 03, 05, 06, 15) |
| S023-D3 | Issues | **#158 + #165** residual ship |
| S023-D4 | S022 close | Path A PASS; Path B rechunk waived |
| S023-D5 | Branch | `evolve/EV-020-retrieval-topk-packing` from `main` |
| S023-D6 | Fn + targets | **F50** top_k=**8**; **F51** default **P3**; close issues after ship |
| S023-D7 | Sources UX | Retrieve count = sources shown (no FE cap) |
| S023-D8 | 01 complete | Spec deltas + RD-229–236 → **02-verify-plan** |

### Phase 0 status

EV-020 **in_progress**. Phase 0 **approved** (user option 1).

### Decisions (Phase A–C — 2026-08-02 / 2026-08-03)

| ID | Topic | Choice |
|----|-------|--------|
| S023-D9 | 02 verify | Product plan audit PASS |
| S023-D10 | Gate A→B | **PASS** |
| S023-D11 | 04 drafted | Phase 25 M105–M107; TP1–TP6 recommended |
| S023-D12 | Gate B→C / TP1–TP6 | **Approve all** → **07-build @ T105.1** |
| S023-D13 | Phase C build | M105–M107 complete; Gate C→D pending |

### Phase A status

01-requirements **completed**.  
02-verify-plan **completed** — Gate A→B **PASS** (S023-D10).

### Phase B status

04-tech-plan **completed** 2026-08-03 — TP1–TP6 (S023-D12); Gate B→C **PASS**.

### Phase C status

07-build **completed** 2026-08-03 — M105–M107 (T105.1–T107.3).  
Verification: [verification-report.md](../sessions/S023-retrieval-topk-packing/reports/verification-report.md).  
Next: **Gate C→D** → 09-qa + 10-e2e.

---

## Cycle EV-022 — Scope (S024 / epic #185)

**Approved (Phase 0):** 2026-08-03  
**Session:** S024-website-scrape-crawl  
**Predecessor:** S023 / EV-020 (completed 2026-08-03)  
**Issues:** [#185](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/185) (epic),
[#69](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/69),
[#71](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/71),
[#70](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/70)  
**Features:** **F59**, **F60**, **F61**  
**Branch:** `evolve/EV-022-website-scrape-crawl`  
**Routing:** Standard (skip 03, 05, 06, 15)

### Scope summary

Website **scrape → crawl → tree UI** for multi-page ingest. Independent PRs in order
**#69 → #71 → #70**. Admin/ops Data Management primary; ChatRAG **backend** nested metadata
only (no ChatRAG UI — licensing research tracked).

### Decisions (session open + Phase 0 — 2026-08-03)

| ID | Topic | Choice |
|----|-------|--------|
| S024-D1 | Session | Open **S024-website-scrape-crawl** after S023/EV-020 close |
| S024-D2 | Routing | **Standard**; skip 03, 05, 06, 15 |
| S024-D3 | Issues | Epic #185; order **#69 → #71 → #70**; independent PRs |
| S024-D4 | Cycle | **EV-022** |
| S024-D5 | 00 artifacts | Session brief/routing/HANDOFF/01-seed written |
| S024-D6 | Personas | Admin/ops DM only; ChatRAG UI deferred (licensing) |
| S024-D7 | #69 JS-render | **Required in v1** |
| S024-D8 | #71 crawl | Seed→N, limits, link graph, soft per-page fail |
| S024-D9 | #70 tree | Full tree + flat toggle; strong nesting UX in corpus |
| S024-D10 | Flow | Job form → job → Jobs detail → Corpus tree |
| S024-D11 | API shape | Additive `POST /jobs` crawl options (not `/jobs/crawl`) |
| S024-D12 | Hierarchy | Domain → path segments → document → chunks |
| S024-D13 | Errors | Soft per-page fail; partial metrics; failed tree nodes |
| S024-D14 | Boundaries | Out: ChatRAG UI, #94, full OCR, provider ABC; **In:** JS-render + basic PDF text |
| S024-D15 | Compatibility | Additive API only |
| S024-D16 | Safety | Public URLs; robots/rate-limit/UA; no auth crawl; no body PII logs |
| S024-D17 | ChatRAG license | Research track item only (no UI ship) |
| S024-D18 | Apps | ingest + DM + Modal + write/OpenAPI + **ChatRAG backend meta** |
| S024-D19 | Config/secrets | Defaults preferred; no scrape auth secrets |
| S024-D20 | Connectivity | Same Admin SPA; no new CORS/VITE origins |
| S024-D21 | JS-render runtime | Lock in **04** via short spike |
| S024-D22 | Defaults | max_pages≈25, max_depth≈2, polite; conditional JS-render |
| S024-D23 | Tests | Per-slice AC + UJ/TC; unit + API e2e + Vitest tree |
| S024-D24 | E2E tier | T0/T2 required; T3 live crawl smoke post-deploy |
| S024-D25 | Fn allocation | **F59** (#69), **F60** (#71), **F61** (#70) |
| S024-D27 | 01 seed | Confirm L1–L16 |
| S024-D28 | Hierarchy API | Nested JSON `corpus/tree` + `jobs/{id}/tree` |
| S024-D29 | PDF | Best-effort extract; soft-fail if no text |
| S024-D30 | ChatRAG meta | Path/parent on documents; no FE |
| S024-D31 | Test ids | UJ-064–066; TC-196–207; AC-SC* |
| S024-D32 | 01→02 | User confirm complete 01 → start 02 |
| S024-D33 | Start 02 | 02-verify-plan in_progress |
| S024-D34 | Gate A→B | **PASS** — approve L1–M5; surgical api-contract + TC-204/AC-SC11 |
| S024-D35 | 04 TP locks | **TP1–TP6 all recommended**; JS-render **A** (Playwright in Modal worker); extract **`trafilatura`**; PDF **`pypdf`**; **ADR-045** |
| S024-D36 | Phase 26 | M108 F59 → M109 F60 → M110 F61 → M111 e2e/OpenAPI; PR-59 / #69→#71→#70 |
| S024-D37 | Gate B→C | **PASS** — Phase 26 approved; start 07-build T108.1 |
| S024-D38 | T110.2 verify | Unit tests only; TC-204 e2e deferred until Docker/Postgres (option 2) |
| S024-D40 | T111.3 block | Docker daemon not running; cannot `make db-ready` |
| S024-D41 | T111.3 waive | **Skip local Docker** — TC-204 CI-gated + skip-without-Postgres; local closeout = unit tree + Playwright UJ-066 (user 2026-08-03) |
| S024-D42 | Gate C→D | **PASS** — Phase C approved; start Phase D (09-qa + 10-e2e) |
| S024-D43 | Phase D | **PASS** — 09+10 accepted; start 11-verify-impl |
| S024-D44 | 11 inspect | UI preview **Yes** (local); inspection env **staging** |
| S024-D45 | 11 inspect | **Skip live browser** — approve from T0 + OpenAPI; staging visuals post-deploy |
| S024-D46 | 11 signoff | **Approve all** — UJ-064–066 + F59–F61; close 11 → start 12-verify-deploy (user 2026-08-03) |
| S024-D47 | 12 deploy gate | **Approve mitigations + rollback + Decision A** — ship static scrape/crawl/tree; JS-render browser path follow-up; close 12 → 13 (user 2026-08-03) |

### Impact analysis (docs / code)

| Area | Paths |
|------|-------|
| Product specs | `feature-list.md`, `spec.md`, `user-journeys.md`, `test-plan.md`, `acceptance-criteria.md` |
| Contracts | `api-contract.md`, `openapi/data-management.yaml`, optional ChatRAG OpenAPI for meta |
| Config / ops | `config-spec.md`, `data-management-plan.md`, `dependency-inventory.md` |
| Architecture | **ADR-045** (scrape/crawl/tree + soft-fail + Playwright worker) |
| Code | `packages/ingest`, DM backend/Modal, DM frontend (JobForm + Corpus tree), write API, chat-rag-backend meta |
| Research | ChatRAG nesting UI licensing note (issue comment / session report) |

### Phase 0 status

EV-022 **in_progress**. Phase 0 **approved** (user option 1 — allocate F59–F61).

### Phase A status

| Gate | Status |
|------|--------|
| 01-requirements | **completed** (S024-D32/D33) |
| 02-verify-plan | **completed** — Gate A→B **PASS** (S024-D34) |
| 03-plan-tooling | skipped |

### Phase B status

| Gate | Status |
|------|--------|
| 04-tech-plan | **TP1–TP6 locked** (S024-D35); Phase 26 + ADR-045 drafted |
| 05-verify-tech | skipped |
| 06-tech-tooling | skipped |
| Gate B→C | **PASS** (S024-D37) — 07-build started |

**Tech artifacts:** [tech-plan-delta](../sessions/S024-website-scrape-crawl/reports/tech-plan-delta.md),
[roadmap](../sessions/S024-website-scrape-crawl/roadmap.md),
[ADR-045](../adr/ADR-045-website-scrape-crawl-tree.md), execution-plan Phase 26.

### Phase C status

| Stage | Status |
|-------|--------|
| 07-build | **M108–M111 complete** (T111.3 S024-D41 waive local Docker) |
| 08-verify-build | **PASS** — see `reports/verification-report.md` |
| Gate C→D | **PASS** (S024-D42) |

### Phase D status

| Stage | Status |
|-------|--------|
| 09-qa | **completed** — `pass_with_advisories` (`reports/qa-report.md`) |
| 10-e2e | **completed** — T0 PASS; TC-204 CI-gated (`reports/e2e-report.md`) |
| Phase D checkpoint | **PASS** (S024-D43) |
| 11-verify-impl | **completed** (S024-D46) — `reports/verify-impl.md` |
| 12-verify-deploy | **completed** (S024-D47) — `reports/deploy-checklist.md` |
| 13-deploy-smoke | **completed** (Path A PASS @ `cc2750c`) |
| Close | **S024-D48** — closed without 15/17; cleared for S025/#194 |

---

## Cycle EV-023 — Scope (S025 / #194)

**Approved:** 2026-08-03  
**Session:** S025-ci-release-automation  
**Issues:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/194  
(children [#182](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/182),
[#103](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/103))  
**Features:** F62, F63  
**Preset:** Lean+build

### Scope summary

Minimal DX + release automation: lean Husky push (#182) and post-CD semver tagging (#103).
No product UI/API. #181 stays under retrieval epic #83.

### Decisions (intake + Phase 0)

| ID | Topic | Choice |
|----|-------|--------|
| S025-D1 | Session type | `feature` → 16-evolve |
| S025-D2 | Routing | Lean+build (`01→02→07→08→10→13`) |
| S025-D3 | Prior session | Closed S024/EV-022 without 15/17 |
| S025-D4 | Scope | Both #182 + #103 in EV-023 |
| S025-D5 | Husky | Pre-commit = typecheck + security-scan + job-dispatch; format-check PR-only; stop hooks keep typecheck |
| S025-D6 | Release | After DO CD; patch bump; annotated tag + GitHub Release; `[skip release]`; no floating tags; no semantic-release |
| S025-D7 | Fn | Allocate **F62**, **F63** |
| S025-D8 | Phase 0 | Approved → 01-requirements |

### Docs / artifacts

| Area | Paths |
|------|-------|
| Product | `feature-list.md` F62–F63; UJ-067–068; TC-208–215; AC-CI*/AC-REL* |
| Decisions | RD-264–RD-271; this section |
| Code (07) | `.husky/`, `scripts/ci/`, `.github/workflows/release*.yml`, LOCAL_DEV, rules |

### Phase 0 status

EV-023 **in_progress**. Phase 0 **approved** (user `1,1,1,1`).

### Phase A status

| Gate | Status |
|------|--------|
| 01-requirements | **completed** (S025 closed) |
| 02-verify-plan | completed |
| 03-plan-tooling | skipped |

---

## Cycle EV-024 — Scope (S026 / #193)

**Approved intake:** 2026-08-04  
**Session:** S026-frontend-ux-polish  
**Issues:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/193  
(children [#87](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/87),
[#93](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/93),
[#104](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/104),
[#106](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/106);
related-in-scope [#186](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/186),
[#170](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/170))  
**Features:** F64, F65, F66, F67, F68, F69  
**Preset:** Standard  
**Branch:** `evolve/EV-024-frontend-ux-polish`

### Scope summary

ChatRAG + Admin UX polish epic, expanded to include Feedback (#186) and audit username (#170).
One session / one evolve branch; **strict one PR per issue** (six PRs). F40 cold-start core
already shipped; #87 residual = query tips + VECINA marketing only (**no mini surveys**).

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| S026-D1 | Session | `feature` → 16-evolve; open S026 |
| S026-D2 | Ship model | One branch/session; **one PR per issue** |
| S026-D3 | #87 residual | Tips + marketing; re-audit F40; **no surveys** |
| S026-D4 | Related | Include #186 + #170 |
| S026-D5 | #93 energy | Backend heuristic Wh/CO₂e + **UI estimate advisory**; Modal power-as-proxy conceptual basis |
| S026-D6 | #186 | Backend endpoint + store/forward (privacy review in 01) |
| S026-D7 | #170 | Read-time enrich; no name on `audit_log` |
| S026-D8 | #106 Tooltip | Shared `packages/frontend-ui` |
| S026-D9 | Routing | Standard |
| S026-D10 | Open | Approved → Fn allocation next |
| S026-D11 | Fn allocation | **F64–F69** (one Fn per issue); Phase 0 complete → 01-requirements |
| S026-D12 | F65 energy constants | T4 **70 W** × util **50%** × ask wall time → Wh; fixed US-avg gCO₂e/kWh; approximate + UI advisory |
| S026-D13 | F68 feedback store | Corpus Postgres `feedback` via internal-write; ChatRAG `POST /feedback`; optional email notify; **90d** retention |
| S026-D14 | F64 content | Extend F40 fact catalog with typed entries (`tip` / `marketing` / `fact`) |
| S026-D15 | F66/F67 MVP | Ship issue MVP lists as written (#104 surfaces; #106 theme/locale + ≥1 domain control/app) |
| S026-D16 | F68 PII | No visitor email; ADR-046 anonymous feedback only |
| S026-D17 | F68 admin | Admin Feedback page (admin+super-admin) |
| S026-D18 | F65 API | `energy_estimate` on `/ask` + stream `done` + UI advisory |
| S026-D19 | F69 display | Prefer Supabase email; fallback truncated actor_id |
| S026-D20 | Gate 24a | 01-requirements complete → 02-verify-plan |
| S026-D21 | 02 medium/low | L1+M1–M6 approved (25a–28a); M7 car-equivalent framing pending |
| S026-D22 | 02 M7 | Car framing = distance (251 g/km); day/year % in use guide (29a) |
| S026-D23 | Gate A→B | PASS (30a) → start 04-tech-plan |
| S026-D24 | 04 TP1–TP6 | 31a 32a+b 33a 34a — Phase 27 + ADR-047 + Path A |
| S026-D25 | Gate 35a | 04-tech-plan complete → 05-verify-tech |
| S026-D26 | 05 M2–M4 | 37a 38a 39a — T118.1+T114.3; feedback in data-mgmt plan; secrets in T118.2; **M1 pending explain** |
| S026-D27 | 05 M1 | Admin Feedback: DM `GET /admin/feedback` + internal-write POST (40a) |
| S026-D28 | Gate B→C | **PASS** (41a) → **07-build** M112/F66 (#104); 06 skipped |
| S026-D29 | Merge #200 → M113 | AskQuestion **42c→42a**: merge PR #200 (M112 F66) first, then continue M113 (F67 Tooltip / #106); merge_policy approved; PR not marked merged yet |

### Docs / artifacts

| Area | Paths |
|------|-------|
| Session | `docs/sessions/S026-frontend-ux-polish/` |
| Decisions | this section; RD + TP in decisions.md |
| Product | feature-list F64+; journeys/TC/AC; api-contract deltas |
| Verify | `reports/02-verify-plan-audit.md`; `reports/05-verify-tech-audit.md` |
| Tech | `reports/tech-plan-delta.md` (locked); `roadmap.md`; Phase 27 execution-plan |
| ADRs | ADR-046, ADR-047 |

### Phase 0 status

EV-024 **in_progress**. Gate B→C **PASS** (S026-D28). **07-build** — S026-D29: merging PR #200 then M113/F67.

### Feature map

| Fn | Issue | Title |
|----|-------|-------|
| F64 | #87 | Cold-start wait: query tips + VECINA marketing |
| F65 | #93 | Ask energy estimate + use guide + advisory |
| F66 | #104 | Action icon micro-interactions |
| F67 | #106 | Bilingual tooltips / contextual hints |
| F68 | #186 | ChatRAG feedback page + backend |
| F69 | #170 | Admin audit actor username (read-time) |

---

## Cycle EV-025 — Scope (S027 / #159)

**Intake locked:** 2026-08-05 (Phase 0 Fn gate pending)  
**Session:** S027-multilingual-embeddings  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/159  
**Features:** F70, F71  
**Preset:** Standard  
**Branch:** `evolve/EV-025-multilingual-embeddings`

### Scope summary

Implement multilingual 384-d embedding swap (prefer E1 `multilingual-e5-small`), allow
sentence-transformers/ONNX if FastEmbed cannot host, re-embed corpus via F41, and **cut over
prod this cycle** (user override of ticket “no prod re-embed” OOS). Build on S019 spike; ship
call must include recorded EN vs ES metrics. Out: dual-index, dim≠384, UI, bge-m3 multi-vector.

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| S027-D1 | Outcome | Investigate **and implement** switch + re-embed (1c) |
| S027-D2 | Prior art | Build on S019; fill FastEmbed/ONNX + ADR gaps (2a) |
| S027-D3 | Done when | Recommendation + ADR + recorded EN/ES metrics (3b) |
| S027-D4 | Session | Open S027 → 16-evolve (4a) |
| S027-D5 | Deploy | **Prod cutover this cycle** (5c); **amended by D21** — staging shadow→F36→promote first, then prod (not “minimal-only”) |
| S027-D6 | Scope | 6a — 384-d; no dual-index / UI / bge-m3 MV |
| S027-D7 | Runtime | Allow ST / custom ONNX if FastEmbed cannot host (7b) |
| S027-D8 | Routing | **Standard** (8a) |
| S027-D9 | Fn allocation | **F70 + F71** approved; Phase 0 complete → 01-requirements |
| S027-D10 | Locked intake | Confirm all S027-D1–D9 as written (10a) |
| S027-D11 | Promote abort | **Operator judgment** after F36 report — no hard numeric gate (11c) |
| S027-D12 | Runtime order | FastEmbed upgrade/extend first; ST/ONNX fallback if winner unloadable (12a) |
| S027-D13 | e5 prefixes | Enforce `query:` on ask + `passage:` on ingest/re-embed in shared client (13a) |
| S027-D14 | Model pin | E1 is **planned candidate**; final pin after F36 operator review (14b / D11) |
| S027-D15 | Tokenizer | **Amended 02 M2b:** align `VECINITA_CHUNK_TOKENIZER_ID` with embed pin + **rechunk+reembed** this cycle (was reembed-only 15c) |
| S027-D16 | Journeys/tests | Extend UJ-053/054 + UJ-075/076; API e2e + prefix units; no new Playwright if Jobs UI unchanged (16a) |
| S027-D17 | ADR | New **ADR-048** supersedes ADR-008 (17a) |
| S027-D18 | F36 report | EN/ES relevancy + faithfulness (Hy1) vs E0 + dense hit@k/mean_rank if available (18a) |
| S027-D19 | ADR-013 / F44 | **May tune** soft language filter if ES improves (19b) — scope expand vs earlier “doc only” |
| S027-D20 | F44 scope | Fold tune into **F71** (no F72); only if post-pin F36 shows ES/lang-filter harm (22a) |
| S027-D21 | Cutover order | **Staging first**: shadow reembed → F36 → promote on staging; then repeat on prod (23c — amends D5 “minimal staging”) |
| S027-D22 | Rollback | Keep prior E0 revision restorable via F41 promote/rollback + runbook (24a) |
| S027-D23 | Cost/latency | No hard $/latency budget; FastEmbed preferred; ST/ONNX OK; re-embed may run overnight (25a) |
| S027-D24 | 01 write gate | Delta specs written (26a / user `1`) → 02-verify-plan |
| S027-D25 | 02 verdicts | M1a E1 planned default; **M2b tokenizer+rechunk**; M3b rewrite F10; L1–L3 addressed (ADR-048 Accepted; deps; api-contract note) |
| S027-D26 | Gate A→B | **PASS** (recommended) — Phase A approved; start 04-tech-plan for F70/F71 |
| S027-D27 | 04 TP1–TP5 | **Approve all recommended** — Phase 28 M119–M122; FE timebox→ST; CPU Modal; pin ranges; F41 rechunk |
| S027-D28 | 04→05 | Complete 04-tech-plan → start **05-verify-tech** (option 1) |
| S027-D29 | 05 M1–M6 | **Approve all recommended fixes** — applied to Phase 28 (incl. T120.3b); Gate B→C pending |
| S027-D30 | Gate B→C | **PASS** (option 1) → start 07-build M119 / T119.1 |
| S027-D33 | M119 next | **Merge #208 first, then M120** (option 3) |
| S027-D34 | Merge + CI | **Merge #208** @`2c884bd`; CI split — remote: unit + coverage **PR comment** + strict lint/format; local: compose/integration/long-running (`make test-py` / `ci-push`); rich asserts |
| S027-D35 | T120.5 compose e2e | **Waive** local compose e2e this cycle (unit+CI gate @`837f996`; e2e when Docker works or staging ops). Cite **S027-D32** Docker userns class; T120.5/`M120` → `completed_conditional`; PR **#210** open_ci_green — await explicit merge (Gate C→D pending) |
| S027-D36 | Merge #210 | **Approve merge** PR #210 (option 1) — tip @`837f996` open_ci_green |
| S027-D37 | #210 merged + Gate C→D | **PR #210 MERGED** @`b35e980` (2026-08-05T17:45:19Z); main CI + deploy-preflight **green**; **Gate C→D PASS** (conditional on **S027-D35** compose-e2e waive). Phase C checkpoint AskQuestion before 09-qa / M121 |
| S027-D38 | Phase C checkpoint | **Option 1** — continue **07-build M121** (prod cutover + E0 rollback) before Phase D; T121.1 `in_progress`; 09-qa deferred; branch `evolve/EV-025-multilingual-embeddings` (synced with main after #210) |
| S027-D39 | T121.3 F44 | **Skipped / not_triggered** — no post-pin F36 ES harm evidence this cycle (S027-D19/D20); F44 soft language-filter tune deferred. T121.2 @`bf325e3` TC-240 green; T121.4 green confirm in progress |

### Feature map

| Fn | Issue | Title |
|----|-------|-------|
| F70 | #159 | Multilingual embedding runtime + model pin |
| F71 | #159 | Corpus re-embed + prod cutover (multilingual pin) |
