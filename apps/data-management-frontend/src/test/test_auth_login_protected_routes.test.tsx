vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: () => true,
}));

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

import App from "@/App";
import { AuthProvider } from "@/auth/AuthContext";
import { setSupabaseClientForTests } from "@/auth/supabaseClient";
import { ThemeProvider } from "@/components/ThemeProvider";
import { LocaleProvider } from "vecinita-frontend-ui";

vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: () => true,
}));

const mockGetSession = vi.fn();
const mockOnAuthStateChange = vi.fn();
const mockSignOut = vi.fn();

function buildSupabaseMock(session: object | null) {
  mockGetSession.mockResolvedValue({ data: { session } });
  mockOnAuthStateChange.mockReturnValue({
    data: { subscription: { unsubscribe: vi.fn() } },
  });
  return {
    auth: {
      getSession: mockGetSession,
      onAuthStateChange: mockOnAuthStateChange,
      signInWithPassword: vi.fn(),
      signOut: mockSignOut,
    },
  };
}

function renderApp(initialPath = "/dashboard") {
  return render(
    <LocaleProvider>
      <ThemeProvider>
        <MemoryRouter initialEntries={[initialPath]}>
          <AuthProvider>
            <Routes>
              <Route path="/*" element={<App />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>
    </LocaleProvider>,
  );
}

describe("admin auth protected routes (TC-084)", () => {
  beforeEach(() => {
    setSupabaseClientForTests(null);
    vi.stubEnv("VITE_SUPABASE_URL", "https://test.supabase.co");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "test-publishable");
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "http://localhost:8002");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "key");
    mockSignOut.mockResolvedValue({ error: null });
  });

  it("redirects unauthenticated users to login", async () => {
    setSupabaseClientForTests(buildSupabaseMock(null) as never);
    renderApp("/dashboard");
    expect(await screen.findByTestId("login-form")).toBeInTheDocument();
  });

  it("renders dashboard when session exists and shows current user", async () => {
    setSupabaseClientForTests(
      buildSupabaseMock({
        access_token: "jwt-token",
        user: {
          id: "user-1",
          email: "admin@vecinita.admin",
          app_metadata: { role: "admin" },
        },
      }) as never,
    );
    renderApp("/dashboard");
    await waitFor(() => {
      expect(screen.getByTestId("admin-nav")).toBeInTheDocument();
    });
    expect(screen.getByTestId("admin-user-menu")).toHaveTextContent(
      "admin@vecinita.admin",
    );
  });

  it("logout clears session via signOut", async () => {
    setSupabaseClientForTests(
      buildSupabaseMock({
        access_token: "jwt-token",
        user: {
          id: "user-1",
          email: "admin@vecinita.admin",
          app_metadata: { role: "admin" },
        },
      }) as never,
    );
    renderApp("/dashboard");
    const menu = await screen.findByTestId("admin-user-menu");
    fireEvent.click(menu.querySelector("[data-testid='admin-sign-out']")!);
    expect(mockSignOut).toHaveBeenCalled();
  });
});
