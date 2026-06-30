import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { setSupabaseClientForTests } from "@/auth/supabaseClient";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { SetPasswordPage } from "@/pages/SetPasswordPage";

const mockResetPasswordForEmail = vi.fn();
const mockUpdateUser = vi.fn();

function buildSupabaseMock() {
  return {
    auth: {
      resetPasswordForEmail: mockResetPasswordForEmail,
      updateUser: mockUpdateUser,
    },
  };
}

describe("password reset flows (TC-093, UJ-033)", () => {
  beforeEach(() => {
    setSupabaseClientForTests(buildSupabaseMock() as never);
    mockResetPasswordForEmail.mockReset();
    mockUpdateUser.mockReset();
    mockResetPasswordForEmail.mockResolvedValue({ error: null });
    mockUpdateUser.mockResolvedValue({ error: null });
  });

  afterEach(() => {
    cleanup();
    setSupabaseClientForTests(null);
  });

  it("forgot-password shows success after reset email is sent", async () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("forgot-password-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "user@example.org" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /send reset link/i }),
    );

    expect(await screen.findByRole("status")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /send reset link/i }),
    ).not.toBeInTheDocument();
  });

  it("forgot-password surfaces Supabase errors", async () => {
    mockResetPasswordForEmail.mockResolvedValue({
      error: new Error("rate limited"),
    });

    render(
      <LocaleProvider>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("forgot-password-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "user@example.org" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /send reset link/i }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("rate limited");
  });

  it("forgot-password falls back when reset rejects with a non-Error", async () => {
    // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- exercises non-Error catch branch
    mockResetPasswordForEmail.mockRejectedValue("network down");

    render(
      <LocaleProvider>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("forgot-password-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "user@example.org" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /send reset link/i }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /sign in failed/i,
    );
  });

  it("forgot-password submits resetPasswordForEmail", async () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("forgot-password-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "user@example.org" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /send reset link/i }),
    );

    await waitFor(() => {
      expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
        "user@example.org",
        expect.objectContaining({
          redirectTo: expect.stringContaining("/reset-password") as string,
        }),
      );
    });
  });

  it("reset-password shows mismatch error before calling Supabase", async () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="reset" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("reset-password-form");
    fireEvent.change(within(form).getByLabelText(/^password$/i), {
      target: { value: "newpass123" },
    });
    fireEvent.change(within(form).getByLabelText(/confirm password/i), {
      target: { value: "different" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /update password/i }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(/match/i);
    expect(mockUpdateUser).not.toHaveBeenCalled();
  });

  it("reset-password surfaces update errors", async () => {
    mockUpdateUser.mockResolvedValue({
      error: new Error("weak password"),
    });

    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="reset" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("reset-password-form");
    fireEvent.change(within(form).getByLabelText(/^password$/i), {
      target: { value: "newpass123" },
    });
    fireEvent.change(within(form).getByLabelText(/confirm password/i), {
      target: { value: "newpass123" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /update password/i }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("weak password");
  });

  it("reset-password shows success state after update", async () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="reset" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("reset-password-form");
    fireEvent.change(within(form).getByLabelText(/^password$/i), {
      target: { value: "newpass123" },
    });
    fireEvent.change(within(form).getByLabelText(/confirm password/i), {
      target: { value: "newpass123" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /update password/i }),
    );

    expect(await screen.findByRole("status")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /update password/i }),
    ).not.toBeInTheDocument();
  });

  it("reset-password calls updateUser with matching passwords", async () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="reset" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("reset-password-form");
    fireEvent.change(within(form).getByLabelText(/^password$/i), {
      target: { value: "newpass123" },
    });
    fireEvent.change(within(form).getByLabelText(/confirm password/i), {
      target: { value: "newpass123" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /update password/i }),
    );

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith({ password: "newpass123" });
    });
  });

  it("accept-invite uses invite copy and updateUser", async () => {
    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="invite" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    expect(await screen.findByText(/accept invitation/i)).toBeInTheDocument();

    const form = screen.getByTestId("invite-password-form");
    fireEvent.change(within(form).getByLabelText(/^password$/i), {
      target: { value: "invitepass" },
    });
    fireEvent.change(within(form).getByLabelText(/confirm password/i), {
      target: { value: "invitepass" },
    });
    fireEvent.click(
      within(form).getByRole("button", { name: /update password/i }),
    );

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith({ password: "invitepass" });
    });
  });
});
