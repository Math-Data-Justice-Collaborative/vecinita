---
name: beta-features
description: >
  Recommend Beta labeling + GitHub feedback issue links for new or flaky admin
  surfaces (Fine-tune, Playground, etc.). Use when adding admin features, evolve
  intake for unstable paths, or updating README Beta section (F86).
---

# Beta features

[Corpus: feature-list.md §F86]

## When to use

- Adding a new admin surface that is incomplete, GPU-backed, or flaky
- Evolve / build for Fine-tune, Evaluation Playground, or similar
- Updating operator-facing README / GitHub About copy about Beta

## Checklist

- [ ] AskQuestion: mark as Beta? (default **yes** for new/unstable admin features)
- [ ] Mount `BetaFeatureNotice` on the page (and nav chip if top-level route)
- [ ] EN/ES strings under `admin.beta.*`
- [ ] README §Beta features row + link to #374 (or `VITE_BETA_FEEDBACK_ISSUE_URL`)
- [ ] Label related GH issues `beta-feedback`
- [ ] Tests: badge/banner/link (TC-338) and nav chip (TC-339) when UI changes

## Feedback URL

Default: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/374

Rule: `.cursor/rules/beta-features.mdc`
