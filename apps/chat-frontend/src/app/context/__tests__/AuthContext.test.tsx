import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';

const STORAGE_KEY = 'vecinita-admin-session';

async function loadAuthModule() {
  vi.resetModules();

  const mod = await import('../AuthContext');
  return mod;
}

function createWrapper(AuthProvider: ({ children }: { children: ReactNode }) => JSX.Element) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <AuthProvider>{children}</AuthProvider>;
  };
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('returns anonymous state when admin auth is disabled', async () => {
    vi.stubEnv('VITE_ADMIN_AUTH_ENABLED', 'false');

    const { AuthProvider, useAuth } = await loadAuthModule();

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(AuthProvider),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
    expect(result.current.isAnonymous).toBe(true);
    expect(result.current.isAdmin).toBe(false);
  });

  it('hydrates stored admin session', async () => {
    vi.stubEnv('VITE_ADMIN_AUTH_ENABLED', 'true');
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        email: 'admin@example.com',
        token: 'admin-token',
        createdAt: '2026-01-01T00:00:00.000Z',
      })
    );

    const { AuthProvider, useAuth } = await loadAuthModule();

    const { result, unmount } = renderHook(() => useAuth(), {
      wrapper: createWrapper(AuthProvider),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user?.email).toBe('admin@example.com');
    expect(result.current.isAdmin).toBe(true);

    unmount();
  });

  it('supports direct admin sign-in flow', async () => {
    vi.stubEnv('VITE_ADMIN_AUTH_ENABLED', 'true');
    vi.stubEnv('VITE_ADMIN_EMAIL', 'dev-admin@example.com');
    vi.stubEnv('VITE_ADMIN_PASSWORD', 'password123');
    vi.stubEnv('VITE_ADMIN_TOKEN', 'admin-token');

    const { AuthProvider, useAuth } = await loadAuthModule();

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(AuthProvider),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      const response = await result.current.signIn('dev-admin@example.com', 'password123');
      expect(response.error).toBeNull();
    });

    expect(result.current.user?.email).toBe('dev-admin@example.com');
    expect(result.current.isAdmin).toBe(true);
    expect(localStorage.getItem(STORAGE_KEY)).toContain('admin-token');

    await act(async () => {
      await result.current.signOut();
    });

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('returns sign-in error on invalid credentials', async () => {
    vi.stubEnv('VITE_ADMIN_AUTH_ENABLED', 'true');
    vi.stubEnv('VITE_ADMIN_EMAIL', 'dev-admin@example.com');
    vi.stubEnv('VITE_ADMIN_PASSWORD', 'password123');

    const { AuthProvider, useAuth } = await loadAuthModule();

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(AuthProvider),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      const response = await result.current.signIn('dev-admin@example.com', 'bad-password');
      expect(response.error).toBeTruthy();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAdmin).toBe(false);
  });

  it('disables self-service sign-up', async () => {
    vi.stubEnv('VITE_ADMIN_AUTH_ENABLED', 'true');
    vi.stubEnv('VITE_ADMIN_EMAIL', 'dev-admin@example.com');
    vi.stubEnv('VITE_ADMIN_PASSWORD', 'password123');

    const { AuthProvider, useAuth } = await loadAuthModule();

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(AuthProvider),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      const signUpResult = await result.current.signUp('user@example.com', 'pass');
      expect(signUpResult.error?.message).toMatch(/sign-up is disabled/i);
    });
  });

  it('throws when useAuth is called outside provider', async () => {
    const { useAuth } = await loadAuthModule();

    expect(() => renderHook(() => useAuth())).toThrow(
      'useAuth must be used within an AuthProvider'
    );
  });
});
