# Vecinita — GitHub Project Board

> [Math-Data-Justice-Collaborative/vecinita](https://github.com/Math-Data-Justice-Collaborative/vecinita) · Paste into Project → ⋯ → Settings → README  
> **Updated:** 2026-05-30

**Vecinita** is a bilingual community Q&A (ChatRAG) and corpus admin platform — six apps, hybrid **DigitalOcean + Modal**, zero PII ([ADR-004](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/adr/ADR-004-cost-sovereignty-zero-personal-data.md)). See [README](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/README.md) for architecture.

This board tracks **issues and PRs in flight**. Specs live in [`docs/`](https://github.com/Math-Data-Justice-Collaborative/vecinita/tree/main/docs); pipeline state in [`workflow-state.yaml`](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/workflow-state.yaml).

## Status

| Area | Status |
|------|--------|
| v1 (F1–F18) + EV-001/002/003 | Shipped |
| Staging | Live — [deploy-state](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/deploy-state.md) |
| Backlog | [roadmap](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/reference.md#roadmap) Phase 6 |

## Columns

**Backlog** → **Ready** → **In progress** → **In review** → **Blocked** → **Deploy / verify** → **Done**

- **Ready:** acceptance criteria clear, unblocked
- **Deploy / verify:** merged; staging smoke (H1–H5) pending
- **Done:** merged, CI green on `main`, deploy verified if user-facing

Move cards on **state change** — draft PRs stay *In progress*; merged PRs awaiting smoke stay *Deploy / verify*.

## Work types & branches

| Type | Branch | Notes |
|------|--------|-------|
| Feature (post-v1) | `evolve/EV-NNN-slug` | Update [feature-list](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/feature-list.md) |
| Bug | `fix/slug` | Repro test in `tests/bugs/` |
| Infra / deploy | `infra/slug` | Watch `deploy-preflight` on `main` |
| Docs / chore | `docs/slug`, `chore/slug` | — |

Do not track secrets (`*-spec.yaml`, `prod.env`) on the board.

## Issues & PRs

**Titles:** `[EV-NNN] …` · `[Fnn] …` · `[fix] …`

**Issue body:** feature ID (F1–F30), user journey if applicable (UJ-*), spec/ADR link, apps touched, deploy impact.

**PRs:** link issues (`Closes #N`); `ci.yml` green on branch; on `main` also `deploy-preflight.yml`. After merge: `bash scripts/ci/watch_github_ci.sh main`.

**Labels (recommended):** `evolve`, `hotfix`, `app:chat-rag`, `app:admin`, `app:infra`, `privacy`, `deploy`, `blocked`

## Views

| View | Layout | Filter |
|------|--------|--------|
| **Board** | Board | `repo:Math-Data-Justice-Collaborative/vecinita` — group by **Status** in UI |
| **Active sprint** | Board | `status:"Ready","In progress","In review"` |
| **Deploy queue** | Table | `status:"Deploy / verify"` |
| **Deploy label** | Table | `label:deploy -status:Done` |
| **By app** | Table | `label:app:chat-rag,app:admin,app:infra` |
| **Evolve cycles** | Table | `label:evolve` |
| **Bugs** | Table | `label:bug,hotfix` |
| **Blocked** | Board | `status:Blocked` |
| **All items** | Table | `repo:Math-Data-Justice-Collaborative/vecinita` |

## Definition of done

Merged to `main` · tests + types green · no PII regressions · CI green · staging smoke if shipped · docs/ADR updated for new behavior.

Hotfixes: bug report in `docs/bug-reports/` + repro test (red → green).

## Key docs

[feature-list](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/feature-list.md) · [execution-plan](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/execution-plan.md) · [user-journeys](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/user-journeys.md) · [acceptance-criteria](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/acceptance-criteria.md) · [deploy-checklist](https://github.com/Math-Data-Justice-Collaborative/vecinita/blob/main/docs/deploy-checklist.md) · [adr/](https://github.com/Math-Data-Justice-Collaborative/vecinita/tree/main/docs/adr)

## Priorities

1. Bugs breaking CI or staging smokes beat new features.
2. Backlog from roadmap Phase 6 and evolve cycles — not ad-hoc work without a feature ID.
3. Constraints: zero PII, US hosting, ~$50/mo pilot cap (ADR-004).

*Update **Status** when an evolve cycle ships or staging changes.*
