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

### Phase 0 status

**Approved** (S020-D8). Feature-list F43–F45 written; F42 marked Implemented. Phase A `01-requirements` in progress.
