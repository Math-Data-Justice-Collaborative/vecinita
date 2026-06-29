# 18-pr-review — Reviewer personas

A panel of role-based review lenses applied during review to **catch issues early** and
surface high-signal nits. Each persona is a focused checklist; walk the panel after the
mechanical checklist ([checklist.md](checklist.md) §A–H) and fold findings into the same
severity model.

These personas are **reusable**: any review or verify stage may apply them —
[08-verify-build](../08-verify-build/SKILL.md) (pre-PR early catch),
[11-verify-impl](../11-verify-impl/SKILL.md), and [18-pr-review](SKILL.md) (canonical).

Severity uses the shared key from [checklist.md](checklist.md): 🔴 blocking · 🟡 advisory
(nit) · 🟢 praise. A persona may only escalate to 🔴 with concrete evidence in the diff,
CI, or a subagent finding — otherwise the observation is a 🟡 nit.

> **Voice, not veto.** Personas are framing devices to broaden coverage. They do not
> override the verdict matrix, the constraint/scope rules in `.cursor/rules/`, or the
> Bugbot / Security-review subagents (which remain the source of truth for confirmed bugs
> and vulnerabilities — see [checklist.md](checklist.md) §G).

---

## How to run the panel

1. Map the touched paths to the **relevant personas** (table below). Skip personas whose
   surface area the PR does not touch — do not invent findings to fill a lens.
2. For each active persona, walk its checklist against the diff; record 🔴 / 🟡 / 🟢.
3. De-duplicate: if two personas raise the same point, keep one finding and attribute the
   strongest lens.
4. Attribute each finding to its persona in the review body so the author sees the angle,
   e.g. `🟡 [Staff Backend] N+1 query in loader…`.

| Touched paths (examples) | Activate personas |
|--------------------------|-------------------|
| `apps/**/api`, `src/`, routers, models, migrations | Staff Backend, CTO |
| `apps/*-frontend/**`, `*.tsx`, `vite`, styles | Staff Frontend, Community Partner |
| `.github/workflows/**`, `infra/**`, Modal/deploy, `Dockerfile`, env/secrets | Senior DevOps, CTO |
| schema, corpus, ingest, embeddings, ACLs/PII | Data & Privacy Steward, Staff Backend |
| docs, user-facing copy, error messages, i18n | Community Partner, CTO |
| architecture, new dependency, cross-cutting, scope | CTO (always) |

---

## 🧱 Staff Backend Engineer

**Lens:** correctness, data integrity, and API contracts under real load and failure.

Nits & issues to catch:

- API contract drift — request/response shape matches `docs/api-contract.md`; OpenAPI
  regenerated (ties to checklist F3).
- Error handling — no bare `except`, errors mapped to correct status codes, failures are
  observable not swallowed.
- Idempotency & transactions — writes are safe to retry; multi-step writes wrapped in a
  transaction; no partial-commit windows.
- Data access — N+1 queries, missing indexes, unbounded result sets, missing pagination.
- Concurrency — blocking I/O inside async paths; shared mutable state; race conditions.
- Resource discipline — timeouts and retries on outbound calls; connections/clients closed.
- Typing — no explicit `Any` (per `.cursor/rules/strict-typing.mdc`); precise return types.
- Backward compatibility — migration is additive/reversible; old clients still work.

Escalate 🔴 when: data loss/corruption risk, contract break without version/docs, missing
test for a changed write path (checklist C1/C5), or `Any` in changed code (B8).

---

## 🎨 Staff Frontend Engineer

**Lens:** the user-facing journey, accessibility, and build-time wiring.

Nits & issues to catch:

- State coverage — loading, empty, error, and success states all handled (no spinner that
  never resolves).
- Accessibility — semantic elements, labels/`aria-*`, keyboard navigation, focus
  management, color contrast.
- Wiring — `VITE_*` values read correctly and baked into the bundle (checklist F1 / H5);
  no API base URL hardcoded.
- TS strictness — no `any`/unsafe casts (per `.cursor/rules/strict-typing.mdc`); typed
  fetch mocks in tests.
- Test coverage — new branches covered (poll intervals, refresh handlers, unmount guards,
  `??` fallbacks) so the 95% frontend branch gate holds (see 08-verify-build Agent 4).
- UX details — optimistic vs pessimistic updates, debounce on inputs, no layout shift,
  responsive at small widths.
- Bundle — no accidental large/duplicate deps; code-split heavy routes.

Escalate 🔴 when: a journey breaks, `VITE_*` wiring would ship a broken bundle (F1),
inaccessible critical control, or coverage gate would fail CI.

---

## ☁️ Senior DevOps / Platform Engineer

**Lens:** deploy safety, secrets, observability, and rollback.

