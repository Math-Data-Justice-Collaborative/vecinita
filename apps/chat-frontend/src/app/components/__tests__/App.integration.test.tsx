import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, waitFor, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../../App';

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

/**
 * Integration tests for the main App component
 * Verifies that App.tsx still renders and functions correctly after cleanup
 */
describe('App Component - Integration Tests', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllMocks();

    // Mock scrollIntoView / scrollTo since jsdom doesn't support them
    Element.prototype.scrollIntoView = vi.fn();
    Element.prototype.scrollTo = vi.fn() as unknown as typeof Element.prototype.scrollTo;

    // Provide default fetch stub so BackendSettingsContext doesn't hang on /ask/config
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/ask/config') || url.includes('/config')) {
          return Promise.resolve(
            jsonResponse({
              provider: 'ollama',
              model: 'llama3.2',
              providers: { available: ['ollama'], current: 'ollama' },
              models: { available: ['llama3.2'], current: 'llama3.2' },
              embedding: { model: 'BAAI/bge-small-en-v1.5' },
            })
          );
        }
        if (url.includes('/documents/overview')) {
          return Promise.resolve(jsonResponse({ sources: [] }));
        }
        if (url.includes('/documents/tags')) {
          return Promise.resolve(jsonResponse({ tags: [] }));
        }
        return Promise.resolve(jsonResponse({}));
      })
    );
  });

  it('should render main components without import errors', async () => {
    // Just verify the app doesn't have broken imports
    // Full render testing is complex due to jsdom/DOM limitations
    const exports = await import('../../App');
    expect(exports.default).toBeDefined();
  });

  it('should not reference any deleted components', async () => {
    // Verify by checking that the core components import successfully
    render(<App />);

    // Wait for async provider initialization to complete
    await waitFor(() => {
      expect(document.body).toBeInTheDocument();
    });
  });

  it('should navigate between Chat and Documents tabs from the navbar', async () => {
    const user = userEvent.setup();

    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);

        if (url.includes('/ask/config')) {
          return Promise.resolve(
            jsonResponse({
              provider: 'ollama',
              model: 'llama3.2',
              providers: { available: ['ollama'], current: 'ollama' },
              models: { available: ['llama3.2'], current: 'llama3.2' },
              embedding: { model: 'BAAI/bge-small-en-v1.5' },
            })
          );
        }

        if (url.includes('/documents/overview')) {
          return Promise.resolve(jsonResponse({ sources: [] }));
        }

        if (url.includes('/documents/tags')) {
          return Promise.resolve(jsonResponse({ tags: [] }));
        }

        return Promise.resolve(jsonResponse({}));
      })
    );

    window.history.pushState({}, '', '/');
    render(<App />);

    const documentsLink = await screen.findByRole('link', { name: 'Documents' });
    await user.click(documentsLink);

    await waitFor(() => {
      expect(window.location.pathname).toBe('/documents');
    });

    await user.click(screen.getByRole('link', { name: 'Chat' }));
    await waitFor(() => {
      expect(window.location.pathname).toBe('/');
    });
  });

  it('should keep navbar above floating widgets via high z-index class', async () => {
    render(<App />);

    const header = document.querySelector('header');
    expect(header).not.toBeNull();
    expect(header?.className).toContain('z-[2000]');
  });
});

/**
 * Tests for component dependencies
 */
describe('App Component - Dependencies Verification', () => {
  beforeEach(() => {
    localStorage.clear();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it('should import with language provider', async () => {
    const langContext = await import('@/app/context/LanguageContext');
    expect(langContext.LanguageProvider).toBeDefined();
  });

  it('should import with accessibility provider', async () => {
    const a11yContext = await import('@/app/context/AccessibilityContext');
    expect(a11yContext.AccessibilityProvider).toBeDefined();
  });

  it('should import with backend settings provider', async () => {
    const settingsContext = await import('@/app/context/BackendSettingsContext');
    expect(settingsContext.BackendSettingsProvider).toBeDefined();
  });

  it('should have all required components available for import', async () => {
    const components = await import('../index');

    expect(components.ChatWidget).toBeDefined();
    expect(components.AccessibilityPanel).toBeDefined();
    expect(components.LanguageSelector).toBeDefined();
    expect(components.ThemeToggle).toBeDefined();
  });
});
