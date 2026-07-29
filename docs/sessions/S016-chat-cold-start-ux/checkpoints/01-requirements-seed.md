# 01-requirements seed — S016 / EV-014 (#87 / F40)

Generated from Phase 0 intake (2026-07-29). Locked decisions are **confirm-only**.

## Locked decisions (confirm)

See `docs/decisions/evolve-decisions.md` §Cycle EV-014 — S016-D1…D17.

Highlights:

- **F40** — ChatRAG cold-start wait UX (new Fn)
- Triggers: cold-start **retry** OR **>8s** with no first token
- Rotate bilingual fun facts ~**4–5s**; keep short “starting up…” line
- Static EN/ES i18n (WRWC / Providence / ways-to-give curated copy)
- Soft donate CTA → `https://wrwc.org/donate/` (optional `VITE_WRWC_DONATE_URL`)
- FE `/warm` only (`prewarmChatServices`) — no Modal/backend
- Consent banner (friendly no-tracking copy) **before** remembering seen facts
- Remember: `localStorage` fact ids; opt-out via **HTTP cookie**
- Apps: `chat-rag-frontend` (+ shared packages as needed)
- Tests: Vitest + UI e2e; live at 13 only if easy
- Routing: Lean+build

## Document manifest (delta)

| Document | Action |
|----------|--------|
| `docs/feature-list.md` | F40 stub present — expand AC bullets if needed |
| `docs/user-journeys.md` | Add **UJ-052** cold-start wait UX |
| `docs/test-plan.md` | Add **TC-156+** (Vitest + UI e2e; no API e2e — no contract change) |
| `docs/acceptance-criteria.md` | Add **AC-C*** or ChatRAG wait ACs for F40 |
| `docs/spec.md` | Short ChatRAG FE delta (wait UX / consent) |
| `docs/config-spec.md` | Optional `VITE_WRWC_DONATE_URL` |
| `docs/adr/` | ADR for ChatRAG first-party consent cookie + seen-facts (vs EV-013 RD-181 admin “no cookies”) |
| `docs/decisions.md` | RD-183+ |
| Session `reports/01-requirements-cold-start-ux.md` | Stage report |

Skip: api-contract, openapi, dependency inventory (no API/contract change).

## Open questions for 01 interview

1. Fun-fact pool size / approve curated draft list from Phase 0 scrape (~8–12)?
2. Playwright **T0-ui** required for consent banner ↔ ChatPanel (recommended: yes) vs Vitest-only?
3. Cookie + storage key names — use defaults `vecinita.chat.coldstart.consent` / `vecinita.chat.coldstart.facts.v1`?
4. Consent dismiss: must choose Accept or Opt out before facts rotate with memory, or allow “Ask later” and rotate without remembering?

## Proposed RD range

RD-183+ (after RD-182).
