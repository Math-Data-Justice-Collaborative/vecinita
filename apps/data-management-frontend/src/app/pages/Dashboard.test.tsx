import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Dashboard } from './Dashboard';
import { ragApi } from '../api/rag-api';

vi.mock('../api/rag-api', () => ({
  ragApi: {
    getStats: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}));

describe('Dashboard warmup status banners', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('shows recovery banner when data returns after warmup threshold', async () => {
    vi.mocked(ragApi.getStats).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              total_documents: 2,
              total_embeddings: 20,
              documents_by_type: { website: 1, document: 1 },
              documents_by_language: { English: 2 },
              recent_documents: [],
              warmup_status: 'live',
            });
          }, 1800);
        }),
    );

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Connected after warmup. Live data is now available.')).toBeInTheDocument();
    }, { timeout: 4000 });
  });

  it('shows fallback banner when API returns fallback stats', async () => {
    vi.mocked(ragApi.getStats).mockResolvedValue({
      total_documents: 1,
      total_embeddings: 4,
      documents_by_type: { website: 1 },
      documents_by_language: { Unknown: 1 },
      recent_documents: [],
      warmup_status: 'fallback',
      warmup_message: 'Document endpoint unavailable; showing scraper-job derived stats.',
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByText('Document endpoint unavailable; showing scraper-job derived stats.'),
      ).toBeInTheDocument();
    });
  });
});
