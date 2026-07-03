# Vecinita Data Flow Diagrams

> **Status:** Draft (issue #58)  
> **Last updated:** 2026-07-03  
> **Format:** Mermaid in `docs/` — render on GitHub or in VS Code Mermaid preview.

Companion to [architecture.md](architecture.md). Covers C4-style overview, sequences, ERD, state machines, class diagrams, requirement traceability, user journeys, and flowcharts. **ADR-004** zero-PII boundaries annotated.

---

## Diagram index

| § | Type | Title |
|---|------|-------|
| — | Legend | [Color coding](#color-legend) |
| 1 | C4 context | System context |
| 2 | Flowchart | Container diagram (DO + Modal split) |
| 3–6 | Sequence | Ingest, query, admin, eval |
| 7 | Table | Data store summary |
| 8 | ERD | Corpus Postgres schema |
| 9–11 | State | Job, eval run, admin auth session |
| 12–13 | Class | RAG pipeline + shared schemas |
| 14 | Requirement | Features → components |
| 15–16 | Journey / flowchart | Key user journeys |
| 17 | Flowchart | CI/CD deploy pipeline |

Narrative journey steps: [user-journeys.md](user-journeys.md).

---

## Color legend

Apply these `classDef` styles across flowcharts for consistent parsing. Actors use **cool blue** (community), **purple** (operator), platforms use **green** (DO), **indigo** (Modal), **amber** (Supabase), **teal** (data stores).

| Class | Meaning | Fill | Stroke |
|-------|---------|------|--------|
| `community` | Community member / ChatRAG surface | `#e3f2fd` | `#1565c0` |
| `operator` | Corpus operator / admin UI | `#f3e5f5` | `#7b1fa2` |
| `do` | DigitalOcean services | `#e8f5e9` | `#2e7d32` |
| `modal` | Modal GPU/CPU workers | `#e8eaf6` | `#3949ab` |
| `supabase` | Supabase Auth (operator identity) | `#fff3e0` | `#ef6c00` |
| `datastore` | Postgres / pgvector corpus | `#e0f2f1` | `#00695c` |
| `package` | Shared `packages/*` modules | `#f5f5f5` | `#616161` |
| `external` | Public web, CI, browsers | `#fafafa` | `#9e9e9e` |

```mermaid
flowchart LR
    subgraph Legend["Diagram color legend"]
        L1[community]:::community
        L2[operator]:::operator
        L3[do]:::do
        L4[modal]:::modal
        L5[supabase]:::supabase
        L6[datastore]:::datastore
        L7[package]:::package
        L8[external]:::external
    end
    classDef community fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef operator fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef do fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef modal fill:#e8eaf6,stroke:#3949ab,color:#1a237e
    classDef supabase fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef datastore fill:#e0f2f1,stroke:#00695c,color:#004d40
    classDef package fill:#f5f5f5,stroke:#616161,color:#212121
    classDef external fill:#fafafa,stroke:#9e9e9e,color:#424242
```

---

## 1. C4-style system context

Community members use ChatRAG (anonymous). Corpus operators use the admin UI (Supabase-authenticated). All corpus content is **public community material** — no end-user PII in Postgres.

```mermaid
C4Context
    title Vecinita — System Context (C4 Level 1)

    Person communityMember as "Community member"
    Person operator as "Corpus operator"

    System(vecinita as "Vecinita", "Bilingual RAG Q&A + corpus management") {
        System(chatrag as "ChatRAG", "Anonymous Q&A")
        System(admin as "Admin platform", "Ingest + corpus CRUD")
    }

    System_Ext(supabase as "Supabase Auth", "Operator identity only")
    System_Ext(publicWeb as "Public web", "Source URLs for ingest")

    Rel(communityMember, chatrag, "Asks questions (EN/ES)", "HTTPS")
    Rel(operator, admin, "Manages corpus", "HTTPS + JWT")
    Rel(operator, supabase, "Login / invite accept", "HTTPS")
    Rel(admin, publicWeb, "Scrapes public URLs", "HTTPS")
    Rel(admin, supabase, "Verify JWT", "JWKS")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## 2. C4-style container diagram

Shows the **Modal + DigitalOcean split** and where data stores live. Dashed boundary = zero PII in corpus DB (ADR-004).

```mermaid
flowchart TB
    subgraph Browser["Browser"]
        CF[ChatRAG Frontend<br/>EN/ES UI chrome]
        AF[Admin Frontend<br/>EN/ES + Supabase session]
    end

    subgraph DO["DigitalOcean — US region"]
        CB[ChatRAG Backend<br/>FastAPI + LlamaIndex]
        IW[Internal Write API<br/>Sole write path to Postgres]
        PG[(Managed Postgres<br/>pgvector 384-dim<br/>documents · chunks · embeddings · tags · jobs · audit)]
    end

    subgraph Modal["Modal — US workspace"]
        DM[Data Mgmt ASGI<br/>POST /jobs]
        WQ[Ingest Workers<br/>scrape · chunk · tag]
        FE[FastEmbed<br/>384-dim vectors]
        LLM[vLLM Qwen2.5-1.5B<br/>generate + judge]
    end

    subgraph Supabase["Supabase — separate DB"]
        AUTH[(auth.users<br/>operator email/password)]
    end

    CF -->|POST /api/v1/ask/stream<br/>GET /documents, /tags| CB
    AF -->|Bearer JWT| IW
    AF -->|Bearer JWT| DM
    AF -->|session| AUTH

    CB -->|read| PG
    CB -->|embed query| FE
    CB -->|generate| LLM
    CB -.->|async stats| IW

    DM --> WQ
    WQ -->|fetch HTML| PublicWeb[Public URLs]
    WQ --> FE
    WQ --> LLM
    WQ -->|VECINITA_INTERNAL_API_KEY<br/>chunks + embeddings + tags| IW
    IW -->|write| PG

    classDef community fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef operator fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c
    classDef do fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef modal fill:#e8eaf6,stroke:#3949ab,color:#1a237e
    classDef supabase fill:#fff3e0,stroke:#ef6c00,color:#e65100
    classDef datastore fill:#e0f2f1,stroke:#00695c,color:#004d40
    classDef external fill:#fafafa,stroke:#9e9e9e,color:#424242

    class CF community
    class AF operator
    class CB,IW do
    class DM,WQ,FE,LLM modal
    class AUTH supabase
    class PG datastore
    class PublicWeb external
```

**PII boundary:** Postgres stores **no** emails, names, or chat history. Supabase holds operator identity only. Audit log may store opaque `actor_id` (UUID) — not PII (ADR-026).

---

## 3. Sequence — Ingest → embed → store

Operator submits URLs from admin UI. Content flows through Modal workers; persistence goes through DO internal write API only.

```mermaid
sequenceDiagram
    autonumber
    participant Op as Operator (admin UI)
    participant AF as Admin Frontend
    participant DM as Modal Data Mgmt ASGI
    participant Q as Modal Ingest Worker
    participant Web as Public URL
    participant LLM as Modal vLLM
    participant FE as Modal FastEmbed
    participant IW as DO Internal Write API
    participant PG as DO Postgres

    Op->>AF: Submit URL list + options
    AF->>DM: POST /jobs (JWT + proxy auth)
    DM->>Q: Enqueue scrape job
    DM-->>AF: job_id

    Q->>Web: HTTP GET (scrape)
    Web-->>Q: HTML / text
    Note over Q: Chunk text (config chunk_size)
    Q->>LLM: Auto-tag document/chunks<br/>(seed vocabulary, max 10/5 tags)
    LLM-->>Q: tag labels (EN/ES aware)
    Q->>FE: POST /embed/batch
    FE-->>Q: vector(384) per chunk

    Q->>IW: POST /internal/v1/... (service key)<br/>documents + chunks + embeddings + tags
    IW->>PG: Upsert rows
    PG-->>IW: OK
    IW-->>Q: 200
    Q->>IW: PATCH job status
    AF->>DM: GET /jobs/{id} (poll)
    DM-->>AF: completed | failed
```

**Bilingual note:** Source pages may be EN or ES; tagging uses vocabulary slugs with language metadata. No translation step in ingest — content stored as scraped.

**Privacy note:** Job records store URL and status only — no operator email in Postgres.

---

## 4. Sequence — Query → retrieval → LLM response

Community member asks a question. ChatRAG is **stateless** — no server-side chat history (ADR-004, ADR-006).

```mermaid
sequenceDiagram
    autonumber
    participant User as Community member
    participant CF as ChatRAG Frontend
    participant CB as ChatRAG Backend
    participant FE as Modal FastEmbed
    participant PG as DO Postgres (pgvector)
    participant RAG as packages/rag (LlamaIndex)
    participant LLM as Modal vLLM
    participant IW as Internal Write API

    User->>CF: Type question (EN or ES)<br/>optional tag filter
    CF->>CB: POST /api/v1/ask/stream<br/>{question, tags?}

    Note over CB: detect_language(question) → en | es
    CB->>FE: Embed query text
    FE-->>CB: query vector(384)

    CB->>PG: pgvector similarity + tag JOIN<br/>top_k chunks
    PG-->>CB: retrieved chunks + metadata

    CB->>RAG: Build context + synthesize prompt
    RAG->>LLM: POST /generate/stream
    LLM-->>CB: token stream
    CB-->>CF: SSE tokens
    CF-->>User: Render answer in detected language

    CB--)IW: POST /stats/served (async, fire-and-forget)
    IW--)PG: increment serving counter
