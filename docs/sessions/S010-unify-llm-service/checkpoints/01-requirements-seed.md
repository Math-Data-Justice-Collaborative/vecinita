# 01-requirements seed — S010 client consolidation (EV-011 / F39)

**Purpose:** Handoff from **00-context** (2026-07-10 partial re-run) so **01-requirements**
can **pre-populate** the delta interview and ask confirm/modify — not re-litigate locked
decisions.

**Status:** Ready for 01-requirements  
**Session:** `S010-unify-llm-service`  
**Cycle:** EV-011 · Feature **F39** (follow-on; not a new Fn unless interview expands scope)  
**Mode:** `delta`  
**Sources:** [context-brief.md](../context-brief.md) R6–R16 · [routing-plan.md](../routing-plan.md)  
**Prior 01:** [reports/01-requirements.md](../reports/01-requirements.md) (RD-154–RD-162, ADR-037)

---

## How 01-requirements should use this

1. `read_context` → confirm `active_session=S010`, `current_stage=01-requirements`, mode delta.
2. **Do not** restart greenfield interview. Load this seed + context-brief R6–R16.
3. Present **Document Manifest** (below) for confirm/modify.
4. For each template section: show **Pre-filled** answers → AskQuestion confirm / modify.
5. Allocate next RD numbers starting at **RD-163** (after RD-162).
6. Write delta updates to standing docs; append session report
   `reports/01-requirements-client-consolidation.md` (do not overwrite 2026-07-08 report).
7. On completion: advance to **04-tech-plan** (delta) per routing plan (02/03 skipped).

---

## Locked decisions (confirm only — do not re-open unless user overrides)

| Seed ID | 00 ID | Decision | Proposed RD |
|---------|-------|----------|-------------|
| S1 | R7 / item 1 | Merge `LlmClient` + `OllamaModelsClient` into one client; shared env/auth/timeout. Engine mental model: **vLLM inference + HuggingFace downloads** (drop Ollama as provider). | RD-163 |
| S2 | R8 / item 2 | Wire **real vLLM token streaming** into `/generate/stream` SSE (replace word-chunk fake stream in `LlmService.stream_tokens`). | RD-164 |
| S3 | R9 / item 3 | Require **`VECINITA_MODAL_PROXY_KEY`** on all LLM routes: `/generate`, `/warm`, `/models/*` (`/health` may stay open). | RD-165 |
| S4 | R10 / item 4 | Rename modules/types Ollama → playground/LLM; **keep** `/models/ollama` (+ `/internal/v1/models/ollama`) path aliases for FE. | RD-166 |
| S5 | R11 / item 5 | Centralize chat wrapping via HF **`apply_chat_template`** (shared helper). | RD-167 |
| S6 | R12 / item 6 | Gate list/pull catalog to tags **`resolve_hf_repo` accepts**; clear error on unmapped. | RD-168 |
| S7 | R13 / item 7 | **Isolate engines**: separate Modal class (or app surface) for playground; **prod pinned** to fixed default model so playground/eval reloads do not stomp ChatRAG. | RD-169 |
| S8 | R14 / item 8 | Drop legacy `VECINITA_MODAL_OLLAMA_URL` / `VECINITA_OLLAMA_MODEL_ID` fallbacks after cutover; fix package docstrings; declare **`shared-schemas`** dep on `llm-client`. | RD-170 |
| S9 | R15 / item 9 | **Skip** provider ABC / multi-provider plugin framework. | RD-171 |
| S10 | R16 | Build order: slices **A→E**; first slice **A = (1)+(4)** one client + rename. | RD-172 |

Host: consolidation stays in **S010/EV-011** (not S011).

---

## Document manifest (delta — proposed)

### Mandatory (delta sections only)

| Document | Action | Sections to update |
|----------|--------|-------------------|
| `docs/feature-list.md` | Update F39 | Add follow-on bullets: unified client, rename, streaming, auth, chat-template, catalog gate, engine isolate, env cleanup; out-of-scope: provider ABC |
| `docs/spec.md` | Delta | LLM client component; Modal `LlmService` vs playground class; prompt helper location |
| `docs/user-journeys.md` | Delta | UJ-048 (list/pull naming); ChatRAG stream journey if UX claims live tokens; auth failure journey |
| `docs/test-plan.md` | Delta | New/extended TCs per layer table below |

### Recommended

| Document | Action | Rationale |
|----------|--------|-----------|
| `docs/api-contract.md` | Update | Auth on `/generate`/`/warm`; optional `/models/playground` alias; streaming contract (real tokens) |
| `docs/config-spec.md` | Update | Remove/deprecate legacy Ollama env; proxy key required for all LLM clients |
| `docs/acceptance-criteria.md` | Update | AC for streaming, auth, catalog gate, engine isolation |
| `docs/deployment-integration.md` | Update | Dual Modal class deploy; proxy key sync; slice D operator notes |
| `docs/decisions.md` | Append | RD-163–RD-172 under EV-011 |
| `docs/adr/` | New or amend | ADR for engine isolation (7) + auth policy (3) if not folded into ADR-037 amendment |
| `.cursor/rules/unified-vecinita-llm.mdc` | Update | One client; no Ollama mental model; auth everywhere; path aliases |

### Excluded this delta

| Document | Why |
|----------|-----|
| Data management plan | No new corpus assets |
| README.md full rewrite | Delta only; optional one-liner under LLM section |
| New Fn (F40+) | Stay under **F39** unless interview finds product-scope expansion |

