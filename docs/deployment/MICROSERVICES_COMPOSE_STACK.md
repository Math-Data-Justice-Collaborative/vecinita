# Microservices Compose Stack

This stack runs Vecinita in a routing-centric microservices topology:

- `chat-agent` routes model and embedding calls through `direct-routing`.
- `direct-routing` fans out to `model-service`, `embedding-service`, and `scraper-service`.
- `chat-gateway` is the public API edge for the chat app.
- Two separate UIs are exposed: `chat-frontend` and `data-manager-frontend`.

## Services

The runtime is defined in `docker-compose.microservices.yml`.

- `postgres` + `postgrest` for local Supabase-style API compatibility
- `chroma` for vector persistence used by chat services
- `ollama` + `model-service` for local model API behavior
- `embedding-service` for local embedding API behavior
- `scraper-service` for background ingestion/reindex jobs
- `direct-routing` as the service-to-service policy and routing layer
- `chat-agent` + `chat-gateway` + `chat-frontend`
- `data-manager-frontend`

## Start / Stop

```bash
make microservices-up
make microservices-logs
make microservices-down
```

## Contract Tests

Run API contract checks that validate health and routing behavior for the routing chain:

```bash
make test-microservices-contracts
```

To run everything in one command (bring up stack, execute contracts, tear down):

```bash
make test-microservices
```

## Default Local Endpoints

- Gateway: `http://localhost:8004`
- Agent: `http://localhost:8000`
- Modal Routing: `http://localhost:10000`
- Model Service: `http://localhost:8008`
- Embedding Service: `http://localhost:8011`
- Scraper Service: `http://localhost:8020`
- Chat Frontend: `http://localhost:5173`
- Data Manager Frontend: `http://localhost:4173`
