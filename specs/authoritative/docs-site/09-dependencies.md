# docs-site — Dependencies

> Auto-generated: 2026-05-12

## Overview

Docusaurus 3 with the classic preset. Minimal dependency surface for a static documentation site.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| Documentation content | `docs/` | Markdown source files for the site |

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| @docusaurus/core | ^3.8.1 | Static site generator framework | Yes |
| @docusaurus/preset-classic | ^3.8.1 | Docs + theme + search preset | Yes |
| @mdx-js/react | ^3.1.0 | MDX support for React components in markdown | Yes |
| react | ^19.0.0 | UI framework (Docusaurus requirement) | Yes |
| react-dom | ^19.0.0 | DOM rendering | Yes |
| clsx | ^2.1.1 | Conditional class names | No |
| prism-react-renderer | ^2.4.1 | Syntax highlighting for code blocks | No |

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| Node.js 20+ | Local / CI | Build requirement |
| GitHub Pages or Render | Cloud | Static file hosting |

## Service Dependencies (runtime calls)

None. The docs-site has zero runtime service dependencies.

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
