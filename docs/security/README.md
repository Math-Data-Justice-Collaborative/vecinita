# Vecinita security: method and inventory

Vecinita does not add security features ad hoc. Every security feature starts in
the same written method, gets an id, is chosen and prioritized by the team, and
is traced from decision to code to test. This page is the map and the inventory.

Each chosen security feature is also a numbered feature in the
[feature list](../feature-list.md), so it follows the normal workflow
(requirements, tests first, implementation, verification). The recipe id
(for example **F-HUMAN**) names the *dish* in the security method; the feature
number (for example **F87**) names the *work item* in this repo.

## The method

| Step | Document | What it holds |
|---|---|---|
| 1. Concepts | *Vecinita Security and Privacy White Paper* | Plain-language foundations, for example authentication ("who, if anyone, is asking?") vs. authorization ("what may they do?"). |
| 2. Every option | *Vecinita Security Cookbook* (book one) | Every security feature we might add, written as a **dish** with a stable id (F-HUMAN, F-FLOOD, ...), options, and tradeoffs. No dish is chosen here. House rules bind every dish. |
| 3. Chosen and prioritized | *Vecinita Security Guide* (book two) | Only the dishes the team selected, in priority order, each with a decision sentence. |
| 4. Recipe in the repo | `docs/security/F-*.md` | The decision, how each house rule is kept, the tests, and open items. |
| 5. Work item | A feature entry in [docs/feature-list.md](../feature-list.md) and a GitHub issue | Starts the implementation and testing workflow. |
| 6. Code | A PR named after the dish | The implementation. |
| 7. Proof | Security QA cases, each naming the dish it proves (`dish:`) | The runner reports results by dish. |

The White Paper, Cookbook, and Guide live in the team's shared Drive.

**House rules** (from the Cookbook, binding on every dish):

- **Zero-PII**: no raw questions, no IP or identity columns.
- **Transparency**: we write down how security works.
- **Auditable**: we can produce a record without reconstructing anyone's question.

## Inventory

| Dish | Question | Feature | Status | Recipe | Reference implementation | QA cases |
|---|---|---|---|---|---|---|
| **F-HUMAN** | Is this request from a person? | [F87](../feature-list.md#f87-are-you-human-verification-security-recipe-f-human) | **In review.** Ported to this repo in [PR #394](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/394) (base `stage`), off by default | [F-HUMAN.md](F-HUMAN.md) (decision), [F-HUMAN-README.md](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/feat/F-HUMAN-turnstile/docs/security/F-HUMAN-README.md) (how-to, arrives with #394) | #394; origin: gateway [PR 39](https://github.com/acadiagit/vecinita/pull/39) | 24 backend and 5 frontend tests in #394; gateway QA HV-01 to HV-11 |
| **F-FLOOD** | How do we stop a flood? | [F88](../feature-list.md#f88-flood-control-security-recipe-f-flood) | **Planned**, next after F87. Coded and tested only in the reference gateway, not yet in this repo | [F-FLOOD.md](F-FLOOD.md) | Gateway [PR 40](https://github.com/acadiagit/vecinita/pull/40) (stacked on PR 39) | Gateway: 37 unit tests, RATE-01 to RATE-05 |
| **F-FAQ** | Who may edit the FAQ? | not yet | Guide recipe 3. Not coded | (not yet) | (not yet) | (none yet) |
| **F-JAIL** | Can a crafted question push the assistant off its plate? | not yet | Future menu | (not yet) | (not yet) | (none yet) |
| **F-LOGS** | What we record and for how long | not yet | Future menu | (not yet) | (not yet) | (none yet) |
| **F-STAFF-AUTH** | How editors and operators sign in | not yet | Future menu. Related: F34, F35 (Supabase Auth for admin surfaces) | (not yet) | (not yet) | (none yet) |
| **F-VISITOR-ACCOUNT** | Optional history for returning users | not yet | Future menu. Related: F33 (browser-local chat history) | (not yet) | (not yet) | (none yet) |
| **F-ENFORCE** | One door vs. many checks | not yet | Future menu | (not yet) | (not yet) | (none yet) |

F-FAQ is about who may *edit* the FAQ. It is not the FAQ fast-path (F85).

## Where the code lives

Each dish was first built and tested as middleware on the FastAPI gateway in
`acadiagit/vecinita` (the *reference gateway*, with a live QA harness in
`tests/security_qa`). The live site answers questions through
`apps/chat-rag-backend`, which does not use that gateway, so each dish is
**ported** here:

- **F-HUMAN** is ported in [PR #394](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/394), in review.
- **F-FLOOD** is not ported yet. A port would follow #394's pattern and be stacked on it.

## Other security documents

- [static-analysis.md](static-analysis.md): hard-fail suite for SAST, secrets, IaC, SBOM and vulnerability scanning, and its commands
- [static-analysis-remediation-2026-07-28.md](static-analysis-remediation-2026-07-28.md): baseline and remediation of the first scan (2026-07-28)
- [gitleaks-resolution.md](gitleaks-resolution.md): Gitleaks findings (QA-005) and how they were resolved

## Adding a security feature

1. Find the dish in the Cookbook, or write a new one there in the same six-block shape.
2. The team selects it into the Guide, gives it a priority, and fills in the decision sentence.
3. Copy [F-HUMAN.md](F-HUMAN.md) as the template for `docs/security/F-<ID>.md`.
4. Add a feature entry (next free F number) to [docs/feature-list.md](../feature-list.md) and open a GitHub issue for it.
5. Build it in a PR named after the dish. Write the tests first. Open the PR against `stage`, not `main` (see `.cursor/rules/stage-before-main.mdc`).
6. Update the inventory table above.
