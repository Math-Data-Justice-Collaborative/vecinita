import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminAccess } from './AdminAccess';

const useAuth = vi.fn();

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => useAuth(),
}));

vi.mock('../api/scraper-config', () => ({
  getScraperConfigDiagnostic: () => ({
    configured: true,
    validUrl: true,
    hasDeprecatedBrowserAuthEnv: false,
    apiBaseUrl: 'https://data-api.example.com',
    issues: [],
    warnings: [],
  }),
}));

describe('AdminAccess', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows active session details', () => {
    useAuth.mockReturnValue({
      user: { displayName: 'API key tok...1234' },
      session: { preview: 'tok...1234', createdAt: '2026-01-01T00:00:00.000Z' },
    });

    render(
      <MemoryRouter>
        <AdminAccess />
      </MemoryRouter>,
    );

    expect(screen.getByText(/access & runtime/i)).toBeInTheDocument();
    expect(screen.getByText(/api key tok...1234/i)).toBeInTheDocument();
    expect(screen.getByText(/auth mode: direct api key bearer/i)).toBeInTheDocument();
  });

  it('renders connectivity diagnostics', async () => {
    useAuth.mockReturnValue({
      user: { displayName: 'API key tok...1234' },
      session: { preview: 'tok...1234', createdAt: '2026-01-01T00:00:00.000Z' },
    });

    render(
      <MemoryRouter>
        <AdminAccess />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/configured base url: https:\/\/data-api.example.com/i)).toBeInTheDocument();
    });
  });
});