---

## Pre-filled interview answers (by template)

### Feature list (F39 follow-on)

**In scope**

1. One HTTP client: generate / stream / warm / list / pull.
2. Real vLLM SSE streaming.
3. Proxy key required on all LLM ASGI routes (except health).
4. Rename Ollama → playground in code/types; path aliases retained.
5. Shared `apply_chat_template` helper for chat-rag, tagging, eval.
6. Catalog/list/pull only for `resolve_hf_repo`-mapped tags.
7. Separate playground Modal class; prod pinned default model.
8. Env/doc cleanup (legacy Ollama vars, llm-client deps/docs).

**Out of scope**

- Provider ABC / second backend (SaaS, llama.cpp, Ollama runtime).
- Migrating Ollama blob volumes.
- Mandatory FE path rename away from `/models/ollama` (aliases OK).

**Delivery slices (product sequencing)**

| Slice | Items | User-visible? |
|-------|-------|----------------|
| A | 1 + 4 | Mostly internal; FE still hits ollama paths |
| B | 2 + 3 | Streaming feels live; 401 without proxy key |
| C | 5 + 6 | Better non-Qwen prompts; no “listed but unmapped” pulls |
| D | 7 | Playground switch does not stall/break prod chat |
| E | 8 | Operator/docs only |

### Spec / components

| Component | Change |
|-----------|--------|
| `packages/llm-client` | Single client class; absorb models client |
| `apps/internal-write-api` | Use unified client; rename imports |
| `infra/modal/llm_app.py` | Real `stream_tokens`; `_authorized` on generate/warm; later split playground class |
| `packages/shared-schemas` | Rename ollama_* → playground_* (compat re-exports optional) |
| Shared prompt helper | New small module (prefer `packages/llm-client` or `shared-schemas`) using HF tokenizer template |
| Chat-rag / tagging / eval | Call shared helper; stop hand-rolled Qwen wrappers |

### User journeys

| UJ | Delta |
|----|-------|
| UJ-048 playground list/pull | Still works via aliases; unmapped tags fail clearly; catalog only mapped tags |
| Chat ask (stream) | Tokens arrive incrementally from vLLM (not post-hoc word split) |
| Chat ask (prod) | Unaffected by playground `model_id` reload (after slice D) |
| Auth | Missing proxy key → 401 on generate/warm/models |

### Test requirements (by layer) — must capture in test-plan

| Change | Layer | Suggested TC / path |
|--------|-------|---------------------|
| Unified client env/auth/timeout | Unit | `tests/unit/test_llm_client.py` (extend) |
| Rename + path aliases | Unit + integration | models list/pull still hit `/models/ollama` |
| Real streaming | Unit (Modal helper) + bug regression | Replace/extend stream_tokens tests; assert not full-then-split |
| Auth on generate/warm | Unit + integration | Unauthorized → 401 |
| `apply_chat_template` | Unit | Non-Qwen + Qwen fixtures |
| Catalog gate | Unit | Unmapped tag rejected; catalog ⊆ registry (BUG-2026-07-09 related) |
| Engine isolation | Unit / smoke | Prod class ignores playground model_id or separate app |
| Journey UJ-048 | API E2E + Playwright (existing) | Extend for clear unmapped error |
| Chat stream UX | API E2E and/or UI E2E if FE claims live tokens | New or extend chat stream TC |

### Config / API / deploy

| Topic | Pre-fill |
|-------|----------|
| `VECINITA_MODAL_LLM_URL` | Sole base URL |
| `VECINITA_MODAL_PROXY_KEY` | Required for all LLM client calls |
| `VECINITA_LLM_MODEL_ID` | Prod/default pin; playground overrides only on playground class |
| Legacy `VECINITA_MODAL_OLLAMA_*` | Remove fallbacks (slice E); already dropped from DO specs (RD-161) |
| Modal routes | Keep `/models/ollama*`; optional add `/models/playground*` aliases |
| Deploy | Slice D: deploy/prod pin + playground class; sync proxy secret |

---

## Open questions for 01 interview (only these need fresh AskQuestion)

Prefer confirm defaults; only ask if user wants to override.

1. **Feature ID:** Keep under **F39** vs allocate **F40** for client-consolidation follow-on?
   - Recommended: **F39 follow-on** (same ADR-037 surface).
2. **ADR:** Amend ADR-037 vs new ADR-038 for engine isolation + auth?
   - Recommended: **amend ADR-037** + short ADR only if isolation is a hard deploy split.
3. **Playground path:** Keep ollama aliases only, or also add `/models/playground` in this cycle?
   - Recommended: **aliases only in Slice A**; optional playground paths in Slice A or C.
4. **Prod pin model:** Which tag/HF id is the production pin?
   - Recommended: current default `qwen2.5:1.5b-instruct` / `Qwen/Qwen2.5-1.5B-Instruct` unless ops says otherwise.
5. **UI E2E scope:** Does ChatRAG streaming need new Playwright, or API E2E only until FE copy changes?
   - Recommended: **API E2E + unit** for streaming; Playwright only if FE asserts token-by-token UX.

---

## Explicitly out of interview scope

- Building a provider plugin system
- Reintroducing Ollama runtime
- Implementing code in 01 (planning only)

---

## Next after 01 completes

**04-tech-plan** (delta) — map RD-163–RD-172 → tasks/milestones; Slice A first for 07-build.
