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
| S027-D40 | Merge #211 | **Approve merge** PR #211 (option 1) — tip @`0e65f14` CI green; **MERGED** @`e38516a` (2026-08-05T19:24:50Z); main CI [31039293277](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31039293277) + deploy-preflight [31039596545](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31039596545) success; continue **M122 / T122.1** |
| S027-D41 | Merge #213 | **Approve merge** PR #213 (option 1) — tip @`2e9044b` CI green; **MERGED** @`de1355c`; then **08-verify-build**; **17-retrospective** queued after cycle (prod bugs observed) |
| S027-D42 | Phase D | **Start 09-qa** (option 1) — 08 PASS (cond. S027-D35); 17-retro remains after cycle |
| S027-D43 | QA advisories | User option **3** — address QA advisories before 11-verify-impl; rem. note `reports/qa-remediation.md`; recommended package: Accept S027-D35 (001), carry H4–H5→13 (002), accept DM Vitest flake (003; 736/736 reconfirm), queue 004+005 → 17-retro after cycle; AskQuestion disposition pending |
| S027-D44 | QA + 11 | User option **1** — **accept** QA-S027-001..005 dispositions (per `qa-remediation.md`); start **11-verify-impl**; H4–H5 remain required at 13; 17-retro remains after cycle |
| S027-D45 | 11 journeys | User option **1** — **Approve** UJ-075 + UJ-076 (T0 stub PASS / compose WAIVED S027-D35); live T3/H4–H5 at **13** |
| S027-D46 | 11 inspection | User option **1** — **Skip** live Swagger/UI inspection; OpenAPI + unit/e2e evidence only (S027-D16); live cutover @ 13 |
| S027-D47 | 11 features | User option **1** — **Approve F70 + F71**; 11-verify-impl **completed** (cond. live @ 13 / S027-D35); next → 12-verify-deploy |
| S027-D48 | 12 start | User option **1** — **Start 12-verify-deploy**; checklist draft `reports/deploy-checklist.md`; staging drift `c942971`→`de1355c` |
| S027-D49 | 12 sign-off | User option **1** — **Approve** all failure mitigations + rollback; deploy checklist **ready**; 12-verify-deploy **completed**; next → 13-deploy-smoke |
| S027-D50 | 13 start | User option **1** — **Start 13-deploy-smoke**; Path A validate CD @`de1355c` (Modal [31042438756](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31042438756) + DO [31042551937](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31042551937) success) then H1–H5 + staging cutover |
| S027-D51 | 13 H3 | User option **1** — **Investigate+fix** ChatRAG H3 ask hang → `504 no_healthy_upstream` (basic-xxs single instance) |
| S027-D52 | BUG-2026-08-05 | User option **1** — confirm root cause (async ask blocks event loop); apply `asyncio.to_thread` on `/api/v1/ask` + stream setup |
| S027-D53 | Hotfix ship | User option **1** — PR **#220** MERGED @`903d5e7`; Modal+DO CD success; UH **fixed** (health stays up during ask); H4–H5 **PASS**; H3 ask still hangs ≥120s after warm (separate) |
| S027-D54 | 13 H3 hang | User option **1** — **Investigate H3 ask hang** separately from UH fix (Modal generate / retrieve / timeouts); BUG-2026-08-05 UH **fixed_deployed**; 13-deploy-smoke remains **in_progress** |
| S027-D55 | H3 embed fix | User: **2 then 1** — ops `VECINITA_EMBED_RUNTIME=sentence_transformers` (Modal secret + stage + redeploy) first; then code FastEmbed→ST fallback (S027-D12) |
| S027-D56 | Hotfix PR | User option **1** — commit + open hotfix PR [#221](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/221) (`a354fc0`) for embed E1 FastEmbed→ST |
| S027-D57 | Merge #221 | User: **merge + ensure live** — PR **#221** MERGED @`4b7231b`; verify CI/CD + H1–H5 |
| S027-D58 | F71 cutover | User option **1** — start staging shadow→F36→promote; no prod corpus mutation |
| S027-D59 | Staging promote | User option **1** (continue-with-recommended) — **promote staging** shadow `094e957e-…` → live after F36 PASS; executed: **385** chunks / **47** docs; post-promote H3 EN sources=8 / ES sources=3; H4–H5 PASS; **no prod** corpus mutation |
| S027-D60 | Staging accept → prod path | User option **2** — start prod cutover next; **blocked on Ambiguity**: no distinct prod DO apps/DB found (only `vecinita-*-…ondigitalocean.app` + `vecinita-staging*` Postgres); staging promote may already be the live cutover — AskQuestion `prod_f71_target` |
| S027-D61 | Prod target | User option **1** — **staging-as-live complete**; D59 promote + H3/H4–H5 = F71 cutover this cycle; no second promote; **13-deploy-smoke PASS** (cond.); deploy/phase_d gates passed |
| S027-D62 | Cycle close path | User option **2** — run **15-service-health** first (post-F71 staging-as-live @`4b7231b`), then close EV-025 |
| S027-D63 | Cycle close | User option **1** — **close EV-025**; evolve-summary + evolve-history archived; next **17-retrospective** |
| S027-D64 | State reconcile + session close | User option **1** — treat HANDOFF/reports/D63 as truth; reconcile `workflow-state.yaml` (EV-025 + routing 07–13/15/16 completed @ tip `4b7231b`); **close_session** — archive S027, `active_session: null`, overall `idle` (YAML had been wiped mid-build by HEAD restore) |

### Feature map

| Fn | Issue | Title |
|----|-------|-------|
| F70 | #159 | Multilingual embedding runtime + model pin |
| F71 | #159 | Corpus re-embed + prod cutover (multilingual pin) |

## Cycle EV-026 — Scope (S028 / #222 #223 #224)

**Intake locked:** 2026-08-06 (Phase 0 approved → Phase 1)
**Session:** S028-chat-source-ux
**Issues:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/222 · [#223](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/223) · [#224](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/224)
**Features:** F72, F73, F74
**Preset:** Feature (skip 03/06 unless Phase 1 finds need)
**Branch:** `feat/S028-chat-source-ux` → planned `evolve/EV-026-chat-source-ux`

### Scope summary

Chat source UX in one cycle:

| Fn | Issue | Scope |
|----|-------|--------|
| F72 | #222 | ChatRAG FE: only render `<a href>` for valid absolute `http:`/`https:` URLs; invalid/fixture URLs stay in backend for tests; show title/label without link |
| F73 | #223 | `top_k` is max; drop hits below `min_retrieval_score` (+ CE/rerank threshold if enabled); do not pad; synthesis + UI use same filtered `sources[]` (length 0…top_k) |
| F74 | #224 | Separate `documents.display_title`; scrape updates raw `title`; admin single-doc rename + bulk metadata; citations/admin prefer `display_title` then `title`; chunks inherit display name; optional ingest title if cheap |

**Out:** #94/#217 source-add curation; LLM title generation; community end-user title edit; ingest/job URL rejection.

**API/version:** Prefer compatible deltas (`display_title` nullable; chat `sources[].title` remains the display string). If any breaking change is unavoidable → **major version bump** (S028-D15). Repo presently `0.1.0`.

**Deploy:** Build + verify fully; stages 12–13 AskQuestion-gated — live DO/Modal is **prod** (S028-D2/D7).

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| S028-D1 | Session | Open S028 + feature preset (1a/2a) |
| S028-D2 | Deploy | Prod-only careful; AskQuestion before 12–13 / corpus mutation |
| S028-D3 | Cycle | Start EV-026 Phase 0 |
| S028-D4 | Fn map | F72=#222, F73=#223, F74=#224 |
| S028-D5 | AC | As written on issues |
| S028-D6 | #222 URLs | FE display filter only; backend keeps URLs for tests |
| S028-D7 | Deploy cadence | Build+verify; 12–13 optional gated |
| S028-D8 | Curation | F74 title/display edits only — not #94/#217 |
| S028-D9 | #223 filter | top_k max; score filter; no pad; same set synth+UI |
| S028-D10 | #224 model | Separate `display_title`; scrape → `title` |
| S028-D11 | #224 UX | DocumentAdmin rename + bulk; optional ingest title; chunks inherit |
| S028-D12 | Breaking | Compatible API preferred |
| S028-D13 | Apps | chat-rag FE/BE + rag pkg; internal-write + migration; admin FE |
| S028-D14 | Tests | Vitest + unit/e2e + admin; eval note; T0 only if 12–13 approved |
| S028-D15 | Version | Prefer compatible; if breaking → major version change |
| S028-D16 | Phase 0 close | Allocate F72–F74; enter Phase 1 |
| S028-D17 | Phase 1 | Impact/routing approved → 01-requirements |
| S028-D18 | 00→01 seed | `checkpoints/01-requirements-seed.md` |
| S028-D19 | 01 Phase 0C | Locked + OQ all recommended (1a/2a/3a/4a); RD-309–321; delta specs written |
| S028-D20 | 02-verify-plan | C1/M1/M2/M3/L1 all recommended (1a×4); UJ-063 + RD-231/F72 cites/AC-ME10 fixed; Gate A→B pass |
| S028-D21 | 04 start | Gate A→B confirmed; start 04-tech-plan |
| S028-D22 | 04 TP lock | TP1=Phase 29 M123–M126; TP2=defer ingest title; TP3=frontend-ui helper+SourceList Vitest; TP4=filter+ADR-051+skip 06 |

### Tech plan (04)

| ID | Topic | Choice |
|----|-------|--------|
| TP1 | Milestones | Phase 29: M123 F72 → M124 F73 → M125 F74 → M126 gate |
| TP2 | RD-321 | Defer ingest→display_title |
| TP3 | F72 helper | `vecinita-frontend-ui` + SourceList Vitest |
| TP4 | F73/ADR/06 | Wire score filter; ADR-051; skip 06; OpenAPI+CORS H0c |
| S028-D23 | 04 close | Phase 29 plan approved (TP5=1) |
| S028-D24 | 05 M1–L1 | AC-SU cite fix; F72 surfaces; package name `vecinita-frontend-ui` |

### Verify (09–11)

| ID | Topic | Choice |
|----|-------|--------|
| S028-D30 | 09 remediation | QA-S028-001/002 Fixed; 003→13; 004 accepted; 005→11 |
| S028-D31 | 11 journeys | Approve UJ-077/078/079 (T0; T3→13); staging inspect preferred; no local UI preview |
| S028-D32 | 11 features | Staging tip drift (`c942971` ≠ `8537690`) → approve F72–F74 from T0/OpenAPI only; live UI/API @ 13; close #222–#224 |
| S028-D33 | 12 start | Proceed to 12-verify-deploy (S028-D2 option 1) |
| S028-D34 | 12 gate | GHA outage → RA-009 remote CI **waived**; full local `make ci-push` + **CLI deploy**; `env_role=staging_as_live`; mitigations 1–6 + rollback **approved** |
| S028-D35 | 13 Path A | CLI deploy + Alembic `20260806_0014`; H1–H5 PASS @ `da7cf8b` (#229) |
| S028-D36 | Closeout interrupt | GHA returned → restore remote coverage before close (do not close on docs-only #230 skip) |
| S028-D37 | Coverage restore | PR [#231](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/231) — FE display_title Vitest + write-api branch tests; tip `ad15667` |
| S028-D38 | Cycle close | User option **1** — merge #231, watch main CI + deploy-preflight, **close EV-026**; skip optional 15-service-health |

### Feature map

| Fn | Issue | Title |
|----|-------|-------|
| F72 | #222 | Citation UI — validate URLs before href |
| F73 | #223 | Dynamic relevance-gated sources (no fixed pad) |
| F74 | #224 | Operator-settable `display_title` (durable vs scrape) |

### Close (2026-08-07)

**Tip:** `ad15667` — [CI](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31136499387) + [deploy-preflight](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31136805324) success.  
**Artifacts:** `docs/sessions/S028-chat-source-ux/reports/evolve-summary.md` · `docs/evolve-report-EV-026.md`  
**RA-009:** superseded (remote coverage green).

## Cycle EV-027 — Scope (S030 / #73 #72 #219)

**Intake locked:** 2026-08-07 (Phase 0 approved → Phase 1)  
**Session:** S030-corpus-automations  
**Issues:** [#73](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/73) · [#72](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/72) · [#219](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/219)  
**Features:** F78, F79, F80 (renumbered after `main` took F75/F76 for EV-030/EV-031)  
**Preset:** **Full** (03 + 06 required; S030-D9)  
**Branch:** `evolve/EV-027-corpus-automations`

### Scope summary

| Fn | Issue | Scope |
|----|-------|--------|
| F78 | #73 | Corpus change automations: job completion + cron + doc CRUD hooks; **catch-up only** (failed/partial/missing embed; optional retag — RD-334); idempotency/retries; kill-switch + cost caps; DM run history + enable/disable |
| F79 | #219 | Corpus freshness: scheduled refresh, stale detection, change-aware ingest (hash skip), operator refresh controls |
| F80 | #72 | Modal LoRA/PEFT on pinned Qwen; train data from corpus; versioned adapters; serve via llm_app; **manual train approve**; **human promote** after eval evidence (no auto metric abort — RD-338); operator should promote only when they judge better than base |

**Out:** #192 full dashboard widgets; blind FT promote without operator review of eval evidence; casual prod corpus mutation without AskQuestion.

**Deploy:** Prod FT serve only after human promote judgment + AskQuestion (S030-D10 / RD-331/338). Live DO/Modal is prod-careful.

**02-verify-plan (S030-D25):** C1 amended F78 catch-up wording; C2 clarified “eval better” / “eval-gated” = human judgment + eval evidence (not automated abort).

**Corpus cites:** [Corpus: product] [Corpus: system-spec] [Corpus: deploy-integration] [Corpus: data] [Corpus: api] [Corpus: journeys] [Corpus: tests] [Corpus: acceptance]

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| S030-D0 | Session | Open S030 feature session for #73 |
| S030-D1 | Routing | Standard initially |
| S030-D2 | Intent Q1 | Full #73 checklist this cycle |
| S030-D3 | Intent Q2 | All gaps equal (follow-ons, cron, DM observability) |
| S030-D4 | Intent Q3 | Fine-tune in scope if #72 pulled |
| S030-D5 | Scope Q4 | Pull **full #72** into EV-027 |
| S030-D6 | Scope Q5 | Triggers = job complete + cron + doc CRUD |
| S030-D7 | Scope Q6 | Fold **#219** into EV-027 |
| S030-D8 | Scope Q7 | DM UI = run history + enable/disable |
| S030-D9 | Constraints Q8 | One cycle; upgrade to **Full** (03+06) |
| S030-D10 | Constraints Q9 | Prod FT path; promote when operator judges better than base (clarified S030-D25 / RD-338: human gate + eval evidence, not auto-abort) |
| S030-D11 | Constraints Q10 | Kill-switch + caps; **manual approve** each train |
| S030-D12 | Constraints Q11 | Prefer **LoRA/PEFT** on pinned Qwen |
| S030-D13 | Phase 0 close | Allocate **F78–F80**; enter Phase 1 |

### Feature map

| Fn | Issue | Title |
|----|-------|-------|
| F78 | #73 | Corpus change automations |
| F79 | #219 | Corpus freshness automation |
| F80 | #72 | Modal LoRA fine-tune + human promote (eval evidence) |

### Phase 1

| Artifact | Path |
|----------|------|
| Evolve Plan Card | `docs/sessions/S030-corpus-automations/evolve-plan-card.md` |
| Impact analysis | `docs/sessions/S030-corpus-automations/impact-analysis.md` |
| Routing | `docs/sessions/S030-corpus-automations/routing-plan.md` (Full) |
| 01 seed | `docs/sessions/S030-corpus-automations/checkpoints/01-requirements-seed.md` |

**Next:** 01-requirements (delta) after Phase 1 confirm.

### 04-tech-plan (2026-08-07) — TP1–TP10 locked

| ID | Topic | Choice |
|----|-------|--------|
| S030-D28 | Phase B start | Start **04-tech-plan** after 03 complete |
| S030-D29 | TP lock | Approve TP1–TP10 (Phase 30; schedule `Period(days=1)` amended S030-D31 M2; `automation_runs`; `finetune_app.py` / `vecinita-llm-finetune` / `llm-finetune-adapters`; FT max concurrent=1 + max runs/day=3; approve API; freshness fields; Playwright T0-ui; staging-first; 06 required) |

### 05-verify-tech (2026-08-07) — M1–M5 + L1 approved

| ID | Topic | Choice |
|----|-------|--------|
| S030-D30 | Phase B verify | Start **05-verify-tech** after 04 |
| S030-D31 | Medium/low verdicts | **Approve all recommended** — M1 Playwright required UJ-082–084; M2 `schedule=modal.Period(days=1)`; M3 T129.3 Depends On = T129.1 + blocked-until-06 note; M4 T130.4 confirm Accepted + closeout only; M5 deployment-integration EV-027 stub; **L1 waive** Build Plan Card (SoT = tech-plan-delta + Phase 30) |

**Waiver (L1):** `[Corpus: WAIVED — Build Plan Card; reason: evolve SoT is tech-plan-delta + Phase 30 Task Tracking; decided: S030-D31]`

**Artifacts:** `reports/05-verify-tech-audit.md` · surgical updates to test-plan, ADR-052, execution-plan, deployment-integration, api-contract, tech-plan-delta.

### Gate B→C + 06-tech-tooling (2026-08-07)

| ID | Topic | Choice |
|----|-------|--------|
| S030-D32 | Gate B→C | **PASS** → start 06 |
| S030-D33 | 06 FT pins | Approve all + **exact** Modal FT pins: `peft==0.20.0`, `trl==1.9.2`, `transformers==4.57.6` (train), `accelerate==1.14.0`, `datasets==4.8.5`; bitsandbytes deferred; `infra/modal/finetune_pins.py`; inventory updated |

**Artifacts:** `reports/06-tech-tooling.md` · `infra/modal/finetune_pins.py` · `tests/unit/modal/test_finetune_pins.py`

**Next:** **07-build** Phase 30 M127.

## Cycle EV-252 — Locale system prompt (#252)

**Approved:** 2026-08-22  
**Session:** EV-252-locale-system-prompt (local store)  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/252

### Scope summary

ChatRAG synthesis always used English `production.system_prompt` even when the frontend sent `language: "es"`. Fix: add `DEFAULT_EVAL_SYSTEM_PROMPT_ES` + locale resolver; wire into ask/stream synthesis paths. No `EvalConfig` schema change in v1.

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| EV252-D1 | Config | Constants fallback: EN → `production.system_prompt`; ES → `DEFAULT_EVAL_SYSTEM_PROMPT_ES` |
| EV252-D2 | Out of scope | Admin eval EN/ES textareas; #245 corpus translation; #251 ingest translation |
| EV252-D3 | Scale | Standard (delta docs + unit + API e2e) |
| EV252-D4 | Success | Issue #252 acceptance criteria |
| EV252-D5 | Spec gate | Spec-first; Build blocked until operator approves gate |

### Close (2026-08-22)

**Merge:** `6ed408ef` — PR #255 · closes #252  
**CI:** [ci.yml](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions) + [deploy-preflight](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/32598818761) success on `main`.

## Cycle EV-249 — Blocked ingest hosts (#249)

**Approved:** 2026-08-22  
**Session:** EV-249-blocked-ingest-hosts (local store)  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/249

### Scope summary

Follow-up to #243/#248: three community hosts still failed staging re-ingest. Add scrape fallbacks (`www.` on TLS failure, alternate Chrome UA on 403) and stable `error_code` values (`host_waf_blocked`, `tls_handshake_failed`).

### Decisions

| ID | Topic | Choice |
|----|-------|--------|
| EV249-D1 | TLS apex | Retry `www.{host}` before failing |
| EV249-D2 | WAF 403 | Retry without VecinitaBot in UA + browser Sec-Fetch headers |
| EV249-D3 | Persistent block | `ScrapeFetchError` with stable `error_code` in job metrics |
| EV249-D4 | Out of scope | Playwright JS-render for WAF; prod corpus mutation |

## Cycle EV-216 — Suggested question refresh (#216)

**Approved:** 2026-08-22  
**Session:** EV-216-suggested-questions (local store)  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/216

### Scope summary

Replace empty-state suggested-question chips (EN/ES) with staging-verified wording aligned to
post–EV-029/EV-218 corpus coverage. Content-only i18n change in `messages.ts` + Vitest.

### Proposed chips (staging-verified)

| # | English | Spanish |
|---|---------|---------|
| 1 | Where can I get food assistance in Rhode Island? | ¿Dónde puedo conseguir ayuda con comida en Rhode Island? |
| 2 | How do I get rent assistance in Providence? | ¿Cómo solicito ayuda para pagar el alquiler en Providence? |
| 3 | Where can I find free ESL classes in Providence? | ¿Dónde puedo encontrar clases gratis de inglés en Providence? |

### Decisions (intake)

| ID | Topic | Choice |
|----|-------|--------|
| EV216-D1 | Chip selection | Staging eval pass on RI food / Providence rent / Providence ESL |
| EV216-D2 | Placeholders | Update `questionPlaceholder` to mirror chip 1 topic |
| EV216-D3 | Out of scope | Dynamic chips; backend query rewrite; coldstart facts copy |
| EV216-D4 | Success | Issue #216 acceptance criteria; TC-259 / UJ-081 |
| EV216-D5 | Spec gate | Spec-first; Build blocked until operator approves gate |

---

## Session S031 — Brownfield docs gap-fill (2026-08-18)

**Orchestrator:** brownfield (standard) — **not** an evolve cycle  
**Session:** S031-docs-gapfill  
**Branch:** `feat/S031-docs-gapfill` (rebased onto `main` after PR #238 merge)

| ID | Topic | Choice |
|----|-------|--------|
| S031-D0 | Proceed gate | Open S031 → documenting → verify → HANDOFF → implement; local only; S030 closed; PR #238 left as-is |
| S031-D1 | Gap-fill batch | **feature-list** F78–F80 status → Implemented (in-tree; live cutover deferred); **rewrite** plan-adherence / constraint-enforcement / template-conformance to ChatRAG |
| S031-D2 | Branch base | Rebased onto `main` after PR #238 merge (was `evolve/EV-027-corpus-automations`) |
| S031-D3 | Expand gap-fill | Draft inventory items **2–12** (staging-runbook, architecture FT, schema, data-flow, deploy-checklist, CHANGELOG, spec overview, CORPUS satellites, eval-golden F77 note, maps-mock waiver) |
| S031-D4 | Documenting→implementing gate | **Open** + leftover rules (`open_leftover`) — rewrite `domain-vocabulary.mdc` ChatRAG-first; no maps product; no live mutation |
| S031-D5 | `test_fast.sh` bash 3.2 | **Portable rewrite** (replace bash-4-only builtins) so implementing `tests` pack / `make test-fast` works on macOS stock bash |
| S031-D6 | Close session | **Close** then commit on `feat/S031-docs-gapfill` (`close_then_commit`) |

### Ship path close (2026-08-23)

| ID | Topic | Choice |
|----|-------|--------|
| S030-D67 | Final ship close | **Close EV-027 ship path** — #238 merged `32d94c9b`; #247 merged `d84162ea`; `overall_status=idle`; skip 17-retrospective this session; cutover/enable/FT promote remain deferred (S030-D64) |

## Cycle EV-028 — Scope (S032 / #181)

**Title:** ChatRAG performance regression gate  
**Session:** S032-rag-regression-gate (local store: `EV-028-rag-regression-gate`)  
**Issue:** [#181](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/181)  
**Milestone:** Retrieval and answer quality  
**Branch:** `evolve/EV-028-rag-regression-gate`  
**Status:** **closed (merged)** — PR [#258](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/258) @ `b977599d`; CI + deploy-preflight green on `main`. Operator: add `rag-regression` required check on branch protection.

### Ship close (2026-08-24)

| ID | Topic | Choice |
|----|-------|--------|
| S032-D7 | EV-028 close | **Closed** — #181 closed; `rag-regression` green on `main`; session `EV-028-rag-regression-gate` archived |
| S032-D6 | Spec→Build gate | **Closed** — shipped on `evolve/EV-028-rag-regression-gate`, merged `b977599d` |

| ID | Topic | Choice |
|----|-------|--------|
| S032-D1 | Goal | Full #181 — baseline store + CI regression compare + reviewable bump |
| S032-D2 | Gate scope | PRs to `main` + pushes to `main` |
| S032-D3 | Corpus / runtime | Fixture golden + mocked judge + CI postgres (no Modal GPU on PR) |
| S032-D4 | Tolerances | Quality ≤0.02 abs drop (with floors); retrieval ≤2pp drop; latency p95 max(+10%, +500ms) vs baseline, 15s ceiling |
| S032-D5 | Scale / angles | Standard + all v1 documenting packs |
| S032-D6 | Spec→Build gate | **Closed** — merged `b977599d` |

## Cycle EV-029 — Scope (S033 / #83 #82)

**Title:** Smart retrieval + reranking ship + LLM query refinement  
**Session:** EV-029-smart-retrieval-rerank (local store)  
**Issues:** [#83](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/83),
[#82](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/82)  
**Milestone:** Retrieval and answer quality  
**Branch:** `evolve/EV-029-smart-retrieval-rerank`  
**Status:** **completed** — 11-verify-impl + 13-deploy-smoke 2026-08-24

### Close-out (2026-08-24)

| Item | Result |
|------|--------|
| PR #260 | Merged `c69f8646` |
| Hotfix #261 | Merged `9d95133e` (starlette image + rerank-client proxy header) |
| Staging H3 ask | PASS (AC-SR3 / UJ-059) |
| AC-SR1–SR7 | PASS — see `docs/acceptance-criteria.md` |
| F81 staging enable | Deferred (`VECINITA_RAG_QUERY_REFINE=false`) |
| Reports | session `reports/verify-impl.md`, `reports/deploy-smoke.md` |

### Intake (S033-D1 — 2026-08-24)

| ID | Topic | Choice |
|----|-------|--------|
| S033-D1 | Goal | Full #83 ship — Modal CE + ChatRAG wiring + staging enable; include #82 F81 |
| S033-D2 | #82 | **In scope** — F81 LLM query refinement (not deferred) |
| S033-D3 | Prod CE | **Deferred** — staging flag on; prod AskQuestion at deploy (AC-FO4) |
| S033-D4 | Success | AC-BB9 met + CE wired + staging on + UJ-059 green + `rag-regression` passes |
| S033-D5 | Scale / angles | Standard + all v1 documenting packs |
| S033-D6 | Spec→Build gate | **Closed** — pending operator approval at HANDOFF |

**Cites:** [Corpus: feature-list.md §F45] [Corpus: feature-list.md §F81] [Corpus: acceptance §AC-BB9]
[Spec: docs/config-spec.md §VECINITA_RAG_RERANK_CE] [Spec: docs/test-plan.md §TC-280]

## Cycle EV-030 — Scope (S034 / #84)

**Title:** Output verification (groundedness) + inline citations  
**Session:** EV-030-groundedness-answer-formatting (local store)  
**Issue:** [#84](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/84)  
**Milestone:** Retrieval and answer quality (last open item)  
**Branch:** `evolve/EV-030-groundedness-answer-formatting`  
**Status:** **closed (merged + live)** — PR [#262](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/262) @ `17c5b631`; DO deploy `357f3e4a` ACTIVE; live `VECINITA_RAG_OUTPUT_VERIFY=true`; #84 closed

### Closeout (2026-08-24)

| ID | Topic | Choice |
|----|-------|--------|
| S034-D8 | EV-030 close | F82 live; post-deploy smoke PASS (hedge + `[1]`…`[N]`); golden sweep non-regression |
| S034-D9 | DO outage | Apps API 503/504 ~17:30–18:59 UTC; recovered; manual sync+deploy succeeded |
| S034-D10 | Live verify (AC-FO4) | Operator approved `VECINITA_RAG_OUTPUT_VERIFY=true` on live ChatRAG (ADR-049 staging-as-live); H1–H3b smoke PASS 2026-08-24 |

### Intake (S034-D1 — 2026-08-24)

| ID | Topic | Choice |
|----|-------|--------|
| S034-D1 | Verifier | Self-hosted LLM YES/NO (`score_faithfulness` on `vecinita-llm`) |
| S034-D2 | Fail action | Hedge — prepend bilingual disclaimer; keep answer body |
| S034-D3 | Streaming | Buffer full answer → verify+cite → emit (sync + SSE) |
| S034-D4 | Formatting | Inline `[1]`…`[N]` citations mapped to `sources[]` |
| S034-D5 | Rollout | Flag default-off; staging enable after F36 / `rag-regression` |
| S034-D6 | Scale / angles | Standard + all v1 documenting packs |
| S034-D7 | Spec→Build gate | **Closed** — pending operator approval at HANDOFF |

**Feature:** F82  
**Cites:** [Corpus: feature-list.md §F82] [Spec: docs/acceptance-criteria.md §AC-OV1–OV7]
[Spec: docs/adr/ADR-033-ev008-rag-evaluation-implementation.md §9]

## Cycle EV-031 — Live enable F78/F79 + F80 eval (S035)

**Title:** Corpus automations live enable + FT playground eval path  
**Session:** EV-031-corpus-automations-live-enable (local store)  
**Prior:** EV-027 (S030-D64 deferred cutover)  
**Branch:** `evolve/EV-031-corpus-automations-live-enable`  
**Status:** **complete** (2026-08-26) — M133–M135 signed off; post-enable hotfix [#267](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/267) merged (Refresh now internal key auth on Modal DM `POST /jobs`; prod verified)

### Intake (S035-D1 — 2026-08-24)

| ID | Topic | Choice |
|----|-------|--------|
| S035-D1 | Scope | F78 + F79 live enable + F80 playground eval (no prod promote) |
| S035-D2 | Enable order | F78 + F79 together in one deploy |
| S035-D3 | Kill-switch | ON until post-enable smoke, then off |
| S035-D4 | Scale | Full evolve band |

**Features:** F78, F79, F80  
**Cites:** [Corpus: feature-list.md §F78–F80] [Spec: ADR-052] [Spec: ADR-053]
[Spec: docs/staging-runbook.md §EV-031 live enable sequence]

### Intake (S032-D1 — 2026-08-23)

**Waivers**

- `[Corpus: WAIVED — community maps/alerts mock; reason: non-normative HTML mock, no Fn; decided: S031]`
- `[Corpus: WAIVED — research-brief.md; reason: antibody leftover; decided: S031]`

**Cites:** [Corpus: product] [Corpus: orchestrators] [Corpus: feature-list.md §F78–F80] [Corpus: staging] [Corpus: architecture] [Corpus: data] [Corpus: data-flow] [Corpus: deploy]

---

## Cycle EV-staging-do-supabase — Distinct staging (F83)

**Title:** Distinct staging on DO + Supabase + Modal Environment  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-staging-do-supabase`  
**Status:** implementing (Build gate open; Modal Environments amend)  
**Date:** 2026-08-28

### Intake / context

| ID | Topic | Choice |
|----|-------|--------|
| EV-STG-D0 | Naming | Keep current stack as **prod**; new `*-staging` resources |
| EV-STG-D1 | Modal | **Amended:** same workspace **`vecinita`**; native Modal Environment **`staging`** (web suffix `staging`) — not a second workspace |
| EV-STG-D2 | Corpus | Staging migrations + seed only |
| EV-STG-D3 | Merge gate | Ruleset on `main`: CI + staging deploy/H1–H5 smoke |
| EV-STG-D4 | Modal CLI | After Spec→Build gate (not during Spec) |
| EV-STG-D5 | Feature | **F83**; ADR-054 |
| EV-STG-D6 | Modal auth | Reuse `vecinita` token; `modal environment create staging` + web suffix `staging` |

### Provision closeout (2026-08-28)

- Staging DO apps + `vecinita-staging-db` + Modal Environment + Supabase `camkatfbjguwvymfgdme`
- H1–H5 PASS; ruleset `21766359`; ADR-049 interim banner flipped in runbook
- **EV-STG-D7 (2026-08-28):** Destroy orphan DO DB `vecinita-staging` only; keep
  `vecinita-staging-db` + prod `vecinita-staging-restored-20260701` as separate clusters.
  One-cluster/two-DB merge deferred. Orphan deleted (`cb528db3-…`).

**Cites:** [Corpus: product] §F83 [Corpus: staging] [Spec: docs/adr/ADR-054-distinct-staging-and-production.md] [Spec: docs/adr/ADR-049-single-env-staging-as-live.md]

---

## Cycle EV-033-stage-before-main — Stage before Main rule + GH tracking

**Title:** Enforce Stage→Main via agent rule and GitHub ticket alignment  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-033-stage-before-main`  
**Status:** implementing (Build gate open; rule + #288/#289 shipped)  
**Date:** 2026-08-29

### Intake / requirements

| ID | Topic | Choice |
|----|-------|--------|
| EV-033-D0 | Goal | Align docs + always-applied rule + #212 to ADR-054 (not `stage` branch) |
| EV-033-D1 | GH tracking | Rewrite #212; children (A) rule (B) docs/CORPUS |
| EV-033-D2 | Acceptance | AC-ST8 + TC-298 |
| EV-033-D3 | Rule | `.cursor/rules/stage-before-main.mdc` alwaysApply |
| EV-033-D4 | Model | PR tip → `staging-smoke` → merge `main` → prod CD |
| EV-033-D5 | Out | No new DO/Modal; keep ruleset `21766359`; no live corpus mutate |
| EV-033-D6 | Verify waiver | `inline-documentation` FAIL waived — pre-existing repo-wide; not introduced by EV-033 |

**Cites:** [Corpus: feature-list.md §F83] [Corpus: staging] [Corpus: acceptance] [Corpus: tests] [Spec: docs/adr/ADR-054-distinct-staging-and-production.md] [Spec: docs/adr/ADR-050-ci-cd-blocks-live-deploy.md]

### Build closeout (2026-08-29)

- Rule + TC-298 + #212 rewrite; children #288/#289 closed
- Implementing verify: **ACCEPTED WITH WAIVER** — `inline-documentation` FAIL is repo-wide pre-existing (341 missing); not introduced by EV-033 (EV-033-D6, mirrors EV-staging waiver)
- PR: pending on `evolve/EV-033-stage-before-main`

---

## Cycle EV-036-admin-monitoring-grafana — Monitoring + staging Grafana/Loki (#114)

**Title:** Admin Monitoring dashboard (privacy-safe) + staging Grafana/Loki/alerts  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-036-admin-monitoring-grafana`  
**Status:** documenting (draft-docs complete; feasibility next)  
**Date:** 2026-08-29  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/114

### Intake / requirements

| ID | Topic | Choice |
|----|-------|--------|
| EV-036-D1 | Path | Hybrid: admin Monitoring (#114) + staging Grafana/Loki/alerts |
| EV-036-D2 | Scale | standard (+ tech-plan / verify-tech) |
| EV-036-D3 | Grafana | Staging-only micro compose `infra/observability/` on small Droplet |
| EV-036-D4 | Fn | Single **F84** |
| EV-036-D5 | Alerts | Alertmanager → generic webhook (staging secret) |
| EV-036-D6 | Route | Dedicated `/monitoring` (F25 stays corpus-only) |
| EV-036-D7 | Manifest | Feature/Spec/UJ/TC + API/Config/ADR-055/AC/runbook/deps |
| EV-036-D8 | UI preview | No — interview from docs/#114 |
| EV-036-D9 | Metrics API host | **internal-write-api** (DO holds `DATABASE_URL`) |
| EV-036-D10 | Chat emit | Fire-and-forget HTTP after `/ask` — no question/answer |
| EV-036-D11 | Prod Grafana | Deferred until cost AskQuestion (ADR-004 ≤$50) |
| EV-036-D12 | Tech plan | **Approve TP-EV-036** — M136–M140; Droplet s-1vcpu-1gb; no chart npm lib; Modal `metrics_rollup`; defer Modal→Loki ship |
| EV-036-D13 | Staging Droplet | **Approve create** `s-1vcpu-1gb` (~$6/mo) for Grafana/Loki/Alertmanager (2026-08-30) — blocked until doctl has Droplet scopes |
| EV-036-D14 | Verify waive | **WAIVE** implementing `inline-documentation` — 348 missing repo-wide; **0** in F84 metrics/monitoring paths (2026-08-30) |
| EV-036-D15 | PR base | **Always PR into `stage` first** when `origin/stage` exists; promote via second PR `stage`→`main` after CI + `staging-smoke`. If `stage` missing: AskQuestion to create (do not silently PR to `main`). Hotfix→`main` only via AskQuestion. Supersedes prior “no stage branch” guidance in EV-033 docs. |

### Build progress (2026-08-30)

| Milestone | Status | Commit / notes |
|-----------|--------|----------------|
| M136 | done | `fc3338d8` metrics schema + events |
| M137 | done | `7ee8f83c` summary/timeseries + emitters |
| M138 | done | `0664ae04` admin `/monitoring` UI |
| M139 | done | `0e4261f6` `infra/observability/` compose + TC-305/306 |
| M140 | done | verify band PASS+waive (D14); `18baaa3a` Droplet follow-ups; `701955a0` typecheck tests |
| Droplet | **live** | `vecinita-staging-obs` `159.203.137.236` nyc3; TC-306 webhook drill PASS (2026-08-30) |

### Cross-project Neo4j checkpoint (documenting)

Retrieve for monitoring/Grafana/privacy returned **no_matches** / sparse advisory only
(`reports/memory-context.md`). Disposition: **waive** cross-project Pattern adoption this
cycle; **keep-local** Vecinita ADR-004 / F17 / #114 constraints. Re-check at implementing
verify with HANDOFF dispositions if new Patterns appear.

**Cites:** [Corpus: product] §F84 [Corpus: ADR-004] [Corpus: journeys] [Corpus: api] [Corpus: tests] [Corpus: staging] [Spec: docs/adr/ADR-055-operational-monitoring-grafana-loki.md]

---

## Cycle EV-037-staff-ux-maintainability — Staff UX maintainability review (#199)

**Title:** Non-technical staff maintainability review of ChatRAG + Admin UX polish  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-037-staff-ux-maintainability`  
**Status:** completed (Build closed 2026-08-31)  
**Date:** 2026-08-31  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/199 (CLOSED)

### Intake / requirements

| ID | Topic | Choice |
|----|-------|--------|
| EV-037-D1 | Deliverable | Session report + #199 comment; follow-on issues; no standing staff CMS doc |
| EV-037-D2 | Follow-ons | Dual-i18n consolidation; staff copy runbook issue; extend/link #214 |
| EV-037-D3 | Energy | Env for numeric knobs; advisory prose needs PR |
| EV-037-D4 | Scale | micro |
| EV-037-D5 | Out | CMS; polish rewrites |
| EV-037-D6 | Surfaces | #87 #93 #104 #106 #186 #170 |

### Build outputs

| Output | Ref |
|--------|-----|
| Session review | `{session}/reports/staff-ux-maintainability-review.md` |
| Consolidate ChatRAG → frontend-i18n | #296 |
| Staff copy-change runbook | #297 |
| Feedback notice/notify (existing) | #214 |
| Gate | Open Build (operator **a**) |
| Implementing verify | 5/5 PASS |

**Cites:** [Corpus: product] [Corpus: ADR-004] #199 #193 #214 #296 #297

---

## Cycle EV-296-chatrag-frontend-i18n — Consolidate ChatRAG messages (#296)

**Title:** Move ChatRAG visitor UI strings into `packages/frontend-i18n`  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-296-chatrag-frontend-i18n`  
**Status:** documenting (gate closed)  
**Date:** 2026-08-31  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/296  
**Parent:** EV-037-D2 / #199

### Requirements decisions

| ID | Topic | Choice |
|----|-------|--------|
| EV-296-R1 | Key shape | `chat.<camelCase>` (e.g. `chat.welcomeHeading`) |
| EV-296-R2 | Call sites | Update all ChatRAG call sites to package `t(locale, "chat.*")` in the same PR (operator `B:B` → option 2) |
| EV-296-R3 | Pairing guard | Full package EN/ES string-key set equality (TC-307) |
| EV-296-R4 | Pagination | Use existing `shared.pagination` (do not invent `chat.pagination`) |
| EV-296-R5 | Out | CMS; polish rewrites; `coldstart/facts.ts`; #297 runbook body; #214 polish |

### Spec deltas

| Doc | Change |
|-----|--------|
| `docs/feature-list.md` §F31 | ChatRAG catalog ownership bullet |
| `docs/CORPUS.md` | `[Corpus: frontend-i18n]` satellite path |
| `docs/test-plan.md` | TC-307; TC-067/069 cross-links |
| Session `reports/requirements-delta.md` | Full AC |

**Cites:** [Corpus: product] [Corpus: feature-list.md §F31] [Corpus: frontend-i18n] [Corpus: tests] #296 #297

---

## Cycle EV-297-staff-copy-runbook — Staff copy-change runbook (#297)

**Title:** Standing staff/ops checklist for ChatRAG + Admin UX copy changes  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-297-staff-copy-runbook`  
**Status:** completed (merged PR #300 → `stage` 2026-08-31)  
**Date:** 2026-08-31  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/297 (CLOSED)  
**Parent:** EV-037-D1 / #199 (waiver lifted)  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/300

### Requirements decisions

| ID | Topic | Choice |
|----|-------|--------|
| EV-297-R1 | Path + CORPUS | `docs/runbooks/staff-copy-change.md` + `[Corpus: staff-copy]`; lift EV-037-D1 waiver |
| EV-297-R2 | Feedback triage owner | Role placeholder + Admin Feedback + #214 |
| EV-297-R3 | i18n home | `packages/frontend-i18n`; cold-start facts stay in `coldstart/facts.ts` |
| EV-297-R4 | Proceed | Spec → draft-docs → feasibility → documenting verify |

### Spec deltas

| Doc | Change |
|-----|--------|
| `docs/runbooks/staff-copy-change.md` | **New** staff/ops checklist |
| `docs/CORPUS.md` | `[Corpus: staff-copy]` row; waiver lift note |
| `docs/feature-list.md` §F31 | Point staff path at runbook |
| `docs/decisions/evolve-decisions.md` | This cycle |

**Cites:** [Corpus: staff-copy] [Corpus: frontend-i18n] [Corpus: ADR-004] [Corpus: ADR-046] [Corpus: ADR-047] #297 #199 #214 #296

---

## Cycle EV-214-feedback-polish-notify — Feedback polish + operator notify (#214)

**Title:** Stronger bilingual no-PII/sensitive notice, Feedback UI polish, webhook + Resend email notify  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-214-feedback-polish-notify`  
**Status:** completed (merged PR #303 → `stage` 2026-08-31)  
**Date:** 2026-08-31  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/214 (CLOSED)  
**Branch:** `feat/feedback-polish-notify-214`  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/303  
**Parent:** EV-037-D2 / staff runbook pointer

### Requirements decisions

| ID | Topic | Choice |
|----|-------|--------|
| EV-214-D1 | Notify host | After successful insert on internal-write |
| EV-214-D2 | Webhook | Non-empty `VECINITA_FEEDBACK_NOTIFY_WEBHOOK` |
| EV-214-D3 | Email | **In cycle** — Resend + `VECINITA_FEEDBACK_NOTIFY_EMAIL` (independent of webhook) |
| EV-214-D4 | Payload | id, category, locale, created_at, message only |
| EV-214-D5 | Fail-open | Notify errors must not roll back store |
| EV-214-D6 | Privacy copy | Expand EN/ES in `packages/frontend-i18n` |
| EV-214-D7 | UI | Callout + intro above form |
| EV-214-D8 | AC/TC | AC-UX18–19; TC-308–311; extend UJ-073 |
| EV-214-D9 | Docs | F68 / ADR-046 / config / secrets / api-contract |
| EV-214-D10 | Out | Visitor PII; thumbs; transcripts; retention; live prod without AskQuestion |

### Spec deltas

| Doc | Change |
|-----|--------|
| `docs/feature-list.md` §F68 | #214 notice + notify |
| `docs/adr/ADR-046-…` | §6 operator notify; notice consequence |
| `docs/user-journeys.md` §UJ-073 | Notice + notify steps |
| `docs/acceptance-criteria.md` | AC-UX18–19 |
| `docs/test-plan.md` | TC-308–311 + UJ map |
| `docs/api-contract.md` | Public + internal notify detail |
| `docs/config-spec.md` | `VECINITA_FEEDBACK_NOTIFY_EMAIL` + Resend reuse |
| `docs/staging-secrets-matrix.md` | Internal-write notify secrets |
| `docs/dependency-inventory.md` | No new deps (httpx + Resend) |
| `docs/decisions/evolve-decisions.md` | This cycle |

**Cites:** [Corpus: feature-list.md §F68] [Corpus: ADR-046] [Corpus: ADR-004] [Corpus: tests] #214 #186

---

## Cycle EV-212-stage-promote — Promote `stage` → `main` + close #212

**Title:** Land deferred Stage→Main promote; align #212; flip staging write-api to `main`  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-212-stage-promote`  
**Status:** implementing (Build gate open 2026-08-31)  
**Date:** 2026-08-31  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/212

### Intake / requirements

| ID | Topic | Choice |
|----|-------|--------|
| EV-212-D0 | Goal | Promote PR `stage`→`main`; close #212; flip staging write-api to `main` |
| EV-212-D1 | Scale | micro (no tech-plan / qa / e2e) |
| EV-212-D2 | AC | Approve AC-1…AC-6 (promote + checks + merge + DO flip + close #212 + no secret leaks) |
| EV-212-D3 | Out | Redesign Stage→Main; live prod corpus mutate; flip apps already on `main` |
| EV-212-D4 | Merge | AskQuestion before merge; no force-push |
| EV-212-D5 | Gate | Open Build — commit docs → promote PR → CI + staging-smoke → merge AskQuestion |

### Spec deltas (draft-docs)

| Artifact | Change |
|----------|--------|
| GitHub #212 | Body rewritten to EV-036-D15 two-hop + EV-212 closeout |
| `docs/staging-runbook.md` | Post-promote DO staging branch flip-back note |
| Session AC | `reports/requirements.md` |

**Cites:** [Corpus: staging] [Corpus: feature-list.md §F83] [Decision: EV-036-D15] ADR-054 / ADR-050

---

## EV-feedback-notify-secrets — Staging Resend notify enable (2026-08-31)

**Title:** Enable feedback Resend notify secrets on staging write-api  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-feedback-notify-secrets`  
**Status:** in_progress (Build)  
**Date:** 2026-08-31  
**Parent:** EV-214 HANDOFF leftover

| ID | Topic | Choice |
|----|-------|--------|
| EV-FNS-D1 | Channel | Resend email (webhook deferred) |
| EV-FNS-D2 | Target | Staging `vecinita-staging-write-api` only |
| EV-FNS-D3 | To inbox | GitHub account email (`joseph.c.mcg@gmail.com`) — `.env` had no To |
| EV-FNS-D4 | Prod | Deferred — separate AskQuestion |
| EV-FNS-D5 | Infra | YAML SECRET placeholders + `do_apps.py` sync keys |

**Cites:** [Corpus: feature-list.md §F68] [Corpus: ADR-046] [Corpus: staging]

---

## EV-305-staging-resend — Dual Resend path (same account) (2026-08-31)

**Title:** Separate staging Resend path from prod (isolated key + sender)  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-305-staging-resend`  
**Status:** documenting (Spec band)  
**Date:** 2026-08-31  
**Epic:** [#305](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/305) · children #306–#309

| ID | Topic | Choice |
|----|-------|--------|
| EV-305-D1 | Resend account | Same account/environment OK — not a second Resend org |
| EV-305-D2 | Isolation | Distinct API key + staging From under that account |
| EV-305-D3 | Staging From | Same verified domain, local-part `noreply+staging@josephcmcg.com` (A1) |
| EV-305-D4 | Secret names | Keep `RESEND_API_KEY` / `RESEND_SENDER_EMAIL` / `SUPABASE_SMTP_PASS`; distinct values per GH/Modal/Supabase env (B1) |
| EV-305-D5 | Soft epic | Independent PRs per child #306–#309; no mega-PR |
| EV-305-D6 | New Fn | None — F35/F68 hardening under F83 / ADR-054 |
| EV-305-D7 | Out | Prod key rotate; prod feedback notify; visitor PII |

**Docs delta:** `staging-secrets-matrix.md` §Dual Resend · `staging-runbook.md` feedback · `config-spec.md` F35 Resend rows · `infra/resend/.env.example`

**Cites:** [Corpus: ADR-054] [Corpus: feature-list.md §F35] [Corpus: feature-list.md §F68] [Corpus: staging] #305


---

## EV-313-prod-gpu-snapshots — Prod-only GPU snapshots (#313) (2026-08-31)

**Title:** Re-enable Modal GPU memory snapshots on pinned prod `vecinita-llm`  
**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-313-prod-gpu-snapshots`  
**Status:** closed (Build + staging TC-313-02 + prod enable)  
**Date:** 2026-08-31  
**Epic:** [#311](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/311) · slice [#313](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/313)  
**Merge:** [#321](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/321) → `stage` @ `0b08fbeb`

| ID | Topic | Choice |
|----|-------|--------|
| EV-313-D1 | Kill-switch | `VECINITA_LLM_GPU_SNAPSHOT`; unset = false until staging green |
| EV-313-D2 | LoRA | Minimal post-restore resolve in #313 Build (cite #316); base-only snapshot |
| EV-313-D3 | New Fn | None — ADR-022 amendment; not F40/F64 |
| EV-313-D4 | Playground | Snapshots remain off |
| EV-313-D5 | SLO | Honest Useful/Green/Red bands; no silent “sub-second” claim |
| EV-313-D6 | Prod enable | Staging evidence + AskQuestion |
| EV-313-D7 | Staging cutover | `MODAL_ENVIRONMENT=staging` secret sync (`vecinita-llm-gpu`) + deploy with `VECINITA_LLM_GPU_SNAPSHOT=true`; TC-313-02 PASS (restore log + H1/H3) |
| EV-313-D8 | Prod cutover | Operator approved option 1; `main` sync + deploy with snapshot **true**; logs show create + restore |

**Evidence:** session `reports/tc-313-02-staging.md`, `reports/tc-313-02-prod-enable.md`  
**Docs delta:** ADR-022 amendment · `config-spec.md` · `infra/modal/README.md` · `adr/README.md` · `CORPUS.md` cite · `test-plan.md` TC-313-01/02 · this log

**Cites:** [Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md] [Corpus: ADR-037] [Corpus: ADR-004] [Corpus: ADR-053] [Corpus: config] #313 #311 #316

### PR review advisories addressed (2026-08-31)

| Advisory | Fix |
|----------|-----|
| Misleading “Secret + redeploy” | Docs/comments: kill-switch is **deploy-time** `modal deploy` env |
| Silent sleep/wake skip | Fail closed with `TypeError` when `sleep`/`wake_up` missing |
| Proxy key on GPU workers | Prod `LlmService` mounts `vecinita-llm-gpu` only; ASGI keeps `vecinita-llm` |

**Ops note:** CD does not auto-export `VECINITA_LLM_GPU_SNAPSHOT`; operators must set it in the deploy shell (or extend CD later). Staging + prod Environments were enabled manually 2026-08-31.

**Next #311 child (recommended):** [#316](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/316) LoRA-after-restore completeness (ready metadata + promote matrix). Alternates: [#314](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/314) latency harness · [#318](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/318) async GPU `/warm` prewarm.

---

## EV-316-lora-post-restore — LoRA after snapshot restore (#316) (2026-08-31)

**Session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-316-lora-post-restore`  
**Ticket:** [#316](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/316) (child of #311)  
**Intake:** option 2 (RAG preset angles); context option 1; requirements option 1 + **SHA-256** integrity

| ID | Topic | Decision |
|----|-------|----------|
| EV-316-D1 | Resolve mode | Default `VECINITA_LLM_LORA_RESOLVE=post_restore`; `snapshot_bound` legacy/debug only |
| EV-316-D2 | Integrity | **SHA-256** canonical adapter-dir digest; `VECINITA_FINETUNE_ADAPTER_HASH`; `hmac.compare_digest`; reject symlink escape; no MD5/SHA-1/CRC |
| EV-316-D3 | Fail closed | Mismatch / missing dir → raise before ready |
| EV-316-D4 | Ready metadata | Extend prod `GET /health` with base_model_id, adapter_id, adapter_hash, snapshot_schema, git_commit |
| EV-316-D5 | Tests / AC | TC-316-01, TC-316-02; AC-FT11 |
| EV-316-D6 | Out of scope | UI; baking LoRA into snapshot; #314/#318; F77 promote UX |

**Cites:** [Spec: ADR-022 §Amendment EV-316] [Spec: ADR-053] [Corpus: feature-list.md §F80] [Corpus: config] [Corpus: api] [Corpus: tests] [Corpus: acceptance]

---

## EV-314 + EV-318 — Layer E harness + async GPU prewarm (2026-09-02)

**Sessions:** `EV-314-cold-start-latency-harness`, `EV-318-async-gpu-prewarm` (parallel)  
**Tickets:** [#314](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/314), [#318](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/318) (children of #311)  
**Intake:** operator **A** + recommended parallel; context **Proceed with recommended** (1+4+7+10)

| ID | Topic | Choice |
|----|-------|--------|
| EV-314-D1 | Samples | Staged N≈20 smoke → ≥100 for publishable p95 |
| EV-314-D2 | Stamps | Modal-only first; DO-receive deferred |
| EV-314-D3 | Metrics surface | Structured logs + harness JSON; F84 dimensions deferred |
| EV-314-D4 | Feature id | No new Fn — ADR-022 Layer E |
| EV-318-D1 | Predictors | Mount-only this cycle |
| EV-318-D2 | Modal warm | `.spawn()` / detach (mirror embedding); not health-only |
| EV-318-D3 | F40/F64 | Keep residual wait UX |
| EV-318-D4 | Feature id | No new Fn — ADR-022 prewarm lever / S001 T11 |

**Cites:** [Spec: ADR-022 §Amendment EV-314/EV-318] [Corpus: api] [Corpus: tests] [Corpus: acceptance] [Corpus: feature-list.md §F40]

---

## EV-315 + EV-317 + EV-319 — Seed snapshots, thin ingress, scaledown (2026-09-02)

**Sessions:** `EV-315-seed-gpu-snapshots`, `EV-317-thin-cpu-ingress`, `EV-319-scaledown-window` (parallel)  
**Tickets:** [#315](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/315), [#317](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/317), [#319](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/319) (children of #311)  
**Intake:** operator **1** parallel packaging; requirements **all recommended**

| ID | Topic | Choice |
|----|-------|--------|
| EV-315-D1 | Delivery | Staging script + runbook; optional advisory CI — not hard CD gate |
| EV-315-D2 | Done signal | `#314` `cold_kind` → `snapshot_restore`; fail closed on create |
| EV-315-D3 | Prod | AskQuestion-gated prime |
| EV-317-D1 | Depth | Lazy-import + thin ASGI first; CPU snap only if profile warrants |
| EV-317-D2 | Image | Prefer same image + lazy imports; defer second image |
| EV-319-D1 | Evidence | Timestamp-only gaps; thin traffic → default **120s** + env revert |
| EV-319-D2 | Config | `VECINITA_LLM_SCALEDOWN_WINDOW` at deploy-import; no min/buffer containers |
| EV-*-D0 | Feature id | No new Fn — ADR-022 Layers A/B/C under #311 |

**Cites:** [Spec: ADR-022 §Amendment EV-315/EV-317/EV-319] [Corpus: config] [Corpus: tests] [Corpus: acceptance] [Corpus: staging] [Corpus: ADR-004]

---

## EV-320 — FAQ fast-path Layer D (F85) (2026-09-02)

**Session:** `EV-320-chat-rag-wire-faq-fast-path-into-cold-start-late`  
**Tickets:** [#320](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/320), [#79](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/79) (parent [#311](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/311))  
**Intake / context / requirements:** operator **all recommended**

| ID | Topic | Choice |
|----|-------|--------|
| EV-320-D1 | Feature id | **F85** (not F79 freshness) |
| EV-320-D2 | Match | Exact + normalized; same-language only |
| EV-320-D3 | Metadata | `answer_path` faq_bypass \| rag_llm; keep `cold_kind` GPU-only |
| EV-320-D4 | Kill-switch | `VECINITA_FAQ_FASTPATH_ENABLED` default true |
| EV-320-D5 | UI | No #81 admin editor this cycle; API e2e required |
| EV-320-D6 | Seed content | In-repo bilingual YAML from #79 topics; replaceable |
| EV-320-D7 | Ops | Spec first; staging seed+scaledown after gate; prod AskQuestion |

**Cites:** [Corpus: feature-list.md §F85] [Spec: ADR-022 §Amendment EV-320] [Corpus: api] [Corpus: config] [Corpus: tests] [Corpus: ADR-004]


---

## EV-338 — Staging corpus re-seed from prod (2026-09-03)

**Session:** `EV-338-staging-reseed-from-prod`  
**Ticket:** [#338](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/338)  
**Intake / context / requirements:** operator **all recommended**

| ID | Topic | Choice |
|----|-------|--------|
| EV-338-D1 | Feature id | **F83 / ADR-054** ops — no new Fn |
| EV-338-D2 | Method | Selective `pg_dump`/`pg_restore` corpus tables (prod read-only → staging) |
| EV-338-D3 | Tables | Include documents/chunks/embeddings/tags/document_tags/chunk_tags; exclude jobs/metrics/eval/shadow |
| EV-338-D4 | Docs | staging-runbook §Prod → staging corpus mirror; UJ-094; TC-321–324 |
| EV-338-D5 | Safety | Staging write AskQuestion + corpus-db-safety ack; never mutate prod |
| EV-338-D6 | Done | Non-empty staging corpus + alembic heads + H3 + zero test-artifact URLs |

**Cites:** [Corpus: staging] [Corpus: feature-list.md §F83] [Corpus: corpus-db-safety] [Corpus: no-live-prod-corpus-push] [Spec: ADR-054]

---

## EV-311 — Close cold-start umbrella on evidence (#311) (2026-09-04)

**Session:** `EV-311-infra-sub-second-chatrag-latency-on-cheap-server`  
**Ticket:** [#311](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/311)  
**Filter:** open + `priority:high` only  
**Intake / requirements:** operator **recommended** (close on evidence; defer #315/#317/#319)

| ID | Topic | Choice |
|----|-------|--------|
| EV-311-D1 | Scope | Close umbrella on evidence; no #315/#317/#319 impl this cycle |
| EV-311-D2 | Env | Staging Modal forced-cold only; prod cite EV-313 (no prod stop without AskQuestion) |
| EV-311-D3 | Harness | `cold_start_bench.py` generate + `--force-cold`; N≈20 smoke; optional N≥100 |
| EV-311-D4 | E2E | Staging ChatRAG `chat-ask` and/or H3; never silent 504 |
| EV-311-D5 | SLO | Green / Useful / Red per ADR-022; Useful + documented frontier may close |
| EV-311-D6 | Docs | ADR-022 EV-311 frontier table + staging-runbook + modal README; session research note |
| EV-311-D7 | UI | Docs/repo only (no UI feature interview) |
| EV-311-D8 | New Fn | None — latency system already in ADR-022 / F40/F64/F85 |

**Build evidence (2026-09-04):** Force-cold harness fixed for Modal CLI 1.5+. Staging restore
after snapshot re-enable measured **Red** (~22–72s n=5). FAQ E2E Useful (~226ms).
**Do not close #311** until restore enters Useful/Green or AskQuestion waiver.

**Cites:** [Spec: ADR-022 §Amendment EV-311] [Corpus: acceptance] [Corpus: tests] [Corpus: staging] [Corpus: ADR-004] #311

