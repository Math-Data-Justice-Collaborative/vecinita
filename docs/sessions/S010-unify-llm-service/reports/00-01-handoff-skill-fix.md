# 00↔01 handoff skill fix — S010

**Date:** 2026-07-10  
**Trigger:** User could not connect 00-context → 01-requirements after consolidation decisions;
seed existed but skills did not mandate or consume it.

## Root cause

1. **00-context** ended with “Ready for: 01-requirements” and a context brief, but did not
   require a structured handoff artifact (locked vs open, document manifest, how 01 loads it).
2. **01-requirements** still pointed at archived
   `docs/sessions/S000-internal-docs-archive/context-brief.md` and only vaguely “pre-populate
   from context brief” — no Phase to load `checkpoints/01-requirements-seed.md`.
3. Session S010 already had a good seed (`checkpoints/01-requirements-seed.md`) written ad hoc;
   the skill contract lagged the practice.

## Fix (skills)

| File | Change |
|------|--------|
| `.cursor/skills/00-context/SKILL.md` | New **Phase 4.5** — mandatory `01-requirements-seed.md`; Phase 5 points at seed + invoke 01 |
| `.cursor/skills/01-requirements/SKILL.md` | **Phase 0C** load seed; fix prerequisites paths; Phase 2/3/5 + output rules use seed |
| `.cursor/skills/sessions-reference.md` | Document seed under `checkpoints/` |
| `.cursor/skills/pipeline-preamble.md` | Stage roles: 00 outputs brief + seed |

## S010 status after fix

- Do **not** re-open 00 (already completed; seed present).
- Resume **01-requirements** Phase 0C → Phase 2 document manifest from seed.
- Locked S1–S10 → RD-163–RD-172; open questions 1–5 only.
