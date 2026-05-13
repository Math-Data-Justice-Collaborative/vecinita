import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';

const mocks = vi.hoisted(() => {
  const readStoredApiKeySession = vi.fn();
  const storeApiKeySession = vi.fn();
  const clearStoredApiKeySession = vi.fn();
  const validateApiKey = vi.fn();

  return {
    readStoredApiKeySession,
    storeApiKeySession,
    clearStoredApiKeySession,
    validateApiKey,
  };
});

vi.mock('./apiKeyAuth', () => ({
  buildApiKeyUser: (session: { preview: string }) => ({
    id: `api-key:${session.preview}`,
    email: null,
    displayName: `API key ${session.preview}`,
  }),
  readStoredApiKeySession: mocks.readStoredApiKeySession,
  storeApiKeySession: mocks.storeApiKeySession,
  clearStoredApiKeySession: mocks.clearStoredApiKeySession,
  validateApiKey: mocks.validateApiKey,
}));

function AuthHarness() {
  const { user, session, loading, signIn, signOut } = useAuth();

  return (
    <div>
      <p data-testid="loading">{String(loading)}</p>
      <p data-testid="user">{user?.id ?? 'none'}</p>
      <p data-testid="session">{session?.preview ?? 'none'}</p>
      <button onClick={() => signIn('token-abc-1234')}>sign-in</button>
      <button onClick={() => signOut()}>sign-out</button>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mocks.readStoredApiKeySession.mockReturnValue({
      token: 'token-1',
      preview: 'toke...en-1',
      createdAt: '2026-01-01T00:00:00.000Z',
    });
    mocks.storeApiKeySession.mockReturnValue({
      token: 'token-abc-1234',
      preview: 'toke...1234',
      createdAt: '2026-01-02T00:00:00.000Z',
    });
    mocks.validateApiKey.mockResolvedValue(undefined);
  });

  it('initializes session from local storage', async () => {
    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    expect(screen.getByTestId('user')).toHaveTextContent('api-key:toke...en-1');
    expect(screen.getByTestId('session')).toHaveTextContent('toke...en-1');
  });

  it('exposes sign-in and sign-out actions', async () => {
    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    await userEvent.click(screen.getByRole('button', { name: 'sign-in' }));
    await userEvent.click(screen.getByRole('button', { name: 'sign-out' }));

    expect(mocks.validateApiKey).toHaveBeenCalledWith('token-abc-1234');
    expect(mocks.storeApiKeySession).toHaveBeenCalledWith('token-abc-1234');
    expect(mocks.clearStoredApiKeySession).toHaveBeenCalledTimes(1);
  });
});
