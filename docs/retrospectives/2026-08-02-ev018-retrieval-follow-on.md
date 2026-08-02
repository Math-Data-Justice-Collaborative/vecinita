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

### 16-evolve (2026-08-02)

| Prompt | User choice |
|--------|-------------|
| Went well | **A** Continue-from-recommended / resume via workflow-state; **B** Multi-Fn in one cycle (F46 → F45) |
| Improve | **D** workflow-state sync commit / `commits_pending` thrash; **C** CE ship_gate PASS vs flag-still-off messaging |
| Friction | **B** Some friction — mainly **number and length of sessions**; unsure how to address overall |

**Notes:** Session sprawl is a cross-cutting theme for Phase 4 (not only 16-evolve skill text).

### 14-hotfix (2026-08-02)

| Prompt | User choice |
|--------|-------------|
| Went well | **C** 16 vs 14 routing clear at S021-D10; **A** keeping wipe fix in 07/evolve was right |
| Improve | **B** corpus wipe/promote checklist even when evolve owns fix; **D** unclear BUG-report vs 14 vs 07 ownership |
| Friction | **A** Smooth (skipping 14 was fine) |

**Clarification given:** S021-D10 = keep mid-cycle incident as evolve/07 Fn work unless trivial one-liner → nested 14.

### pipeline (handoffs) (2026-08-02)

| Prompt | User choice |
|--------|-------------|
| Went well | **A** continue-with-recommended resume; **B** workflow-state + reports enough to pick up; **C** child stages sequenced without full pipeline re-run |
| Improve | **A** fewer/longer turns; **D** auto-handoff template on new chat; **E** cap subagent/state-sync noise; **B** explicit safe-stop/new-chat checkpoints; **C** rolling session digest card *(listed beyond “up to 2” — all retained)* |
| Friction | **B** Some friction |

### Cross-cutting (2026-08-02)

| Prompt | User choice |
|--------|-------------|
| Overall went well | **a** Resume/continue-with-recommended; **b** Multi-Fn evolve (F46→F45) |
| Overall improve | **a** Session sprawl (fewer chats + safe-stops); **b** Auto-handoff / digest on new chat; **c** Cut workflow-state sync / subagent noise |
| Biggest surprise | **a** How many Cursor chats EV-018 took; **b** Staging basis_vector wipe mid-build |

## Brainstorm / actions

### Phase 4 — user choices (2026-08-02)

| Theme | Choice |
|-------|--------|
| Session sprawl | **b** Prefer fewer chats — batch more stages when user says continue-with-recommended |
| Auto-handoff / digest | **c** Both — one-screen digest on resume **and** `HANDOFF.md` at safe-stops |
| State / subagent noise | **c** Both — batch workflow-state updates **and** no solo `workflow-state.yaml` commits except gate/stage close |
| Secondary themes | **c** Bring CE flag messaging + BUG/14/07 ownership into workshop this session |

### Phase 5 — proposed actions

| ID | Action | Target | Priority |
|----|--------|--------|----------|
| RA-001 | Batch stages on “continue with recommended” (fewer chats) | `.cursor/skills/16-evolve/SKILL.md` | P1 |
| RA-002 | Emit one-screen digest on mid-cycle resume | `00-context` + `16-evolve` SKILL.md | P1 |
| RA-003 | Regenerate `docs/sessions/{id}/HANDOFF.md` at safe-stops | `16-evolve` + sessions-reference | P1 |
| RA-004 | One workflow-state-manager `update` per user-visible step | `workflow-state-agent-protocol` / 16-evolve | P1 |
| RA-005 | No solo `workflow-state.yaml` commit unless gate/stage close | `atomic-commits.mdc` or 16-evolve | P2 |
| RA-006 | CE metrics PASS ≠ flag enable — checklist language | `12-verify-deploy` / `13-deploy-smoke` | P2 |
| RA-007 | BUG vs 14 vs 07 ownership + corpus wipe checklist | `14-hotfix` + `07-build` + bug-investigation | P2 |
