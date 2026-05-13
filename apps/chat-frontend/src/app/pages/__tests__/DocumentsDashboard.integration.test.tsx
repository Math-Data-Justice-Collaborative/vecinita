import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import DocumentsDashboard, { resolveApiBase } from '../DocumentsDashboard';

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  const headers = new Headers(init.headers);
  if (!headers.has('content-type')) {
    headers.set('content-type', 'application/json; charset=utf-8');
  }

  return new Response(JSON.stringify(body), {
    ...init,
    headers,
  });
}

vi.mock('../../context/LanguageContext', () => ({
  useLanguage: () => ({
    t: (key: string) =>
      ({
        documentsTitle: 'Documents',
        documentsSubtitle: 'Community resources and reference materials available to everyone.',
        docsTotalSources: 'Community Sources',
        docsTotalTopics: 'Topics',
        docsVisibleResources: 'Visible Resources',
        docsResources: 'Resources',
        docsSearchPlaceholder: 'Search resources…',
        docsTopics: 'Topics',
        docsClearFilters: 'Clear filters',
        docsNoTopics: 'No topics available yet.',
        docsSourcesLabel: 'sources',
        docsResource: 'Resource',
        docsActions: 'Actions',
        docsNoResults: 'No resources match your filters.',
        docsOpenSource: 'Open source',
        docsDownload: 'Download',
        docsLoading: 'Loading resources…',
        docsLoadFailed: 'Failed to load resources',
        docsUnknownError: 'Unknown error',
        docsDownloadError: 'Unable to resolve a download link',
        docsNoDownloadAvailable: 'This resource does not have a downloadable file.',
        docsDownloadFailed: 'Failed to download resource',
      })[key] ?? key,
  }),
}));