```

**Bilingual paths:**

| Step | EN path | ES path |
|------|---------|---------|
| UI chrome | `vecinita.locale=en` or browser `en*` | `vecinita.locale=es` or default ES |
| Query language | Auto-detect from question text | Auto-detect from question text |
| Response language | Matches detected query language | Matches detected query language |
| Retrieval | Same pgvector index; corpus has EN + ES documents | Same |

User-selected **tags** override LLM-inferred tags when provided (spec §Data Flow step 9).

---

## 5. Sequence — Admin / corpus management

Operators browse, edit tags, bulk delete, view audit — via internal write API. Ingest jobs via Modal ASGI.

```mermaid
sequenceDiagram
    autonumber
    participant Op as Operator
    participant AF as Admin Frontend
    participant SB as Supabase Auth
    participant IW as Internal Write API
    participant DM as Modal Data Mgmt
    participant PG as DO Postgres

    Op->>AF: Login (email + password)
    AF->>SB: signInWithPassword
    SB-->>AF: JWT (admin | viewer role)

    Op->>AF: Open corpus dashboard
    AF->>IW: GET /internal/v1/stats/summary (JWT)
    IW->>PG: aggregate queries
    PG-->>IW: stats
    IW-->>AF: dashboard data

    Op->>AF: Bulk tag / delete documents
    alt viewer role
        AF->>IW: PATCH bulk (JWT)
        IW-->>AF: 403 Forbidden
    else admin role
        AF->>IW: PATCH /internal/v1/documents/bulk/tags
        IW->>PG: update + audit_log row<br/>(actor_id UUID only)
        IW-->>AF: 200
    end

    Op->>AF: Start ingest job
    AF->>DM: POST /jobs (JWT)
    Note over DM,IW: See ingest sequence diagram

    Op->>AF: View audit log
    AF->>IW: GET /internal/v1/audit
    IW->>PG: paginated audit_log
    IW-->>AF: entries (request_id, actor_id — no email)
