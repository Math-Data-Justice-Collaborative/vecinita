import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fetchModelRegistry } from '../modelRegistry';

const fetchMock = vi.fn();

describe('modelRegistry service contracts', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    fetchMock.mockReset();
  });

  it('parses embedding providers from legacy available.providers shape', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          providers: [{ key: 'ollama', label: 'Ollama' }],
          models: { ollama: ['gemma3'] },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          available: {
            providers: [{ key: 'huggingface', label: 'HuggingFace' }],
            models: { huggingface: ['sentence-transformers/all-MiniLM-L6-v2'] },
          },
        }),
      });

    const data = await fetchModelRegistry();

    expect(data.embeddingProviders.huggingface).toEqual({
      name: 'HuggingFace',
      models: ['sentence-transformers/all-MiniLM-L6-v2'],
    });
  });

  it('parses embedding providers from flat backend/service config shape', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          providers: [{ key: 'ollama', label: 'Ollama' }],
          models: { ollama: ['gemma3'] },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          provider: 'huggingface',
          model: 'sentence-transformers/all-MiniLM-L6-v2',
          dimension: 384,
        }),
      });

    const data = await fetchModelRegistry();

    expect(data.embeddingProviders.huggingface).toEqual({
      name: 'huggingface',
      models: ['sentence-transformers/all-MiniLM-L6-v2'],
    });
  });
});
