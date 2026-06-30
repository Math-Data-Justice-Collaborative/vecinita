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
import { SetPasswordPage } from "@/pages/SetPasswordPage";

const mockGetSession = vi.fn();
const mockOnAuthStateChange = vi.fn();
const mockExchangeCodeForSession = vi.fn();
const mockUpdateUser = vi.fn();

function installSupabaseMock(session: object | null) {
  mockGetSession.mockResolvedValue({ data: { session } });
  mockExchangeCodeForSession.mockResolvedValue({ error: null });
  mockUpdateUser.mockResolvedValue({ error: null });
  mockOnAuthStateChange.mockImplementation(
    (callback: (event: string, nextSession: object | null) => void) => {
      if (session) {
        callback("INITIAL_SESSION", session);
      }
      return {
        data: { subscription: { unsubscribe: vi.fn() } },
      };
    },
  );
  setSupabaseClientForTests({
    auth: {
      getSession: mockGetSession,
      onAuthStateChange: mockOnAuthStateChange,
      exchangeCodeForSession: mockExchangeCodeForSession,
      updateUser: mockUpdateUser,
    },
  } as never);
}

describe("auth link callback (TC-106, TC-107, UJ-031/033)", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/accept-invite");
    window.location.hash = "";
  });

  afterEach(() => {
    cleanup();
    setSupabaseClientForTests(null);
    vi.useRealTimers();
  });

  it("accept-invite gates password form until session exists", async () => {
    window.location.hash = "#access_token=abc&refresh_token=def";
    installSupabaseMock({
      access_token: "abc",
      refresh_token: "def",
    });

    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="invite" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    expect(await screen.findByTestId("invite-password-form")).toBeInTheDocument();
  });

  it("accept-invite shows bilingual expired link error for otp_expired hash", async () => {
    window.location.hash =
      "#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired";
    installSupabaseMock(null);

    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="invite" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    expect(await screen.findByTestId("invite-link-expired")).toBeInTheDocument();
    expect(screen.queryByTestId("invite-password-form")).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(/expired/i);
  });

  it("reset-password shows expired link panel from hash error", async () => {
    window.history.replaceState({}, "", "/reset-password");
    window.location.hash = "#error=access_denied&error_code=otp_expired";
    installSupabaseMock(null);

    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="reset" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    expect(await screen.findByTestId("reset-link-expired")).toBeInTheDocument();
  });

  it("accept-invite without session shows verifying then invalid link state", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    installSupabaseMock(null);

    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="invite" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    expect(screen.getByRole("status")).toHaveTextContent(/verifying/i);
    await vi.advanceTimersByTimeAsync(10_000);
    expect(await screen.findByTestId("invite-link-invalid")).toBeInTheDocument();
  }, 15_000);

  it("accept-invite calls updateUser after session is ready", async () => {
    installSupabaseMock({ access_token: "token" });

    render(
      <LocaleProvider>
        <MemoryRouter>
          <SetPasswordPage variant="invite" />
        </MemoryRouter>
      </LocaleProvider>,
    );

    const form = await screen.findByTestId("invite-password-form");
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
