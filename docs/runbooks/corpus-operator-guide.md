# Corpus Operator Guide

> **Audience:** Corpus operators and community admins  
> **Issue:** [#52](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/52)  
> **Last updated:** 2026-07-03  
> **Developer reference:** [data-management-dev-guide.md](data-management-dev-guide.md)

---

## What you can do

The **admin frontend** (`data-management-frontend`) lets authenticated operators:

- Submit **URL ingest jobs** (scrape public web pages into the corpus)
- Monitor **job status** (pending, running, completed, failed)
- **Browse, search, and filter** corpus documents by tags
- **Edit tags** (human overrides on top of LLM auto-tags)
- Run **bulk operations** — delete, retag, metadata edit (admin role only)
- View **dashboard stats** and **service health**
- Review the **audit log** and document version history
- Run **RAG evaluation** against golden fixtures (EV-008)
- Use **Playground** for sandboxed RAG config (EV-009, super-admin promote)

Community members use the **ChatRAG frontend** separately — no login required.

---

## Getting access

1. An existing **admin** invites you by email (invitation-only — no public sign-up).
2. You receive an email with a link to **`/accept-invite`** on the admin frontend.
3. Set your password and log in with **email + password**.
4. Your role is either **`admin`** (full write) or **`viewer`** (read-only).

**Roles:**

| Role | Read corpus | Write / ingest / bulk | Eval / playground |
|------|-------------|----------------------|-------------------|
| `viewer` | Yes | No (403) | Read-only where exposed |
| `admin` | Yes | Yes | Yes |
| super-admin | Yes | Yes | Promote playground config to production |

Identity is stored in **Supabase** — not in the Vecinita corpus database (privacy by design).

**Troubleshooting login:** See [staging-runbook.md](../staging-runbook.md) §EV-007 invite flow. Common issues: expired OTP link, wrong `site_url` in Supabase config.

---

## Ingesting content

### What to ingest

- **Public community URLs only** — food pantry hours, housing resources, public program pages
- Content in **English and/or Spanish** (stored as scraped; bilingual UI is separate)
- Do **not** ingest pages with personal identifiers, private forms, or member-only content

### Submit a job

1. Open admin frontend → **Jobs** tab.
2. Click **New job** (or equivalent).
3. Paste one or more **HTTPS URLs** (one per line or as configured).
4. Optional: adjust chunk size / ingest options if exposed.
5. Submit — you receive a **job ID**.
6. Poll job status until **completed** or **failed**.

### What happens behind the scenes

```
Your URLs → Modal scrape worker → chunk → LLM auto-tag → embed → Postgres (via secure write API)
```

See [data-flow.md](../data-flow.md) §Ingest sequence for the full diagram.

### Job outcomes

| Status | Meaning | Action |
|--------|---------|--------|
| `completed` | Documents in corpus | Verify in corpus browser |
| `failed` | Scrape/chunk/embed error | Check error code in job detail; retry or fix URL |
| `running` | In progress | Wait; refresh job status |

**Failed jobs do not corrupt existing corpus** — they leave prior data unchanged.

---

## Managing the corpus

### Browse and search

- **Corpus** tab: paginated document list
- Filter by **tags**, **title**, or **URL search**
- Open **original source URL** in a new tab (no in-app document reader)

### Tags

- Documents and chunks receive **LLM auto-tags** at ingest (from seed vocabulary + new tags capped)
- Operators may **add/remove tags manually** (`source: human`)
- Tag provenance is recorded — no operator name in corpus DB, only audit UUID

**Limits (config):** max ~10 document tags, ~5 chunk tags per item — see [config-spec.md](../config-spec.md).

### Bulk operations (admin only)

Available from corpus selection UI:

| Action | Effect |
|--------|--------|
| Bulk delete | Removes documents, chunks, embeddings, tags |
| Bulk tag | Apply tag to many documents |
| Bulk retag | Re-run LLM tagging |
| Bulk metadata | Edit titles/metadata fields |

All writes create **audit log** entries (immutable).

### Version history

Per-document **history** shows prior versions after metadata/tag edits (EV-002).

---

## Dashboard and health

### Stats summary

Dashboard shows aggregated counts — documents, chunks, recent ingest activity, top-served documents (from ChatRAG usage stats).

### Health panel

Polls all eight services (DO backends, frontends, Modal embed/LLM/data-mgmt). Use before/after deploys or when users report errors.

If a service is red, escalate to infra — see [staging-runbook.md](../staging-runbook.md).

---

## Evaluation and playground (admin)

### RAG evaluation (EV-008)

1. Open **Evaluation** tab.
2. Trigger a **golden-set run** (fixed Q&A fixtures in repo).
3. Review scores (judge LLM metrics) and per-item drill-down.
4. Compare runs over time on dashboard charts.

### Playground (EV-009)

Sandbox RAG + judge settings without affecting production ChatRAG until a **super-admin promotes** config.

---

## Privacy and data handling (ADR-004)

**You must not:**

- Paste personal emails, phone numbers, or names into corpus fields
- Ingest pages containing member PII or private account data
- Expect the system to store **chat conversations** — ChatRAG is stateless on the server

**The system guarantees:**

- Corpus Postgres has **no user accounts or chat history**
- Audit logs use opaque IDs — not your email
- Community chat is **anonymous** — no login on ChatRAG

Report privacy concerns to the project lead before ingesting sensitive content.

---

## Bilingual operation

| Surface | How language works |
|---------|-------------------|
| Admin UI | Toggle EN/ES in header (`vecinita.locale` in browser) |
| ChatRAG UI | Same toggle on chat frontend |
| Ingested content | Stored in source language (EN or ES pages) |
| ChatRAG answers | Auto-matches question language |

Both UIs share locale preference when using the same browser profile.

---

## Staging vs production

| Environment | Admin URL | Notes |
|-------------|-----------|-------|
| Staging | See [deploy-state.md](../deploy-state.md) | Safe for training; corpus may include fixtures |
| Production | TBD at cutover | Ingest only vetted public URLs |

**Corpus protection:** Staging Postgres has backup verification — do not run destructive test scripts against `.ondigitalocean.com` hosts. See [staging-runbook.md](../staging-runbook.md) §Corpus protection.

---

## When to escalate

| Symptom | Likely layer | Reference |
|---------|--------------|-----------|
| 401 on admin API | Supabase session expired | Re-login |
| 403 on write | Viewer role | Request admin role change |
| Ingest stuck / all jobs fail | Modal or write API | Health panel + infra |
| Chat answers wrong language | ChatRAG backend | Not corpus — escalate separately |
| Missing documents after ingest | Write API / migration | Check job completed + corpus browser |

---

## References

- [data-management-dev-guide.md](data-management-dev-guide.md) — schema, APIs, local dev
- [architecture.md](../architecture.md) — system overview
- [data-flow.md](../data-flow.md) — diagrams
- [user-journeys.md](../user-journeys.md) — UJ-003 corpus admin, UJ-001 ask flow
- [LOCAL_DEV.md](../LOCAL_DEV.md) — developer local setup (not operator)
