import {
  cleanup,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { AuthProvider } from "@/auth/AuthContext";
import { useAuthLinkCallback } from "@/auth/useAuthLinkCallback";
import { setSupabaseClientForTests } from "@/auth/supabaseClient";
import { SetPasswordPage } from "@/pages/SetPasswordPage";

const mockGetSession = vi.fn();
const mockOnAuthStateChange = vi.fn();
const mockExchangeCodeForSession = vi.fn();
const mockUpdateUser = vi.fn();

function installRaceSupabaseMock() {
  const session = { access_token: "from-detect-session-in-url" };
  let sessionReady = false;

  mockGetSession.mockImplementation(async () => ({
    data: { session: sessionReady ? session : null },
  }));
  mockExchangeCodeForSession.mockImplementation(async () => {
    sessionReady = true;
    return {
      error: new Error("invalid flow state, no valid flow state found"),
    };
  });
  mockUpdateUser.mockResolvedValue({ error: null });
  mockOnAuthStateChange.mockImplementation(
    (callback: (event: string, nextSession: object | null) => void) => {
      if (sessionReady) {
        callback("SIGNED_IN", session);
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

describe("BUG-2026-06-30 PKCE double-exchange race (PR #110)", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/accept-invite?code=pkce-code");
    window.location.hash = "";
  });

  afterEach(() => {
    cleanup();
    setSupabaseClientForTests(null);
    vi.clearAllMocks();
  });

  it("useAuthLinkCallback stays ready when exchange fails but session already exists", async () => {
    installRaceSupabaseMock();

    const { result } = renderHook(() => useAuthLinkCallback());

    await waitFor(() => {
      expect(result.current.status).toBe("ready");
    });
    expect(mockExchangeCodeForSession).toHaveBeenCalledWith("pkce-code");
  });

  it("accept-invite shows password form when AuthProvider and detectSessionInUrl consumed code first", async () => {
    installRaceSupabaseMock();

    render(
      <LocaleProvider>
        <MemoryRouter>
          <AuthProvider>
            <SetPasswordPage variant="invite" />
          </AuthProvider>
        </MemoryRouter>
      </LocaleProvider>,
    );

    expect(
      await screen.findByTestId("invite-password-form"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("invite-link-invalid")).not.toBeInTheDocument();
  });
});
