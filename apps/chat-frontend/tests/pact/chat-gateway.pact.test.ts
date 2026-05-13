/**
 * Pact consumer: chat SPA ↔ unified gateway (`/api/v1` agent routes).
 * Covers chat/config/document surfaces under `/api/v1`.
 */
import { describe, it, expect } from 'vitest';
import { MatchersV3, PactV3 } from '@pact-foundation/pact';
import { AgentServiceClient } from '../../src/app/services/agentService';
import {
  fetchDocumentTagStats,
  fetchDocumentsOverview,
  fetchDownloadUrlForSource,
} from '../../src/app/services/documentsService';
import {
  CHAT_GATEWAY_PACT_CONSUMER,
  CHAT_GATEWAY_PACT_PROVIDER,
  resolveChatPactLogLevel,
  resolveChatPactOutputDir,
} from './pactSetup';

describe('Pact: chat-frontend → vecinita-gateway', () => {
  it('honours agent config + non-stream ask interactions', async () => {
    const pact = new PactV3({
      consumer: CHAT_GATEWAY_PACT_CONSUMER,
      provider: CHAT_GATEWAY_PACT_PROVIDER,
      dir: resolveChatPactOutputDir(),
      logLevel: resolveChatPactLogLevel(),
    });

    const configBody = {
      providers: MatchersV3.eachLike({
        name: MatchersV3.like('groq'),
        models: MatchersV3.eachLike('llama-3.1-8b'),
        default: MatchersV3.like(true),
      }),
      models: {
        groq: MatchersV3.eachLike('llama-3.1-8b'),
      },
      defaultProvider: MatchersV3.like('groq'),
      defaultModel: MatchersV3.like('llama-3.1-8b'),
    };

    const askBody = {
      answer: MatchersV3.like('Pact contract reply'),
      sources: MatchersV3.like([]),
      thread_id: MatchersV3.like('pact-thread-1'),
    };

    const embedConfigBody = {
      model: MatchersV3.like('BAAI/bge-small-en-v1.5'),
      provider: MatchersV3.like('huggingface'),
      dimension: MatchersV3.like(384),
      available: {
        providers: MatchersV3.eachLike({
          key: MatchersV3.like('huggingface'),
          label: MatchersV3.like('HuggingFace'),
        }),
        models: {
          huggingface: MatchersV3.eachLike('BAAI/bge-small-en-v1.5'),
        },
      },
    };

    const documentsOverviewBody = {
      sources: MatchersV3.eachLike({
        id: MatchersV3.like('doc-1'),
        url: MatchersV3.like('https://example.com/community-resource'),
        title: MatchersV3.like('Community Resource'),
        source_domain: MatchersV3.like('example.com'),
        resource_type: MatchersV3.like('document'),
        format: MatchersV3.like('HTML'),
        language: MatchersV3.like('en'),
        organization: MatchersV3.like('Vecinita'),
        embedding_status: MatchersV3.like('completed'),
        source_of_truth: MatchersV3.like('postgres'),
        canonical_visibility_updated_at: MatchersV3.like('2026-01-01T00:00:00.000Z'),
        tags: MatchersV3.eachLike('community'),
      }),
    };

    const documentTagsBody = {
      tags: MatchersV3.eachLike({
        tag: MatchersV3.like('community'),
        source_count: MatchersV3.like(2),
      }),
    };

    const downloadUrlBody = {
      download_url: MatchersV3.like('https://cdn.example.com/resource.pdf'),
    };

    await pact
      .addInteraction({
        uponReceiving: 'a request for gateway agent configuration',
        withRequest: {
          method: 'GET',
          path: '/api/v1/ask/config',
          headers: { Accept: 'application/json' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: configBody,
        },
      })
      .addInteraction({
        uponReceiving: 'a non-streaming ask request',
        withRequest: {
          method: 'GET',
          path: '/api/v1/ask',
          query: { question: 'hello pact' },
          headers: { Accept: 'application/json' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: askBody,
        },
      })
      .addInteraction({
        uponReceiving: 'a streaming ask request',
        withRequest: {
          method: 'GET',
          path: '/api/v1/ask/stream',
          query: { question: 'hello pact stream' },
          headers: { Accept: 'text/event-stream' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'text/event-stream' },
          body: MatchersV3.regex(
            '^data: .*\\n\\ndata: .*\\n\\n$',
            'data: {"type":"answer_chunk","content":"hello"}\n\ndata: {"type":"complete","answer":"hello"}\n\n'
          ),
        },
      })
      .addInteraction({
        uponReceiving: 'a request for embedding provider configuration',
        withRequest: {
          method: 'GET',
          path: '/api/v1/embed/config',
          headers: { Accept: 'application/json' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: embedConfigBody,
        },
      })
      .addInteraction({
        uponReceiving: 'a documents overview request',
        withRequest: {
          method: 'GET',
          path: '/api/v1/documents/overview',
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: documentsOverviewBody,
        },
      })
      .addInteraction({
        uponReceiving: 'a documents tags request',
        withRequest: {
          method: 'GET',
          path: '/api/v1/documents/tags',
          query: { limit: '5' },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: documentTagsBody,
        },
      })
      .addInteraction({
        uponReceiving: 'a document download-url request',
        withRequest: {
          method: 'GET',
          path: '/api/v1/documents/download-url',
          query: {
            source_url: 'https://example.com/community-resource',
          },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: downloadUrlBody,
        },
      })
      .executeTest(async (mockServer) => {
        const baseUrl = `${mockServer.url.replace(/\/$/, '')}/api/v1`;
        const client = new AgentServiceClient(baseUrl);

        const config = await client.getConfig();
        expect(config.defaultProvider).toBe('groq');

        const answer = await client.ask({ question: 'hello pact' });
        expect(answer.answer).toBe('Pact contract reply');
        expect(answer.thread_id).toBeTruthy();

        const streamResponse = await fetch(
          `${baseUrl}/ask/stream?question=${encodeURIComponent('hello pact stream')}`,
          {
            method: 'GET',
            headers: { Accept: 'text/event-stream' },
          }
        );
        expect(streamResponse.status).toBe(200);
        const streamText = await streamResponse.text();
        expect(streamText).toContain('data:');

        const embedConfigResponse = await fetch(`${baseUrl}/embed/config`, {
          method: 'GET',
          headers: { Accept: 'application/json' },
        });
        expect(embedConfigResponse.status).toBe(200);
        const embedConfig = (await embedConfigResponse.json()) as {
          provider?: string;
          model?: string;
        };
        expect(embedConfig.provider).toBe('huggingface');
        expect(embedConfig.model).toBe('BAAI/bge-small-en-v1.5');

        const overview = await fetchDocumentsOverview(baseUrl);
        expect(overview.sources.length).toBeGreaterThan(0);

        const tags = await fetchDocumentTagStats(baseUrl, 5);
        expect(tags[0]?.tag).toBe('community');

        const downloadUrl = await fetchDownloadUrlForSource(
          baseUrl,
          'https://example.com/community-resource'
        );
        expect(downloadUrl).toBe('https://cdn.example.com/resource.pdf');
      });
  });
});
