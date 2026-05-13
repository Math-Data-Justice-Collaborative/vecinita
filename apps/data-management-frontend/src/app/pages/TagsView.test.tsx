import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { TagsView } from './TagsView';
import { ragApi } from '../api/rag-api';

vi.mock('../api/rag-api', () => ({
  ragApi: {
    getAllTags: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}));

const tagInventory = {
  tags: [
    { tag: 'housing', label: 'vivienda', resource_count: 2, source_count: 2, locale: 'es' },
    { tag: 'immigrants', label: 'inmigrantes', resource_count: 1, source_count: 1, locale: 'es' },
    { tag: 'Providence', label: 'Providence', resource_count: 1, source_count: 1, locale: 'es' },
    { tag: 'free', label: 'gratis', resource_count: 1, source_count: 1, locale: 'es' },
  ],
  tag_counts: {
    housing: 2,
    immigrants: 1,
    Providence: 1,
    free: 1,
  },
  locale: 'es',
};

describe('TagsView', () => {
  beforeEach(() => {
    vi.mocked(ragApi.getAllTags).mockReset();
    vi.mocked(ragApi.getAllTags).mockImplementation(async (_locale?: string) => tagInventory);
  });

  it('renders metadata schema categories without runtime reference errors', async () => {
    render(
      <MemoryRouter>
        <TagsView />
      </MemoryRouter>,
    );

    // Schema card title (en or es UI)
    expect(
      await screen.findByRole('heading', {
        name: /Metadata Schema Categories|Categorias del Esquema de Metadatos/i,
      }),
    ).toBeInTheDocument();

    // Tags load in useEffect — wait for translated labels from the API mock
    expect(await screen.findByText('vivienda')).toBeInTheDocument();
    expect(await screen.findByText('inmigrantes')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByText('Providence').length).toBeGreaterThan(0);
    });
    expect(await screen.findByText('gratis')).toBeInTheDocument();

    expect(screen.getByText(/Vecinita does not maintain or independently verify/i)).toBeInTheDocument();
  });
});
