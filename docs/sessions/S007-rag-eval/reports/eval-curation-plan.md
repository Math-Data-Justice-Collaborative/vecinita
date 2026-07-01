# Eval curation plan — S007 / F36 / #99

**Session:** S007-rag-eval  
**Stage:** 00-context (planning artifact for 01-requirements)  
**Date:** 2026-07-01  
**Decision:** R67 — golden prompts and expected results via user interview

---

## Purpose

Before build, capture **what we measure** and **what “good” looks like** for Vecinita’s RAG
pipeline. Engineering (harness, UI, persistence) depends on interview-approved golden content.

---

## Interview agenda (01-requirements)

Run as a dedicated **F36 eval curation** block within the 01-requirements interview (not a
separate skill). Batch AskQuestion calls by topic; record resolutions as RD-NNN in session report.

### Block A — Coverage & size

| # | Question | Captures |
|---|----------|----------|
| A1 | Which corpus domains must the golden set cover? (housing, legal aid, food, transit, …) | Domain tags per example |
| A2 | Minimum examples per language (en / es)? | Fixture size target |
| A3 | Include “hard” cases (empty retrieval, ambiguous query, cross-language)? | Edge-case rows in fixture |

### Block B — Golden questions (prompts)

| # | Question | Captures |
|---|----------|----------|
| B1 | For each domain, 2–3 realistic user questions in English | `question` (en) |
| B2 | Approved Spanish equivalents (not machine-default) | `question` (es) |
| B3 | Any questions that must **not** be answerable from corpus? | Negative / abstain cases |

### Block C — Expected retrieval results

| # | Question | Captures |
|---|----------|----------|
| C1 | For each question, which document URL(s) must appear in top-k? | `expected_doc_url` / `expected_doc_urls[]` |
| C2 | Is exact URL match enough, or require specific chunk content? | Harness assertion type |

### Block D — Expected answer results

| # | Question | Captures |
|---|----------|----------|
| D1 | Full reference answer or bullet **required_facts** only? | Fixture field choice |
| D2 | What facts must appear for groundedness pass? | `required_facts[]` |
| D3 | Optional full `reference_answer` for semantic comparison | Long-form rubric |

### Block E — Metric thresholds & judge prompts

| # | Question | Captures |
|---|----------|----------|
| E1 | Retain ≥80% retrieval relevance on golden set? | AC benchmark |
| E2 | Minimum faithfulness / answer-relevancy scores (0–1)? | CI gate vs display-only |
| E3 | Bilingual judge instructions (judge answers in query language?) | Evaluator prompt config |
| E4 | Latency SLO per question on staging (informative vs gate)? | `test-plan` latency TC |

### Block F — Privacy & roles

| # | Question | Captures |
|---|----------|----------|
| F1 | Confirm no real resident PII in golden set | ADR-004 compliance |
| F2 | Can `viewer` role see eval results, or admin-only run + view? | UJ + auth matrix |

---

## Deliverables after interview sign-off

| Deliverable | Path |
|-------------|------|
| Expanded golden fixture | `data/fixtures/eval/qa_pairs.json` |
| Curation runbook | `docs/eval-golden-set.md` (new — how to add/change examples) |
| F36 feature entry | `docs/feature-list.md` |
| User journey | `docs/user-journeys.md` — UJ-NNN admin run eval + drill-down |
| Test cases | `docs/test-plan.md` — TC-NNN harness + admin e2e |
| Acceptance criteria | `docs/acceptance-criteria.md` — per-metric thresholds |
| Session report | `docs/sessions/S007-rag-eval/reports/01-requirements.md` |

---

## Optional: baseline results capture

After golden set is approved and a **staging** eval run is possible (post-07-build or dry-run in
01 with mocked scores):

1. Run golden set once through pipeline.
2. Store snapshot in session report as **baseline v1**.
3. Admin tab “history” compares future runs to this baseline.

Baseline capture is **post-build** unless user wants to paste expected scores manually during interview.

---

## Sequencing

```
00-context (R63 tooling + R67 interview plan) ✓
    ↓
01-requirements — Blocks A–F interview → qa_pairs.json + docs
    ↓
04-tech-plan — schema, API, ADR for R63
    ↓
07-build — runner uses interview-approved fixture
```
