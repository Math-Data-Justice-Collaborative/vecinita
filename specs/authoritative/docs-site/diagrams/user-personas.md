# docs-site — User Personas Diagram

> Auto-generated: 2026-05-12

```mermaid
graph TB
    subgraph Personas
        Dev[Developer / Contributor]
        Maintainer[Solo Developer / Maintainer]
    end

    subgraph "Docs Site Touchpoints"
        Home[Home Page /]
        Docs[Documentation Hub /docs]
        Edit[Edit This Page - GitHub]
        LocalDev[Local Dev Server :3000]
    end

    Dev -->|"read"| Home
    Dev -->|"browse"| Docs
    Dev -->|"contribute"| Edit
    Maintainer -->|"preview"| LocalDev
    Maintainer -->|"publish"| Docs
```