```

---

## 6. Evaluation path (admin — EV-008)

Golden-set eval runs use the same Modal LLM as ChatRAG for judging. Results stored in Postgres via internal write API.

```mermaid
sequenceDiagram
    participant AF as Admin Frontend
    participant IW as Internal Write API
    participant ER as Eval Runner
    participant CB as ChatRAG Backend
    participant LLM as Modal vLLM
    participant PG as DO Postgres

    AF->>IW: POST /internal/v1/eval/runs (JWT admin)
    IW->>ER: Trigger golden run
    loop each eval item
        ER->>CB: POST /api/v1/ask (fixture question)
        CB-->>ER: answer + sources
        ER->>LLM: Judge prompt (metrics)
        LLM-->>ER: scores
    end
    ER->>IW: Persist results
    IW->>PG: eval_runs + eval_run_items
    AF->>IW: GET /internal/v1/eval/runs/{id}
    IW-->>AF: history + drill-down
```

---

## 7. Data store summary

| Store | Contents | PII? | Region |
|-------|----------|------|--------|
| DO Postgres | Corpus, embeddings, jobs, audit, eval | No (opaque actor UUID only) | US (DO) |
| Supabase Auth | Operator accounts, invites | Yes — admin only, separate DB | Supabase project |
| Modal volumes | Model weights (FastEmbed, Qwen) | No user content | US Modal |
| Browser localStorage | `vecinita.locale`, eval dashboard prefs | Device-local only | Client |

---

## 8. Entity-relationship diagram (corpus Postgres)

Alembic head `20260702_0007`. **Supabase `auth.users` is a separate database** — not shown. `owner_id` / `promoted_by` / `actor_id` are opaque UUIDs only (ADR-004, ADR-026).

```mermaid
erDiagram
    documents ||--o{ chunks : "has"
    chunks ||--|| embeddings : "vector384"
    documents ||--o{ document_tags : "tagged"
    tags ||--o{ document_tags : "applied"
    chunks ||--o{ chunk_tags : "tagged"
    tags ||--o{ chunk_tags : "applied"
    documents ||--o{ document_versions : "history"
    documents ||--o| document_serving_stats : "served_count"
    eval_runs ||--o{ eval_run_items : "contains"
    eval_config_presets ||--o{ eval_runs : "optional preset"

    documents {
        uuid id PK
        text url UK
        text title
        text content_hash
        string language
        timestamptz created_at
    }
    chunks {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text text
        int token_count
    }
    embeddings {
        uuid id PK
        uuid chunk_id FK UK
        vector384 embedding
    }
    tags {
        uuid id PK
        text slug
        text label
        string language
    }
    document_tags {
        uuid document_id FK
        uuid tag_id FK
        string source
    }
    chunk_tags {
        uuid chunk_id FK
        uuid tag_id FK
        string source
    }
    jobs {
        uuid id PK
        string status
        string job_type
        json urls
    }
    audit_log {
        uuid id PK
        string event_type
        uuid entity_id
        uuid request_id
        uuid actor_id
        string actor_role
        json payload
    }
    document_versions {
        uuid id PK
        uuid document_id FK
        int version_number
        json tags_snapshot
    }
    document_serving_stats {
        uuid document_id PK FK
        int served_count
    }
    eval_runs {
        uuid id PK
        string status
        string mode
        uuid preset_id FK
        json config_snapshot
        json metrics_summary
    }
    eval_run_items {
        uuid id PK
        uuid run_id FK
        string case_id
        text question
        json metrics
    }
    eval_criteria {
        uuid id PK
        string slug UK
        string scorer_type
        text rubric
        bool enabled
    }
    eval_config_presets {
        uuid id PK
        string preset_name
        uuid owner_id
        json config
        bool shared
    }
    rag_production_config {
        uuid id PK
        json config
        int config_version
        bool is_active
        uuid promoted_by
    }
    config {
        text key PK
        json value
    }
```

**Note:** `GET /jobs` may surface eval runs with virtual `job_type=eval` merged from `eval_runs` (F37) — not a `jobs` table column.

---

## 9. State diagram — ingest job lifecycle

Modal ingest workers update job status via the internal write API. Operators poll from the admin UI.

```mermaid
stateDiagram-v2
    [*] --> pending: POST /jobs (URLs submitted)

    pending --> running: worker dequeues
    running --> completed: scrape + chunk + embed + upsert OK
    running --> failed: scrape/LLM/embed/write error

    completed --> [*]
    failed --> [*]

    note right of pending
        job_type: ingest | retag
        No operator email in row (ADR-004)
    end note
```

---

## 10. State diagram — eval run lifecycle

Golden-set and playground eval runs (F36, F37). Persisted in `eval_runs`; items in `eval_run_items`.

```mermaid
stateDiagram-v2
    [*] --> queued: POST /internal/v1/eval/runs

    queued --> running: runner starts
    running --> completed: all items judged
    running --> failed: ChatRAG or judge error

    completed --> [*]
    failed --> [*]

    state running {
        [*] --> ask_item
        ask_item --> judge_item: POST /api/v1/ask
        judge_item --> ask_item: more items
        judge_item --> [*]: last item
    }
```

---

## 11. State diagram — admin auth session

Operator identity lives in **Supabase only**. JWT carries `admin` or `viewer` role claim for internal-write API authorization.

```mermaid
stateDiagram-v2
    [*] --> anonymous: open admin UI

    anonymous --> authenticating: login / invite accept / password reset
    authenticating --> authenticated: Supabase JWT issued
    authenticating --> anonymous: invalid credentials

    authenticated --> viewer_session: role=viewer
    authenticated --> admin_session: role=admin

    viewer_session --> anonymous: logout / token expiry
    admin_session --> anonymous: logout / token expiry

    state viewer_session {
        [*] --> read_only
        read_only --> forbidden: write API call
        forbidden --> read_only
    }

    state admin_session {
        [*] --> read_write
        read_write --> audit_logged: corpus mutation
        audit_logged --> read_write
    }
```

---

## 12. Class diagram — RAG pipeline (`packages/rag`)

Core types used by ChatRAG backend. LlamaIndex `BaseRetriever` adapter wraps pgvector SQL.

```mermaid
classDiagram
    direction LR

    class CorpusPgvectorRetriever {
        -Engine engine
        -EmbedFn embed_fn
        -int top_k
        +retrieve(query) NodeWithScore[]
        -_fetch_chunks(embedding, tags) RetrievedChunk[]
    }

    class RetrievedChunk {
        <<dataclass>>
        +UUID chunk_id
        +UUID document_id
        +str text
        +float score
        +str title
        +str url
        +str language
    }

    class RagAnswer {
        <<dataclass>>
        +str answer
        +str language
        +list~RetrievedChunk~ sources
    }

    class BaseRetriever {
        <<LlamaIndex>>
        +retrieve(query)
    }

    BaseRetriever <|-- CorpusPgvectorRetriever
    RagAnswer --> RetrievedChunk : sources
    CorpusPgvectorRetriever ..> RetrievedChunk : produces
```

---

## 13. Class diagram — shared schemas (write path)

Pydantic models in `packages/shared-schemas` at the Modal → internal-write API boundary.

```mermaid
classDiagram
    direction TB

    class BatchUpsertRequest {
        +list~DocumentUpsert~ documents
        +str request_id
    }

    class DocumentUpsert {
        +str url
        +str title
        +str language
        +list~ChunkUpsert~ chunks
        +list~TagInput~ tags
    }

    class ChunkUpsert {
        +int chunk_index
        +str text
        +list~float~ embedding
        +list~TagInput~ tags
    }

    class TagInput {
        +str slug
        +str label
        +str language
        +str source
    }

    class Job {
        +UUID id
        +str status
        +Literal job_type
        +list urls
    }

    BatchUpsertRequest --> DocumentUpsert
    DocumentUpsert --> ChunkUpsert
    DocumentUpsert --> TagInput
    ChunkUpsert --> TagInput
```

---

## 14. Requirement diagram — features to components

Traceability from [feature-list.md](feature-list.md) to deployable components. Verification via [test-plan.md](test-plan.md) / `tests/e2e/`.

```mermaid
requirementDiagram

    requirement F1_bilingual_qa {
        id: F1
        text: Bilingual community Q&A (RAG)
        risk: high
        verifymethod: test
    }

    requirement F7_ingest {
        id: F7
        text: URL scrape, chunk, embed, store
        risk: high
        verifymethod: test
    }

    requirement F15_privacy {
        id: F15
        text: Zero PII in corpus DB
        risk: high
        verifymethod: inspection
    }

    requirement F34_admin_auth {
        id: F34
        text: Supabase auth for admin surfaces
        risk: medium
        verifymethod: test
    }

    requirement F36_eval {
        id: F36
        text: Golden-set RAG evaluation
        risk: medium
        verifymethod: test
    }

    element chat_rag_backend {
        type: module
        docref: apps/chat-rag-backend
    }

    element chat_rag_frontend {
        type: module
        docref: apps/chat-rag-frontend
    }

    element modal_workers {
        type: module
        docref: apps/data-management-backend
    }

    element internal_write_api {
        type: module
        docref: apps/internal-write-api
    }

    element supabase_auth {
        type: module
        docref: supabase/
    }

    element eval_runner {
        type: module
        docref: packages/eval
    }

    element privacy_tests {
        type: test
        docref: tests/privacy/
    }

    F1_bilingual_qa - satisfies -> chat_rag_backend
    F1_bilingual_qa - satisfies -> chat_rag_frontend
    F7_ingest - satisfies -> modal_workers
    F7_ingest - satisfies -> internal_write_api
    F15_privacy - satisfies -> privacy_tests
    F15_privacy - satisfies -> internal_write_api
    F34_admin_auth - satisfies -> supabase_auth
    F34_admin_auth - satisfies -> internal_write_api
    F36_eval - satisfies -> eval_runner
    F36_eval - satisfies -> internal_write_api
```

---

## 15. User journey maps (Mermaid `journey`)

Satisfaction scores are illustrative (1–5). Full step lists: [user-journeys.md](user-journeys.md).

### UJ-001 — Ask community question (streaming)

```mermaid
journey
    title UJ-001: Ask community question (F1, F2, F11)
    section Discover
      Open ChatRAG UI: 5: Community member
      Optional browse corpus by tags: 4: Community member
    section Ask
      Type question EN or ES: 5: Community member
      POST ask/stream: 5: ChatRAG backend
      Stream answer with sources: 5: Community member
    section Outcome
      Answer matches query language: 5: Community member
      No server-side chat row: 5: System
```

### UJ-002 — Ingest public URLs

```mermaid
journey
    title UJ-002: Ingest public URLs (F7, F8, F12)
    section Submit
      Paste URLs in admin UI: 4: Operator
      POST Modal /jobs: 4: Admin frontend
    section Process
      Scrape and chunk: 3: Modal worker
      LLM auto-tag: 4: Modal vLLM
      Embed and upsert via write API: 4: Modal worker
    section Verify
      Poll job until completed: 4: Operator
      Smoke question hits new content: 5: Operator
```

### UJ-026 — Admin login

```mermaid
journey
    title UJ-026: Admin logs in (F34)
    section Auth
      Open admin login: 4: Operator
      Supabase signInWithPassword: 4: Supabase
      JWT stored in browser session: 4: Admin frontend
    section Access
      Protected routes load: 5: Operator
      Viewer or admin role enforced: 5: Internal write API
```

---

## 16. Flowchart — query path (RAG decision flow)

End-to-end ChatRAG query logic from browser to streamed response.

```mermaid
flowchart TD
    Start([Community member submits question]) --> Detect[detect_language EN or ES]
    Detect --> Tags{User selected tags?}
    Tags -->|yes| Filter[pgvector + tag JOIN]
    Tags -->|no| Retrieve[pgvector top_k]
    Filter --> Embed[Modal FastEmbed query vector]
    Retrieve --> Embed
    Embed --> DB[(Postgres chunks + embeddings)]
    DB --> Context{Llm context above threshold?}
    Context -->|no| Safe[Return no-context response F5]
    Context -->|yes| Synth[LlamaIndex synthesize prompt]
    Synth --> Gen[Modal vLLM stream tokens]
    Gen --> SSE[SSE to ChatRAG frontend]
    SSE --> Display[Render answer + citations]
    Display --> Stats[Async POST stats/served F28]
    Stats --> End([Done — no server chat history F3])
    Safe --> End

    classDef community fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef do fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef modal fill:#e8eaf6,stroke:#3949ab,color:#1a237e
    classDef datastore fill:#e0f2f1,stroke:#00695c,color:#004d40

    class Start,Display,End community
    class Detect,Filter,Retrieve,Synth,Safe do
    class Embed,Gen modal
    class DB datastore
```

---

## 17. Flowchart — CI/CD deploy pipeline

On merge to `main`. See [architecture.md](architecture.md) §Deploy pipeline and [ci-after-push.mdc](../.cursor/rules/ci-after-push.mdc).

```mermaid
flowchart LR
    Push([git push main]) --> CI[ci.yml<br/>lint · typecheck · tests · builds]
    CI -->|success| Preflight[deploy-preflight.yml<br/>Modal import smoke]
    Preflight -->|success| Supa[Supabase config push<br/>+ migrations]
    Supa --> ModalD[Modal deploy<br/>embedding → data-mgmt → llm]
    ModalD --> DOD[DO deploy<br/>write-api → chat-api → frontends]
    DOD --> Health([H0ci service health])

    CI -->|fail| FixCI[Fix and push]
    Preflight -->|fail| FixPF[Fix and push]
    FixCI --> Push
    FixPF --> Push

    classDef external fill:#fafafa,stroke:#9e9e9e,color:#424242
    classDef do fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef modal fill:#e8eaf6,stroke:#3949ab,color:#1a237e
    classDef supabase fill:#fff3e0,stroke:#ef6c00,color:#e65100

    class Push,FixCI,FixPF,Health external
    class CI,Preflight,DOD do
    class ModalD modal
    class Supa supabase
```

---

## References

- [architecture.md](architecture.md) — service map and environments
- [spec.md](spec.md) §Data Flow — tabular stage list
- [ADR-004](adr/ADR-004-cost-sovereignty-zero-personal-data.md) — zero PII
- [ADR-007](adr/ADR-007-modal-do-database-write-boundary.md) — write boundary
- [runbooks/corpus-operator-guide.md](runbooks/corpus-operator-guide.md) — operator procedures
