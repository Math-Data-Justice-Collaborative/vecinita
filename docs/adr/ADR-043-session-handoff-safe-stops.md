# ADR-043: Session handoff & safe-stops (fewer chats)

**Status:** Accepted (RET-001 / S021 / EV-018)  
**Date:** 2026-08-02  
**Context:** RET-001 — session sprawl (many Cursor chats per evolve cycle); RA-001–RA-003

## Context

EV-018 / S021 spanned many short Cursor chats. Resume via “continue with recommended” worked,
but chat count and length caused friction. Agents often ended a turn at a natural AskQuestion
boundary even when the user had already approved continuing through the next stage.

## Decision

### 1. Prefer fewer chats on “continue with recommended”

When the user selects or pastes **continue with recommended** (or equivalent) and the next
stage is already in the approved routing plan with gates satisfied:

- Finish the current stage’s bookkeeping **and** start the next stage **in the same turn**
  when safe (no unmet AskQuestion, no deploy approval still pending).
- Do **not** force a new chat solely because a stage boundary was crossed.

### 2. Safe-stops (intentional new chat)

Ending a chat (or offering a stop) is appropriate after:

| Stop | Why |
|------|-----|
| Phase 0–1 (Fn + routing approved) | Specs not yet written; user may pause |
| Phase A / B / C / D checkpoint AskQuestion | User may want to review before continuing |
| After 11-verify-impl | Deploy optional |
| After 13-deploy-smoke | Cycle close / health / retro |
| Blocking AskQuestion unanswered | Cannot proceed without user |

At each safe-stop, regenerate `docs/sessions/{id}/HANDOFF.md`.

### 3. Mid-cycle resume digest

When **00-context** or **16-evolve** resumes an `in_progress` session/cycle (including a
brand-new Cursor chat mid-cycle), emit a **one-screen digest** before other work:

1. Session id · evolve cycle id · current stage / action  
2. Branch + tip SHA (short)  
3. Next AskQuestion or next stage  
4. Material flags (e.g. `VECINITA_RAG_RERANK_CE=false`)  
5. Pointer to `HANDOFF.md` + latest stage report  

### 4. `HANDOFF.md`

Canonical rolling handoff file under the session folder. Overwrite (do not append forever)
at safe-stops and on resume. Keep short — status, next action, flags, links.

## Consequences

- Skills **16-evolve**, **00-context**, and **sessions-reference** document these rules.
- Does not waive required AskQuestion gates or phase checkpoints.
- Follow-up RET after next evolve/hotfix may tune digest template.

## References

- RET-001 · `docs/retrospectives/2026-08-02-ev018-retrieval-follow-on.md`
- RA-001, RA-002, RA-003
