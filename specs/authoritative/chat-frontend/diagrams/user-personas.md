# chat-frontend — User Personas Diagram

> Auto-generated: 2026-05-12

```mermaid
graph TB
    subgraph Personas
        Community[Community Member]
        Admin[Admin / Developer]
    end

    subgraph "Chat Frontend Touchpoints"
        Chat[Chat Page - /]
        Docs[Documents - /documents]
        AdminRoute[Admin - /admin]
        Login[Login - /login]
    end

    Community -->|"public"| Chat
    Community -->|"public"| Docs
    Admin -->|"authenticated"| AdminRoute
    Admin -->|"auth flow"| Login
    Admin -->|"public"| Chat
```
