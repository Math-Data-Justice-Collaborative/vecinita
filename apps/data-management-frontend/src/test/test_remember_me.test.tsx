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
import {
  REMEMBER_STORAGE_KEY,
  createRoutingStorage,
  persistRememberPreference,
  readRememberPreference,
  resetSupabaseClient,
  setSupabaseClientForTests,
} from "@/auth/supabaseClient";
import { LoginPage } from "@/pages/LoginPage";

const mockGetSession = vi.fn();
const mockOnAuthStateChange = vi.fn();
const mockSignInWithPassword = vi.fn();

function buildSupabaseMock() {
  mockGetSession.mockResolvedValue({ data: { session: null } });
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

function renderLogin() {
  return (
    <LocaleProvider>
      <MemoryRouter initialEntries={["/login"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </LocaleProvider>
  );
}

describe("remember-me (TC-091, UJ-032)", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    setSupabaseClientForTests(null);
    vi.stubEnv("VITE_SUPABASE_URL", "https://test.supabase.co");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "test-publishable");
    mockSignInWithPassword.mockReset();
  });

  afterEach(() => {
    cleanup();
    setSupabaseClientForTests(null);
    vi.unstubAllEnvs();
  });

  it("createRoutingStorage uses localStorage when remember is true", () => {
    const storage = createRoutingStorage(true);
    storage.setItem("k", "v");
    expect(localStorage.getItem("k")).toBe("v");
    expect(sessionStorage.getItem("k")).toBeNull();
  });

  it("createRoutingStorage uses sessionStorage when remember is false", () => {
    const storage = createRoutingStorage(false);
    storage.setItem("k", "v");
    expect(sessionStorage.getItem("k")).toBe("v");
    expect(localStorage.getItem("k")).toBeNull();
  });

  it("remember checkbox defaults to checked and persists preference on sign-in", async () => {
    setSupabaseClientForTests(buildSupabaseMock() as never);
    mockSignInWithPassword.mockResolvedValue({ error: null });

    render(renderLogin());

    const checkbox = await screen.findByTestId("remember-me");
    expect(checkbox).toBeChecked();

    const form = screen.getByTestId("login-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "admin@example.org" },
    });
    fireEvent.change(within(form).getByLabelText(/password/i), {
      target: { value: "secret" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(localStorage.getItem(REMEMBER_STORAGE_KEY)).toBe("true");
    });
    expect(mockSignInWithPassword).toHaveBeenCalled();
  });

  it("unchecked remember-me stores false preference", async () => {
    setSupabaseClientForTests(buildSupabaseMock() as never);
    mockSignInWithPassword.mockResolvedValue({ error: null });

    render(renderLogin());

    const checkbox = await screen.findByTestId("remember-me");
    fireEvent.click(checkbox);

    const form = screen.getByTestId("login-form");
    fireEvent.change(within(form).getByLabelText(/email/i), {
      target: { value: "admin@example.org" },
    });
    fireEvent.change(within(form).getByLabelText(/password/i), {
      target: { value: "secret" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(localStorage.getItem(REMEMBER_STORAGE_KEY)).toBe("false");
    });
  });

  it("readRememberPreference defaults to true", () => {
    expect(readRememberPreference()).toBe(true);
    persistRememberPreference(false);
    expect(readRememberPreference()).toBe(false);
  });

  it("resetSupabaseClient rebuilds client with routing storage", () => {
    const client = resetSupabaseClient(false);
    expect(client).toBeDefined();
  });
});
