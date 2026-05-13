# Indexing Worker

Document indexing pipeline running on Modal serverless infrastructure.

## Capabilities

- Single-document indexing
- Batch indexing of multiple pages/content
- Selective re-indexing of changed documents
- Full rebuild when the embedding model changes

## Runtime

- Deploy target: Modal serverless (GPU for embedding)
- Protocol: Modal function invocation, Modal Batch (spawn_map)

## Status

Placeholder — source code will be populated in spec 022 (vLLM/LlamaIndex integration).
