import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { RequireAuth } from './RequireAuth';

const useAuth = vi.fn();

vi.mock('./AuthContext', () => ({
  useAuth: () => useAuth(),
}));

function LoginLocationProbe() {
  const location = useLocation();
  return <div data-testid="login-search">{location.search}</div>;
}

describe('RequireAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state while session is resolving', () => {
    useAuth.mockReturnValue({ session: null, loading: true });

    render(
      <MemoryRouter initialEntries={['/secure']}>
        <RequireAuth>
          <div>Secret area</div>
        </RequireAuth>
      </MemoryRouter>,
    );

    expect(screen.getByText('Loading session...')).toBeInTheDocument();
  });

  it('redirects unauthenticated users with encoded return path', () => {
    useAuth.mockReturnValue({ session: null, loading: false });

    render(
      <MemoryRouter initialEntries={['/corpus?tab=jobs&name=hello world']}>
        <Routes>
          <Route
            path="/corpus"
            element={
              <RequireAuth>
                <div>Secret area</div>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<LoginLocationProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByTestId('login-search')).toHaveTextContent(
      '?redirect=%2Fcorpus%3Ftab%3Djobs%26name%3Dhello%20world',
    );
  });

  it('renders children when user is authenticated', () => {
    useAuth.mockReturnValue({ session: { token: 'token-1' }, loading: false });

    render(
      <MemoryRouter initialEntries={['/secure']}>
        <RequireAuth>
          <div>Secret area</div>
        </RequireAuth>
      </MemoryRouter>,
    );

    expect(screen.getByText('Secret area')).toBeInTheDocument();
  });
});
