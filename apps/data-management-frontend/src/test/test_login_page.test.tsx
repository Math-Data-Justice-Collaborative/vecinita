import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { AuthProvider } from "@/auth/AuthContext";
import { setSupabaseClientForTests } from "@/auth/supabaseClient";
import { LoginPage } from "@/pages/LoginPage";

const mockGetSession = vi.fn();
const mockOnAuthStateChange = vi.fn();
const mockSignInWithPassword = vi.fn();

function buildSupabaseMock(session: object | null) {
  mockGetSession.mockResolvedValue({ data: { session } });
  mockOnAuthStateChange.mockReturnValue({
    data: { subscription: { unsubscribe: vi.fn() } },
  });
  return {
    auth: {
      getSession: mockGetSession,
      onAuthStateChange: mockOnAuthStateChange,
      signInWithPassword: mockSignInWithPassword,
      signOut: vi.fn(),
    },
  };
}

function renderLogin(initialPath = "/login") {
  return render(
    <LocaleProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={<div data-testid="dashboard" />}
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </LocaleProvider>,
  );
}

describe("LoginPage (F34)", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    setSupabaseClientForTests(null);
    vi.stubEnv("VITE_SUPABASE_URL", "https://test.supabase.co");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "test-publishable");
    mockSignInWithPassword.mockReset();
  });

  it("submits credentials via signInWithPassword", async () => {
    setSupabaseClientForTests(buildSupabaseMock(null) as never);
    mockSignInWithPassword.mockResolvedValue({ error: null });
    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: " admin@vecinita.admin " },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => {
      expect(mockSignInWithPassword).toHaveBeenCalledWith({
        email: "admin@vecinita.admin",
        password: "secret",
      });
    });
  });

  it("shows sign-in error message from Supabase", async () => {
    setSupabaseClientForTests(buildSupabaseMock(null) as never);
    mockSignInWithPassword.mockResolvedValue({
      error: new Error("Invalid credentials"),
    });
    renderLogin();
    const form = await screen.findByTestId("login-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "admin@vecinita.admin" },
    });
    fireEvent.change(within(form).getByLabelText(/password/i), {
      target: { value: "wrong" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /sign in/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid credentials",
    );
  });

  it("redirects authenticated users to dashboard", async () => {
    setSupabaseClientForTests(
      buildSupabaseMock({
        access_token: "jwt",
        user: {
          id: "u1",
          email: "admin@vecinita.admin",
          app_metadata: { role: "admin" },
        },
      }) as never,
    );
    renderLogin();
    expect(await screen.findByTestId("dashboard")).toBeInTheDocument();
  });

  it("redirects authenticated users to prior route from location state", async () => {
    setSupabaseClientForTests(
      buildSupabaseMock({
        access_token: "jwt",
        user: {
          id: "u1",
          email: "admin@vecinita.admin",
          app_metadata: { role: "admin" },
        },
      }) as never,
    );
    render(
      <LocaleProvider>
        <MemoryRouter
          initialEntries={[{ pathname: "/login", state: { from: "/jobs" } }]}
        >
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/jobs"
                element={<div data-testid="jobs-landing" />}
              />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </LocaleProvider>,
    );
    expect(await screen.findByTestId("jobs-landing")).toBeInTheDocument();
  });

  it("shows generic error when signIn throws non-Error", async () => {
    setSupabaseClientForTests({
      auth: {
        getSession: mockGetSession,
        onAuthStateChange: mockOnAuthStateChange,
        signInWithPassword: vi.fn().mockRejectedValue("nope"),
        signOut: vi.fn(),
      },
    } as never);
    mockGetSession.mockResolvedValue({ data: { session: null } });
    renderLogin();
    const form = await screen.findByTestId("login-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "admin@vecinita.admin" },
    });
    fireEvent.change(within(form).getByLabelText(/password/i), {
      target: { value: "wrong" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /sign in/i }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