Nits & issues to catch:

- Secrets — no secrets, `.env`, or operator-spec exports in the diff (checklist D4/D5;
  `.cursor/rules/no-operator-spec-commits.mdc`); secret refs use placeholders.
- CI/CD parity — workflow changes keep `ci.yml` and (main-bound) `deploy-preflight.yml`
  green; deploy config matches template (`.cursor/rules/template-conformance.mdc`).
- Migration safety — schema migrations are zero-downtime / reversible and ordered before
  code that depends on them (checklist F5).
- Config & env — new env vars documented and defaulted; no `DATABASE_URL` leaking into
  Modal (`check_modal_no_database_url.sh`, checklist F4).
- Observability — meaningful logs (no secrets in logs), health checks, error surfacing for
  on-call.
- Resilience — timeouts, retries/backoff, resource limits; bind `0.0.0.0:$PORT`; treat the
  filesystem as ephemeral (Render).
- Rollback — change is revertible; feature is flag-guarded or backward compatible.

Escalate 🔴 when: secret/operator-spec in diff, CI/preflight would go red, irreversible or
unordered migration, or DB URL exposed to Modal.

---

## 🧭 CTO / Principal Engineer

**Lens:** scope, architecture, cost, and blast radius — "should we do it this way?"

Nits & issues to catch:

- Scope vs plan — change maps to an approved feature/task; no scope creep or gap (checklist
  E5; `.cursor/rules/plan-adherence.mdc` / `spec-adherence.mdc`).
- Decisions recorded — non-trivial choices have an ADR (`considerations.md` §8); new deps
  are inventoried (`.cursor/rules/plan-adherence.mdc` Dependency Verification).
- Architecture — change fits existing boundaries (RAG core stays Modal/FastAPI/DB-free per
  template); no leaky abstractions or duplicated subsystems.
- Cost — LLM/embedding/DB/compute cost implications considered; no accidental hot loop or
  unbounded fan-out.
- Blast radius — size of change vs risk; could this be smaller / behind a flag / split into
  reviewable PRs?
- Tech debt — shortcut is acknowledged with a follow-up, not silent; no new constraint
  violation (`.cursor/rules/constraint-enforcement.mdc`).
- Maintainability — the next engineer can understand it; naming and module placement match
  conventions.

Escalate 🔴 when: out-of-scope/excluded work (constraint or scope rule violation), missing
ADR for an architectural decision, or undocumented new dependency.

---

## 🤝 Community Partner / End-user Advocate

**Lens:** does this serve real Vecinita users — clearly, inclusively, and safely?

Nits & issues to catch:

- Plain language — user-facing copy and error messages are clear, non-technical, and
  actionable (no raw stack traces or codes shown to end users).
- Inclusivity & i18n — copy is translatable; Spanish/locale strings handled; no hardcoded
  English in user-facing surfaces; respectful, community-appropriate tone.
- Accessibility — usable with assistive tech and on low-end devices / poor networks.
- Trust & safety — content moderation, abuse/edge-case handling, no surprising or harmful
  default behavior.
- Privacy & dignity — no over-collection or unnecessary display of personal data; users can
  understand what happens to their data.
- Journey fit — the change matches the documented user journey
  (`docs/user-journeys.md`); the happy path actually helps the user accomplish their goal.

Escalate 🔴 when: user-facing privacy/safety regression, a documented journey breaks, or
sensitive data is exposed to the wrong audience.

---

## 🔐 Data & Privacy Steward

**Lens:** the RAG corpus, PII, retention, and access control (RAG-specific).

Nits & issues to catch:

- ACLs — retrieval respects document access controls; no cross-tenant/cross-user leakage
  in query results.
- PII — corpus ingest redacts/handles personal data per spec; embeddings/logs don't persist
  raw PII unintentionally.
- Retention — data lifecycle (TTL, deletion) honored; no dev fixtures or seed corpus headed
  to production (`considerations.md` §6).
- Migrations & integrity — schema changes preserve referential integrity; backfills are
  bounded and idempotent.
- Provenance — ingested content has source/citation metadata so answers stay attributable.

Escalate 🔴 when: access-control bypass, PII leak into logs/embeddings/responses, or
dev/seed data bound for production. Defer confirmed vulnerabilities to the Security-review
subagent (checklist G2).

---

## Output mapping

Fold persona findings into the existing review delivery (checklist §H):

- 🔴 / substantive 🟡 → inline comment on the diff line, prefixed with the persona tag.
- Summary in the review body **Findings** section, grouped or tagged by persona.
- Persona nits never change the verdict matrix on their own — only confirmed 🔴 do
  ([checklist.md](checklist.md) §Verdict matrix).
