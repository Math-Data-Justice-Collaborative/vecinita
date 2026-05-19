# Modal apps (deploy)

| App | Module | Deploy command |
|-----|--------|----------------|
| `vecinita-embedding` | `infra/modal/embedding_app.py` | `modal deploy infra/modal/embedding_app.py` |
| `vecinita-data-management` | `infra/modal/data_management_app.py` | `modal deploy infra/modal/data_management_app.py` |
| `vecinita-llm` | (M9) | TBD |

## vecinita-embedding (FastEmbed)

- **Model:** `BAAI/bge-small-en-v1.5` (384-dim, ADR-008)
- **Volume:** `embedding-models` (HF cache)
- **Endpoints:** `GET /health`, `POST /embed`, `POST /embed/batch`
- **Consumer env:** `VECINITA_MODAL_EMBED_URL` on DO backends (`packages/embedding-client`)

First deploy downloads weights into the Modal volume; allow several minutes on cold start.
