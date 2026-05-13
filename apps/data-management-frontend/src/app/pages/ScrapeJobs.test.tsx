import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ScrapeJobs } from './ScrapeJobs';
import { ragApi } from '../api/rag-api';

vi.mock('../api/rag-api', () => ({
  ragApi: {
    getScrapeJobs: vi.fn(),
    getScrapeStatus: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}));

describe('ScrapeJobs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loaded job stats', async () => {
    vi.mocked(ragApi.getScrapeJobs).mockResolvedValue({
      jobs: [
        {
          job_id: 'abc',
          url: 'https://example.org',
          depth: 1,
          status: 'processing',
          backend_status: 'processing',
          created_at: new Date().toISOString(),
          progress: 55,
          current_step: 'chunking',
          pages_scraped: 3,
          documents_created: [],
        },
      ],
    });

    render(
      <MemoryRouter>
        <ScrapeJobs />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('https://example.org')).toBeInTheDocument();
      expect(screen.getByText('Total Jobs')).toBeInTheDocument();
      expect(screen.getAllByText('1').length).toBeGreaterThan(0);
    });
  });
});
