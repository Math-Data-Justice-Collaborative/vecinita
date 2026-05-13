import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Login } from './Login';

const signIn = vi.fn();

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({
    signIn,
  }),
}));

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls auth sign-in with submitted credentials', async () => {
    signIn.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText(/api key/i), 'token-abc-1234');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(signIn).toHaveBeenCalledWith('token-abc-1234');
  });
});
