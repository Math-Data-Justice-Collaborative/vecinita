# docs-site — Technical Decisions

> Auto-generated: 2026-05-12

## Overview

Technical decisions for the docs-site, focused on documentation tooling and hosting choices.

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Documentation framework | Docusaurus 3 | MkDocs, VitePress, GitBook, plain HTML | 2026-05-12 | Moderate |
| TD-002 | Content source | Monorepo `docs/` directory | Separate repo, inline in docs-site | 2026-05-12 | Easy |
| TD-003 | Sidebar strategy | Auto-generated from directory structure | Manual sidebar config | 2026-05-12 | Easy |
| TD-004 | Blog feature | Disabled | Enabled for changelog/updates | 2026-05-12 | Easy |
| TD-005 | Broken link policy | Warn (not error) | Throw (strict), ignore | 2026-05-12 | Easy |

### TD-001: Documentation Framework — Docusaurus 3

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Need a documentation site for the Vecinita project |
| Decision | Use Docusaurus 3 with the classic preset |
| Rationale | React-based (consistent with the project stack), excellent markdown support, built-in search, versioning capability, GitHub Pages integration, active maintenance by Meta |
| Alternatives considered | **MkDocs** — Python-based, doesn't match stack. **VitePress** — Vue-based. **GitBook** — hosted service with less control. |
| Consequences | Adds React 19 as a dependency (different version from frontends using React 18). Build requires Node.js 20+. |
| Reversibility | Moderate — markdown content is portable, but theme/config is Docusaurus-specific |

### TD-002: Content Source — Monorepo `docs/` Directory

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Where should documentation markdown files live |
| Decision | Read from `../docs/` (monorepo root `docs/` directory), not duplicated into `docs-site/` |
| Rationale | Single source of truth. Docs stay close to code. No content duplication. |
| Alternatives considered | **Separate repo** — harder to keep in sync. **Inline** — duplicates content. |
| Consequences | Docusaurus config uses relative path `../docs`. Build must run from `docs-site/` directory context. |
| Reversibility | Easy — change `docs.path` in config |

### TD-005: Broken Link Policy — Warn

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | How to handle broken markdown links during build |
| Decision | `onBrokenLinks: "warn"` — log warnings but don't fail the build |
| Rationale | Documentation is evolving. Strict mode would block deployments for non-critical link issues. |
| Alternatives considered | **throw** — strictest, fails build. **ignore** — hides problems. |
| Consequences | Broken links may ship to production. Requires periodic review of build warnings. |
| Reversibility | Easy — change config setting |

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | Hosting platform | GitHub Pages, Render static, both | Cost, deployment complexity | Low | GitHub Pages |
| PTD-002 | Doc content expansion | Include more docs, keep minimal | Documentation coverage | Low | Expand includes |

### PTD-001: Hosting Platform

| Property | Value |
|----------|-------|
| Status | Pending |
| Identified | 2026-05-12 |
| Evidence | Config targets GitHub Pages (`url: "https://acadiagit.github.io"`, `baseUrl: "/vecinita/"`) but the service could also run on Render |
| Impact | Deployment workflow, cost, URL structure |
| Decision deadline | Before first public documentation release |

**Option A: GitHub Pages**
- Pros: Free, automatic deployment via GitHub Actions, standard for OSS docs
- Cons: Limited to static files, no custom headers
- Effort: S
- Ecosystem fit: Excellent — already configured in `docusaurus.config.ts`

**Option B: Render static site**
- Pros: Consistent with other Vecinita services, preview environments
- Cons: Uses starter plan allocation, one more service to manage
- Effort: S
- Ecosystem fit: Good — fits existing Render infrastructure

**Recommendation:** GitHub Pages — purpose-built for static documentation, free, already configured.
**Risk of continued deferral:** Low. Documentation site can be built and previewed locally regardless.

### PTD-002: Documentation Content Expansion

| Property | Value |
|----------|-------|
| Status | Pending |
| Identified | 2026-05-12 |
| Evidence | `docs.include` only has `["README.md", "guides/greeting.md"]` — very narrow inclusion list despite more content in `docs/` |
| Impact | Documentation coverage and usefulness |
| Decision deadline | Before first public documentation release |

**Recommendation:** Expand includes to cover deployment guides, API references, and architecture docs.
**Risk of continued deferral:** Documentation site has minimal content, reducing its value.

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
