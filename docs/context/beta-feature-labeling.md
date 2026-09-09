# Context — Beta feature labeling (EV-beta-feature-labeling)

[Corpus: product] [Corpus: feature-list.md §F86]  
**Session:** `EV-beta-feature-labeling` · **Orchestrator:** evolve · **Scale:** standard

## Problem

Fine-tune (F80), Evaluation playground (F37/F38), and similar GPU/cold-start-heavy admin
surfaces are live enough to use but not fully hardened. Operators need clear **Beta**
signaling and a path to file feedback without digging through docs.

## Users / journeys

- Admin / super-admin on Data Management UI (`/finetune`, `/evaluation?tab=playground`)
- Contributors reading README / GitHub About who want to know what is Beta and how to report

## Surfaces

| Surface | Change |
|---------|--------|
| Admin Fine-tune page | Beta badge + short banner + link to feedback issue |
| Admin Evaluation playground (+ download) | Same chrome |
| Admin nav (Fine-tune, Evaluation) | Optional compact Beta chip next to label |
| README | Beta features section + feedback issue link |
| GitHub About (description) | Mention Beta + feedback |
| Cursor rules / skills | Recommend Beta + issue link on new Fn |

## Out of scope (this cycle)

Automations/Freshness/Rebuild Beta; ChatRAG public Beta banner; runtime FT/playground behavior changes.

## Success

Operators see unmistakable Beta labeling on FT + playground; README/About document Beta + issue URL; new-feature process asks for Beta tagging by default.
