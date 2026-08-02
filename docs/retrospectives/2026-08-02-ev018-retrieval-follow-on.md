# Retrospective — EV-018 / S021 Retrieval follow-on

> **RET:** RET-001  
> **Date:** 2026-08-02  
> **Session:** S021-retrieval-follow-on  
> **Cycle:** EV-018 (F46 + F45 re-gate)  
> **Status:** Phase 3 interview in progress  
> **Intake:** scope=`evolve_hotfix` · window=`this_session_ev018` · depth=`deep` · transcripts=`full`

## Intake (Phase 0)

| Field | Choice |
|-------|--------|
| Scope | Evolve/hotfix only |
| Time window | This session / EV-018 only |
| Depth | Deep (per-stage) |
| Transcripts | Full |

## Evidence digest (Phase 1)

### Sessions reviewed (parent transcripts)

| Short title | UUID | Role in EV-018 |
|-------------|------|----------------|
| [Path A deploy + retro](3960fb5b-a003-44d3-ad6c-4c06541b8d52) | `3960fb5b-…` | 12 Phase 2/3 → 13 Path A → cycle close → 17 |
| [T99.4 waive Docker → Phase D](5ae12a70-76e2-4cea-a5b0-e685f1a360e1) | `5ae12a70-…` | Post–Path B; T99.4/T99.5; 08–11 |
| [Path B rebuild approve](8aa5289c-bde0-4714-9ba4-3b3333533775) | `8aa5289c-…` | T99.3 Path B + BUG/guard |
| [Gate B→C → 07-build](7db28b04-a879-4007-9c26-75055e3013f7) | `7db28b04-…` | 02/04 → Gate B→C |
| [Open S021 after EV-017](5ac4caa9-fa29-460c-949a-72d702cf7c7c) | `5ac4caa9-…` | 00-context + 01 Phase 0 |

*(Subagent IDs omitted per privacy hygiene.)*

### Stages touched (EV-018 routing)

`00` → `16` → `01` → `02` → `04` → `07` → `08` → `09`+`10` → `11` → `12` → `13` → `17`  
Skipped: `03`, `05`, `06`, `15` (Standard preset).

### Recurring patterns

1. **Continue-with-recommended** — user often replies `1` / paste prior AskQuestion block; agents resume well via workflow-state.
2. **Corpus incident mid-build** — empty retrieve → diagnose → Path B full E0 rebuild + BUG-2026-08-02 + guard (S021-D20–D22); not a nested 14-hotfix (S021-D10).
3. **Local Docker gap** — TC-185 blocked; waived via S021-D23; CI-gated + staging Path B as closeout.
4. **CE metrics vs flag** — AC-BB9 PASS but CE stays off until separate approval (S021-D24/D26); easy to conflate “ship gate PASS” with “enable flag”.
5. **Docs/state commit churn** — many `docs: sync workflow-state` commits; `commits_pending` thrash.
6. **CI template drift** — `test_ce_ship_gate_doc` still required `PENDING` after S020 template filled to PASS (fixed `dd92615`).
7. **Deploy race** — manual `do_apps.py deploy` canceled when CD Deploy DigitalOcean started; CD deploy won (ACTIVE `ade67338`).
8. **AskQuestion tool gap** — agents fell back to markdown numbered options when MCP AskQuestion unavailable; still usable.

### issue_log / hotfix themes

| Theme | Evidence |
|-------|----------|
| Staging basis_vector wipe | BUG-2026-08-02; `attach_embeddings` / clear guard |
| Corpus DB safety | skill + CI `check_corpus_reset_guard.sh` |
| #83 CE flag | open until explicit flip |

### Spec vs tooling

| Class | Count (approx) |
|-------|----------------|
| Outcome-based ACs (defer root cause) | intentional (S021-D13) |
| Waiver (Docker) | 1 (S021-D23) |
| Fix-in-place (CI test) | 1 on Path A |
| Deploy cancel/supersede | 1 (non-fatal) |

### Open questions for user (Phase 3+)

- Was keeping Path B inside 07-build (vs 14-hotfix) the right call?
- Did CE “PASS but flag off” messaging cause confusion at 11/12/13?
- Should 07-build encode a Docker/CI-gated e2e closeout pattern?
- Should 13-deploy-smoke warn against manual DO deploy while CD is running?

## Skill rubric (Phase 2) — hypotheses only

Scope for interview (`evolve_hotfix`): **16-evolve**, **14-hotfix**, **pipeline** handoffs. Child stages noted under 16.

| Stage | Skill worked? | Evidence | Hypothesis | Confidence |
|-------|---------------|----------|------------|------------|
| **16-evolve** | Yes | Full Standard cycle closed; Path A PASS; D1–D28 logged | Orchestration strong; Path A vs Path B naming collision (corpus Path B vs deploy Path A) | medium |
| **14-hotfix** | N/A / underused | Incident handled in 07 (S021-D10) | Unclear when mid-build production wipe should open 14 vs stay in 07 | medium |
| **pipeline** (handoffs) | Partially | Continue-from-paste works; AskQuestion MCP missing | Resume-from-digest is the real handoff UX; skill text assumes AskQuestion tool always present | high |
| 07-build (under 16) | Partially | Path B + guard success; Docker block; many state sync commits | Need explicit “staging mutate / Path B” checklist + local-DB waiver recipe | high |
| 13-deploy-smoke | Partially | Full Path A success; manual deploy canceled by CD | Document “wait for CD; do not force-deploy in parallel” | high |
| 09/10 | Yes | Parallel PASS; T2 deferred to 13 correctly | Fine for delta | medium |
| 11/12 | Yes | Clear CE-hold ship note | Good; keep AC vs flag distinction in checklist template | medium |

## Interview responses (Phase 3)

_(filled as user answers)_

## Brainstorm / actions

_(Phases 4–6)_
