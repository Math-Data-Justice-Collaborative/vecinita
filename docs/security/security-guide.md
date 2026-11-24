# Vecinita Security Guide (book two of two)

**Three recipes to begin: F-HUMAN, F-FLOOD, F-FAQ.**

September 2026. Pulled from the Security cookbook. Grow this file by appending the next selected dish.

> **About this copy.** This is a repo copy of the *Vecinita Security Guide*, a team
> worksheet kept in the shared Drive. It is reproduced as written, including the
> blank decision lines and the empty KEEP / DROP / LATER and TRUE? columns, which the
> team fills in. The decisions *proposed* for F-HUMAN and F-FLOOD, with how each house
> rule is kept, are on the recipe pages [F-HUMAN.md](F-HUMAN.md) and
> [F-FLOOD.md](F-FLOOD.md). The inventory and the method are in [README.md](README.md).

The cookbook helps every dish we might cook. This guide is only the recipes we are cooking now. House rules travel with every recipe: zero-PII, transparency, auditable records. Good taste: privacy, accountability, and a written trace of how a role got its privileges.

## 00. Before you cook: confirm the pantry

| Shelf | As we understand it today | True? Y / N / note |
|---|---|---|
| **Visitors** | No account required. Supabase Auth exists and is optional. | |
| **Public promise** | Answers stay in the browser. Feedback stored anonymously. | |
| **Admin** | One shared token, hashed client-side, value baked into the frontend build. | |
| **Gateway / auth-proxy** | Validates API keys; per-key rate limits are in-memory. | |
| **Content path** | qo_layer: PII scrub → crisis → FAQ → scope → RAG. | |
| **Logging posture** | Zero-PII: no raw questions persisted; no IP/identity columns; short retention. | |

> Basic assumptions to be confirmed. **If a shelf is wrong, fix it before Recipe 1.**

## 1. F-HUMAN: Is this request from a person?

**From** cookbook dish F-HUMAN. **Not** an account. Not staff login. Not a flood cap.

A Safe Viewer on a cheap phone, in Spanish, must complete this with no extra puzzle.

| Option | Pro | Con | Room: keep / drop / later |
|---|---|---|---|
| **Honeypot + current limits** | No UI. Accessible. No vendor. | Naive bots only. | |
| **Proof-of-work** (Friendly Captcha, ALTCHA, Cap, Private Captcha) | Invisible. Accessible. Fits zero-PII. | Phone pause. CPU can be bought. | |
| **Cloudflare Turnstile** | Invisible. Free. | US path. VPN / AT loops possible. | |
| **reCAPTCHA v3 or image CAPTCHA** | Familiar. | Tracking or accessibility failure. | **Drop unless pantry changes** |
| **WebAuthn key** | Strong personhood. | Not for anonymous visitors. | **Staff only: later dish** |

> **F-HUMAN DECISION**
> Human-check = ____________________ No account. No visual puzzle. No identity created.

Proposed decision, house-rule review and tests: [F-HUMAN.md](F-HUMAN.md) (work item F87).

## 2. F-FLOOD: How do we stop a flood?

**From** cookbook dish F-FLOOD. Protect expensive RAG without naming Maria. Login is not the cap. Do not persist IP as identity.

| Option | Pro | Con | Room: keep / drop / later |
|---|---|---|---|
| **Leave limits in-memory on auth-proxy** | Already there. | Resets per process. | |
| **Sliding window at the gateway** | Smoother than fixed windows. | Needs shared counters if many instances. | |
| **Tier by endpoint cost** (RAG vs health vs feedback) | Protects what actually costs. | Must list the expensive routes. | |
| **Shared counter store** | Holds across instances. | New dependency. Not an identity log. | |
| **Force login to cap by account** | Easy. | Breaks anonymous default. | **Drop as flood control** |
| **Persist IPs as the key** | Simple. | Shared NATs. Fights zero-PII. | **Do not persist** |

> **F-FLOOD DECISION**
> Flood control = ____________________ No login required. No IP kept as identity.

Proposed decision, house-rule review and tests: [F-FLOOD.md](F-FLOOD.md) (work item F88).

## 3. F-FAQ: Who may edit the FAQ?

**From** cookbook dish F-FAQ. A safe editor is a named person with staff login and content-edit only. Mark the grid.

> **The proof we owe is on paper.**
> This table is why Priya may edit listings and may not read questions.

| Privilege | Safe viewer | FAQ editor | Partner (one org) | Operator | Mark: real / want / never |
|---|---|---|---|---|---|
| **Edit FAQ / listings** | **No** | **Yes** | **Own org only** | **Yes** | |
| **Review feedback queue** | **No** | **Decide today** | **Own org only** | **Yes** | |
| **Read a visitor's question** | **No** | **No** | **No** | **No** | |
| **Change guardrails** | **No** | **No** | **No** | **Yes** | |
| **Deploy / secrets / grant roles** | **No** | **No** | **No** | **Yes** | |
| **Shared frontend token** | **No** | **No: retire** | **No** | **No: retire** | |

> **F-FAQ DECISION**
> FAQ editor = named person + staff login + content only.
> Feedback queue: yes / no. Partners: own org only. Cannot read visitor questions. Shared token is not this role.

F-FAQ is about who may *edit* the FAQ. It is not the FAQ fast-path (F85). It has no recipe page or feature entry yet.

## 04. Future menu

Not cooked in this guide. When one is selected, copy its stub from the cookbook and append a recipe page here.

| Dish | What it covers |
|---|---|
| F-JAIL | Crafted questions that push the assistant off its plate. |
| F-VISITOR-ACCOUNT | Magic link or OAuth. Must not become F-HUMAN or F-FLOOD. |
| F-STAFF-AUTH | How editors and operators sign in. After F-FAQ, not instead of it. |
| F-ENFORCE | One door vs many checks. |
| F-LOGS | What we record and for how long. |

This list will grow as gaps appear. Decide implementation by priority.

> **Transparency and audit.**
> We document how each recipe was decided so users and partners can trust the plate. Auditable means we can produce the right record on demand, including the written chain from cookbook dish to role to privilege, without handing over Maria's question.

## 05. Glossary

In order of appearance.

**Cookbook:** The white paper of dishes. Not this file.

**Recipe:** One selected dish, cooked here.

**Gateway / auth-proxy:** Door in front of the backend. API keys and per-key limits. Limits live in memory today.

**Logging posture / Zero-PII:** No raw questions stored. No IP or identity columns. Short retention.

**Honeypot:** Hidden field only bots fill.

**Proof-of-work:** The device does a small puzzle. The person does nothing.

**Cloudflare Turnstile:** Invisible bot check. U.S. path. An F-HUMAN option, not a pick.

**Flood / DDoS:** Too many requests, from one place or many, aimed at cost or downtime.

**RAG:** Lookup-then-model path. The expensive call F-FLOOD protects.

**Tier by endpoint cost:** Different routes, different caps.

**Shared NAT:** Many people appear as one IP. Do not persist that IP.

**Safe Viewer:** Anonymous guest. Default.

**FAQ editor:** Named person who may change curated listings only.

**Privilege:** One allowed action.

**Proof of accuracy:** A written trace of how a role received its privileges. Not runtime.
