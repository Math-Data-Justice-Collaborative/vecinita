import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
