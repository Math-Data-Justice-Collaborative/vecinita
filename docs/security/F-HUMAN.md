# F-HUMAN: Is this request from a person?

Recipe page for the *Vecinita Security Guide* (book two), copied from the
*Vecinita Security Cookbook* dish F-HUMAN. Work item:
[F87](../feature-list.md#f87-are-you-human-verification-security-recipe-f-human).
How dishes are chosen, built, and tested: [README.md](README.md).

This page holds the **decision and the house-rule review**. The how-to (run it
locally with Cloudflare test keys, turn it on in DigitalOcean, roll back) is
[F-HUMAN-README.md](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/feat/F-HUMAN-turnstile/docs/security/F-HUMAN-README.md),
added by PR #394. (Switch this link to a relative `F-HUMAN-README.md` once #394 is merged.)

| | |
|---|---|
| **What it is** | A check that the requester is a person, not a bot. |
| **What it is not** | An account, a staff login, or a flood cap (that is F-FLOOD, [F88](../feature-list.md#f88-flood-control-security-recipe-f-flood)). |
| **Who it serves** | Maria, the Safe Viewer: anonymous, on a cheap phone, in Spanish. She must finish it with no picture puzzle. |
| **White paper** | Authentication *before login* (Security and Privacy White Paper, sections 3 and 6.1). It proves "a person is asking" without saying who. It is not authorization. |
| **Status in this repo** | **In review.** [PR #394](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/394), branch `feat/F-HUMAN-turnstile`, base `stage`. Off by default. |
| **Where it runs** | `apps/chat-rag-backend` (gate on `/api/v1/ask` and `/api/v1/ask/stream`) and `apps/chat-rag-frontend` (widget before the first question). |
| **Origin** | Ported from the reference gateway, `acadiagit/vecinita` [PR 39](https://github.com/acadiagit/vecinita/pull/39). |

## Decision (proposed, to confirm with the team)

> **Human-check = Cloudflare Turnstile, visitor IP not shared by default,
> 1-hour signed pass held in memory.** No account. No identity created.

Options considered (from the cookbook): honeypot + current limits, proof-of-work
(Friendly Captcha, ALTCHA, Cap, Private Captcha), Cloudflare Turnstile,
reCAPTCHA v3 / image CAPTCHA (dropped: tracking or accessibility failure),
WebAuthn (staff dish, not this one).

## How it works (as built in PR #394)

1. The chat UI asks `GET /api/v1/human/config` whether the check is on, and for the site key. A backend without this route is treated as "off".
2. The Turnstile widget runs, in the site's language (EN or ES). Most visitors never see a puzzle: the check usually runs invisibly.
3. The UI sends the widget token to `POST /api/v1/human/verify`. The backend checks it with Cloudflare.
4. The backend returns a pass, HMAC-SHA256 signed, valid for 1 hour by default (`VECINITA_HUMAN_PASS_TTL_S`, 60 to 86400 seconds). The UI keeps it in memory only, never in `localStorage`.
5. The UI sends the pass with each question in the `X-Human-Pass` header. The header is added to the CORS allowed headers. The pass is **never** in a URL, so it stays out of access logs (the chat UI streams with `fetch`).
6. A question to `/api/v1/ask` or `/api/v1/ask/stream` without a valid pass gets `403 human_verification_required`. The UI shows the check again.

Settings (all `VECINITA_` prefixed): `HUMAN_VERIFICATION_ENABLED` (default `false`), `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `HUMAN_PASS_SIGNING_KEY` (falls back to the secret key if unset), `HUMAN_PASS_TTL_S`, `TURNSTILE_SEND_REMOTE_IP` (default `false`). They are listed in `docs/config-spec.md` and `infra/do/.env.example`.

## House rules: how this recipe keeps them

| Rule / taste | How |
|---|---|
| **Zero-PII** | The pass holds only an expiry time and a random value. Nothing is stored per visitor. Questions never reach this code. The visitor IP goes to Cloudflare only if `VECINITA_TURNSTILE_SEND_REMOTE_IP=true`. |
| **Transparency** | This page and the README, plus public text on the site (see open item 1). |
| **Auditable** | `GET /api/v1/human/stats` returns outcome counts only: `verify_passed`, `verify_failed`, `verify_unavailable`, `pass_accepted`, `pass_refused`, with a `since` time. No IP, token, or question. Counts are per instance and reset on restart. Longer-lived records belong to F-LOGS. |
| **Anonymous stays first-class** | Everyone gets the same check. Logging in is not the test, and is never needed to ask. |
| **Login is not the test** | No account is involved. |
| **Spanish / accessibility** | The widget language follows the site (EN or ES). The check usually runs invisibly. |
| **No dead end** (cookbook: "VPN or assistive tech can loop") | If Cloudflare's script fails to load, the visitor sees a message instead of a silent failure. Whether the message offers a retry is for the reviewers of the UI. |
| **Fails closed** | Enabled without a secret key gives 503. Cloudflare unreachable means no pass is issued. |

## Tests

| Where | What |
|---|---|
| `tests/unit/chat_rag/test_human_verification.py` (24 tests) | The pass, the config route, both ask routes, verify success / failure / Cloudflare unreachable, IP opt-in, stats hold no personal data. |
| `apps/chat-rag-frontend/src/test/test_f_human_check.test.tsx` (5 tests) | The widget and the gate in the chat UI. The full chat frontend suite (234 tests) passed on the PR. |
| Reference: gateway QA cases HV-01 to HV-11 | Live checks in `acadiagit/vecinita` (`tests/security_qa`). Not yet ported to this repo. |

Per the PR description, `test_app_routes.py` (needs Postgres), `make security-scan` and gitleaks were not run locally; CI covers them. Formal AC / TC numbers are not yet allocated.

## Open items

These match the open questions on PR #394, plus the ones this recipe adds.

1. **Transparency text (team).** The widget loads from Cloudflare (U.S.), so Cloudflare sees the visitor's browser even though we don't send the IP by default. Say so on the site, in English and Spanish.
2. **If Cloudflare is down (team).** The check fails closed: nobody can ask. Alternative: let questions through for a short time and lean on F-FLOOD.
3. **Server-to-server and eval callers (team).** Today only `/api/v1/ask*` is gated, and other routes are untouched. Decide whether eval and other non-browser callers skip the check, for example with an internal key.
4. **Other entry points (team).** Confirm that no other public route reaches retrieval or the LLM without the check.
5. **Logs (F-LOGS).** In the reference gateway, the web server access log recorded the question text in the URL. Not yet checked in this repo.
6. **Floods (F-FLOOD).** F-HUMAN makes a bot solve a check; it does not cap volume. See [F88](../feature-list.md#f88-flood-control-security-recipe-f-flood).

## Glossary to carry

**Turnstile:** Cloudflare's bot check; usually invisible.
**Human pass:** the signed, one-hour proof the browser sends with each question. Not an identity.
**Fail closed:** when the check can't run, deny rather than allow.
