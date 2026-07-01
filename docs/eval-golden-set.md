# Golden evaluation set — curation runbook

> **Feature:** F36 (EV-008 / S007 / GitHub #99)  
> **Fixture:** `data/fixtures/eval/qa_pairs.json`  
> **Last updated:** 2026-07-01 (01-requirements interview RD-099–RD-110)

## Purpose

The golden set is the **regression benchmark** for Vecinita RAG quality. It drives:

- CI harness (`tests/eval/`) — retrieval + answer-quality metrics
- Admin **Evaluation** tab — on-demand runs and history (F36)
- Coordination with #83 (reranking) and #84 (groundedness)

## Fixture schema

Each row is one locale variant of an eval case (`id` groups bilingual pairs).

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Stable case id (e.g. `community-food-pantry`) |
| `locale` | Yes | `en` or `es` |
| `domain` | Yes | `community`, `housing`, `legal`, or `edge` |
| `question` | Yes | User phrasing (no production PII) |
| `expected_doc_url` | For `hit` | Single doc URL that must appear in top-k |
| `expected_doc_urls` | For `any_of` | Any listed URL in top-k passes retrieval |
| `retrieval_expectation` | Yes | `hit` \| `any_of` \| `abstain` \| `empty` |
| `required_facts` | Yes | Bullets the answer must satisfy for faithfulness / answer relevancy |

**Retrieval aggregate (≥80%):** Computed over rows with `retrieval_expectation` of `hit` or `any_of` only (11 rows in v1). Edge `abstain` / `empty` rows use separate assertions (TC-113).

## v1 coverage (interview-approved)

| Domain | Cases | Locales | Notes |
|--------|-------|---------|-------|
| Community | 4 | en + es | Food pantry, Wi-Fi, story time, Vecinita intro |
| Housing | 1 | en only | Eviction written notice — add es when corpus has es doc (#94) |
| Legal aid | 2 | en only | Housing disputes, benefits appeals |
| Edge | 3 | en | Abstain (mayor phone), ambiguous query, empty retrieval |

**Total:** 10 cases, 14 locale rows.

## How to add or change an example

1. **Pick domain** — must map to a real corpus document (or intentional edge case).
2. **Draft question** — realistic community phrasing; get product sign-off for en and es pairs.
3. **Set expected source(s)** — `fixture://` URL(s) that exist in `data/fixtures/corpus/` (or production corpus URL after ingest).
4. **List `required_facts`** — short bullets grounded in the source doc; no invented PII.
5. **Update fixture** — append/edit `qa_pairs.json`; keep `id` stable when editing wording.
6. **Run harness locally** — `uv run pytest tests/eval -m integration` (Postgres required).
7. **Record baseline** — after a staging eval run, note scores in the admin tab or session report.

## Privacy (ADR-004)

- No real resident names, addresses, phone numbers, or case details.
- Use synthetic or public-corpus-only scenarios.
- Eval run persistence stores **question text from the fixture only** — not live operator or visitor prompts.

## Bilingual policy

- Community rows: **paired en/es** with locale-appropriate corpus URLs.
- Housing/legal: **en-only in v1** until Spanish corpus documents land (#94). Do not add es rows that expect en doc URLs without an explicit interview decision.

## Judge guidelines (LlamaIndex evaluators)

- Judge LLM uses the **same Modal self-hosted HTTP LLM** as ChatRAG.
- Evaluator prompts evaluate in the **query language** (en question → en rubric; es → es).
- Faithfulness: answer must be supported by retrieved context and include `required_facts` where applicable.
- Answer relevancy: answer must address the question without unrelated filler.
- When #84 groundedness lands, the eval tab should surface the **same groundedness signal** — do not maintain a duplicate verifier.

## Related specs

- Thresholds: `docs/acceptance-criteria.md` (AC-E12–AC-E16)
- API: `docs/api-contract.md` §EV-008 eval routes
- Config: `docs/config-spec.md` §RAG evaluation (F36)
- Implementation: `docs/adr/ADR-033-ev008-rag-evaluation-implementation.md`
