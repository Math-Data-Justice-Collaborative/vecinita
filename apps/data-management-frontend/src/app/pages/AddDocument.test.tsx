import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AddDocument } from './AddDocument';
import { ragApi } from '../api/rag-api';

vi.mock('../api/rag-api', () => ({
  ragApi: {
    scrapeUrl: vi.fn(),
    uploadDocument: vi.fn(),
    createDocument: vi.fn(),
    generateEmbeddings: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

describe('AddDocument', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('submits a scraping job and shows progress label', async () => {
    vi.mocked(ragApi.scrapeUrl).mockResolvedValue({
      job_id: 'job-1',
      status: 'queued',
      created_at: new Date().toISOString(),
      url: 'https://example.com',
    });

    render(
      <MemoryRouter>
        <AddDocument />
      </MemoryRouter>,
    );

    const urlInput = screen.getByLabelText(/url to scrape/i);
    await userEvent.type(urlInput, 'https://example.com');

    const submitButton = screen.getByRole('button', { name: /start scraping job/i });
    await userEvent.click(submitButton);

    expect(ragApi.scrapeUrl).toHaveBeenCalledWith(
      expect.objectContaining({ url: 'https://example.com' }),
    );
  });
});
