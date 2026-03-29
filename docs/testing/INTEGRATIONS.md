# Integration Test Coverage Catalogue

This catalogue tracks every external integration point, where it is tested, and whether credentials are required.

| Service | Protocol | Test File | CI Job | Credential-Gated |
|---|---|---|---|---|
| Supabase Auth | HTTPS REST | `backend/tests/integration/test_supabase_api.py` | `backend-integration` | Yes |
| Supabase DB (`document_chunks`) | HTTPS REST | `backend/tests/integration/test_supabase_api.py` | `backend-integration` | Yes |
| Supabase RPC (`search_similar_documents`) | HTTPS REST | `backend/tests/integration/test_supabase_api.py` | `backend-integration` | Yes |
| Supabase Edge Functions (`generate-embedding`) | HTTPS REST | `backend/tests/integration/test_supabase_api.py` | `backend-integration` | Yes |
| Groq (`ChatGroq`) | HTTPS REST | `backend/tests/integration/test_llm_providers.py` | `backend-integration` | Yes |
| DeepSeek (`ChatOpenAI` base URL) | HTTPS REST | `backend/tests/integration/test_llm_providers.py` | `backend-integration` | Yes |
| OpenAI (`ChatOpenAI`) | HTTPS REST | `backend/tests/integration/test_llm_providers.py` | `backend-integration` | Yes |
| Ollama | HTTP | `backend/tests/integration/test_llm_providers.py` | `backend-integration` | Partial |
| Embedding Service (`/embed`, `/embed-batch`) | HTTP | `backend/tests/integration/test_embedding_service_live.py` | `backend-integration` | Partial |
| Tavily Search | HTTPS REST | `backend/tests/integration/test_web_search_live.py` | `backend-integration` | Yes |
| DuckDuckGo Search | HTTPS REST | `backend/tests/integration/test_web_search_live.py` | `backend-integration` | No |
| ChromaDB | HTTP | `backend/tests/integration/test_chroma_documents_admin_chat_flow.py` | `backend-integration` | No |
| Auth Proxy | HTTP | `backend/tests/integration/test_auth_proxy.py`, `backend/tests/integration/test_auth_matrix.py` | `backend-integration` | No (mocked) |
| Modal Reindex Trigger | HTTPS REST | `backend/tests/integration/test_modal_reindex_trigger.py` | `backend-integration` | Partial |
| Modal Proxy -> Model/Embedding/Scraper chain | HTTP | `tests/integration/test_microservices_contracts.py` | `microservices-contracts` | No (local compose defaults) |
| Postgres + pgvector | TCP | `backend/tests/integration/*` with `db` marker | `backend-integration-pgvector` | No |
| Redis (if enabled in runtime) | TCP | `backend/tests/integration/test_redis_integration.py` | `backend-integration` | No |

## Notes

- Credential-gated tests should use `pytest.mark.skipif` with explicit env var checks.
- Integration test additions should keep this table updated to avoid blind spots.
