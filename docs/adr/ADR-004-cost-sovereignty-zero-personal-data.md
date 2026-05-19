# ADR-004: Cost control, data sovereignty, zero personal data

**Status:** Accepted  
**Stage:** 00-context  
**Date:** 2026-05-19

## Context

The user requires:

1. **Low operating cost** — minimize always-on spend and third-party API usage.
2. **Data sovereignty** — corpus and queries remain under their chosen jurisdiction and infrastructure; no silent export to vendors for training or analytics.
3. **Zero personal data (option B)** — no storage of end-user **or operator** personal data (no accounts, emails, names, chat history tied to identity, or admin user profiles).

Prior sibling designs used Supabase Auth, admin invites, and optional chat/session persistence — **out of scope** for Vecinita v1.

## Decision

### Zero personal data (hard constraint)

| Allowed in database | Forbidden |
|---------------------|-----------|
| Public corpus: documents, chunks, embeddings, scrape job metadata (URLs, status) | User accounts, profiles, emails, passwords |
| Anonymous job IDs, document IDs, content hashes | Chat session tables, message history with identifiers |
| Operational config (models, feature flags) | Admin invite lists, `user_roles`, audit logs with operator identity |

| Allowed in logs (short retention) | Forbidden |
|-----------------------------------|-----------|
| Request IDs, latency, error codes | Raw chat prompts/responses with persistent storage |
| Aggregated metrics | IP addresses stored long-term (avoid or ≤24h if needed for abuse prevention) |

**ChatRAG:** Stateless request/response — no server-side conversation memory across requests unless implemented purely in browser memory (client-only).

**Data management access:** No login UI with personal identifiers. Protect admin APIs with **infrastructure credentials only** (e.g. deploy-time API key, mTLS, private network, or SSO outside the app that does not persist identity in Vecinita DB). Operators authenticate to the **platform**, not to a Vecinita `users` table.

**Excluded dependencies/patterns:** Supabase Auth, OAuth user profiles, invite-by-email flows, analytics SDKs (Segment, PostHog with identity), persistent LangGraph checkpointing keyed to users.

### Data sovereignty

- Deploy **DigitalOcean Managed Postgres** and **Modal** workloads in **US regions only** (resolution R10a: e.g. DO `nyc1`/`sfo3`, Modal workspace US).
- Prefer **self-hosted inference** on Modal (e.g. Ollama + local embeddings) so RAG queries and corpus text are not sent to US SaaS LLM APIs by default.
- External LLM APIs require an explicit **ADR or spec exception** with data-processing terms documented.
- Corpus and vectors stay in customer-controlled Postgres; Modal volumes hold **model weights only**, not user content long-term.

### Cost control

- **Budget targets (R9):** **≤ $25/month preferred**, **≤ $50/month hard cap** (all infrastructure: DO + Modal + egress).
- Modal: pay-per-invocation for ingest/embed; avoid GPU tiers unless benchmarked; scale-to-zero on web endpoints where possible.
- DigitalOcean: prefer **one consolidated runtime** (single Droplet or one App Platform service running multiple processes) over five always-on App Platform components — five separate paid apps likely exceeds $25.
- Managed Postgres: smallest viable tier; validate against cap in `04-tech-plan` (may be largest line item).
- No paid third-party embedding/chat APIs in default architecture.
- Budget alerts at 80% / 100% of $50 cap; monthly cost review in deploy smoke.

## Consequences

- **R5 resolved:** No identity auth in Vecinita — infrastructure gates only.
- Sibling **admin-invite** and **AuthProvider** patterns must not be ported verbatim.
- E2E tests use API keys or testcontainers — not user fixtures with email/password in DB.
- `01-requirements` must list forbidden data fields, **privacy enforcement** mechanisms (see ADR-004 §Privacy enforcement), and acceptance criteria for “no PII persistence.”
- `04-tech-plan` must produce a **cost estimate** proving ≤ $50/month (with path to ≤ $25) or raise `[Decision]` to relax scope/topology.

## Privacy enforcement

“Privacy enforcement” means **provable guardrails** so the zero–personal-data rule cannot be broken by accident during build or operations — not just a policy statement.

| Layer | Mechanism | Example |
|-------|-----------|---------|
| **Schema** | Migrations forbid identity tables | No `users`, `accounts`, `sessions`, `messages` with `user_id`; schema review checklist |
| **API** | Reject or strip identity fields | No `email`, `name`, `user_id` in request bodies; OpenAPI `additionalProperties: false` on public routes |
| **Application** | Stateless chat | No server-side conversation store; no LangGraph checkpoints keyed to identity |
| **Logging** | Redaction + short retention | No raw prompts in persistent logs; aggregate errors only; 7-day log retention max |
| **Tests** | Automated regression | `tests/privacy/test_no_pii_tables.py` introspects DB metadata; contract tests reject identity fields |
| **CI** | Lint / policy hooks | Fail build if migrations add forbidden table names; optional grep for `supabase.auth` |
| **Operations** | Access without identity in DB | Data-mgmt protected by deploy secret / private network — operators never stored as rows |

Enforcement is **verified** in QA (09) and deploy smoke (13), not assumed from design docs alone.
- Operational tradeoff: without admin accounts, key rotation and access control are entirely platform/DevOps responsibility.

## References

- Resolutions R9, R10, R11 (`docs/context-brief.md`)
- User confirmation: option B (no personal data including admin accounts)
