# ADR-039: ChatRAG cold-start fun-fact consent cookie (EV-014 / F40)

**Status:** Accepted (2026-07-29)  
**Session:** S016-chat-cold-start-ux / EV-014  
**Related:** RD-183–RD-187; F40; GitHub #87; ADR-004 (visitor zero-PII); ADR-025 (device-local chat history)

## Context

Issue #87 asks for informational messages during long ChatRAG startups. Product intake (S016)
chose rotating WRWC/Providence fun facts, a soft donate CTA, and **remembering which facts were
already shown** so users do not see immediate repeats. Remembering requires device-local state.
Users also asked for an explicit **consent banner** with friendly “we’re not tracking you” copy
and an **HTTP cookie** opt-out.

This is intentionally **different** from EV-013 / RD-181 (admin truncation: no cookies, no new
localStorage, no consent UI). Admin polish was presentational only; F40 needs a preference to
avoid repeat facts.

## Decision

1. **Wait UX** is ChatRAG-frontend-only: cold-start retry **or** >8s with no first token;
   rotate ~10 static EN/ES facts every ~4–5s; keep the short “starting up…” line; soft donate
   CTA to `VITE_WRWC_DONATE_URL` (default `https://wrwc.org/donate/`).
2. **FE `/warm` only** via existing `prewarmChatServices` — no Modal/backend warm-path changes
   in EV-014.
3. **Consent before memory**: Show a friendly banner (EN/ES) stating we do not track personal
   data and only want to avoid repeat messages. Actions: **Accept** / **No thanks**. Facts may
   rotate either way; **persist seen-fact ids only after Accept**.
4. **Storage**:
   - `localStorage` key `vecinita.chat.coldstart.facts.v1` — JSON list of fact ids (Accept only).
   - First-party HTTP cookie `vecinita_chat_coldstart_consent` = `1` (accept) or `0` (opt-out);
     `Path=/`; `SameSite=Lax`; not `HttpOnly` (SPA must read preference). **Max-Age = 1 year**
     (`31536000` seconds) — locked Gate A→B M1; documented in config-spec.
5. **Privacy**: Cookie and storage hold **no PII**, no chat content, no analytics. They are
   **not** required by ChatRAG ask/stream and must **not** be attached as auth. Aligns with
   ADR-004 visitor zero-PII for network payloads.
6. **Tests**: Vitest TC-156–159; Playwright T0-ui TC-160 (UJ-052). No API contract / OpenAPI
   change → no new API e2e.

## Consequences

- ChatRAG introduces a **first-party preference cookie** + new `localStorage` key (documented).
- Docs must distinguish F40 consent from admin RD-181 “no cookies” rule.
- Future analytics of fact impressions remain **out of scope**.
