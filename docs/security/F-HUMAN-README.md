# F-HUMAN: "are you human?" check — start here

F-HUMAN protects the public ChatRAG ask routes from bots with
[Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/). Most
visitors never see a puzzle: the check usually runs invisibly, in English or
Spanish to match the site.

It ships **off** (`VECINITA_HUMAN_VERIFICATION_ENABLED=false`), so merging this
branch changes nothing until the keys are set and the flag is turned on.

Next security feature in line: **F-FLOOD** (rate limiting).

## How it works

```
Chat UI ── GET  /api/v1/human/config ──▶ { enabled, site_key }
Chat UI ── Turnstile widget ──▶ one-time token
Chat UI ── POST /api/v1/human/verify {token} ──▶ backend ──▶ Cloudflare siteverify
        ◀── { human_pass, expires_at }   (HMAC-signed, 1 h by default, kept in memory only)
Chat UI ── POST /api/v1/ask/stream + X-Human-Pass ──▶ 200   (no/invalid pass ──▶ 403)
```

| Piece                                       | File                                                                    |
| ------------------------------------------- | ----------------------------------------------------------------------- |
| Backend check, routes, audit counters       | `apps/chat-rag-backend/vecinita_chat_rag_backend/human_verification.py` |
| Wiring (CORS header, ask + ask/stream gate) | `apps/chat-rag-backend/vecinita_chat_rag_backend/app.py`                |
| Frontend API client + in-memory pass        | `apps/chat-rag-frontend/src/api/human.ts`                               |
| Widget (EN/ES, load-failure fallback)       | `apps/chat-rag-frontend/src/components/HumanCheck.tsx`                  |
| Gate before the first question              | `apps/chat-rag-frontend/src/components/ChatPanel.tsx`                   |
| Strings (EN/ES)                             | `packages/frontend-i18n/src/messages.ts` (`chat.humanCheck.*`)          |
| Backend tests                               | `tests/unit/chat_rag/test_human_verification.py`                        |
| Frontend tests                              | `apps/chat-rag-frontend/src/test/test_f_human_check.test.tsx`           |

## Security and privacy choices

- **Fails closed.** Enabled without a secret → 503. Cloudflare unreachable → no pass.
- **Stateless passes.** Signed with HMAC-SHA256, they expire, and they contain only an expiry and a random value.
- **Header only.** The pass travels in `X-Human-Pass`, never in a URL, so it doesn't land in access logs. (The chat UI streams with `fetch`, so no query-string form is needed.)
- **No personal data.** Questions never reach this code. The visitor IP goes to Cloudflare only if `VECINITA_TURNSTILE_SEND_REMOTE_IP=true`. The pass is never written to `localStorage`.
- **Auditable.** `GET /api/v1/human/stats` returns outcome counts only (`verify_passed`, `verify_failed`, `verify_unavailable`, `pass_accepted`, `pass_refused`). Counts are per instance and reset on restart.
- **Backward compatible.** If the backend has no `/api/v1/human/config` route, the UI treats the check as off.

## Test it on your computer

```bash
uv run pytest tests/unit/chat_rag/test_human_verification.py -v
cd apps/chat-rag-frontend && npx vitest run src/test/test_f_human_check.test.tsx
```

To click through it, run the chat backend and frontend as usual, with Cloudflare's
public **test keys** (always pass, no account needed):

```bash
export VECINITA_HUMAN_VERIFICATION_ENABLED=true
export VECINITA_TURNSTILE_SITE_KEY=1x00000000000000000000AA
export VECINITA_TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA
export VECINITA_HUMAN_PASS_SIGNING_KEY=local-dev-only
```

Then:

- Ask a question. The check appears, and then your question is answered.
- Switch to Spanish. The check text and widget are in Spanish.
- `curl -X POST localhost:8000/api/v1/ask -H 'Content-Type: application/json' -d '{"question":"hi"}'` returns **403** `human_verification_required`.
- `curl localhost:8000/api/v1/human/stats` shows the counts.

To test failures, use the site key `2x00000000000000000000AB` (always fails) or
the secret `2x0000000000000000000000000000000AA` (always fails).

## Turn it on in DigitalOcean

1. In Cloudflare, create a Turnstile widget for the chat frontend hostnames (staging and prod).
2. In App Platform → `vecinita-chat-rag-backend` → **Environment Variables**, set these values. Mark the two secrets **Encrypt**, and share them through the password manager only:

   | Variable                              | Value                               |
   | ------------------------------------- | ----------------------------------- |
   | `VECINITA_HUMAN_VERIFICATION_ENABLED` | `false` at first                    |
   | `VECINITA_TURNSTILE_SITE_KEY`         | site key                            |
   | `VECINITA_TURNSTILE_SECRET_KEY`       | secret key (encrypt)                |
   | `VECINITA_HUMAN_PASS_SIGNING_KEY`     | `openssl rand -base64 32` (encrypt) |

   You may also want to add them to `infra/do/chat-rag-backend.yaml`. This PR documents them in `infra/do/.env.example` and `docs/config-spec.md` but leaves the app spec alone.

3. Deploy the backend and frontend to **stage** with the flag off. Confirm that chat still works.
4. Set `VECINITA_HUMAN_VERIFICATION_ENABLED=true` on stage. Ask a question in EN and ES, and check `/api/v1/human/stats`.
5. Promote to main.

**To roll back:** set `VECINITA_HUMAN_VERIFICATION_ENABLED=false`. No redeploy of the frontend is needed.

## Open questions for review

1. If Cloudflare is down, the check currently refuses everyone (fail closed). Should we let people through for a short time instead?
2. Should server-to-server or eval callers skip the check (for example with an internal API key)? Today, only `/api/v1/ask*` is gated and other routes are untouched.
3. The privacy notice on the site may need a line about Cloudflare Turnstile, in EN and ES.
