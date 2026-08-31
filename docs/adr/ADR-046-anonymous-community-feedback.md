# ADR-046: Anonymous community feedback rows (ADR-004 amendment)

**Status:** Accepted  
**Stage:** 01-requirements (EV-024 / S026)  
**Date:** 2026-08-04  
**Related:** ADR-004; F68; GitHub #186 / #214; S026-D13/D16/D17; EV-214-D1–D10

## Context

Epic #193 / #186 adds a ChatRAG Feedback page with backend persistence so community members
can send product feedback. ADR-004 forbids end-user emails/names and identity-tied chat
history in the corpus DB. Intake chose a **backend store** (17a) but resolved the email
contradiction (20a): **no visitor contact email** — message + category only.

## Decision

1. **Allow** a corpus Postgres table `feedback` with: `id`, `created_at`, `category`,
   `message`, optional `locale`, optional `user_agent` hash or omit — **no email, name,
   user_id, or chat transcript auto-attach**.
2. **Amend ADR-004** narrowly: anonymous product-feedback rows are permitted; they are
   **not** personal accounts and must not store identity fields. Visitor optional email is
   **forbidden**.
3. **Retention**: purge rows older than **90 days** (job or scheduled SQL).
4. **Access**: write via ChatRAG `POST /api/v1/feedback` → internal-write; read via admin
   Feedback UI (admin + super-admin only). Optional operator notify (webhook/email to
   operators) must not include visitor PII beyond the message body the user typed.
5. Privacy tests assert schema has no email/name columns and reject those fields on write.
6. **Operator notify (#214 / EV-214):** After a successful `feedback` insert on
   internal-write, optionally notify operators:
   - **Webhook:** non-empty `VECINITA_FEEDBACK_NOTIFY_WEBHOOK` → HTTP POST JSON
     (`id`, `category`, `locale`, `created_at`, `message`).
   - **Email:** non-empty `VECINITA_FEEDBACK_NOTIFY_EMAIL` plus configured Resend
     (`RESEND_API_KEY`, `RESEND_SENDER_EMAIL`) → send to the operator inbox (not a
     visitor address). Reuse the existing Resend HTTP pattern (no new vendor SDK).
   - Channels are independent; either or both may fire. Notify failure must **not**
     roll back a successful store (log + continue). Missing/disabled config → submit
     still succeeds.

## Consequences

- New ADR-004 exception documented here; standing ADR-004 table should link this ADR.
- Admin Feedback page is in scope for F68 (S026-D17).
- If product later wants **visitor** contact email, require a new ADR + explicit consent UI.
- ChatRAG Feedback UI must show a bilingual no-PII / no-sensitive-data notice above the
  form before submit (#214; AC-UX18).

## Alternatives rejected

| Option | Why rejected |
|--------|----------------|
| Optional visitor email in DB | Contradicts ADR-004 zero-PII for community path |
| Forward-only / no store | Rejected in intake (17a) for operator inbox needs |
| Auto-attach chat history | Privacy-sensitive; out of #186 scope |
