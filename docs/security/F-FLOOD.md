# F-FLOOD: How do we stop a flood?

Recipe page for the *Vecinita Security Guide* (book two), copied from the
*Vecinita Security Cookbook* dish F-FLOOD. Work item:
[F88](../feature-list.md#f88-flood-control-security-recipe-f-flood).
How dishes are chosen, built, and tested: [README.md](README.md).

| | |
|---|---|
| **What it is** | A cap on request volume that protects the expensive RAG path from cost spikes and downtime. |
| **What it is not** | An "are you human" check (that is F-HUMAN, [F87](../feature-list.md#f87-are-you-human-verification-security-recipe-f-human)), an account, or a staff login. |
| **Who it serves** | Maria, the Safe Viewer: anonymous, often on a shared connection. She is never asked who she is, and a normal conversation never reaches the limits. |
| **White paper** | Protecting a public service without identifying its users (Security and Privacy White Paper). |
| **Status in this repo** | **Planned.** Not yet implemented here. It is the next security feature after F-HUMAN (named as such in PR #394) and would be stacked on it. |
| **Reference implementation** | Gateway repo `acadiagit/vecinita`, [PR 40](https://github.com/acadiagit/vecinita/pull/40) (branch `feat/flood-control`, stacked on PR 39): `backend/src/api/flood_control.py`, 37 unit tests in `backend/tests/test_flood_control.py`, and live QA cases RATE-01 to RATE-05 in `tests/security_qa`. |
| **Target in this repo** | `apps/chat-rag-backend`, in the same place as the F-HUMAN gate (`/api/v1/ask` and `/api/v1/ask/stream`), following the pattern of [PR #394](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/394). Pending the team's go-ahead, see open item 5. |

## Decision (proposed, to confirm with the team)

> **Flood control = sliding-window limits per anonymous visitor, tiered by endpoint
> cost, with a global ceiling per tier. Visitor keys live in memory only.**
> No login required. No IP kept as identity.

Options considered (from the cookbook): leave limits in memory on the auth-proxy
(only covers API-key clients; this recipe extends the same in-memory idea to
anonymous visitors), sliding window at the gateway (chosen), tier by endpoint cost
(chosen), shared counter store (later, see open item 2), force login to cap by
account (dropped: breaks anonymous default), persist IPs as the key (do not
persist).

## How it works (as built in the reference implementation)

Paths below are the reference gateway's. A port would list this repo's routes (F-HUMAN adds `/api/v1/human/*`, which fits the light tier) and decide which public routes belong to which tier.

1. Requests are grouped into tiers by path prefix. **ask** (`/api/v1/ask`, which
   includes the stream) is the expensive RAG path. **light** (`/api/v1/human`,
   `/api/v1/documents`) is cheap. Anything else (health, docs, API-key routes,
   which keep their own per-key limits) is not limited here.
2. The visitor key is an HMAC of the client address, using a random salt created
   when the process starts. Salt and keys exist only in memory.
3. Each request is checked against the visitor's windows and the tier's global
   window. Over a limit: `429` with `Retry-After` and a bilingual message
   (`{"error": "rate_limited", "detail": "...", "retry_after_seconds": N}`).
4. Denied requests are not counted, so retrying never extends a wait.
5. Starting limits (all configurable with `FLOOD_*` settings in the reference; a port here would follow F-HUMAN's `VECINITA_` prefix):

| Tier | Per visitor | All visitors |
|---|---|---|
| ask | 10 / minute and 60 / hour | 300 / minute |
| light | 60 / minute | 600 / minute |

Off by default (`ENABLE_FLOOD_CONTROL=false`). In the reference gateway the
middleware runs after the CORS layer (so the frontend can read the 429) and before
the human check (so a flood is cut before it reaches Cloudflare).

## House rules: how this recipe keeps them

| Rule / taste | How |
|---|---|
| **Zero-PII** | No address, key, question, or per-request time is written anywhere. The key is a salted HMAC held in memory, and restarting forgets everyone. The question is never read, so it is never echoed. The address is never logged. |
| **Transparency** | This page, plus public text on the site (see open item 4). |
| **Auditable** | `GET /api/v1/flood/stats` returns outcome counts only (`ask_allowed`, `ask_limited_visitor`, `ask_limited_global`, and the same for `light`), with a `since` time. Counts are per server process and reset on restart. Longer-lived records belong to F-LOGS. |
| **Anonymous stays first-class** | Everyone gets the same limits. Logging in is never needed, and never raises or lowers a limit. |
| **Login is not the cap** | No account is involved. API-key clients keep their existing per-key limits. |
| **Spanish / accessibility** | The 429 message is English and Spanish. No puzzle, no extra step; the visitor only waits. |
| **Do not persist IP as identity** | The IP is used in memory to compute a key and is never stored or logged. |

## Tests

| Where | What |
|---|---|
| Reference: `backend/tests/test_flood_control.py` | Sliding windows and retry time, hourly limit, independent visitors, global ceiling, key is not the address and depends on the salt, address never in state or logs, memory sweep and table cap, forged `X-Forwarded-For` ignored, middleware tiers and exemptions, bilingual 429, question not echoed, audit counters, no personal details in test data. |
| Reference: `tests/security_qa` (cases RATE-01 to RATE-05) | Live checks against a running backend with `ENABLE_FLOOD_CONTROL=true`: a burst of asks reaches a 429, the 429 is bilingual and does not echo the question, health stays open, stats hold counts only and are read-only. |
| In this repo | To be written first (tests before code) in the requirements stage of F88, porting the cases above to `apps/chat-rag-backend`. Acceptance criteria and test-case numbers are allocated there. |

How the live cases were run in the reference gateway (start it with
`ENABLE_FLOOD_CONTROL=true DEMO_MODE=true` first, and restart it between runs to
reset the counters):

```bash
cd tests
python -m security_qa.runner --target local --only F-FLOOD --include-burst --max-asks 200
```

`--max-asks 200` is needed because the burst in RATE-01 sends 70 asks, more than the
default cap of 15, and RATE-02 would be skipped. Run only the F-FLOOD cases: with the
limit on, every other case that asks questions from the same address would hit a 429
after 10 questions in a minute.

## Open items

1. **Starting limits (team).** The numbers above are a first guess. Confirm them,
   or adjust after seeing real traffic in the stats.
2. **Per process, not shared (team).** Counters live in each process, so a
   restart resets them and several instances each keep their own. That is enough
   for one small instance. If the service runs several, move to a shared counter
   store, which must also hold counts only, never an identity log.
3. **Shared connections (team).** Many people behind one address (a library, a
   community event) share one visitor budget. Watch `ask_limited_visitor` in the
   stats after real events; raise the per-minute ask limit if needed.
4. **Transparency text (team).** Say on the site, in English and Spanish, that
   there is a request limit and that nothing identifying is stored for it.
5. **Go-ahead and where it runs (team).** F-FLOOD is coded and tested only in the
   reference gateway (`acadiagit/vecinita`), which the live site does not use.
   Porting it to `apps/chat-rag-backend` (stacked on PR #394) needs the team's
   go-ahead, ideally after the review of #394. Confirm that no other public route
   reaches retrieval or the LLM without a limit.
6. **Frontend (team).** The frontend should show the 429 message and a retry
   time instead of a generic error.
7. **Proxy setting (ops).** `FLOOD_TRUSTED_PROXY_HOPS` must match the number of
   proxies in front of the service. Too low and visitors collapse into one budget;
   too high and the key can be forged. Check it once on the deployed target.

## Glossary to carry

**Flood:** too many requests, from one place or many, aimed at cost or downtime.
**Sliding window:** counts the requests in the last N seconds, so the limit
moves smoothly instead of resetting on the clock.
**Tier:** a group of routes with the same cost and the same limits.
**Visitor key:** a salted, in-memory fingerprint of the address. Not an identity.
**Global ceiling:** a cap on the whole tier, so many addresses together still hit a limit.
**Trusted proxy hops:** how many proxies in front of the service are trusted to append the real address.
