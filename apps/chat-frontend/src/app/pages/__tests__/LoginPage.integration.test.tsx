import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import LoginPage from '../LoginPage';

const mockNavigate = vi.fn();
const mockSignIn = vi.fn();

const authState = {
  user: null as { id: string } | null,
  isAdmin: false,
  loading: false,
};

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    signIn: (...args: unknown[]) => mockSignIn(...args),
    user: authState.user,
    isAdmin: authState.isAdmin,
    loading: authState.loading,
  }),
}));

describe('LoginPage integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authState.user = null;
    authState.isAdmin = false;
    authState.loading = false;
    mockSignIn.mockResolvedValue({ error: null });
  });

  it('renders login form and documents shortcut link', () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Admin Login' })).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Browse documents/i })).toHaveAttribute(
      'href',
      '/documents'
    );
  });

  it('submits credentials and calls signIn', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter
        initialEntries={['/login?redirect=/admin']}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <LoginPage />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');

    await user.clear(emailInput);
    await user.type(emailInput, 'admin@example.org');
    await user.clear(passwordInput);
    await user.type(passwordInput, 'secret-pass');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith('admin@example.org', 'secret-pass');
    });
  });

  it('shows sign-in errors returned by auth provider', async () => {
    const user = userEvent.setup();
    mockSignIn.mockResolvedValue({ error: { message: 'Invalid credentials' } });

    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <LoginPage />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');

    await user.clear(emailInput);
    await user.type(emailInput, 'admin@example.org');
    await user.clear(passwordInput);
    await user.type(passwordInput, 'wrong-pass');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
  });

  it('redirects admin users to requested destination', async () => {
    authState.user = { id: 'admin-1' };
    authState.isAdmin = true;

    render(
      <MemoryRouter
        initialEntries={['/login?redirect=/admin']}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <LoginPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin', { replace: true });
    });
  });
});
