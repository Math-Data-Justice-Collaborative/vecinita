# Staff copy-change runbook (ChatRAG + Admin UX)

> **Audience:** Program staff and ops (non-engineers)  
> **Issue:** [#297](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/297)  
> **Source review:** [#199](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/199) / EV-037  
> **Last updated:** 2026-08-31  
> **Cite:** `[Corpus: staff-copy]`

---

## Who owns what

| Role | Owns |
|------|------|
| **Designated program staff** *(set name here when assigned)* | Feedback **triage** (read Admin → Feedback); requesting copy changes; EN/ES content intent |
| **Ops / deploy** | Env knobs (`VECINITA_ENERGY_*`, `VITE_WRWC_DONATE_URL`); Supabase Auth invites / display emails for audit actors |
| **Engineering** | All message keys, cold-start facts, CSS/motion — via PR → `stage` → `main` |

Feedback **notify / stronger no-PII notice** polish is tracked in [#214](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/214) (not editable from this runbook).

---

## 1. Editable without a content PR

These do **not** require changing UI string files. Prefer **staging** first; live prod env changes still need an explicit ops decision.

| What | How | Notes |
|------|-----|-------|
| Donate CTA **URL** | Build/deploy env `VITE_WRWC_DONATE_URL` (default `https://wrwc.org/donate/`) | Changes the link only — CTA **label** still needs a PR (`chat.coldStartDonateCta`) |
| Energy **numeric** factors | ChatRAG backend env: `VECINITA_ENERGY_GPU_TDP_W`, `VECINITA_ENERGY_GPU_UTIL`, `VECINITA_ENERGY_GCO2E_PER_KWH`, `VECINITA_ENERGY_CAR_GCO2E_PER_KM`, optional day/year factors | Tune the heuristic only — [Corpus: config] / ADR-047 |
| Feedback **triage (read)** | Sign in to Admin → **Feedback** | Copy/labels still need a PR until #214 |
| Audit actor **name/email shown** | Supabase Auth user record / invite flow | UI chrome labels are i18n (`admin.audit.*`) |

**Do not confuse:** energy **prose** (advisory / use-guide text) is **not** env-editable — see §2.

---

## 2. Needs an engineering PR

Almost all visitor- and admin-facing copy requires a pull request and deploy.

| Surface | Where engineers edit | Examples |
|---------|----------------------|----------|
| ChatRAG + Admin UI strings | **`packages/frontend-i18n/src/messages.ts`** | Tips, tooltips, energy advisory prose, feedback labels, nav, errors |
| Cold-start **rotating facts** | `apps/chat-rag-frontend/src/coldstart/facts.ts` | Fun facts / marketing blurbs (paired `en` / `es` per entry) |
| Icon motion / reduced-motion | ChatRAG + Admin components + `packages/frontend-ui` | Not copy — accessibility/CSS; respect OS “reduce motion” |

**Single i18n home (after #296):** UI strings live in `packages/frontend-i18n` under `chat.*`, `admin.*`, and `shared.*`. ChatRAG’s local `messages.ts` is only a re-export — do not add a second string table there.

**How to request a change:** File or comment on a GitHub issue with (1) surface, (2) EN text, (3) ES text, (4) screenshot or key name if known. Engineers open a PR into **`stage`** first.

---

## 3. EN / ES pairing rules

1. Every user-visible string change updates **both** English and Spanish in the **same** PR.
2. UI keys: edit both locale maps in `packages/frontend-i18n/src/messages.ts`.
3. Cold-start facts: each fact object must include both `en` and `es`.
4. Do not ship one language “now” and the other “later” — orphaned locales confuse community users.

---

## 4. Feedback triage

1. **Owner:** Designated program staff *(set name in the table above when assigned)*.
2. **Today:** Open Admin → Feedback and read submissions (no visitor accounts — anonymous product feedback).
3. **Notify / stronger bilingual no-PII notice:** tracked in [#214](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/214) — not live until that ships.
4. **Changing public feedback copy** (button labels, privacy note): engineering PR to `chat.feedback*` keys in `frontend-i18n`.

---

## 5. Privacy don’ts (copy)

[Corpus: ADR-004] [Corpus: ADR-046]

- **Never** ask visitors for names, emails, phone numbers, addresses, IDs, immigration/case details, medical info, or other personal data in UI copy, tips, or feedback prompts.
- Feedback is for **product/experience** comments only — we do not need personal identifiers to act on it.
- Audit log shows **operator** Auth emails (admin identity), not ChatRAG visitors — do not treat that column as a place to store community PII.

---

## Quick checklist (before asking eng)

- [ ] Is this an **env** change (donate URL or energy **numbers**) or **prose** (needs PR)?
- [ ] Do I have **EN and ES** for every string?
- [ ] Am I accidentally asking for visitor **PII** in the new copy?
- [ ] For feedback: am I **triaging** in Admin, or requesting **copy/notify** (#214 / PR)?

---

## Related

| Doc / issue | Role |
|-------------|------|
| [corpus-operator-guide.md](corpus-operator-guide.md) | Corpus ingest / tags / automations (not UI copy) |
| [staging-runbook.md](../staging-runbook.md) | Stage → Main promote |
| [#199](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/199) | Maintainability review that spawned this runbook |
| [#296](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/296) | ChatRAG → `frontend-i18n` consolidation (merged) |
| [#214](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/214) | Feedback notice + operator notify |
| `packages/frontend-i18n` | `[Corpus: frontend-i18n]` |