describe('DocumentsDashboard integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal('alert', vi.fn());

    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/documents/overview')) {
          return Promise.resolve(
            jsonResponse({
              sources: [
                {
                  url: 'https://example.org/a',
                  title: 'Example Source A',
                  source_domain: 'example.org',
                  tags: ['housing'],
                },
                {
                  url: 'https://example.org/b',
                  title: 'Example Source B',
                  source_domain: 'example.org',
                  tags: ['benefits'],
                },
              ],
            })
          );
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(
            jsonResponse({
              tags: [
                { tag: 'housing', source_count: 2, chunk_count: 7 },
                { tag: 'benefits', source_count: 1, chunk_count: 3 },
              ],
            })
          );
        }

        if (url.includes('/documents/preview')) {
          return Promise.resolve(jsonResponse({ chunks: [] }));
        }

        return Promise.resolve(new Response(null, { status: 404 }));
      })
    );
  });

  it('renders community resources and topic filters from API data', async () => {
    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Documents')).toBeInTheDocument();
    });

    expect(screen.getByText('Community Sources')).toBeInTheDocument();
    expect(screen.getByText('Visible Resources')).toBeInTheDocument();
    expect(screen.getByText('Example Source A')).toBeInTheDocument();
    expect(screen.getByText('Example Source B')).toBeInTheDocument();
    expect(screen.getByText('https://example.org/a')).toBeInTheDocument();
    expect(screen.getByText('housing (2)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'housing (2)' })).toBeInTheDocument();
    expect(screen.queryByText('Total Chunks')).not.toBeInTheDocument();
    expect(screen.queryByText('Embedding Model')).not.toBeInTheDocument();
    expect(screen.queryByText('Download')).not.toBeInTheDocument();
  });

  it('renders an error state when the documents request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/documents/overview')) {
          return Promise.resolve(new Response(null, { status: 503 }));
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(jsonResponse({ tags: [] }));
        }

        return Promise.resolve(new Response(null, { status: 404 }));
      })
    );

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load resources: HTTP 503')).toBeInTheDocument();
    });
  });

  it('renders resources when tags request fails but overview succeeds', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/documents/overview')) {
          return Promise.resolve(
            jsonResponse({
              sources: [
                {
                  url: 'https://example.org/partial',
                  title: 'Partial Success Source',
                  source_domain: 'example.org',
                  tags: ['housing'],
                },
              ],
            })
          );
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(new Response(null, { status: 503 }));
        }

        return Promise.resolve(new Response(null, { status: 404 }));
      })
    );

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Partial Success Source')).toBeInTheDocument();
    });

    expect(screen.queryByText(/Failed to load resources/i)).not.toBeInTheDocument();
    expect(screen.getByText('No topics available yet.')).toBeInTheDocument();
  });

  it('renders an error state when overview returns HTML instead of JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/documents/overview')) {
          return Promise.resolve(
            new Response('<!doctype html><html><body>fallback</body></html>', {
              status: 200,
              headers: { 'content-type': 'text/html; charset=utf-8' },
            })
          );
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(jsonResponse({ tags: [] }));
        }

        return Promise.resolve(new Response(null, { status: 404 }));
      })
    );

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText(
          /Failed to load resources: \/documents\/overview returned non-JSON response/i
        )
      ).toBeInTheDocument();
    });
  });

  it('supports topic filtering and renders actionable source links', async () => {
    const user = userEvent.setup();

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Example Source A')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'benefits (1)' }));

    await waitFor(() => {
      expect(screen.queryByText('Example Source A')).not.toBeInTheDocument();
      expect(screen.getByText('Example Source B')).toBeInTheDocument();
    });

    const openSourceLink = screen.getByRole('link', { name: 'Open source' });
    expect(openSourceLink).toHaveAttribute('href', 'https://example.org/b');
    expect(openSourceLink).toHaveAttribute('target', '_blank');
  });

  it('renders open-source actions only for external http resources', async () => {
    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Example Source A')).toBeInTheDocument();
    });

    expect(screen.getAllByRole('link', { name: 'Open source' })).toHaveLength(2);
    expect(screen.queryByRole('button', { name: 'Download' })).not.toBeInTheDocument();
  });

  it('resolves document download links and opens them in a new tab', async () => {
    const user = userEvent.setup();
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);

    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/documents/overview')) {
          return Promise.resolve(
            jsonResponse({
              sources: [
                {
                  url: 'stored/clinic-flyer.pdf',
                  title: 'Clinic Flyer',
                  source_domain: 'storage',
                  tags: ['health'],
                  downloadable: true,
                },
              ],
            })
          );
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(jsonResponse({ tags: [{ tag: 'health', source_count: 1 }] }));
        }

        if (url.includes('/documents/download-url')) {
          return Promise.resolve(
            jsonResponse({ download_url: 'https://downloads.example.org/clinic-flyer.pdf' })
          );
        }

        return Promise.resolve(new Response(null, { status: 404 }));
      })
    );

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Clinic Flyer')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Download' }));

    await waitFor(() => {
      expect(openSpy).toHaveBeenCalledWith(
        'https://downloads.example.org/clinic-flyer.pdf',
        '_blank',
        'noopener,noreferrer'
      );
    });
  });

  it('uses an existing download_url without requesting a new one', async () => {
    const user = userEvent.setup();
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    const fetchSpy = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes('/documents/overview')) {
        return Promise.resolve(
          jsonResponse({
            sources: [
              {
                url: 'stored/ready-download.pdf',
                title: 'Ready Download',
                source_domain: 'storage',
                tags: ['health'],
                download_url: 'https://downloads.example.org/ready-download.pdf',
              },
            ],
          })
        );
      }

      if (url.includes('/documents/tags')) {
        return Promise.resolve(jsonResponse({ tags: [{ tag: 'health', source_count: 1 }] }));
      }

      return Promise.resolve(new Response(null, { status: 404 }));
    });

    vi.stubGlobal('fetch', fetchSpy);

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Ready Download')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Download' }));

    expect(openSpy).toHaveBeenCalledWith(
      'https://downloads.example.org/ready-download.pdf',
      '_blank',
      'noopener,noreferrer'
    );
    expect(fetchSpy).not.toHaveBeenCalledWith(expect.stringContaining('/documents/download-url'));
  });

  it('disables the download action while resolving the download URL', async () => {
    const user = userEvent.setup();
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    let resolveDownloadRequest: ((value: Response) => void) | undefined;

    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/documents/overview')) {
          return Promise.resolve(
            jsonResponse({
              sources: [
                {
                  url: 'stored/pending-download.pdf',
                  title: 'Pending Download',
                  source_domain: 'storage',
                  tags: ['health'],
                  downloadable: true,
                },
              ],
            })
          );
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(jsonResponse({ tags: [{ tag: 'health', source_count: 1 }] }));
        }

        if (url.includes('/documents/download-url')) {
          return new Promise<Response>((resolve) => {
            resolveDownloadRequest = resolve;
          });
        }

        return Promise.resolve(new Response(null, { status: 404 }));
      })
    );

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Pending Download')).toBeInTheDocument();
    });

    const downloadButton = screen.getByRole('button', { name: 'Download' });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '…' })).toBeDisabled();
    });

    resolveDownloadRequest?.(
      jsonResponse({ download_url: 'https://downloads.example.org/pending-download.pdf' })
    );

    await waitFor(() => {
      expect(openSpy).toHaveBeenCalledWith(
        'https://downloads.example.org/pending-download.pdf',
        '_blank',
        'noopener,noreferrer'
      );
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Download' })).toBeEnabled();
    });
  });

  it('alerts when download URL resolution fails', async () => {
    const user = userEvent.setup();
    const alertSpy = vi.mocked(globalThis.alert);

    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/documents/overview')) {
          return Promise.resolve(
            jsonResponse({
              sources: [
                {
                  url: 'stored/failing-download.pdf',
                  title: 'Failing Download',
                  source_domain: 'storage',
                  tags: ['health'],
                  downloadable: true,
                },
              ],
            })
          );
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(jsonResponse({ tags: [{ tag: 'health', source_count: 1 }] }));
        }

        if (url.includes('/documents/download-url')) {
          return Promise.resolve(new Response(null, { status: 500 }));
        }

        return Promise.resolve(new Response(null, { status: 404 }));
      })
    );

    render(<DocumentsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Failing Download')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Download' }));

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('Unable to resolve a download link (HTTP 500)');
    });
  });

  it('rewrites stale gateway hosts for Render frontends', () => {
    expect(
      resolveApiBase('http://localhost:8004/api/v1', {
        hostname: 'vecinita-frontend.onrender.com',
        protocol: 'https:',
      })
    ).toBe('https://vecinita-gateway.onrender.com/api/v1');
  });

  it('preserves relative API paths for non-frontdoor hosts', () => {
    expect(resolveApiBase('/api/v1', { hostname: 'localhost', protocol: 'http:' })).toBe('/api/v1');
  });

  it('rewrites render agent hosts to gateway for documents API calls', () => {
    expect(
      resolveApiBase('https://vecinita-agent.onrender.com', {
        hostname: 'vecinita-frontend.onrender.com',
        protocol: 'https:',
      })
    ).toBe('https://vecinita-gateway.onrender.com/api/v1');
  });

  it('normalizes render gateway root URLs to /api/v1', () => {
    expect(
      resolveApiBase('https://vecinita-gateway.onrender.com', {
        hostname: 'vecinita-frontend.onrender.com',
        protocol: 'https:',
      })
    ).toBe('https://vecinita-gateway.onrender.com/api/v1');
  });

  it('prefers explicit render backend fallback when gateway env is relative', () => {
    expect(
      resolveApiBase(
        '/api',
        {
          hostname: 'vecinita-frontend.onrender.com',
          protocol: 'https:',
        },
        'https://vecinita-gateway-prod-v5.onrender.com'
      )
    ).toBe('https://vecinita-gateway-prod-v5.onrender.com/api/v1');
  });

  it('normalizes render agent fallback host to gateway for documents routes', () => {
    expect(
      resolveApiBase(
        '/api',
        {
          hostname: 'vecinita-frontend.onrender.com',
          protocol: 'https:',
        },
        'https://vecinita-agent.onrender.com'
      )
    ).toBe('https://vecinita-gateway.onrender.com/api/v1');
  });
});
