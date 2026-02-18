# Privacy Policy

Last updated: January 25, 2026

Vecinita processes user queries to provide answers and related citations using Retrieval-Augmented Generation (RAG). We care about privacy and data minimization. This policy describes what we collect, how we use it, and your choices.

## What We Collect
- Query content: The text you send to the agent/chat endpoints.
- Operational metadata: Basic logs (timestamps, endpoint paths, response status) for reliability and debugging.
- Context sources: Document URLs and titles used to generate answers (already public content).

We do not collect:
- Sensitive personal identifiers (unless you include them explicitly in a query).
- Precise location or device identifiers.

## How We Use Data
- Answer generation: Query text is temporarily processed by an LLM provider (e.g., DeepSeek, Groq, OpenAI, or local Ollama) to produce an answer.
- Retrieval: Query text is embedded and matched against stored public documents to find relevant context.
- Reliability and security: Minimal logs help us diagnose outages and improve performance.

## Data Retention
- Application logs: Rotated and retained for a limited period, typically 30 days.
- Query content: Not stored persistently by default. If tracing is enabled, content may be retained for debugging with access controls.

## Third-Party Providers
We may send query text and minimal metadata to configured providers strictly for inference:
- LLM: DeepSeek, Groq, OpenAI, or local Ollama.
- Embeddings: Local HuggingFace models, FastEmbed, or a self-hosted embedding service.

Each provider has its own privacy policy and terms; usage is limited to inference.

## Your Choices
- Do not include personal or sensitive data in queries.
- Request deletion of any retained tracing data by contacting the maintainers.

## Security
- Environment secrets (API keys) are stored server-side.
- Transport uses HTTPS when deployed; use secure channels for production.

## Contact
For privacy-related questions or requests, contact the Vecinita maintainers.
